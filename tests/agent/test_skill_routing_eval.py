import json
import subprocess
from pathlib import Path

import pytest

from eval.skills import run_skill_routing_eval as routing


def test_live_timeout_is_forwarded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(*args, **kwargs):
        assert kwargs["timeout"] == 17
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(routing.subprocess, "run", fake_run)
    with pytest.raises(subprocess.TimeoutExpired):
        routing.route_case("codex", tmp_path, {"prompt": "Fix bug"}, {"safe-implementation"}, "test-model", 17)


@pytest.mark.parametrize("arguments", [[], ["--validate-only"], ["--model", "test-model"], ["--limit", "1", "--timeout", "1"]])
def test_offline_modes_never_discover_or_invoke_codex(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("Offline fixture validation must not discover or invoke Codex.")

    monkeypatch.setattr(routing.shutil, "which", forbidden)
    monkeypatch.setattr(routing.subprocess, "run", forbidden)
    monkeypatch.setattr(routing, "route_case", forbidden)
    assert routing.main(arguments) == 0
    assert "Skill routing fixtures valid: 20 cases" in capsys.readouterr().out


@pytest.mark.parametrize(
    "arguments, message",
    [
        (["--live"], "--live requires an explicit non-empty --model"),
        (["--live", "--model", ""], "--live requires an explicit non-empty --model"),
        (["--live", "--model", "  "], "--live requires an explicit non-empty --model"),
        (["--live", "--validate-only", "--model", "test-model"], "not allowed with argument --live"),
    ],
)
def test_invalid_live_opt_in_fails_before_codex_discovery(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    message: str,
) -> None:
    monkeypatch.setattr(routing.shutil, "which", lambda *args: pytest.fail("Invalid options must not discover Codex."))
    with pytest.raises(SystemExit) as exc:
        routing.main(arguments)
    assert exc.value.code == 2
    assert message in capsys.readouterr().err


def test_explicit_live_model_and_limit_reach_codex(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routing.shutil, "which", lambda command: "fake-codex")
    calls = []

    def fake_run(arguments, **kwargs):
        calls.append(arguments)
        assert arguments[arguments.index("--model") + 1] == "test-model"
        assert arguments[arguments.index("--sandbox") + 1] == "read-only"
        assert kwargs["timeout"] == 19
        message = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"selected_skills": ["safe-implementation"]})}}
        return subprocess.CompletedProcess(arguments, 0, json.dumps(message), "")

    monkeypatch.setattr(routing.subprocess, "run", fake_run)
    assert routing.main(["--live", "--model", "test-model", "--limit", "1", "--timeout", "19"]) == 0
    assert len(calls) == 1


def test_live_missing_codex_is_explicit(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(routing.shutil, "which", lambda command: None)
    assert routing.main(["--live", "--model", "test-model"]) == 2
    assert "requires an authenticated Codex CLI" in capsys.readouterr().err


def test_failed_cases_count_as_recall_misses(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(routing.shutil, "which", lambda command: "fake-codex")
    count = 0

    def fake_route(codex, root, case, known, model, timeout):
        nonlocal count
        count += 1
        if count == 1:
            return set(case["expected"])
        raise subprocess.TimeoutExpired("codex", timeout)

    monkeypatch.setattr(routing, "route_case", fake_route)
    assert routing.main(["--live", "--model", "test-model", "--limit", "2", "--timeout", "1"]) == 1
    captured = capsys.readouterr()
    assert "completed_cases=1" in captured.out
    assert "failed_cases=1" in captured.out
    assert "recall=1.000" not in captured.out
    assert "timed out after 1s (no retry)" in captured.err


def test_failed_live_case_is_counted_without_retry(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(routing.shutil, "which", lambda command: "fake-codex")
    count = 0

    def fake_route(*args):
        nonlocal count
        count += 1
        raise RuntimeError("fixture runner failed")

    monkeypatch.setattr(routing, "route_case", fake_route)
    assert routing.main(["--live", "--model", "test-model", "--limit", "1"]) == 1
    captured = capsys.readouterr()
    assert count == 1
    assert "completed_cases=0" in captured.out and "failed_cases=1" in captured.out
    assert "recall=0.000" in captured.out
    assert "fixture runner failed" in captured.err


@pytest.mark.parametrize("arguments", [["--validate-only", "--timeout", "0"], ["--limit", "0"]])
def test_invalid_limits_are_rejected(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        routing.main(arguments)
    assert exc.value.code == 2
