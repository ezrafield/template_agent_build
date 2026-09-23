import pytest

from eval.skills import run_skill_routing_eval as routing


def test_default_never_discovers_or_invokes_codex(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def forbidden(*args, **kwargs):
        pytest.fail("Offline fixture validation must not discover or invoke Codex.")

    monkeypatch.setattr(routing.shutil, "which", forbidden)
    monkeypatch.setattr(routing.subprocess, "run", forbidden)
    monkeypatch.setattr(routing, "route_case", forbidden)
    assert routing.main([]) == 0
    assert "Skill routing fixtures valid: 20 cases" in capsys.readouterr().out
