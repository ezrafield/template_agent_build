import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts import run_agent_hook
from scripts.enable_codex_guardrails import enable


def test_normal_prompt_is_silent(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_agent_hook.handle_user_prompt({"prompt": "Explain the API route."}) == 0
    assert capsys.readouterr().out == ""


def test_secret_prompt_is_blocked_without_echo(capsys: pytest.CaptureFixture[str]) -> None:
    secret = "sk-" + "A" * 48

    assert run_agent_hook.handle_user_prompt({"prompt": f"Use {secret} here."}) == 0

    output = capsys.readouterr().out
    assert json.loads(output)["decision"] == "block"
    assert secret not in output


def test_stop_hook_active_prevents_validation_loop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(run_agent_hook, "changed_files", lambda root: (_ for _ in ()).throw(AssertionError()))

    assert run_agent_hook.handle_stop({"stop_hook_active": True}, tmp_path) == 0
    assert capsys.readouterr().out == ""


def test_stop_hook_continues_after_failed_agent_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(run_agent_hook, "changed_files", lambda root: ["AGENTS.md"])
    monkeypatch.setattr(
        run_agent_hook.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 1, "ERROR: invalid agent asset", ""),
    )

    assert run_agent_hook.handle_stop({"stop_hook_active": False}, tmp_path) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["decision"] == "block"
    assert "invalid agent asset" in output["reason"]


def test_guardrail_enablement_generates_local_files_and_refuses_overwrite(tmp_path: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    templates = tmp_path / ".codex" / "templates"
    templates.mkdir(parents=True)
    (templates / "hooks.json").write_text(
        (source_root / ".codex" / "templates" / "hooks.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (templates / "default.rules").write_text(
        (source_root / ".codex" / "templates" / "default.rules").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    handler = tmp_path / "scripts" / "run_agent_hook.py"
    handler.parent.mkdir(parents=True)
    handler.write_text("# test handler\n", encoding="utf-8")

    hooks, rules = enable(tmp_path)

    rendered = json.loads(hooks.read_text(encoding="utf-8"))
    handler_config = rendered["hooks"]["SessionStart"][0]["hooks"][0]
    command = handler_config["commandWindows"] if os.name == "nt" else handler_config["command"]
    assert str(handler) in command
    assert rules.is_file()
    nested = tmp_path / "nested" / "working-directory"
    nested.mkdir(parents=True)
    result = subprocess.run(
        command,
        cwd=nested,
        input=json.dumps({"hook_event_name": "SessionStart", "source": "startup"}),
        shell=True,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    with pytest.raises(FileExistsError):
        enable(tmp_path)
