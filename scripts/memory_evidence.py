"""Safe, portable source fingerprints for manually reviewed memory cards."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_BYTES = 1_000_000


class EvidenceError(ValueError):
    """A source cannot safely be used as memory evidence."""


def _sensitive(parts: tuple[str, ...]) -> bool:
    lowered = [part.casefold() for part in parts]
    name = lowered[-1]
    return (
        ".git" in lowered
        or any(part in {".ssh", ".aws", "secrets", "credentials"} for part in lowered)
        or name == ".env"
        or name.startswith(".env.")
        or name in {"id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
        or name.endswith((".pem", ".key", ".p12", ".pfx"))
    )


def safe_path(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or any(ord(char) < 32 for char in relative):
        raise EvidenceError("expected a repository-relative path with forward slashes")
    parts = PurePosixPath(relative).parts
    if relative.startswith("/") or not parts or any(part in {".", ".."} for part in relative.split("/")):
        raise EvidenceError("absolute paths and path traversal are not allowed")
    if _sensitive(parts):
        raise EvidenceError("sensitive or repository-internal source is not allowed")
    try:
        resolved_root = root.resolve()
        path = (root / relative).resolve()
    except (OSError, RuntimeError) as exc:
        raise EvidenceError("source cannot be resolved safely") from exc
    if not path.is_relative_to(resolved_root):
        raise EvidenceError("source resolves outside the repository")
    resolved_parts = path.relative_to(resolved_root).parts
    if resolved_parts and _sensitive(resolved_parts):
        raise EvidenceError("source resolves to a sensitive or repository-internal file")
    return path


def read_source(root: Path, relative: object) -> str:
    path = safe_path(root, relative)
    if not path.is_file():
        raise EvidenceError("source file is missing")
    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            raise EvidenceError(f"source exceeds {MAX_SOURCE_BYTES} bytes")
        raw = path.read_bytes()
        if len(raw) > MAX_SOURCE_BYTES:
            raise EvidenceError(f"source exceeds {MAX_SOURCE_BYTES} bytes")
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise EvidenceError(f"source is not readable UTF-8 ({type(exc).__name__})") from exc
    if "\0" in text:
        raise EvidenceError("binary source is not allowed")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def source_sha256(root: Path, relative: str) -> str:
    resolved = safe_path(root, relative)
    if resolved == (root / ".agent/memory/index.json").resolve():
        raise EvidenceError("the memory index cannot be its own evidence")
    return hashlib.sha256(read_source(root, relative).encode("utf-8")).hexdigest()


def capture_evidence(root: Path, paths: list[str]) -> list[dict[str, str]]:
    return [{"path": path, "sha256": source_sha256(root, path)} for path in dict.fromkeys(paths)]


@dataclass
class EvidenceReport:
    status: str
    details: list[str] = field(default_factory=list)


def inspect_evidence(root: Path, entry: dict, *, required: bool = False) -> EvidenceReport:
    if "evidence" not in entry:
        return EvidenceReport("missing-evidence" if required else "untracked", ["no source fingerprints recorded"])
    evidence = entry["evidence"]
    if not isinstance(evidence, list) or not evidence:
        return EvidenceReport("invalid-evidence", ["evidence must be a non-empty list"])
    errors: list[str] = []
    missing: list[str] = []
    changed: list[str] = []
    seen: set[str] = set()
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("each evidence item requires exactly path and sha256")
            continue
        path, expected = item["path"], item["sha256"]
        if not isinstance(path, str):
            errors.append("evidence path must be a string")
            continue
        if path.casefold() in seen:
            errors.append(f"duplicate evidence path: {path}")
        seen.add(path.casefold())
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"{path}: sha256 must be 64 lowercase hexadecimal characters")
            continue
        try:
            actual = source_sha256(root, path)
        except (EvidenceError, OSError) as exc:
            message = f"{path}: {exc}"
            (missing if str(exc) == "source file is missing" else errors).append(message)
            continue
        if actual != expected:
            changed.append(f"{path}: content changed; review the memory claim before refreshing evidence")
    details = errors + missing + changed
    if errors:
        return EvidenceReport("invalid-evidence", details)
    if missing:
        return EvidenceReport("missing-evidence", details)
    return EvidenceReport("needs-reverification" if changed else "unchanged", details)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture fingerprints after reviewing memory evidence sources.")
    parser.add_argument("paths", nargs="+", help="Reviewed repository-relative UTF-8 source files.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        evidence = capture_evidence(args.root, args.paths)
    except (EvidenceError, OSError) as exc:
        parser.exit(1, f"Cannot capture evidence: {exc}\n")
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
