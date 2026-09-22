"""Offline catalog validation or explicit, observational Jev measurements."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.decision_advice import (  # noqa: E402
    DEFAULT_MODEL, INSUFFICIENT, OUT_OF_SCOPE, DecisionAdvice, DecisionCatalog,
    JevProvider, load_catalog,
)


def validate_cases(data: dict, catalog: DecisionCatalog) -> list[str]:
    errors = []
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("cases"), list):
        return ["Expected a version 1 object with cases."]
    if not isinstance(data.get("label_source"), str) or not data["label_source"].strip():
        errors.append("Labels require a review provenance note.")
    seen = set()
    if not data["cases"]:
        errors.append("At least one case is required.")
    for case in data["cases"]:
        if not isinstance(case, dict):
            errors.append("Cases must be objects.")
            continue
        name = case.get("id")
        if not isinstance(name, str) or not name or name in seen:
            errors.append("Case IDs must be nonempty and unique.")
        elif name:
            seen.add(name)
        if not isinstance(case.get("task"), str) or not case["task"].strip():
            errors.append(f"{name}: missing task")
        if not isinstance(case.get("route"), str) or case["route"] not in set(catalog.routes) | {INSUFFICIENT, OUT_OF_SCOPE}:
            errors.append(f"{name}: unknown route")
        skills = case.get("skills")
        if not isinstance(skills, list) or not all(isinstance(s, str) and s in catalog.skills for s in skills):
            errors.append(f"{name}: unknown skills")
        elif len(set(skills)) != len(skills):
            errors.append(f"{name}: duplicate skills")
        if type(case.get("clarification")) is not bool:
            errors.append(f"{name}: clarification must be boolean")
    return errors


def summarize(cases: list[dict], advice: list[DecisionAdvice]) -> dict:
    if len(cases) != len(advice):
        raise ValueError("Every attempted case must have a result.")
    valid = [(c, a) for c, a in zip(cases, advice) if a.status == "ok"]
    n = len(cases)
    route_correct = sum(a.route == c["route"] for c, a in valid)
    skill_errors = [(p - float(s in c["skills"])) ** 2 for c, a in valid for s, p in a.skill_probabilities.items()]
    route_errors = [sum((p - float(r == c["route"])) ** 2 for r, p in a.route_probabilities.items()) for c, a in valid]
    clarify_errors = [(a.clarification_probability - float(c["clarification"])) ** 2 for c, a in valid]
    skill_correct = sum((p >= 0.5) == (s in c["skills"]) for c, a in valid for s, p in a.skill_probabilities.items())
    average = lambda values: sum(values) / len(values) if values else None
    return {
        "attempted": n, "available": len(valid), "unavailable": n - len(valid),
        "route_accuracy_all_attempts": route_correct / n if n else None,
        "route_accuracy_available": route_correct / len(valid) if valid else None,
        "abstentions": sum(a.route == INSUFFICIENT for _, a in valid),
        "skill_accuracy_available": skill_correct / len(skill_errors) if skill_errors else None,
        "clarification_accuracy_available": average([float((a.clarification_probability >= 0.5) == c["clarification"]) for c, a in valid]),
        "route_brier": average(route_errors), "skill_brier": average(skill_errors),
        "clarification_brier": average(clarify_errors),
        "mean_latency_seconds": average([a.latency_seconds for a in advice]),
        "billed_cost": None,
        "calibration_note": "Brier scores use probabilities, not vendor confidence. Small synthetic samples do not establish production calibration.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly send labeled synthetic tasks to Jev.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--case", action="append", default=[], help="Select case IDs; may repeat.")
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(ROOT)
        data = json.loads((ROOT / "eval/advice/cases.json").read_text(encoding="utf-8"))
        errors = validate_cases(data, catalog)
        if errors:
            for error in errors:
                print(f"FAIL {error}", file=sys.stderr)
            return 2
        unknown = set(args.case) - {c["id"] for c in data["cases"] if isinstance(c, dict) and isinstance(c.get("id"), str)}
        if unknown:
            errors.append(f"Unknown cases: {sorted(unknown)}")
        if errors:
            for error in errors:
                print(f"FAIL {error}", file=sys.stderr)
            return 2
        cases = [c for c in data["cases"] if not args.case or c["id"] in args.case]
        if not args.live:
            print(f"Shadow advice fixtures valid: {len(cases)} cases. Live effectiveness: not yet measured.")
            return 0
        provider = JevProvider(model=args.model)
        results = [provider.advise(c["task"], catalog, live=True) for c in cases]
        report = {"schema_version": 1, "mode": "shadow", "requested_model": args.model,
            "label_source": data["label_source"], "metrics": summarize(cases, results),
            "cases": [{"id": c["id"], "task_sha256": hashlib.sha256(c["task"].encode()).hexdigest(),
                       "advice": asdict(a)} for c, a in zip(cases, results)]}
        destination = ROOT / ".agent/traces/evals" / ("jev-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8] + ".json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Shadow report: {destination}\n{json.dumps(report['metrics'], sort_keys=True)}")
        return 1 if any(a.status != "ok" for a in results) else 0
    except (OSError, ValueError) as exc:
        print(f"Advice evaluation configuration error: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
