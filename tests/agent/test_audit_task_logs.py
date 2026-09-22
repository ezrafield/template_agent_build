import pytest

from scripts.audit_task_logs import CHECKPOINT_FIELDS, REQUIRED_HEADINGS, missing_requirements


def checkpoint() -> str:
    values = {
        "Linked plan": ".agent/plans/active/example.md",
        "Completed acceptance criteria": "Input validation checked; see linked plan",
        "Outstanding material findings": "none",
        "Review independence": "separate agent",
        "Verified revision and dirty-file state": "abc123 with local changes listed in plan",
        "Verification link or new checks/results": "linked plan, Verification section",
        "External effects already performed": "none",
        "Next action and checks invalidated by later edits": "resume documentation; rerun affected checks",
    }
    return "# Task\n\n## Review And Checkpoint\n" + "\n".join(f"- {key}: {value}" for key, value in values.items())


def test_legacy_audit_headings_remain_accepted():
    assert missing_requirements("\n\n".join(REQUIRED_HEADINGS)) == []


def test_concise_checkpoint_can_link_plan_and_verification_without_duplicate_sections():
    assert missing_requirements(checkpoint()) == []


@pytest.mark.parametrize("label", CHECKPOINT_FIELDS)
def test_concise_checkpoint_requires_each_resume_field(label):
    text = "\n".join(line for line in checkpoint().splitlines() if not line.startswith(f"- {label}:"))
    assert any(label in error for error in missing_requirements(text))


def test_checkpoint_rejects_unfilled_values_and_fields_outside_section():
    text = checkpoint().replace("- Linked plan: .agent/plans/active/example.md", "- Linked plan: TODO")
    assert any("Linked plan" in error for error in missing_requirements(text))
    assert missing_requirements("## Review And Checkpoint\n\n## Other\n" + checkpoint().split("## Review And Checkpoint\n")[1])
