import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_ROOT = ROOT / "tools" / "agent"
BIN_DIR = TOOL_ROOT / "bin"
DOWNLOAD_DIR = TOOL_ROOT / ".downloads"
RTK_MANIFEST = TOOL_ROOT / "rtk-manifest.json"
UV_CACHE = TOOL_ROOT / ".uv-cache"
NPM_CACHE = TOOL_ROOT / ".npm-cache"
PYTHON_VERSION = "3.13"
PYTHON_PROJECTS = {
    "semble": TOOL_ROOT / "python" / "semble",
    "serena": TOOL_ROOT / "python" / "serena",
}


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def executable_name(name: str) -> str:
    return f"{name}.exe" if is_windows() else name


def venv_bin_dir(project: Path) -> Path:
    return project / ".venv" / ("Scripts" if is_windows() else "bin")


def node_bin_dir() -> Path:
    return TOOL_ROOT / "node_modules" / ".bin"


def local_python_tool(name: str) -> Path:
    return venv_bin_dir(PYTHON_PROJECTS[name]) / executable_name(name)


def which(name: str) -> str | None:
    return shutil.which(name)


def prepare_command(command: list[str]) -> list[str]:
    executable = shutil.which(command[0])
    if not executable:
        raise RuntimeError(f"Required command `{command[0]}` was not found on PATH.")

    if is_windows() and Path(executable).suffix.lower() in {".bat", ".cmd"}:
        return [os.environ.get("ComSpec", "cmd.exe"), "/d", "/c", executable, *command[1:]]
    return [executable, *command[1:]]


def run(command: list[str], *, cwd: Path = TOOL_ROOT, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(command))
    subprocess.run(prepare_command(command), cwd=cwd, env=env, check=True)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rtk_manifest() -> dict:
    return json.loads(RTK_MANIFEST.read_text(encoding="utf-8"))


def current_asset_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {
        "amd64": "x64",
        "x86_64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, machine)

    if system == "windows":
        os_name = "windows"
    elif system == "darwin":
        os_name = "macos"
    elif system == "linux":
        os_name = "linux"
    else:
        os_name = system

    return f"{os_name}-{arch}"


def rtk_path() -> Path:
    return BIN_DIR / executable_name("rtk")


def rtk_version_ok(path: Path, expected_version: str) -> bool:
    if not path.exists():
        return False
    try:
        result = subprocess.run(
            [str(path), "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    output = f"{result.stdout}\n{result.stderr}"
    return result.returncode == 0 and expected_version.lstrip("v") in output


def download_asset(asset: dict) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    archive = DOWNLOAD_DIR / asset["name"]
    if archive.exists() and hash_file(archive) == asset["sha256"]:
        return archive

    if archive.exists():
        archive.unlink()

    print(f"Downloading {asset['url']}")
    urllib.request.urlretrieve(asset["url"], archive)
    actual_hash = hash_file(archive)
    if actual_hash != asset["sha256"]:
        archive.unlink(missing_ok=True)
        raise RuntimeError(
            f"Checksum mismatch for {asset['name']}: expected {asset['sha256']}, got {actual_hash}"
        )
    return archive


def ensure_within_directory(root: Path, target: Path) -> None:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    if not target_resolved.is_relative_to(root_resolved):
        raise RuntimeError(f"Unsafe archive member path: {target}")


def extract_archive(archive: Path, destination: Path) -> None:
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zip_handle:
            for member in zip_handle.infolist():
                ensure_within_directory(destination, destination / member.filename)
            zip_handle.extractall(destination)
        return

    if archive.name.endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as tar_handle:
            for member in tar_handle.getmembers():
                ensure_within_directory(destination, destination / member.name)
            tar_handle.extractall(destination)
        return

    raise RuntimeError(f"Unsupported RTK archive format: {archive.name}")


def install_rtk() -> None:
    manifest = load_rtk_manifest()
    expected_version = manifest["version"]
    target = rtk_path()
    if rtk_version_ok(target, expected_version):
        print(f"RTK {expected_version} already installed at {target.relative_to(ROOT)}")
        return

    asset_key = current_asset_key()
    asset = manifest["assets"].get(asset_key)
    if not asset:
        supported = ", ".join(sorted(manifest["assets"]))
        raise RuntimeError(f"No RTK asset for platform {asset_key}. Supported: {supported}")

    archive = download_asset(asset)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rtk-extract-") as temp_name:
        temp_dir = Path(temp_name)
        extract_archive(archive, temp_dir)
        matches = [
            path
            for path in temp_dir.rglob(asset["executable"])
            if path.is_file() and path.name.lower() == asset["executable"].lower()
        ]
        if not matches:
            raise RuntimeError(f"Could not find {asset['executable']} in {asset['name']}")
        shutil.copy2(matches[0], target)

    if not is_windows():
        target.chmod(0o755)

    if not rtk_version_ok(target, expected_version):
        raise RuntimeError(f"Installed RTK did not report expected version {expected_version}")
    print(f"Installed RTK {expected_version} at {target.relative_to(ROOT)}")


def sync_python_tools() -> None:
    if not which("uv"):
        raise RuntimeError("uv is required. Install uv first, then rerun make agent-tools-install.")
    env = os.environ.copy()
    env["UV_CACHE_DIR"] = str(UV_CACHE)
    for name, project in PYTHON_PROJECTS.items():
        print(f"Syncing Python tool environment: {name}")
        run(["uv", "sync", "--frozen", "--link-mode", "copy", "--python", PYTHON_VERSION], cwd=project, env=env)


def sync_node_tools() -> None:
    if not which("node"):
        raise RuntimeError("node is required. Install Node.js >=22, then rerun make agent-tools-install.")
    if not which("npm"):
        raise RuntimeError("npm is required. Install npm, then rerun make agent-tools-install.")

    command = ["npm", "ci", "--no-audit", "--no-fund", "--cache", str(NPM_CACHE)]
    if not (TOOL_ROOT / "package-lock.json").exists():
        command = ["npm", "install", "--no-audit", "--no-fund", "--cache", str(NPM_CACHE)]
    run(command)


def check_executable(name: str, dirs: list[Path]) -> bool:
    search_path = os.pathsep.join(str(path) for path in dirs)
    return shutil.which(name, path=search_path) is not None


def local_python_version(project: Path) -> str | None:
    cfg = project / ".venv" / "pyvenv.cfg"
    if not cfg.exists():
        return None
    for line in cfg.read_text(encoding="utf-8").splitlines():
        if line.startswith("version_info = "):
            return line.split("=", 1)[1].strip()
    return None


def collect_check_issues() -> list[str]:
    issues: list[str] = []

    for command in ["uv", "node", "npm"]:
        if not which(command):
            issues.append(f"Missing prerequisite `{command}` on PATH.")

    for path in [
        TOOL_ROOT / "python" / "semble" / "pyproject.toml",
        TOOL_ROOT / "python" / "semble" / "uv.lock",
        TOOL_ROOT / "python" / "serena" / "pyproject.toml",
        TOOL_ROOT / "python" / "serena" / "uv.lock",
        TOOL_ROOT / "package.json",
        TOOL_ROOT / "package-lock.json",
        RTK_MANIFEST,
    ]:
        if not path.exists():
            issues.append(f"Missing committed tool file: {path.relative_to(ROOT)}")

    for name in ["semble", "serena"]:
        if not local_python_tool(name).exists():
            issues.append(
                f"Missing Python tool `{name}` in {venv_bin_dir(PYTHON_PROJECTS[name]).relative_to(ROOT)}."
            )

    for name, project in PYTHON_PROJECTS.items():
        version_info = local_python_version(project)
        if version_info and not version_info.startswith(f"{PYTHON_VERSION}."):
            issues.append(
                f"{name} venv uses Python {version_info}; rerun bootstrap to recreate it with Python {PYTHON_VERSION}."
            )

    for name in ["repomix", "ast-grep"]:
        if not check_executable(name, [node_bin_dir()]):
            issues.append(f"Missing Node tool `{name}` in {node_bin_dir().relative_to(ROOT)}.")

    if RTK_MANIFEST.exists():
        manifest = load_rtk_manifest()
        if not rtk_version_ok(rtk_path(), manifest["version"]):
            issues.append(f"Missing RTK {manifest['version']} at {rtk_path().relative_to(ROOT)}.")

    return issues


def check() -> int:
    issues = collect_check_issues()
    if not issues:
        print("Agent tools are ready.")
        return 0

    print("Agent tools are not fully installed:")
    for issue in issues:
        print(f"- {issue}")
    print("Run `make agent-tools-install` to recreate the project-local tool environment.")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap project-local agent tools.")
    parser.add_argument("--check", action="store_true", help="Only verify the local tool environment.")
    args = parser.parse_args()

    if args.check:
        raise SystemExit(check())

    sync_python_tools()
    sync_node_tools()
    install_rtk()
    raise SystemExit(check())


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
