import argparse
import fnmatch
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath


MANIFEST = "agentkit-manifest.json"
BEGIN = "<!-- agentkit:begin -->"
END = "<!-- agentkit:end -->"
STATE_FILE = ".agentkit-installed-files"


def load_manifest(source: Path) -> dict:
    return json.loads((source / MANIFEST).read_text(encoding="utf-8"))


def iter_manifest_paths(
    source: Path,
    entries: list[str],
    excluded: list[str] | None = None,
) -> list[Path]:
    excluded = excluded or []
    paths: list[Path] = []
    for entry in entries:
        full = source / entry
        if entry.endswith("/") and full.exists():
            for directory, directory_names, file_names in os.walk(full):
                directory_path = Path(directory)
                directory_names[:] = [
                    name
                    for name in directory_names
                    if not is_excluded(
                        (directory_path / name).relative_to(source).as_posix() + "/",
                        excluded,
                    )
                ]
                paths.extend(
                    directory_path / name
                    for name in file_names
                    if not is_excluded(
                        (directory_path / name).relative_to(source).as_posix(),
                        excluded,
                    )
                )
        elif full.exists() and full.is_file():
            if not is_excluded(full.relative_to(source).as_posix(), excluded):
                paths.append(full)
    return sorted(set(paths))


def is_excluded(relative: str, patterns: list[str]) -> bool:
    normalized = relative.replace("\\", "/")
    for pattern in patterns:
        if pattern.endswith("/"):
            directory_name = pattern.rstrip("/")
            if "/" not in directory_name and directory_name in PurePosixPath(normalized).parts:
                return True
            if normalized.startswith(pattern) or fnmatch.fnmatch(normalized, f"*/{pattern}*"):
                return True
        if fnmatch.fnmatch(normalized, pattern):
            return True
    return False


def backup_existing(target_root: Path, relative: Path, backup_root: Path) -> None:
    target = target_root / relative
    if not target.exists() and not target.is_symlink():
        return
    backup = backup_root / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    if target.is_dir() and not target.is_symlink():
        shutil.copytree(target, backup, dirs_exist_ok=True)
    else:
        shutil.copy2(target, backup, follow_symlinks=False)


def copy_file(source_root: Path, target_root: Path, source_file: Path, backup_root: Path) -> str:
    relative_path = source_file.relative_to(source_root)
    target = target_root / relative_path
    backup_existing(target_root, relative_path, backup_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target)
    return relative_path.as_posix()


def copy_if_missing(source_root: Path, target_root: Path, relative_name: str) -> str | None:
    source = source_root / relative_name
    target = target_root / relative_name
    if not source.exists():
        return None
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return Path(relative_name).as_posix()


def merge_file(source_root: Path, target_root: Path, relative_name: str, backup_root: Path) -> str:
    source = source_root / relative_name
    target = target_root / relative_name
    source_text = source.read_text(encoding="utf-8").strip()

    if target.exists():
        target_text = target.read_text(encoding="utf-8")
        if BEGIN in target_text and END in target_text:
            before = target_text.split(BEGIN, 1)[0].rstrip()
            after = target_text.split(END, 1)[1].lstrip()
            merged = f"{before}\n\n{BEGIN}\n{source_text}\n{END}\n"
            if after:
                merged += f"\n{after}"
        else:
            merged = f"{target_text.rstrip()}\n\n{BEGIN}\n{source_text}\n{END}\n"
        backup_existing(target_root, Path(relative_name), backup_root)
    else:
        merged = f"{BEGIN}\n{source_text}\n{END}\n"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(merged, encoding="utf-8")
    return Path(relative_name).as_posix()


def create_symlink(source_root: Path, target_root: Path, item: dict, backup_root: Path) -> str:
    link = Path(item["link"])
    target_name = Path(item["target"])
    link_path = target_root / link
    source_target = source_root / target_name
    backup_existing(target_root, link, backup_root)
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_dir() and not link_path.is_symlink():
            shutil.rmtree(link_path)
        else:
            link_path.unlink()
    link_path.symlink_to(source_target, target_is_directory=source_target.is_dir())
    return link.as_posix()


def read_installed_state(target: Path) -> set[str]:
    path = target / STATE_FILE
    if not path.exists():
        return set()
    return {
        line.strip().replace("\\", "/")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def safe_recorded_relative(value: str) -> Path | None:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        return None
    return Path(*pure.parts)


def remove_empty_parents(path: Path, stop: Path) -> None:
    current = path.parent
    while current != stop and current.is_relative_to(stop):
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def prune_stale_files(
    target: Path,
    previous: set[str],
    current: set[str],
    protected: set[str],
    backup_root: Path,
) -> list[str]:
    removed: list[str] = []
    for value in sorted(previous - current - protected):
        relative_path = safe_recorded_relative(value)
        if relative_path is None:
            print(f"Skipping unsafe stale path from {STATE_FILE}: {value}")
            continue
        target_path = target / relative_path
        if not target_path.exists() and not target_path.is_symlink():
            continue
        backup_existing(target, relative_path, backup_root)
        if target_path.is_dir() and not target_path.is_symlink():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
        remove_empty_parents(target_path, target)
        removed.append(value)
    return removed


def validate_manifest(source: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if not isinstance(manifest.get("version"), str):
        errors.append("version must be a string")
    entries = manifest.get("included_harness_files")
    if not isinstance(entries, list) or not all(isinstance(entry, str) for entry in entries):
        errors.append("included_harness_files must be a string list")
    else:
        for entry in entries:
            if not (source / entry).exists():
                errors.append(f"included harness entry is missing: {entry}")

    skills = manifest.get("skills")
    if not isinstance(skills, list):
        errors.append("skills must be a list")
    else:
        names: list[str] = []
        for skill in skills:
            if not isinstance(skill, dict):
                errors.append("skill entries must be objects")
                continue
            name = skill.get("name")
            path = skill.get("path")
            if not isinstance(name, str) or not isinstance(path, str):
                errors.append("each skill needs string name and path values")
                continue
            names.append(name)
            if not (source / path / "SKILL.md").is_file():
                errors.append(f"skill is missing SKILL.md: {name}")
        if len(names) != len(set(names)):
            errors.append("skill names must be unique")
    return errors


def command_available(command: str, source: Path) -> bool:
    if command == "python":
        return bool(sys.executable)
    if shutil.which(command) is not None:
        return True
    executable_name = command + (".exe" if sys.platform == "win32" else "")
    project_candidates = {
        "semble": source / "tools" / "agent" / "python" / "semble" / ".venv" / (
            "Scripts" if sys.platform == "win32" else "bin"
        ) / executable_name,
        "serena": source / "tools" / "agent" / "python" / "serena" / ".venv" / (
            "Scripts" if sys.platform == "win32" else "bin"
        ) / executable_name,
        "rtk": source / "tools" / "agent" / "bin" / executable_name,
    }
    candidate = project_candidates.get(command)
    return candidate is not None and candidate.is_file()


def check(source: Path, target: Path) -> int:
    manifest = load_manifest(source)
    errors = validate_manifest(source, manifest)
    runtime = manifest.get("runtime", {}) if isinstance(manifest.get("runtime"), dict) else {}
    required = runtime.get("required_commands", [])
    optional = runtime.get("optional_commands", [])
    missing_required = [command for command in required if not command_available(command, source)]
    missing_optional = [command for command in optional if not command_available(command, source)]
    errors.extend(f"required command is unavailable: {command}" for command in missing_required)

    installed_state = read_installed_state(target)
    is_installed_target = source.resolve() != target.resolve() or bool(installed_state)
    if is_installed_target:
        excluded = manifest.get("excluded_files", []) + manifest.get("project_local_files", [])
        expected = [
            path.relative_to(source).as_posix()
            for path in iter_manifest_paths(
                source,
                manifest.get("included_harness_files", []),
                excluded,
            )
        ]
        for relative_name in expected:
            if not (target / relative_name).exists():
                errors.append(f"installed harness file is missing: {relative_name}")
        for relative_name in manifest.get("merge_files", []):
            if not (target / relative_name).is_file():
                errors.append(f"installed merged entrypoint is missing: {relative_name}")
        for relative_name in manifest.get("copy_if_missing_files", []):
            if (source / relative_name).is_file() and not (target / relative_name).is_file():
                errors.append(f"installed starter asset is missing: {relative_name}")
        version_path = target / ".agentkit-version"
        installed_version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else ""
        if installed_version != manifest.get("version"):
            errors.append(
                f"installed version is {installed_version or 'missing'}; expected {manifest.get('version')}"
            )

    for command in missing_optional:
        print(f"Optional command unavailable: {command}")
    if errors:
        for error in errors:
            print(f"Agent kit check failed: {error}")
        return 1
    print(f"Agent kit {manifest.get('version')} is structurally valid.")
    return 0


def install(mode: str, source: Path, target: Path) -> None:
    manifest = load_manifest(source)
    manifest_errors = validate_manifest(source, manifest)
    if manifest_errors:
        raise ValueError("; ".join(manifest_errors))

    backup_root = target / ".agentkit" / "backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    previous = read_installed_state(target)
    installed: list[str] = []
    excluded = manifest.get("excluded_files", []) + manifest.get("project_local_files", [])

    for source_file in iter_manifest_paths(
        source,
        manifest.get("included_harness_files", []),
        excluded,
    ):
        relative_name = source_file.relative_to(source).as_posix()
        if is_excluded(relative_name, excluded):
            continue
        installed.append(copy_file(source, target, source_file, backup_root))

    for relative_name in manifest.get("merge_files", []):
        if (source / relative_name).exists():
            installed.append(merge_file(source, target, relative_name, backup_root))

    for relative_name in manifest.get("copy_if_missing_files", []):
        copied = copy_if_missing(source, target, relative_name)
        if copied:
            installed.append(copied)

    for item in manifest.get("symlinks", []):
        installed.append(create_symlink(source, target, item, backup_root))

    current = set(installed)
    protected = set(manifest.get("merge_files", [])) | set(manifest.get("copy_if_missing_files", []))
    removed = (
        prune_stale_files(target, previous, current, protected, backup_root)
        if mode == "update"
        else []
    )

    version = manifest.get("version", "0.0.0")
    (target / ".agentkit-version").write_text(f"{version}\n", encoding="utf-8")
    (target / STATE_FILE).write_text("\n".join(sorted(current)) + "\n", encoding="utf-8")

    print(f"Agent kit {mode} complete: {len(current)} files recorded.")
    if removed:
        print(f"Backed up and pruned {len(removed)} obsolete managed file(s).")
        for value in removed:
            print(f"- {value}")
    if backup_root.exists():
        print(f"Backups written to {backup_root.relative_to(target)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install, update, or check the agent kit.")
    parser.add_argument("mode", choices=["install", "update", "check"])
    parser.add_argument("--source", default=".", help="Agent kit source directory.")
    parser.add_argument("--target", default=".", help="Project directory to install into.")
    args = parser.parse_args(argv)
    source = Path(args.source).resolve()
    target = Path(args.target).resolve()
    try:
        if args.mode == "check":
            return check(source, target)
        install(args.mode, source, target)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Agent kit {args.mode} failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
