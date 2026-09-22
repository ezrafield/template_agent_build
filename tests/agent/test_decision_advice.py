import json
import urllib.error
from pathlib import Path

import pytest

from eval.advice import run_advice_eval
from eval.advice.run_advice_eval import summarize, validate_cases
from scripts.decision_advice import (
    DecisionAdvice, DecisionCatalog, JevProvider, load_catalog, parse_response, _NoRedirect,
)
from scripts.task_context_engine import build_task_context


CATALOG = DecisionCatalog({"bug-fix": "Fix a bug"}, {"test-debug-loop": "Reproduce a failing test"})


def response():
    return {"model": "jev-1.13.0", "answers": {
        "route": {"type": "choice", "choice": "bug-fix", "confidence": 0.7,
                  "probabilities": {"bug-fix": 0.8, "insufficient_information": 0.1, "out_of_scope": 0.1}},
        "skill:test-debug-loop": {"type": "noul", "noul": 0.9},
        "clarification": {"type": "noul", "noul": 0.2}}, "usage": {"input_tokens": 50, "output_tokens": 8}}


def test_no_live_no_key_never_calls_transport(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    def forbidden(*args):
        pytest.fail("transport must not be called")
    provider = JevProvider(transport=forbidden)
    assert provider.advise("task", CATALOG).error_code == "live_not_enabled"
    assert provider.advise("task", CATALOG, live=True).error_code == "missing_credentials"


def test_live_request_is_redacted_bounded_and_typed():
    calls = []
    def transport(body, key, timeout):
        calls.append((body, key, timeout))
        return response()
    result = JevProvider(api_key="test-key", transport=transport).advise("Fix bug token=do-not-send", CATALOG, live=True)
    assert result.status == "ok" and result.route == "bug-fix"
    assert result.usage == {"input_tokens": 50, "output_tokens": 8}
    assert len(calls) == 1 and calls[0][2] == 10
    assert "do-not-send" not in json.dumps(calls[0][0])
    assert set(calls[0][0]) == {"state", "model", "questions"}
    assert result.confidence == 0.7 and result.route_probabilities["bug-fix"] == 0.8


def test_direct_catalog_is_redacted_at_transport_boundary():
    catalog = DecisionCatalog({"bug-fix": "token=route-secret"}, {"test-debug-loop": "password=skill-secret"})
    def transport(body, key, timeout):
        outbound = json.dumps(body)
        assert all(value not in outbound for value in ("task-secret", "route-secret", "skill-secret"))
        return response()
    result = JevProvider(api_key="test", transport=transport).advise("token=task-secret", catalog, live=True)
    assert result.status == "ok"


@pytest.mark.parametrize("change", [
    lambda r: r["answers"]["route"].update(choice="unknown"),
    lambda r: r["answers"]["route"]["probabilities"].update({"bug-fix": -1}),
    lambda r: r["answers"]["route"]["probabilities"].update({"bug-fix": float("nan")}),
    lambda r: r["answers"]["route"]["probabilities"].update({"bug-fix": True}),
    lambda r: r["answers"]["route"]["probabilities"].update({"bug-fix": 0.3}),
    lambda r: r["answers"]["route"].update(choice="out_of_scope"),
    lambda r: r["answers"]["clarification"].update(type="choice"),
    lambda r: r["answers"].pop("skill:test-debug-loop"),
    lambda r: r.update(usage={"input_tokens": -1}),
])
def test_malformed_answers_are_unavailable_without_echoing(change):
    data = response()
    change(data)
    result = JevProvider(api_key="secret", transport=lambda *args: data).advise("task", CATALOG, live=True)
    assert result.status == "unavailable" and result.error_code == "invalid_response"


@pytest.mark.parametrize("error,code", [
    (urllib.error.HTTPError("url", 401, "secret", {}, None), "authentication"),
    (urllib.error.HTTPError("url", 429, "secret", {}, None), "rate_limit"),
    (urllib.error.HTTPError("url", 500, "secret", {}, None), "http_error"),
    (TimeoutError("secret"), "network_error"),
    (urllib.error.URLError("secret"), "network_error"),
])
def test_transport_failure_no_retry_no_credential_echo(error, code):
    calls = []
    def transport(*args):
        calls.append(1)
        raise error
    result = JevProvider(api_key="secret", transport=transport).advise("task", CATALOG, live=True)
    assert result.error_code == code and "secret" not in str(result)
    assert len(calls) == 1


def test_missing_usage_unknown_and_failed_trials_count():
    data = response()
    data.pop("usage")
    advice = parse_response(data, CATALOG)
    assert advice.usage is None
    cases = [{"route": "bug-fix", "skills": ["test-debug-loop"], "clarification": False}] * 2
    metrics = summarize(cases, [advice, DecisionAdvice("unavailable")])
    assert metrics["attempted"] == 2 and metrics["route_accuracy_all_attempts"] == 0.5
    assert metrics["unavailable"] == 1 and metrics["billed_cost"] is None
    assert metrics["route_brier"] == pytest.approx(0.06)


def test_catalog_fixtures_valid_and_advice_cannot_change_context():
    root = Path(__file__).resolve().parents[2]
    catalog = load_catalog(root)
    cases = json.loads((root / "eval/advice/cases.json").read_text(encoding="utf-8"))
    assert validate_cases(cases, catalog) == []
    before = build_task_context("fix a bug", root, use_search=False, generated_at="fixed")
    JevProvider(api_key="test", transport=lambda *args: response()).advise("task", CATALOG, live=True)
    after = build_task_context("fix a bug", root, use_search=False, generated_at="fixed")
    assert before == after


def test_bad_fixture_labels_are_rejected():
    data = {"version": 1, "label_source": "review", "cases": [
        {"id": "bad", "task": "x", "route": "invented", "skills": [], "clarification": False}]}
    assert "unknown route" in validate_cases(data, CATALOG)[0]


def test_report_contains_no_task_or_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(run_advice_eval, "ROOT", tmp_path)
    monkeypatch.setattr(run_advice_eval, "load_catalog", lambda root: CATALOG)
    folder = tmp_path / "eval/advice"
    folder.mkdir(parents=True)
    task = "Fix the private parser token=secret-input"
    (folder / "cases.json").write_text(json.dumps({"version": 1, "label_source": "test", "cases": [
        {"id": "test", "task": task, "route": "bug-fix", "skills": ["test-debug-loop"], "clarification": False}]}))
    monkeypatch.setattr(run_advice_eval, "JevProvider", lambda **kwargs: JevProvider(api_key="secret-key", transport=lambda *args: response()))
    assert run_advice_eval.main(["--live"]) == 0
    report = next((tmp_path / ".agent/traces/evals").glob("*.json")).read_text()
    assert task not in report and "secret-input" not in report and "secret-key" not in report
    assert json.loads(report)["mode"] == "shadow"


def test_redirect_refused_and_invalid_model_not_sent():
    with pytest.raises(urllib.error.HTTPError):
        _NoRedirect().redirect_request(type("R", (), {"full_url": "https://api.typesafe.ai/v1/systemone"})(), None, 302, "redirect", {}, "https://example.com")
    with pytest.raises(ValueError):
        JevProvider(model="token=secret")
