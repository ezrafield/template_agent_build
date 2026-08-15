from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_context_engine import (  # noqa: E402
    ROUTE_MANIFEST,
    TaskContextError,
    build_task_context,
    load_route_manifest,
)


DEFAULT_FIXTURES = ROOT / "eval" / "context" / "golden_tasks.json"


def load_fixtures(path: Path) -> list[dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TaskContextError(f"Cannot load golden fixtures {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise TaskContextError("Golden task fixtures must contain an object.")
    defaults = payload.get("defaults")
    cases = payload.get("cases")
    if not isinstance(defaults, dict) or not isinstance(cases, list) or not cases:
        raise TaskContextError("Golden task fixtures require defaults and a non-empty cases list.")
    fixtures: list[dict] = []
    for index, fixture in enumerate(cases):
        if not isinstance(fixture, dict):
            raise TaskContextError(f"Golden fixture at index {index} must be an object.")
        fixture = {**defaults, **fixture}
        for field in ("id", "task", "expected_route"):
            if not isinstance(fixture.get(field), str) or not fixture[field]:
                raise TaskContextError(f"Golden fixture at index {index} requires `{field}`.")
        for field in ("expected_docs", "forbidden_docs", "expected_warning_substrings"):
            values = fixture.get(field)
            if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
                raise TaskContextError(f"Golden fixture `{fixture['id']}` field `{field}` must be a string list.")
        for field in ("max_docs", "max_chars"):
            if not isinstance(fixture.get(field), int) or fixture[field] <= 0:
                raise TaskContextError(
                    f"Golden fixture `{fixture['id']}` field `{field}` must be a positive integer."
                )
        fixtures.append(fixture)
    return fixtures


def matches(paths: list[str], pattern: str) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for path in paths)


def evaluate_fixture(fixture: dict, root: Path) -> tuple[list[str], object]:
    result = build_task_context(fixture["task"], root, use_search=False)
    errors: list[str] = []
    selected_paths = [source.path for source in result.selected]
    if result.route_id != fixture["expected_route"]:
        errors.append(f"route expected {fixture['expected_route']}, got {result.route_id}")
    for pattern in fixture.get("expected_docs", []):
        if not matches(selected_paths, pattern):
            errors.append(f"expected document not selected: {pattern}")
    for pattern in fixture.get("forbidden_docs", []):
        if matches(selected_paths, pattern):
            errors.append(f"forbidden document selected: {pattern}")
    warning_text = "\n".join(result.warnings)
    for expected in fixture.get("expected_warning_substrings", []):
        if expected not in warning_text:
            errors.append(f"expected warning not found: {expected}")
    if result.max_docs != fixture["max_docs"]:
        errors.append(f"document budget expected {fixture['max_docs']}, got {result.max_docs}")
    if result.max_chars != fixture["max_chars"]:
        errors.append(f"character budget expected {fixture['max_chars']}, got {result.max_chars}")
    if len(result.selected) > fixture["max_docs"]:
        errors.append(f"selected {len(result.selected)} documents, limit is {fixture['max_docs']}")
    if result.selected_chars > fixture["max_chars"]:
        errors.append(f"selected {result.selected_chars} characters, limit is {fixture['max_chars']}")
    return errors, result


def run(fixtures_path: Path = DEFAULT_FIXTURES, root: Path = ROOT) -> int:
    fixtures = load_fixtures(fixtures_path)
    manifest, _ = load_route_manifest(root, root / ROUTE_MANIFEST)
    fixture_routes = {fixture["expected_route"] for fixture in fixtures}
    manifest_routes = {route["id"] for route in manifest["routes"]}
    if fixture_routes != manifest_routes:
        missing = sorted(manifest_routes - fixture_routes)
        unknown = sorted(fixture_routes - manifest_routes)
        raise TaskContextError(
            f"Golden route coverage mismatch: missing={missing}, unknown={unknown}"
        )

    failed = 0
    for fixture in fixtures:
        errors, result = evaluate_fixture(fixture, root)
        if errors:
            failed += 1
            print(f"FAIL {fixture['id']}: route={result.route_id}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(
                f"PASS {fixture['id']}: route={result.route_id} "
                f"docs={len(result.selected)} chars={result.selected_chars}"
            )
    if failed:
        print(f"Task-context golden evaluation failed: {failed}/{len(fixtures)} fixtures.")
        return 1
    print(f"Task-context golden evaluation passed: {len(fixtures)} fixtures.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic task-context routes.")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    args = parser.parse_args(argv)
    try:
        return run(args.fixtures.resolve(), ROOT)
    except TaskContextError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
