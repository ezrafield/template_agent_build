import subprocess
import sys


DEFAULT_COMMAND = [sys.executable, "-m", "pytest", "tests/integration/test_api.py", "-q"]


def main() -> None:
    command = sys.argv[1:] or DEFAULT_COMMAND
    print(f"Running: {' '.join(command)}")
    raise SystemExit(subprocess.run(command, check=False).returncode)


if __name__ == "__main__":
    main()
