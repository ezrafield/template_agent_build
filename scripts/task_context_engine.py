from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Iterable

try:
    from scripts import run_agent_tool
except ImportError:  # pragma: no cover - direct script execution path
    import run_agent_tool  # type: ignore


ROUTE_MANIFEST = Path("docs/agent/context-routes.json")
SECRET_DIR_NAMES = {"secrets", "credentials", ".ssh", ".gnupg"}
SECRET_FILE_NAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "vault.yaml",
    "vault.yml",
    "vault.properties",
}
SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks", ".crt", ".cer"}
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "the",
    "this",
    "to",
    "we",
    "with",
    # Workflow vocabulary identifies a route, not a concrete optional source.
    "add", "build", "bug", "bugs", "change", "changes", "check", "checks",
    "code", "current", "existing", "fail", "failed", "failing", "failure",
    "failures", "feature", "fix", "implement", "implementation", "improve",
    "new", "read", "refactor", "regression", "request", "review", "task",
    "test", "tests", "testing", "update", "work",
    "explain", "find", "inspect", "investigate", "understand", "please",
    "empty", "error", "errors", "input", "output", "invalid",
}
OPTIONAL_EXCERPT_CHARS = 6000
OPTIONAL_EXCERPT_LINES = 100

URL_CREDENTIAL_RE = re.compile(r"https?://[A-Za-z0-9._%+-]+:[^@\s]+@")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(?<![-\w])\b(password|token|api[-_]?key|secret|jwt[-_]?key)"
    r"(\s*[:=]\s*)([^<\s]+)"
)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


class TaskContextError(Exception):
    """Invalid task-context input or configuration."""


@dataclass(frozen=True)
class SearchResult:
    path: str
    start_line: int
    end_line: int
    score: float = 0.0


@dataclass
class SearchOutcome:
    status: str
    results: list[SearchResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Candidate:
    path: str
    category: str
    origin: str
    required: bool
    sections: list[str] = field(default_factory=list)
    group: str | None = None
    group_limit: int | None = None
    start_line: int | None = None
    end_line: int | None = None
    search_score: float = 0.0
    line_ranges: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class PreparedSource:
    path: str
    category: str
    origin: str
    required: bool
    sections: list[str]
    excerpt: str
    source_hash: str
    score: float
    redactions: dict[str, int]
    group: str | None = None
    group_limit: int | None = None
    line_ranges: list[tuple[int, int]] = field(default_factory=list)
    compact_excerpt: str | None = None


@dataclass
class SelectedSource:
    path: str
    category: str
    origin: str
    sections: list[str]
    excerpt: str
    source_hash: str
    score: float
    selection_reason: str
    redactions: dict[str, int]
    truncated: bool = False
    line_ranges: list[tuple[int, int]] = field(default_factory=list)
    compact_excerpt: str | None = None

    @property
    def char_count(self) -> int:
        return len(self.excerpt)


@dataclass(frozen=True)
class DroppedSource:
    path: str
    origin: str
    reason: str


@dataclass
class BuildResult:
    task: str
    normalized_task: str
    task_hash: str
    generated_at: str
    route_id: str
    route_heading: str
    route_manifest_hash: str
    search_status: str
    max_docs: int
    max_chars: int
    selected: list[SelectedSource]
    dropped: list[DroppedSource]
    warnings: list[str]
    gaps: list[str]
    task_redactions: dict[str, int] = field(default_factory=dict)
    expansion_reason: str = ""
    expansion_notes: list[str] = field(default_factory=list)

    @property
    def selected_chars(self) -> int:
        return sum(source.char_count for source in self.selected)


SearchProvider = Callable[[str, Path, str, int], SearchOutcome]


def normalize_task(task: str) -> str:
    return " ".join(task.split()).casefold()


def task_hash(task: str) -> str:
    return hashlib.sha256(normalize_task(task).encode("utf-8")).hexdigest()[:16]


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _relative_syntax_issue(value: str) -> str | None:
    normalized = value.replace("\\", "/").strip()
    if not normalized:
        return "path is empty"
    if normalized.startswith("~"):
        return "home-relative paths are not allowed"
    if PurePosixPath(normalized).is_absolute() or PureWindowsPath(value).is_absolute():
        return "absolute paths are not allowed"
    if ".." in PurePosixPath(normalized).parts:
        return "parent traversal is not allowed"
    return None


def _normalized_relative(value: str) -> str:
    return PurePosixPath(value.replace("\\", "/")).as_posix()


def _secret_reason(relative_path: str) -> str | None:
    path = PurePosixPath(relative_path.casefold())
    if any(part in SECRET_DIR_NAMES for part in path.parts):
        return "secret directory"
    if path.name in SECRET_FILE_NAMES or path.name.startswith(".env."):
        return "secret-like filename"
    if path.suffix in SECRET_SUFFIXES:
        return "secret-like suffix"
    return None


def _safe_resolve(root: Path, raw_path: str) -> tuple[Path | None, str | None]:
    issue = _relative_syntax_issue(raw_path)
    if issue:
        return None, issue
    relative = _normalized_relative(raw_path)
    secret = _secret_reason(relative)
    if secret:
        return None, secret
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    try:
        resolved_relative = candidate.relative_to(root_resolved).as_posix()
    except ValueError:
        return None, "path resolves outside the repository"
    resolved_secret = _secret_reason(resolved_relative)
    if resolved_secret:
        return None, f"resolved path has {resolved_secret}"
    return candidate, None


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    redactions: dict[str, int] = {}
    redacted, url_count = URL_CREDENTIAL_RE.subn("<REDACTED-URL>@", text)
    if url_count:
        redactions["url_credentials"] = url_count

    assignment_count = 0

    def replace_assignment(match: re.Match[str]) -> str:
        nonlocal assignment_count
        assignment_count += 1
        return f"{match.group(1)}{match.group(2)}<REDACTED-SECRET>"

    redacted = SECRET_ASSIGNMENT_RE.sub(replace_assignment, redacted)
    if assignment_count:
        redactions["secret_assignment"] = assignment_count
    return redacted, redactions


def _merge_counts(target: dict[str, int], incoming: dict[str, int]) -> None:
    for key, count in incoming.items():
        target[key] = target.get(key, 0) + count


def _section_map(text: str) -> dict[str, str]:
    matches = list(H2_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip().casefold()] = text[match.start() : end].strip()
    return sections


def slice_sections(text: str, requested: Iterable[str]) -> tuple[str, list[str], list[str]]:
    names = [name.strip() for name in requested if name.strip()]
    if not names or "*" in names:
        return text.strip(), ["all"], []
    available = _section_map(text)
    selected: list[str] = []
    used: list[str] = []
    missing: list[str] = []
    for name in names:
        section = available.get(name.casefold())
        if section is None:
            missing.append(name)
        else:
            selected.append(section)
            used.append(name)
    if not selected:
        return text.strip(), ["all"], missing
    return "\n\n".join(selected), used, missing


def _merge_ranges(ranges: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _uncovered_ranges(
    ranges: list[tuple[int, int]], covered: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    remaining = ranges
    for covered_start, covered_end in _merge_ranges(covered):
        next_ranges: list[tuple[int, int]] = []
        for start, end in remaining:
            if end < covered_start or start > covered_end:
                next_ranges.append((start, end))
            else:
                if start < covered_start:
                    next_ranges.append((start, covered_start - 1))
                if end > covered_end:
                    next_ranges.append((covered_end + 1, end))
        remaining = next_ranges
    return remaining


def _section_line_ranges(
    text: str, sections: list[str], requested: list[str]
) -> list[tuple[int, int]]:
    """Track source lines separately from excerpt formatting for expansion deduplication."""
    requested = [section.strip() for section in requested if section.strip()]
    if not requested or "*" in requested:
        return [(1, len(text.splitlines()))]
    matches = list(H2_RE.finditer(text))
    available: dict[str, tuple[int, int]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        start_line = text.count("\n", 0, match.start()) + 1
        available[match.group(1).strip().casefold()] = (
            start_line, start_line + len(text[match.start():end].splitlines()) - 1
        )
    if not any(section.strip().casefold() in available for section in requested):
        return [(1, len(text.splitlines()))]
    return _merge_ranges(available[section.casefold()] for section in sections)


def _normalize_expansions(
    requests: Iterable[tuple[str, int, int] | list[str]],
) -> list[tuple[str, list[tuple[int, int]]]]:
    grouped: dict[str, tuple[str, list[tuple[int, int]]]] = {}
    for request in requests:
        if len(request) != 3:
            raise TaskContextError("Each expansion requires PATH START END.")
        path, start, end = request
        if not isinstance(path, str):
            raise TaskContextError("Expansion paths must be repository-relative text.")
        try:
            for value in (start, end):
                if not ((isinstance(value, int) and not isinstance(value, bool))
                        or (isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value))):
                    raise ValueError
            start, end = int(start), int(end)
        except (ValueError, TypeError):
            raise TaskContextError("Expansion line numbers must be integers.") from None
        path = _normalized_relative(path.strip())
        key = path.casefold()
        grouped.setdefault(key, (path, []))[1].append((start, end))
    # Preserve path priority and validate every distinct request against current source
    # before merging. An out-of-bounds range must not disappear inside a wider range.
    return [(path, sorted(set(ranges))) for path, ranges in grouped.values()]


def _manifest_data(path: Path) -> tuple[dict, bytes]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TaskContextError(f"Cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TaskContextError("Task-context route manifest must contain an object.")
    return data, raw


def validate_route_manifest(root: Path, manifest_path: Path | None = None) -> list[str]:
    path = manifest_path or root / ROUTE_MANIFEST
    try:
        data, _ = _manifest_data(path)
    except TaskContextError as exc:
        return [str(exc)]

    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("context-routes.json must use schema_version 1")

    defaults = data.get("defaults")
    if not isinstance(defaults, dict):
        errors.append("context-routes.json defaults must be an object")
        defaults = {}
    for key in ("max_docs", "max_chars", "search_limit"):
        if not isinstance(defaults.get(key), int) or defaults.get(key, 0) <= 0:
            errors.append(f"context-routes.json defaults.{key} must be a positive integer")
    if defaults.get("search_content") not in {"code", "all"}:
        errors.append("context-routes.json defaults.search_content must be `code` or `all`")
    if defaults.get("selection_order") != [
        "routed-required",
        "routed-optional",
        "advisory-search",
    ]:
        errors.append(
            "context-routes.json defaults.selection_order must keep routed-required, "
            "routed-optional, then advisory-search"
        )

    index_value = data.get("index_path")
    index_text = ""
    if not isinstance(index_value, str) or _relative_syntax_issue(index_value):
        errors.append("context-routes.json index_path must be a safe relative path")
    else:
        index_file = root / _normalized_relative(index_value)
        try:
            index_text = index_file.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Cannot read route index {index_value}: {exc}")

    excludes = data.get("exclude_globs")
    if not isinstance(excludes, list) or not all(isinstance(item, str) for item in excludes):
        errors.append("context-routes.json exclude_globs must be a string list")
    else:
        for exclude in excludes:
            if _relative_syntax_issue(exclude):
                errors.append(f"context-routes.json contains an unsafe exclusion glob: {exclude}")

    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        errors.append("context-routes.json routes must be a non-empty list")
        return errors

    route_ids: list[str] = []
    empty_trigger_routes: list[str] = []
    for route_index, route in enumerate(routes):
        label = f"routes[{route_index}]"
        if not isinstance(route, dict):
            errors.append(f"{label} must be an object")
            continue
        route_id = route.get("id")
        if not isinstance(route_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", route_id):
            errors.append(f"{label}.id must be a hyphen-case string")
            route_id = label
        else:
            route_ids.append(route_id)
        heading = route.get("index_heading")
        if not isinstance(heading, str) or not heading.strip():
            errors.append(f"{label}.index_heading must be a non-empty string")
        elif index_text and f"## {heading}" not in index_text:
            errors.append(f"Route {route_id} heading is missing from the index: ## {heading}")
        triggers = route.get("triggers")
        if not isinstance(triggers, list) or not all(
            isinstance(item, str) and item.strip() for item in triggers
        ):
            errors.append(f"{label}.triggers must be a string list")
        elif not triggers:
            empty_trigger_routes.append(str(route_id))

        for collection_name in ("required", "optional"):
            specs = route.get(collection_name)
            if not isinstance(specs, list):
                errors.append(f"{label}.{collection_name} must be a list")
                continue
            for spec_index, spec in enumerate(specs):
                spec_label = f"{label}.{collection_name}[{spec_index}]"
                if not isinstance(spec, dict):
                    errors.append(f"{spec_label} must be an object")
                    continue
                selectors = [key for key in ("path", "glob") if key in spec]
                if len(selectors) != 1 or not isinstance(spec.get(selectors[0]) if selectors else None, str):
                    errors.append(f"{spec_label} must define exactly one string path or glob")
                elif _relative_syntax_issue(str(spec[selectors[0]])):
                    errors.append(f"{spec_label} contains an unsafe path or glob")
                if not isinstance(spec.get("category"), str) or not spec.get("category"):
                    errors.append(f"{spec_label}.category must be a non-empty string")
                sections = spec.get("sections", [])
                if not isinstance(sections, list) or not all(isinstance(item, str) for item in sections):
                    errors.append(f"{spec_label}.sections must be a string list when present")
                max_matches = spec.get("max_matches")
                if max_matches is not None and (
                    not isinstance(max_matches, int) or max_matches <= 0
                ):
                    errors.append(f"{spec_label}.max_matches must be a positive integer")

    if len(route_ids) != len(set(route_ids)):
        errors.append("context-routes.json route IDs must be unique")
    if empty_trigger_routes != ["general"]:
        errors.append("Only the final `general` route may have no triggers")
    if route_ids and route_ids[-1] != "general":
        errors.append("The `general` fallback route must be last")
    return errors


def load_route_manifest(root: Path, manifest_path: Path | None = None) -> tuple[dict, str]:
    path = manifest_path or root / ROUTE_MANIFEST
    errors = validate_route_manifest(root, path)
    if errors:
        raise TaskContextError("; ".join(errors))
    data, raw = _manifest_data(path)
    return data, _sha256_bytes(raw)


def _phrase_matches(phrase: str, text: str) -> bool:
    words = phrase.casefold().split()
    if not words:
        return False
    body = r"[\s\-_/]+".join(re.escape(word) for word in words)
    prefix = r"(?<!\w)" if words[0][0].isalnum() else ""
    suffix = r"(?!\w)" if words[-1][-1].isalnum() else ""
    return re.search(prefix + body + suffix, text, flags=re.IGNORECASE) is not None


def classify_route(task: str, manifest: dict, route_id: str | None = None) -> dict:
    routes = manifest["routes"]
    if route_id:
        selected = next((route for route in routes if route["id"] == route_id), None)
        if selected is None:
            available = ", ".join(route["id"] for route in routes)
            raise TaskContextError(f"Unknown route `{route_id}`. Available routes: {available}")
        return selected

    normalized = normalize_task(task)
    best: dict | None = None
    best_score = 0
    for route in routes:
        score = sum(
            max(1, len(trigger.split()))
            for trigger in route["triggers"]
            if _phrase_matches(trigger, normalized)
        )
        if score > best_score:
            best = route
            best_score = score
    return best or next(route for route in routes if route["id"] == "general")


def _task_tokens(task: str) -> list[str]:
    tokens = re.findall(r"[\w][\w-]*", normalize_task(task), flags=re.UNICODE)
    return sorted({token for token in tokens if token not in STOP_WORDS and not token.isdecimal()})


def _relevance_score(task: str, relative_path: str, excerpt: str) -> float:
    path_text = relative_path.casefold().replace("_", " ").replace("-", " ")
    sample = excerpt.casefold()
    score = 0.0
    body_matches = 0
    normalized_task = normalize_task(task).replace("\\", "/")
    if _phrase_matches(relative_path.casefold(), normalized_task) or _phrase_matches(PurePosixPath(relative_path).name.casefold(), normalized_task):
        score += 100.0
    for token in _task_tokens(task):
        if _phrase_matches(token.replace("_", " ").replace("-", " "), path_text):
            score += 10.0
        occurrences = len(re.findall(rf"(?<![\w]){re.escape(token)}(?![\w])", sample))
        # A named identifier is a strong signal; ordinary content words need
        # corroboration, so one incidental mention cannot pull in a large file.
        defined = re.search(rf"(?m)^\s*(?:async\s+)?(?:def|class|function)\s+{re.escape(token)}\b", sample)
        if occurrences and ("_" in token or "-" in token or defined):
            score += 5.0
        elif occurrences:
            body_matches += 1
    if body_matches >= 2:
        score += body_matches
    return score


def _optional_excerpt(
    task: str, text: str, available: list[tuple[int, int]],
) -> tuple[str, list[tuple[int, int]]]:
    """Return bounded local windows; explicit expansion remains the escape hatch."""
    lines = text.splitlines()
    tokens = _task_tokens(task)
    hits = [index + 1 for index, line in enumerate(lines)
            if any(_phrase_matches(token, line.casefold()) for token in tokens)
            and any(start <= index + 1 <= end for start, end in available)]
    windows = _merge_ranges(
        (max(start, hit - 6), min(end, hit + 12))
        for hit in hits for start, end in available if start <= hit <= end
    ) if hits else available
    selected: list[tuple[int, int]] = []
    characters = 0
    line_count = 0
    for start, end in windows:
        if selected:
            characters += 2
        last = start - 1
        for line in range(start, end + 1):
            cost = len(lines[line - 1]) + 1
            if line_count >= OPTIONAL_EXCERPT_LINES or characters + cost > OPTIONAL_EXCERPT_CHARS:
                break
            last = line
            line_count += 1
            characters += cost
        if last >= start:
            selected.append((start, last))
        if last < end:
            break
    excerpt = "\n\n".join("\n".join(lines[start - 1:end]).strip() for start, end in selected)
    if not selected and windows:
        # Redact a whole enormous line before its later character clipping;
        # clipping first could sever a credential URL before its @ delimiter.
        excerpt = lines[windows[0][0] - 1]
    return excerpt, selected


def _is_excluded(relative_path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(relative_path, pattern) for pattern in patterns)


def _expand_spec(root: Path, spec: dict, origin: str, required: bool, index: int) -> list[Candidate]:
    sections = list(spec.get("sections", []))
    group = f"{origin}:{index}"
    limit = spec.get("max_matches")
    if "path" in spec:
        paths = [str(spec["path"])]
    else:
        pattern = _normalized_relative(str(spec["glob"]))
        paths = sorted(
            path.relative_to(root).as_posix()
            for path in root.glob(pattern)
            if path.is_file()
        )
    return [
        Candidate(
            path=path,
            category=str(spec["category"]),
            origin=origin,
            required=required,
            sections=sections,
            group=group,
            group_limit=limit,
        )
        for path in paths
    ]


def _prepare_candidate(
    root: Path,
    task: str,
    candidate: Candidate,
    exclude_globs: list[str],
    warnings: list[str],
    gaps: list[str],
    dropped: list[DroppedSource],
    covered_ranges: list[tuple[int, int]] | None = None,
) -> PreparedSource | None:
    relative = _normalized_relative(candidate.path)
    path, unsafe_reason = _safe_resolve(root, relative)
    if unsafe_reason:
        message = f"Skipped unsafe context `{relative}`: {unsafe_reason}."
        warnings.append(message)
        if candidate.required:
            gaps.append(message)
        dropped.append(DroppedSource(relative, candidate.origin, f"unsafe: {unsafe_reason}"))
        return None
    assert path is not None
    if _is_excluded(relative, exclude_globs) or _is_excluded(path.relative_to(root.resolve()).as_posix(), exclude_globs):
        message = f"Skipped excluded context `{relative}`."
        warnings.append(message)
        if candidate.required:
            gaps.append(message)
        dropped.append(DroppedSource(relative, candidate.origin, "excluded_by_route"))
        return None
    assert path is not None
    if not path.is_file():
        kind = "Required" if candidate.required else "Optional"
        message = f"{kind} context not found: `{relative}`."
        warnings.append(message)
        if candidate.required:
            gaps.append(message)
        dropped.append(DroppedSource(relative, candidate.origin, "missing"))
        return None

    try:
        raw = path.read_bytes()
    except OSError as exc:
        message = f"Could not read context `{relative}`: {exc}."
        warnings.append(message)
        if candidate.required:
            gaps.append(message)
        dropped.append(DroppedSource(relative, candidate.origin, "read_error"))
        return None
    text = raw.decode("utf-8", errors="replace")

    line_ranges: list[tuple[int, int]]
    if candidate.line_ranges:
        lines = text.splitlines()
        valid_ranges: list[tuple[int, int]] = []
        for start, end in candidate.line_ranges:
            if start < 1 or end < start or start > len(lines):
                warnings.append(f"Ignored invalid expansion range for `{relative}`: {start}-{end}.")
                dropped.append(DroppedSource(relative, candidate.origin, f"invalid_expansion_range: {start}-{end}"))
                continue
            if end > len(lines):
                warnings.append(
                    f"Clipped expansion range for `{relative}` from {start}-{end} to {start}-{len(lines)}."
                )
            valid_ranges.append((start, min(end, len(lines))))
        if not valid_ranges:
            return None
        line_ranges = _uncovered_ranges(_merge_ranges(valid_ranges), covered_ranges or [])
        excerpt = "\n\n".join(
            "\n".join(lines[start - 1:end]).strip() for start, end in line_ranges
        )
        sections = [f"lines {start}-{end}" for start, end in line_ranges]
    elif candidate.start_line is not None and candidate.end_line is not None:
        lines = text.splitlines()
        start = candidate.start_line
        end = candidate.end_line
        if start < 1 or end < start or start > len(lines):
            warnings.append(f"Ignored invalid search range for `{relative}`: {start}-{end}.")
            dropped.append(DroppedSource(relative, candidate.origin, "invalid_search_range"))
            return None
        excerpt = "\n".join(lines[start - 1 : min(end, len(lines))]).strip()
        sections = [f"lines {start}-{min(end, len(lines))}"]
        line_ranges = [(start, min(end, len(lines)))]
    else:
        excerpt, sections, missing_sections = slice_sections(text, candidate.sections)
        line_ranges = _section_line_ranges(text, sections, candidate.sections)
        for section in missing_sections:
            warnings.append(f"Section `{section}` was not found in `{relative}`; included available content.")

    score = candidate.search_score or _relevance_score(task, relative, excerpt)
    compact_excerpt = None
    if candidate.origin == "routed-optional":
        if score <= 0:
            excerpt = ""
        elif len(excerpt) > OPTIONAL_EXCERPT_CHARS or len(excerpt.splitlines()) > OPTIONAL_EXCERPT_LINES:
            excerpt, line_ranges = _optional_excerpt(task, text, line_ranges)
            sections = [f"lines {start}-{end}" for start, end in line_ranges] or ["clipped line"]
            warnings.append(f"Bounded optional context `{relative}` to relevant lines; remaining content omitted. Use explicit expansion if needed.")
    if relative == ".agent/memory/index.json" and candidate.origin.startswith("routed-"):
        try:
            try:
                from scripts.memory_lookup import render_lookup
            except ImportError:
                from memory_lookup import render_lookup  # type: ignore
            compact_excerpt = render_lookup(root, index_text=text)
        except (ImportError, OSError, ValueError) as exc:
            warnings.append(f"Memory lookup projection unavailable ({type(exc).__name__}); compact view retains the original index excerpt.")

    safe_excerpt, redactions = redact_text(excerpt)
    if candidate.origin == "routed-optional" and len(safe_excerpt) > OPTIONAL_EXCERPT_CHARS:
        marker = "\n[Optional excerpt clipped after redaction; expand the source for more.]"
        safe_excerpt = safe_excerpt[:OPTIONAL_EXCERPT_CHARS - len(marker)].rstrip() + marker
        line_ranges = []
    if redactions:
        summary = ", ".join(f"{key}={count}" for key, count in sorted(redactions.items()))
        warnings.append(f"Redacted suspicious content in `{relative}` ({summary}).")
    return PreparedSource(
        path=relative,
        category=candidate.category,
        origin=candidate.origin,
        required=candidate.required,
        sections=sections,
        excerpt=safe_excerpt,
        source_hash=_sha256_bytes(raw),
        score=score,
        redactions=redactions,
        group=candidate.group,
        group_limit=candidate.group_limit,
        line_ranges=line_ranges,
        compact_excerpt=compact_excerpt,
    )


def run_semble_search(task: str, root: Path, content: str, limit: int) -> SearchOutcome:
    env = run_agent_tool.build_env()
    executable = run_agent_tool.find_tool("semble", env)
    if not executable:
        return SearchOutcome(
            status="unavailable",
            warnings=["Semble is unavailable; built routed context without advisory search."],
        )
    command = run_agent_tool.prepare_command(
        [
            executable,
            "search",
            task,
            ".",
            "--content",
            content,
            "-k",
            str(limit),
            "--max-snippet-lines",
            "0",
        ]
    )
    try:
        result = subprocess.run(
            command,
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return SearchOutcome(
            status="error",
            warnings=["Semble search timed out after 30 seconds; built routed context only."],
        )
    except OSError as exc:
        return SearchOutcome(status="error", warnings=[f"Semble could not start: {exc}."])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().replace("\n", " ")[:300]
        safe_detail, _ = redact_text(detail)
        return SearchOutcome(
            status="error",
            warnings=[f"Semble search failed with exit {result.returncode}: {safe_detail}"],
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return SearchOutcome(status="error", warnings=[f"Semble returned invalid JSON: {exc}."])
    raw_results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(raw_results, list):
        return SearchOutcome(status="error", warnings=["Semble JSON did not contain a results list."])

    parsed: list[SearchResult] = []
    warnings: list[str] = []
    for index, item in enumerate(raw_results[:limit]):
        if not isinstance(item, dict):
            warnings.append(f"Ignored malformed Semble result at index {index}.")
            continue
        path = item.get("file_path")
        start = item.get("start_line")
        end = item.get("end_line")
        score = item.get("score", 0.0)
        if (
            not isinstance(path, str)
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
        ):
            warnings.append(f"Ignored incomplete Semble result at index {index}.")
            continue
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            numeric_score = 0.0
        parsed.append(SearchResult(path, start, end, numeric_score))
    return SearchOutcome(status="ok", results=parsed, warnings=warnings)


def _append_selection(
    source: PreparedSource,
    selected: list[SelectedSource],
    dropped: list[DroppedSource],
    warnings: list[str],
    gaps: list[str],
    seen: set[str],
    group_counts: dict[str, int],
    max_docs: int,
    max_chars: int,
) -> None:
    key = source.path.casefold()
    existing = next((item for item in selected if item.path.casefold() == key), None)
    merge = existing is not None and source.origin == "explicit-expansion"
    if key in seen and not merge:
        dropped.append(DroppedSource(source.path, source.origin, "duplicate_path"))
        return
    if source.group and source.group_limit is not None:
        if group_counts.get(source.group, 0) >= source.group_limit:
            dropped.append(DroppedSource(source.path, source.origin, "source_match_limit"))
            return
    if len(selected) >= max_docs and not merge:
        dropped.append(DroppedSource(source.path, source.origin, "document_budget_exhausted"))
        if source.required:
            message = f"Required context `{source.path}` exceeded the {max_docs}-document budget."
            warnings.append(message)
            gaps.append(message)
        return

    separator = "\n\n" if merge and existing is not None and existing.excerpt else ""
    remaining = max_chars - sum(item.char_count for item in selected) - len(separator)
    if remaining <= 0:
        dropped.append(DroppedSource(source.path, source.origin, "character_budget_exhausted"))
        if source.required:
            message = f"Required context `{source.path}` exceeded the {max_chars}-character budget."
            warnings.append(message)
            gaps.append(message)
        return

    excerpt = source.excerpt
    truncated = False
    if len(excerpt) > remaining:
        marker = "\n\n[TRUNCATED: task-context character budget reached]"
        keep = max(0, remaining - len(marker))
        excerpt = (excerpt[:keep].rstrip() + marker)[:remaining]
        truncated = True
        warnings.append(f"Truncated context `{source.path}` to stay within {max_chars} characters.")

    reason = {
        "routed-required": "required_route",
        "routed-optional": "optional_route_match",
        "advisory-search": "advisory_search_rank",
        "explicit-expansion": "explicit_expansion",
    }[source.origin]
    if merge:
        assert existing is not None
        existing.excerpt += separator + excerpt
        existing.sections.extend(source.sections)
        # Full input ranges do not establish coverage of a truncated excerpt.
        if not truncated:
            existing.line_ranges = _merge_ranges(existing.line_ranges + source.line_ranges)
        existing.selection_reason += "+explicit_expansion"
        # Explicitly requested source text must never disappear into a projection.
        existing.compact_excerpt = None
        existing.truncated |= truncated
        _merge_counts(existing.redactions, source.redactions)
        return
    selected.append(
        SelectedSource(
            path=source.path,
            category=source.category,
            origin=source.origin,
            sections=source.sections,
            excerpt=excerpt,
            source_hash=source.source_hash,
            score=source.score,
            selection_reason=reason,
            redactions=source.redactions,
            truncated=truncated,
            line_ranges=[] if truncated else source.line_ranges,
            compact_excerpt=source.compact_excerpt,
        )
    )
    seen.add(key)
    if source.group:
        group_counts[source.group] = group_counts.get(source.group, 0) + 1


def build_task_context(
    task: str,
    root: Path,
    *,
    route_id: str | None = None,
    use_search: bool = True,
    search_provider: SearchProvider | None = None,
    manifest_path: Path | None = None,
    generated_at: str | None = None,
    expand_sources: Iterable[tuple[str, int, int] | list[str]] = (),
    reason: str | None = None,
) -> BuildResult:
    normalized = normalize_task(task)
    if not normalized:
        raise TaskContextError("Task must contain non-whitespace text.")
    expansions = _normalize_expansions(expand_sources)
    if expansions and (reason is None or not reason.strip()):
        raise TaskContextError("Explicit expansion requires a non-empty --reason.")
    if reason is not None and not expansions:
        raise TaskContextError("--reason requires at least one --expand-source.")
    safe_reason, reason_redactions = redact_text(" ".join((reason or "").split()))
    root = root.resolve()
    if not root.is_dir():
        raise TaskContextError(f"Repository root does not exist: {root}")

    manifest, manifest_hash = load_route_manifest(root, manifest_path)
    route = classify_route(task, manifest, route_id)
    defaults = manifest["defaults"]
    max_docs = int(defaults["max_docs"])
    max_chars = int(defaults["max_chars"])
    exclude_globs = [str(item) for item in manifest.get("exclude_globs", [])]

    warnings: list[str] = []
    gaps: list[str] = []
    dropped: list[DroppedSource] = []
    prepared_required: list[PreparedSource] = []
    prepared_optional: list[PreparedSource] = []

    for collection_name, required in (("required", True), ("optional", False)):
        origin = "routed-required" if required else "routed-optional"
        for index, spec in enumerate(route[collection_name]):
            candidates = _expand_spec(root, spec, origin, required, index)
            if not candidates and "glob" in spec:
                message = f"{collection_name.title()} context glob matched no files: `{spec['glob']}`."
                warnings.append(message)
                if required:
                    gaps.append(message)
                dropped.append(DroppedSource(str(spec["glob"]), origin, "glob_no_matches"))
            for candidate in candidates:
                prepared = _prepare_candidate(
                    root, task, candidate, exclude_globs, warnings, gaps, dropped
                )
                if prepared is not None:
                    (prepared_required if required else prepared_optional).append(prepared)

    selected: list[SelectedSource] = []
    seen: set[str] = set()
    group_counts: dict[str, int] = {}
    for source in prepared_required:
        _append_selection(
            source, selected, dropped, warnings, gaps, seen, group_counts, max_docs, max_chars
        )

    expansion_notes: list[str] = []
    for path, ranges in expansions:
        request_label = f"`{redact_text(path)[0]}` lines " + ", ".join(f"{start}-{end}" for start, end in ranges)
        existing = next((item for item in selected if item.path.casefold() == path.casefold()), None)
        dropped_before = len(dropped)
        prepared = _prepare_candidate(
            root, task,
            Candidate(path, "explicit-context", "explicit-expansion", False, line_ranges=ranges),
            exclude_globs, warnings, gaps, dropped,
            covered_ranges=existing.line_ranges if existing else [],
        )
        if prepared is None:
            outcome = "rejected"
        elif not prepared.line_ranges:
            outcome = "already included in routed context"
        else:
            _append_selection(
                prepared, selected, dropped, warnings, gaps, seen, group_counts, max_docs, max_chars
            )
            included = next((item for item in selected if item.path.casefold() == path.casefold()), None)
            if included is None or any(
                item.reason in {"document_budget_exhausted", "character_budget_exhausted"}
                for item in dropped[dropped_before:]
            ):
                outcome = "rejected"
            else:
                outcome = "included with truncation" if included.truncated else "included"
        details = "; ".join(item.reason for item in dropped[dropped_before:])
        expansion_notes.append(f"{request_label}: {outcome}" + (f" ({details})" if details else "") + ".")
    if reason_redactions:
        warnings.append("Redacted suspicious secret-like content from the expansion reason.")

    prepared_optional.sort(key=lambda item: (-item.score, item.path))
    for source in prepared_optional:
        if source.score <= 0:
            dropped.append(DroppedSource(source.path, source.origin, "no_task_relevance"))
            continue
        _append_selection(
            source, selected, dropped, warnings, gaps, seen, group_counts, max_docs, max_chars
        )

    search_status = "disabled"
    if use_search:
        provider = search_provider or run_semble_search
        try:
            outcome = provider(
                task,
                root,
                str(defaults["search_content"]),
                int(defaults["search_limit"]),
            )
        except Exception as exc:  # optional search must fail open
            outcome = SearchOutcome(
                status="error",
                warnings=[
                    "Advisory search failed unexpectedly: "
                    f"{type(exc).__name__}: {redact_text(str(exc))[0]}"
                ],
            )
        search_status = outcome.status
        warnings.extend(outcome.warnings)
        for index, result in enumerate(outcome.results):
            candidate = Candidate(
                path=result.path,
                category="search-result",
                origin="advisory-search",
                required=False,
                start_line=result.start_line,
                end_line=result.end_line,
                search_score=result.score,
                group="advisory-search",
                group_limit=int(defaults["search_limit"]),
            )
            prepared = _prepare_candidate(
                root, task, candidate, exclude_globs, warnings, gaps, dropped
            )
            if prepared is not None:
                _append_selection(
                    prepared,
                    selected,
                    dropped,
                    warnings,
                    gaps,
                    seen,
                    group_counts,
                    max_docs,
                    max_chars,
                )

    safe_task, task_redactions = redact_text(" ".join(task.split()))
    if task_redactions:
        warnings.insert(0, "Redacted suspicious secret-like content from the task text.")
    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    identity = task_hash(task)
    if expansions:
        identity = _sha256_bytes(json.dumps(
            [normalized, expansions, safe_reason], ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8"))[:16]
    return BuildResult(
        task=safe_task,
        normalized_task=normalized,
        task_hash=identity,
        generated_at=timestamp,
        route_id=str(route["id"]),
        route_heading=str(route["index_heading"]),
        route_manifest_hash=manifest_hash,
        search_status=search_status,
        max_docs=max_docs,
        max_chars=max_chars,
        selected=selected,
        dropped=dropped,
        warnings=list(dict.fromkeys(redact_text(value)[0] for value in warnings)),
        gaps=list(dict.fromkeys(redact_text(value)[0] for value in gaps)),
        task_redactions=task_redactions,
        expansion_reason=safe_reason,
        expansion_notes=expansion_notes,
    )


def _table_cell(value: object) -> str:
    return redact_text(str(value))[0].replace("\\", "/").replace("|", "\\|").replace("\n", " ")


def render_markdown(result: BuildResult) -> str:
    lines = [
        "# Task Context",
        "",
        "> Generated cache artifact. Current source files remain authoritative.",
        "> Full audit view: the character budget covers excerpts; this complete audit may be larger.",
        "",
        "## Task",
        "",
        result.task,
        "",
        "## Build Summary",
        "",
        f"- Generated: `{result.generated_at}`",
        f"- Task hash: `{result.task_hash}`",
        f"- Route: `{result.route_id}` ({result.route_heading})",
        f"- Route manifest SHA-256: `{result.route_manifest_hash}`",
        f"- Advisory search: `{result.search_status}`",
        f"- Budget: {len(result.selected)}/{result.max_docs} documents, "
        f"{result.selected_chars}/{result.max_chars} excerpt characters",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in result.warnings or ["(none)"])
    lines.extend(["", "## Gaps", ""])
    lines.extend(f"- {gap}" for gap in result.gaps or ["(none)"])
    if result.expansion_notes:
        lines.extend(["", "## Explicit Expansion", "", f"Reason: {result.expansion_reason}", ""])
        lines.extend(f"- {note}" for note in result.expansion_notes)
    lines.extend(
        [
            "",
            "## Selected Sources",
            "",
            "| # | Path | Origin | Category | Sections | Chars | SHA-256 | Reason |",
            "| ---: | --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for index, source in enumerate(result.selected, start=1):
        sections = ", ".join(source.sections) or "all"
        lines.append(
            f"| {index} | `{_table_cell(source.path)}` | {_table_cell(source.origin)} | "
            f"{_table_cell(source.category)} | {_table_cell(sections)} | {source.char_count} | "
            f"`{source.source_hash}` | {_table_cell(source.selection_reason)} |"
        )
    if not result.selected:
        lines.append("| - | (none) | - | - | - | 0 | - | - |")

    lines.extend(
        [
            "",
            "## Dropped Candidates",
            "",
            "| Path | Origin | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for source in result.dropped:
        lines.append(
            f"| `{_table_cell(source.path)}` | {_table_cell(source.origin)} | "
            f"{_table_cell(source.reason)} |"
        )
    if not result.dropped:
        lines.append("| (none) | - | - |")

    lines.extend(["", "## Context Excerpts", ""])
    for index, source in enumerate(result.selected, start=1):
        lines.extend(
            [
                f"### {index}. `{redact_text(source.path)[0]}`",
                "",
                f"_Origin: {source.origin}; sections: {', '.join(source.sections) or 'all'}; "
                f"SHA-256: `{source.source_hash}`._",
                "",
                source.excerpt,
                "",
            ]
        )
    if not result.selected:
        lines.append("No readable context sources were selected. Review the warnings and route configuration.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_compact_markdown(result: BuildResult) -> str:
    """Budget the complete reading artifact without silently dropping required text."""
    lines = [
        "# Task Context",
        "",
        f"> Compact reading view; current sources remain authoritative. Full audit: `{result.task_hash}.md`.",
        f"> Built {result.generated_at}; manifest SHA-256 prefix `{result.route_manifest_hash[:12]}`.",
        "",
        f"Task: {result.task}",
        f"Route: {result.route_id}; search: {result.search_status}; complete-output limit: {result.max_chars} characters.",
        "",
        "## Warnings",
        "",
        *(f"- {warning}" for warning in result.warnings or ["(none)"]),
        "",
        "## Gaps",
        "",
        *(f"- {gap}" for gap in result.gaps or ["(none)"]),
    ]
    if result.expansion_notes:
        lines.extend(["", "## Explicit Expansion", "", f"Reason: {result.expansion_reason}"])
        lines.extend(f"- {note}" for note in result.expansion_notes)
    drops = Counter(source.reason.split(":", 1)[0] for source in result.dropped)
    lines.extend(["", "## Selection", "",
                  f"{len(result.selected)}/{result.max_docs} sources; {len(result.dropped)} dropped candidates. "
                  + (", ".join(f"{reason}={count}" for reason, count in sorted(drops.items())) or "No drops.")])
    lines.append("Full drop details and full hashes are in the audit; `explain` also lists decisions.")
    introduction = "\n".join(lines)
    omitted = "[Omitted from compact view to preserve the complete-output budget; inspect the full audit.]"
    clipped = "\n[Clipped in compact view to preserve the complete-output budget; inspect the full audit.]"
    headings: list[str] = []
    excerpts: list[str] = []
    mandatory: list[bool] = []
    for source in result.selected:
        projected = source.compact_excerpt is not None
        headings.append(
            f"### `{redact_text(source.path)[0]}`\n\n"
            f"{source.selection_reason}; {_table_cell(', '.join(source.sections) or 'all')}; SHA-256 prefix `{source.source_hash[:12]}`."
            + (" Compact memory projection; raw index and evidence hashes remain in the audit." if projected else "")
        )
        required = source.origin in {"routed-required", "explicit-expansion"}
        mandatory.append(required)
        excerpts.append((source.compact_excerpt if projected else source.excerpt) if required else omitted)

    def compose() -> str:
        blocks = [f"{heading}\n\n{excerpt}" for heading, excerpt in zip(headings, excerpts)]
        return introduction + ("\n\n" + "\n\n".join(blocks) if blocks else "\n\nNo readable context sources selected.") + "\n"

    rendered = compose()
    if len(rendered) > result.max_chars:
        raise TaskContextError(
            f"Compact context needs {len(rendered)} characters for required/explicit excerpts and diagnostics, "
            f"exceeding the {result.max_chars}-character limit. Full audit: {result.task_hash}.md; use --view full "
            "or narrow explicit ranges. Required content was not silently omitted."
        )
    for index, source in enumerate(result.selected):
        if mandatory[index]:
            continue
        excerpt = source.compact_excerpt if source.compact_excerpt is not None else source.excerpt
        capacity = result.max_chars - len(rendered) + len(excerpts[index])
        if len(excerpt) <= capacity:
            excerpts[index] = excerpt
        elif capacity > len(clipped):
            excerpts[index] = excerpt[:capacity - len(clipped)].rstrip() + clipped
        rendered = compose()
    return rendered


def render_explanation(result: BuildResult) -> str:
    lines = [
        f"Route: {result.route_id} ({result.route_heading})",
        f"Search: {result.search_status}",
        f"Budget: {len(result.selected)}/{result.max_docs} documents, "
        f"{result.selected_chars}/{result.max_chars} characters",
        "Selected:",
    ]
    lines.extend(
        f"- {redact_text(source.path)[0]} [{source.origin}] {source.selection_reason} "
        f"chars={source.char_count} sha256={source.source_hash[:12]}"
        for source in result.selected
    )
    if not result.selected:
        lines.append("- (none)")
    lines.append("Dropped:")
    lines.extend(f"- {redact_text(source.path)[0]} [{source.origin}] {redact_text(source.reason)[0]}" for source in result.dropped)
    if not result.dropped:
        lines.append("- (none)")
    lines.append("Warnings:")
    lines.extend(f"- {warning}" for warning in result.warnings)
    if not result.warnings:
        lines.append("- (none)")
    lines.append("Gaps:")
    lines.extend(f"- {gap}" for gap in result.gaps)
    if not result.gaps:
        lines.append("- (none)")
    if result.expansion_notes:
        lines.extend(["Explicit expansion:", f"Reason: {result.expansion_reason}"])
        lines.extend(f"- {note}" for note in result.expansion_notes)
    return "\n".join(lines) + "\n"


def bundle_path(root: Path, result: BuildResult) -> Path:
    return root / ".agent" / "context-cache" / "task-context" / f"{result.task_hash}.md"


def materialize_bundle(root: Path, result: BuildResult) -> Path:
    destination = bundle_path(root, result)
    _write_bundle(destination, render_markdown(result))
    try:
        # A new full-only build must not leave an older companion looking current.
        destination.with_suffix(".read.md").unlink(missing_ok=True)
    except OSError as exc:
        raise TaskContextError("Full audit was written, but its stale reading companion could not be removed.") from exc
    return destination


def materialize_reading_bundle(root: Path, result: BuildResult) -> Path:
    destination = bundle_path(root, result).with_suffix(".read.md")
    try:
        content = render_compact_markdown(result)
    except TaskContextError:
        # Do not leave a previous reading view looking current after a failed rebuild.
        try:
            destination.unlink(missing_ok=True)
        except OSError as exc:
            raise TaskContextError("Compact rebuild failed and its stale reading artifact could not be removed.") from exc
        raise
    return _write_bundle(destination, content)


def _write_bundle(destination: Path, content: str) -> Path:
    temporary = destination.parent / f".{destination.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, destination)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise TaskContextError(f"Could not materialize task-context bundle: {exc}") from exc
    return destination
