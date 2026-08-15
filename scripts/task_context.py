from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from scripts.task_context_engine import (
        TaskContextError,
        build_task_context,
        materialize_bundle,
        render_explanation,
        render_markdown,
    )
except ImportError:  # pragma: no cover - direct script execution path
    from task_context_engine import (  # type: ignore
        TaskContextError,
        build_task_context,
        materialize_bundle,
        render_explanation,
        render_markdown,
    )


ROOT = Path(__file__).resolve().parents[1]


def _add_build_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("task", help="Task text used to classify and build context.")
    parser.add_argument("--route", help="Use an explicit route ID instead of classification.")
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Disable optional Semble advisory search.",
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_context.py",
        description="Build and explain routed Markdown context for one agent task.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build and cache a Markdown bundle.")
    _add_build_arguments(build_parser)
    build_parser.add_argument(
        "--stdout",
        action="store_true",
        help="Also write the complete Markdown bundle to stdout.",
    )

    explain_parser = subparsers.add_parser(
        "explain", help="Print selection, drops, gaps, and warnings without writing a bundle."
    )
    _add_build_arguments(explain_parser)
    return parser


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    args = create_parser().parse_args(argv)
    repository_root = (root or ROOT).resolve()
    try:
        result = build_task_context(
            args.task,
            repository_root,
            route_id=args.route,
            use_search=not args.no_search,
        )
        if args.command == "explain":
            sys.stdout.write(render_explanation(result))
            return 0

        destination = materialize_bundle(repository_root, result)
        if args.stdout:
            sys.stdout.write(render_markdown(result))
        else:
            print(f"Task context written: {destination}")
            print(
                f"Route={result.route_id} docs={len(result.selected)}/{result.max_docs} "
                f"chars={result.selected_chars}/{result.max_chars} search={result.search_status}"
            )
        for warning in result.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        return 0
    except TaskContextError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
