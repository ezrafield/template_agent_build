"""Read a compact, bounded view of memory metadata without changing the index."""

from __future__ import annotations

import argparse
from datetime import date
import html
import json
from pathlib import Path
import re
import sys

try:
    from scripts.memory_evidence import EvidenceError, MAX_SOURCE_BYTES, inspect_evidence, read_source, safe_path
    from scripts.run_agent_hook import SECRET_PATTERNS
    from scripts.validate_memory_links import REQUIRED_ENTRY_FIELDS, VALID_CONFIDENCE, VALID_TYPES, legacy_relative
except ImportError:  # direct script execution
    from memory_evidence import EvidenceError, MAX_SOURCE_BYTES, inspect_evidence, read_source, safe_path
    from run_agent_hook import SECRET_PATTERNS
    from validate_memory_links import REQUIRED_ENTRY_FIELDS, VALID_CONFIDENCE, VALID_TYPES, legacy_relative


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIMIT = 10
MAX_LIMIT = 20
MAX_ENTRIES = 1000
MAX_OUTPUT_CHARS = 12_000
MAX_EVIDENCE_REFERENCES = 128
STOP_WORDS = {"a", "an", "and", "are", "be", "for", "from", "how", "i", "in", "is", "it", "of", "on", "or", "the", "this", "to", "use", "with"}
ASSIGNMENT = re.compile(r'''(?i)\b(password|token|api[-_]?key|secret|jwt[-_]?key)(\s*[:=]\s*)("[^"\n]*"|'[^'\n]*'|[^<\s]+)''')
URL_CREDENTIALS = re.compile(r"https?://[^/\s:@]+:[^@\s]+@")


class MemoryLookupError(ValueError):
    """Invalid or unsafe lookup input; errors never repeat raw index values."""


def _redact(text: str) -> str:
    if re.search(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----", text):
        return "<REDACTED-PRIVATE-KEY>"
    text = URL_CREDENTIALS.sub("<REDACTED-URL>@", text)
    text = ASSIGNMENT.sub(lambda match: match[1] + match[2] + "<REDACTED-SECRET>", text)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("<REDACTED-SECRET>", text)
    return text


def _cell(text: str, limit: int) -> str:
    text = " ".join(_redact(text).split())
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`|\[\]*_!])", r"\\\1", text)


def _entries(index_text: str, root: Path) -> list[dict]:
    try:
        if not isinstance(index_text, str) or len(index_text.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise MemoryLookupError("Memory index exceeds the UTF-8 input limit.")
        data = json.loads(index_text)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise MemoryLookupError("Memory index must be valid UTF-8 JSON.") from exc
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise MemoryLookupError("Memory index must be an object with version 1.")
    entries = data.get("memories")
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise MemoryLookupError(f"Memory index requires a list of at most {MAX_ENTRIES} entries.")
    seen: set[str] = set()
    for position, entry in enumerate(entries, 1):
        prefix = f"Memory entry {position}"
        if not isinstance(entry, dict) or not REQUIRED_ENTRY_FIELDS.issubset(entry):
            raise MemoryLookupError(f"{prefix} lacks required metadata.")
        if any(not isinstance(entry[key], str) or not entry[key].strip() or len(entry[key]) > 4096 for key in REQUIRED_ENTRY_FIELDS - {"keywords"}):
            raise MemoryLookupError(f"{prefix} requires non-empty bounded text metadata.")
        if entry["id"].casefold() in seen:
            raise MemoryLookupError(f"{prefix} repeats a memory ID.")
        seen.add(entry["id"].casefold())
        if entry["type"] not in VALID_TYPES or entry["confidence"] not in VALID_CONFIDENCE:
            raise MemoryLookupError(f"{prefix} has an invalid type or confidence.")
        try:
            date.fromisoformat(entry["last_verified"])
            safe_path(root, legacy_relative(entry["path"]))
            safe_path(root, legacy_relative(entry["source_task"]))
            if "verification_record" in entry:
                safe_path(root, legacy_relative(entry["verification_record"]))
        except (EvidenceError, OSError, ValueError) as exc:
            raise MemoryLookupError(f"{prefix} has an invalid date or unsafe path.") from exc
        keywords = entry["keywords"]
        if not isinstance(keywords, list) or len(keywords) > 64 or any(not isinstance(word, str) or len(word) > 256 for word in keywords):
            raise MemoryLookupError(f"{prefix} requires bounded text keywords.")
        evidence = entry.get("evidence")
        if isinstance(evidence, list) and len(evidence) > MAX_EVIDENCE_REFERENCES:
            raise MemoryLookupError(f"{prefix} has too many evidence references.")
    return entries


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", text.casefold())) - STOP_WORDS


def _score(entry: dict, query: str) -> int:
    if not query:
        return 1
    path = legacy_relative(entry["path"]).casefold()
    if "/" in query:
        return 2000 if query in path else 0
    if query == entry["id"].casefold():
        return 2000
    fields = [entry["id"], entry["scope"], entry["summary"], path, *entry["keywords"]]
    normalized = [" ".join(value.casefold().split()) for value in fields]
    if query in normalized:
        return 1000
    terms = _tokens(query)
    return sum(len(terms & _tokens(value)) for value in fields)


def render_lookup(root: Path, query: str = "", limit: int = DEFAULT_LIMIT, *, index_text: str | None = None) -> str:
    """Return Markdown using supplied index text, or safely read the current index.

    Evidence status is checked against current local sources for displayed rows.
    No index/card/evidence state is mutated. Raises MemoryLookupError on bad input.
    """
    if not isinstance(query, str) or len(query) > 512:
        raise MemoryLookupError("Lookup query must contain at most 512 characters.")
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise MemoryLookupError(f"Lookup limit must be between 1 and {MAX_LIMIT}.")
    root = Path(root)
    if index_text is None:
        try:
            index_text = read_source(root, ".agent/memory/index.json")
        except (EvidenceError, OSError) as exc:
            raise MemoryLookupError("Memory index is missing, unsafe, oversized, or not readable UTF-8.") from exc
    entries = _entries(index_text, root)
    query = " ".join(legacy_relative(query).casefold().split())
    ranked = [(score, position, entry) for position, entry in enumerate(entries) if (score := _score(entry, query))]
    if any(score == 2000 for score, _, _ in ranked):
        ranked = [item for item in ranked if item[0] == 2000]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    candidates = ranked[:limit]
    reference_count = sum(len(entry.get("evidence", [])) for _, _, entry in candidates if isinstance(entry.get("evidence", []), list))
    if reference_count > MAX_EVIDENCE_REFERENCES:
        raise MemoryLookupError("Lookup would check too many evidence sources; reduce --limit.")
    lines = ["# Memory lookup", "", "| ID | Path | Summary | Evidence |", "| --- | --- | --- | --- |"]
    shown = 0
    for _, _, entry in candidates:
        status = inspect_evidence(root, entry).status
        if not safe_path(root, legacy_relative(entry["path"])).is_file():
            status += "; card missing"
        row = f"| {_cell(entry['id'], 120)} | {_cell(legacy_relative(entry['path']), 400)} | {_cell(entry['summary'], 320)} | {status} |"
        if sum(len(line) + 1 for line in lines) + len(row) + 350 > MAX_OUTPUT_CHARS:
            break
        lines.append(row)
        shown += 1
    if not ranked:
        lines.append("| (none) | — | No matching memories. | — |")
    lines.extend(["", f"Shown {shown} of {len(ranked)} matching entries ({len(entries)} indexed)."])
    if shown < len(ranked):
        lines.append("Results omitted by the entry/output limit; narrow the query for other memories.")
    lines.append("Long fields may be shortened. Evidence describes current source fingerprints, not claim truth; verify selected cards before use.")
    return "\n".join(lines) + "\n"


class _LookupParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, f"memory_lookup: {_redact(message)[:512]}\n")


def main(argv: list[str] | None = None) -> int:
    parser = _LookupParser(description="List concise memory summaries and live evidence status without hashes.")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        output = render_lookup(args.root, args.query, args.limit)
    except MemoryLookupError as exc:
        print(f"memory_lookup: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
