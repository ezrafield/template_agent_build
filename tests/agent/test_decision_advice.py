import json

import pytest

from scripts.decision_advice import DecisionCatalog, JevProvider


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
