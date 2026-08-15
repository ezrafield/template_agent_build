import argparse
import json
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

try:
    from scripts.task_context_engine import validate_route_manifest
except ImportError:  # pragma: no cover - direct script execution path
    from task_context_engine import validate_route_manifest  # type: ignore


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ROOT_TARGET_BYTES = 4 * 1024
ROOT_MAX_BYTES = 8 * 1024
NESTED_MAX_BYTES = 4 * 1024
CHAIN_WARN_BYTES = 16 * 1024
CHAIN_MAX_BYTES = 20 * 1024
SKILL_MAX_BYTES = 4 * 1024
SKILL_DESCRIPTION_MAX_CHARS = 300
EXPECTED_SKILL_COUNT = 10
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PLAN_RECORD_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
PLAN_REQUIRED_HEADINGS = {
    "Metadata",
    "Goal",
    "Why This Strategy",
    "Scope",
    "Success Signals",
    "Risks And Assumptions",
    "Outcome And Evidence",
    "Reflection",
}
PLAN_LIFECYCLE_DIRECTORIES = ("active", "backlog", "completed", "reports")
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".agentkit",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}
REQUIRED_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "AGENTS.override.md.example",
    "agentkit-manifest.json",
    "docs/agent/INDEX.md",
    "docs/agent/context-routes.json",
    "docs/agent/CODEMAP.md",
    "docs/agent/CODE_SEARCH.md",
    "docs/agent/CONTEXT_ROUTER.md",
    "docs/agent/COMMAND_OUTPUT_POLICY.md",
    "docs/agent/AGENTS_AND_SKILLS.md",
    "docs/agent/CODEX_CUSTOMIZATION.md",
    "docs/adr/0003-codex-agent-system.md",
    "docs/adr/0004-task-context-compiler.md",
    "docs/agent/TOOLS.md",
    "docs/agent/MCPS.md",
    "docs/agent/MEMORY_POLICY.md",
    "docs/agent/MEMORY_RETRIEVAL.md",
    "docs/agent/MEMORY_PROMOTION_RULES.md",
    "docs/agent/SOURCE_UNDERSTANDING.md",
    ".agent/memory/index.json",
    ".agent/plans/template.md",
    ".codex/templates/hooks.json",
    ".codex/templates/default.rules",
    "scripts/agentkit_installer.py",
    "scripts/enable_codex_guardrails.py",
    "scripts/run_agent_hook.py",
    "scripts/task_context.py",
    "scripts/task_context_engine.py",
    "eval/context/golden_tasks.json",
    "eval/context/run_task_context_eval.py",
}


@dataclass
class ValidationReport:
    details: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def detail(self, message: str) -> None:
        self.details.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip_directory(path: Path, root: Path) -> bool:
    if path.name in IGNORED_DIRECTORY_NAMES:
        return True
    rel = relative(path, root) if path != root else ""
    return rel.startswith(".agent/context-cache") or rel.startswith("tools/agent/") and any(
        part in {".venv", "node_modules", ".uv-cache", ".npm-cache", ".hf-cache", "bin"}
        for part in path.parts
    )


def load_fallback_names(root: Path) -> list[str]:
    config = root / ".codex" / "config.toml"
    if not config.exists():
        return []
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    values = data.get("project_doc_fallback_filenames", [])
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value]


def instruction_candidates(directory: Path, fallback_names: list[str]) -> list[Path]:
    names = ["AGENTS.override.md", "AGENTS.md", *fallback_names]
    return [directory / name for name in names if (directory / name).is_file()]


def select_instruction_file(directory: Path, fallback_names: list[str]) -> Path | None:
    candidates = instruction_candidates(directory, fallback_names)
    return candidates[0] if candidates else None


def discover_instruction_chain(root: Path, cwd: Path, fallback_names: list[str] | None = None) -> list[Path]:
    root = root.resolve()
    cwd = cwd.resolve()
    try:
        parts = cwd.relative_to(root).parts
    except ValueError as exc:
        raise ValueError(f"{cwd} is outside {root}") from exc

    fallback_names = fallback_names if fallback_names is not None else load_fallback_names(root)
    directories = [root]
    current = root
    for part in parts:
        current = current / part
        directories.append(current)

    return [selected for directory in directories if (selected := select_instruction_file(directory, fallback_names))]


def find_instruction_files(root: Path, fallback_names: list[str]) -> list[Path]:
    names = {"AGENTS.md", "AGENTS.override.md", *fallback_names}
    found: list[Path] = []
    for directory, directory_names, file_names in os.walk(root):
        directory_path = Path(directory)
        directory_names[:] = [
            name
            for name in directory_names
            if not should_skip_directory(directory_path / name, root)
        ]
        found.extend(directory_path / name for name in file_names if name in names)
    return sorted(found)


def exact_duplicate_lines(paths: list[Path]) -> list[str]:
    occurrences: dict[str, int] = {}
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            normalized = line.strip()
            if len(normalized) < 16 or normalized.startswith("#"):
                continue
            occurrences[normalized] = occurrences.get(normalized, 0) + 1
    return sorted(line for line, count in occurrences.items() if count > 1)


def validate_instructions(root: Path, report: ValidationReport) -> None:
    fallback_names = load_fallback_names(root)
    files = find_instruction_files(root, fallback_names)
    if not files:
        report.error("No project instruction files were found.")
        return

    candidate_directories = {root, *(path.parent for path in files)}
    selected_at_level: set[Path] = set()
    for directory in sorted(candidate_directories):
        candidates = instruction_candidates(directory, fallback_names)
        if not candidates:
            continue
        selected_at_level.add(candidates[0])
        if len(candidates) > 1:
            report.detail(
                f"Instruction precedence {relative(directory, root) or '.'}: "
                f"selected {candidates[0].name}; ignored {', '.join(path.name for path in candidates[1:])}."
            )

    for path in files:
        size = len(path.read_bytes())
        rel = relative(path, root)
        limit = ROOT_MAX_BYTES if path.parent == root else NESTED_MAX_BYTES
        report.detail(f"Instruction file {rel}: {size} UTF-8 bytes.")
        if path.parent == root and path.name == "AGENTS.md" and size > ROOT_TARGET_BYTES:
            report.warn(f"{rel} is above the {ROOT_TARGET_BYTES}-byte target ({size} bytes).")
        if size > limit:
            report.error(f"{rel} exceeds its {limit}-byte limit ({size} bytes).")

    max_chain: tuple[int, Path, list[Path]] = (0, root, [])
    for directory in candidate_directories:
        chain = discover_instruction_chain(root, directory, fallback_names)
        size = sum(len(path.read_bytes()) for path in chain)
        if size > max_chain[0]:
            max_chain = (size, directory, chain)
        duplicates = exact_duplicate_lines(chain)
        for line in duplicates:
            report.warn(
                f"Exact duplicate instruction in chain to {relative(directory, root) or '.'}: {line}"
            )

    chain_size, directory, chain = max_chain
    sources = ", ".join(relative(path, root) for path in chain)
    report.detail(
        f"Maximum project instruction chain: {chain_size} bytes to "
        f"{relative(directory, root) or '.'} ({sources})."
    )
    if chain_size > CHAIN_MAX_BYTES:
        report.error(f"Maximum instruction chain exceeds {CHAIN_MAX_BYTES} bytes.")
    elif chain_size > CHAIN_WARN_BYTES:
        report.warn(f"Maximum instruction chain exceeds the {CHAIN_WARN_BYTES}-byte warning threshold.")


def parse_skill_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("missing or malformed YAML frontmatter")

    metadata: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line or raw_line[:1].isspace():
            raise ValueError(f"unsupported frontmatter line: {raw_line}")
        key, value = raw_line.split(":", 1)
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(value[0]):
            value = value[1:-1]
        metadata[key.strip()] = value
    return metadata, match.group(2)


def extract_quoted_yaml_value(text: str, key: str) -> str | None:
    match = re.search(rf'^\s+{re.escape(key)}:\s+"([^"]*)"\s*$', text, re.MULTILINE)
    return match.group(1) if match else None


def validate_openai_yaml(path: Path, skill_name: str, report: ValidationReport) -> None:
    rel = path.as_posix()
    if not path.exists():
        report.error(f"Missing skill UI metadata: {rel}.")
        return
    text = path.read_text(encoding="utf-8")
    display_name = extract_quoted_yaml_value(text, "display_name")
    short_description = extract_quoted_yaml_value(text, "short_description")
    default_prompt = extract_quoted_yaml_value(text, "default_prompt")
    if not display_name:
        report.error(f"{rel} must define a quoted interface.display_name.")
    if not short_description or not 25 <= len(short_description) <= 64:
        report.error(f"{rel} short_description must contain 25-64 characters.")
    if not default_prompt or f"${skill_name}" not in default_prompt:
        report.error(f"{rel} default_prompt must mention ${skill_name}.")
    if not re.search(r"^\s+allow_implicit_invocation:\s+true\s*$", text, re.MULTILINE):
        report.error(f"{rel} must enable implicit invocation.")


def validate_manifest_and_skills(root: Path, report: ValidationReport) -> dict:
    manifest_path = root / "agentkit-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.error(f"Cannot load agentkit-manifest.json: {exc}")
        return {}

    if manifest.get("schema_version") != 2:
        report.error("agentkit-manifest.json must use schema_version 2.")
    if manifest.get("version") != "0.4.0":
        report.error("agentkit-manifest.json must declare version 0.4.0.")

    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        report.error("Manifest runtime metadata is missing.")
        runtime = {}
    for field_name in ("required_commands", "optional_commands", "optional_integrations"):
        if not isinstance(runtime.get(field_name), list):
            report.error(f"Manifest runtime.{field_name} must be a list.")
    runtime_required = set(runtime.get("required_commands", []))
    runtime_optional = set(runtime.get("optional_commands", []))
    runtime_integrations = set(runtime.get("optional_integrations", []))
    ci_version = runtime.get("codex_cli_ci_version")
    workflow = root / ".github" / "workflows" / "agent-doc-check.yml"
    if not isinstance(ci_version, str) or not ci_version:
        report.error("Manifest runtime.codex_cli_ci_version must be a non-empty string.")
    elif workflow.is_file():
        workflow_text = workflow.read_text(encoding="utf-8")
        if f"@openai/codex@{ci_version}" not in workflow_text:
            report.error("Agent CI must install the Codex version pinned by the manifest.")
        for required_ci_command in (
            "python -m pytest tests/agent -q",
            "python eval/context/run_task_context_eval.py",
        ):
            if required_ci_command not in workflow_text:
                report.error(f"Agent CI must run `{required_ci_command}`.")

    entries = manifest.get("skills")
    if not isinstance(entries, list):
        report.error("Manifest skills must be a list.")
        entries = []

    discovered = {
        path.parent.name: path.parent
        for path in (root / ".agents" / "skills").glob("*/SKILL.md")
    }
    manifest_names: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            report.error("Every manifest skill entry must be an object.")
            continue
        name = entry.get("name")
        path_value = entry.get("path")
        if not isinstance(name, str) or not isinstance(path_value, str):
            report.error("Every manifest skill requires string name and path values.")
            continue
        manifest_names.append(name)
        expected_path = f".agents/skills/{name}"
        if path_value != expected_path:
            report.error(f"Skill {name} path must be {expected_path}.")
        if entry.get("required") is not True:
            report.error(f"Skill {name} must be marked required in v0.4.0.")
        if entry.get("hosts") != ["codex"]:
            report.error(f"Skill {name} must declare hosts [\"codex\"].")
        for field_name in ("required_commands", "optional_commands"):
            values = entry.get(field_name)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                report.error(f"Skill {name} {field_name} must be a string list.")
        required = set(entry.get("required_commands", []))
        optional = set(entry.get("optional_commands", []))
        if required & optional:
            report.error(f"Skill {name} has commands classified as both required and optional.")
        if not required <= runtime_required:
            report.error(f"Skill {name} has required commands missing from runtime metadata.")
        if not optional <= runtime_optional:
            report.error(f"Skill {name} has optional commands missing from runtime metadata.")
        integrations = entry.get("optional_integrations", [])
        if not isinstance(integrations, list) or not all(isinstance(value, str) for value in integrations):
            report.error(f"Skill {name} optional_integrations must be a string list when present.")
        elif not set(integrations) <= runtime_integrations:
            report.error(f"Skill {name} has optional integrations missing from runtime metadata.")

    if len(manifest_names) != len(set(manifest_names)):
        report.error("Manifest skill names must be unique.")
    if len(discovered) != EXPECTED_SKILL_COUNT:
        report.error(f"Expected exactly {EXPECTED_SKILL_COUNT} skills; found {len(discovered)}.")
    if set(discovered) != set(manifest_names):
        report.error(
            "Manifest/discovered skill mismatch: "
            f"manifest={sorted(manifest_names)}, discovered={sorted(discovered)}."
        )

    parsed_names: list[str] = []
    for directory_name, skill_root in sorted(discovered.items()):
        skill_md = skill_root / "SKILL.md"
        rel = relative(skill_md, root)
        size = len(skill_md.read_bytes())
        report.detail(f"Skill {directory_name}: {size} UTF-8 bytes.")
        if size > SKILL_MAX_BYTES:
            report.error(f"{rel} exceeds {SKILL_MAX_BYTES} bytes.")
        try:
            metadata, body = parse_skill_frontmatter(skill_md)
        except ValueError as exc:
            report.error(f"{rel}: {exc}.")
            continue
        if set(metadata) != {"name", "description"}:
            report.error(f"{rel} frontmatter must contain only name and description.")
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        parsed_names.append(name)
        if name != directory_name or not SKILL_NAME_RE.fullmatch(name):
            report.error(f"{rel} name must match its hyphen-case directory name.")
        if not description or len(description) > SKILL_DESCRIPTION_MAX_CHARS:
            report.error(
                f"{rel} description must contain 1-{SKILL_DESCRIPTION_MAX_CHARS} characters."
            )
        if not body.strip():
            report.error(f"{rel} must contain skill instructions after frontmatter.")
        validate_openai_yaml(skill_root / "agents" / "openai.yaml", name, report)

    if len(parsed_names) != len(set(parsed_names)):
        report.error("Skill frontmatter names must be unique.")

    templates = manifest.get("guardrail_templates", [])
    if not isinstance(templates, list):
        report.error("Manifest guardrail_templates must be a list.")
    else:
        for item in templates:
            if not isinstance(item, str) or not (root / item).is_file():
                report.error(f"Missing guardrail template: {item}.")
    return manifest


def validate_guardrail_templates(root: Path, report: ValidationReport) -> None:
    hooks_path = root / ".codex" / "templates" / "hooks.json"
    try:
        hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.error(f"Invalid hooks template: {exc}")
    else:
        events = set(hooks.get("hooks", {})) if isinstance(hooks.get("hooks"), dict) else set()
        expected = {"SessionStart", "UserPromptSubmit", "Stop"}
        if events != expected:
            report.error(f"Hook template events must be exactly {sorted(expected)}.")

    rules_path = root / ".codex" / "templates" / "default.rules"
    try:
        rules = rules_path.read_text(encoding="utf-8")
    except OSError as exc:
        report.error(f"Cannot read rules template: {exc}")
    else:
        if re.search(r'decision\s*=\s*"allow"', rules):
            report.error("The opt-in rules template must not contain allow decisions.")
        if 'decision = "prompt"' not in rules or 'decision = "forbidden"' not in rules:
            report.error("The rules template must contain prompt and forbidden examples.")


def validate_required_files(root: Path, report: ValidationReport) -> None:
    for required in sorted(REQUIRED_FILES):
        if not (root / required).exists():
            report.error(f"Missing required agent asset: {required}.")


def markdown_h2_headings(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }


def validate_plan_system(root: Path, report: ValidationReport) -> None:
    plan_root = root / ".agent" / "plans"
    for name in PLAN_LIFECYCLE_DIRECTORIES:
        if not (plan_root / name).is_dir():
            report.error(f"Missing plan lifecycle directory: .agent/plans/{name}.")

    template = plan_root / "template.md"
    paths = [template] if template.is_file() else []
    for lifecycle in ("active", "backlog", "completed"):
        directory = plan_root / lifecycle
        if directory.is_dir():
            paths.extend(sorted(directory.glob("*.md")))

    for path in paths:
        rel = relative(path, root)
        missing = sorted(
            PLAN_REQUIRED_HEADINGS - markdown_h2_headings(path.read_text(encoding="utf-8"))
        )
        for heading in missing:
            report.error(f"{rel} is missing required heading ## {heading}.")
        if path != template and not PLAN_RECORD_NAME_RE.fullmatch(path.name):
            report.error(f"{rel} must use YYYY-MM-DD-short-name.md.")

    instruction_markers = {
        "AGENTS.md": ("$plan-evolution", ".agent/plans/"),
        "CLAUDE.md": (".agent/plans/",),
    }
    for filename, markers in instruction_markers.items():
        path = root / filename
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                report.error(f"{filename} must include the plan policy marker {marker}.")
    report.detail(f"Plan records validated: {max(0, len(paths) - 1)}.")


def validate_task_context_routes(root: Path, report: ValidationReport) -> None:
    errors = validate_route_manifest(root)
    for error in errors:
        report.error(error)
    if not errors:
        route_path = root / "docs" / "agent" / "context-routes.json"
        route_count = len(json.loads(route_path.read_text(encoding="utf-8"))["routes"])
        report.detail(f"Task-context routes validated: {route_count}.")


def validate(root: Path) -> ValidationReport:
    root = root.resolve()
    report = ValidationReport()
    validate_required_files(root, report)
    validate_instructions(root, report)
    validate_manifest_and_skills(root, report)
    validate_plan_system(root, report)
    validate_task_context_routes(root, report)
    validate_guardrail_templates(root, report)
    return report


def print_report(report: ValidationReport) -> None:
    for message in report.details:
        print(f"INFO: {message}")
    for message in report.warnings:
        print(f"WARNING: {message}")
    for message in report.errors:
        print(f"ERROR: {message}")
    print(
        f"Agent asset validation: {len(report.errors)} error(s), "
        f"{len(report.warnings)} warning(s)."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate project agent instructions, skills, and guardrails.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Repository root to validate.")
    args = parser.parse_args(argv)
    report = validate(Path(args.root))
    print_report(report)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
