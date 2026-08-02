import ast
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEMAP = ROOT / "docs" / "agent" / "CODEMAP.md"

PURPOSES = {
    "api": "HTTP routes, request validation, response shaping, and transport boundaries.",
    "core": "Configuration, application setup, and cross-cutting primitives.",
    "models": "Domain models and persistence-facing data structures.",
    "services": "Business workflows and application logic.",
    "utils": "Small shared helpers with no business ownership.",
}

TEST_HINTS = {
    "api": ["tests/integration/test_api.py"],
    "models": ["tests/unit/test_models.py"],
    "services": ["tests/unit/test_services.py"],
}


@dataclass
class FileSummary:
    path: str
    exports: list[str]
    classes: list[str]
    functions: list[str]
    dependencies: list[str]


def parse_python_file(path: Path) -> FileSummary:
    relative = path.relative_to(ROOT).as_posix()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return FileSummary(relative, [], [], [], [])

    classes = []
    functions = []
    exports = []
    dependencies = set()

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            if not node.name.startswith("_"):
                exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    exports.extend(read_all_exports(node.value))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                add_local_dependency(dependencies, alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                add_relative_dependency(dependencies, relative, node.level, module)
            else:
                add_local_dependency(dependencies, module)

    return FileSummary(
        path=relative,
        exports=sorted(set(exports)),
        classes=sorted(classes),
        functions=sorted(functions),
        dependencies=sorted(dependencies),
    )


def read_all_exports(value: ast.AST) -> list[str]:
    if not isinstance(value, (ast.List, ast.Tuple)):
        return []
    exports = []
    for item in value.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            exports.append(item.value)
    return exports


def add_local_dependency(dependencies: set[str], module: str) -> None:
    if module == "src" or module.startswith("src."):
        dependencies.add(module.replace(".", "/"))


def add_relative_dependency(dependencies: set[str], relative_path: str, level: int, module: str) -> None:
    package_parts = relative_path.removesuffix(".py").split("/")[:-1]
    base_parts = package_parts[: max(len(package_parts) - level + 1, 0)]
    target_parts = base_parts + ([part for part in module.split(".") if part] if module else [])
    if target_parts and target_parts[0] == "src":
        dependencies.add("/".join(target_parts))


def find_tests(module_name: str, files: list[Path]) -> list[str]:
    hints = [path for path in TEST_HINTS.get(module_name, []) if (ROOT / path).exists()]
    discovered = []
    for file in files:
        stem = file.stem
        candidates = [
            ROOT / "tests" / "unit" / f"test_{stem}.py",
            ROOT / "tests" / "integration" / f"test_{stem}.py",
            ROOT / "tests" / f"test_{stem}.py",
        ]
        discovered.extend(path.relative_to(ROOT).as_posix() for path in candidates if path.exists())
    return sorted(set(hints + discovered))


def risk_notes(module_name: str, summaries: list[FileSummary]) -> list[str]:
    notes = []
    if any(summary.exports for summary in summaries):
        notes.append("Public exports may be imported by other modules; confirm references before renaming.")
    if module_name in {"api", "models"}:
        notes.append("Public API or schema changes should be reflected in specs and tests.")
    if any(summary.dependencies for summary in summaries):
        notes.append("Dependency edges are import hints, not a full call graph; verify behavior in source.")
    return notes or ["Low obvious coupling in generated map; verify with source search before edits."]


def main() -> None:
    source_dirs = [
        path
        for path in (ROOT / "src").iterdir()
        if path.is_dir() and path.name != "__pycache__" and not path.name.startswith(".")
    ]
    lines = [
        "# Code Map",
        "",
        "Generated from the current `src/` directory by `scripts/generate_codemap.py`.",
        "",
        "Use this for quick orientation, then confirm with Semble, `rg`, module cards, and source reads.",
        "",
    ]

    for directory in sorted(source_dirs):
        paths = sorted(path for path in directory.rglob("*.py") if "__pycache__" not in path.parts)
        summaries = [parse_python_file(path) for path in paths]
        name = directory.name
        purpose = PURPOSES.get(name, "Project module. Replace this line with project-specific ownership notes.")
        lines.extend([f"## {directory.relative_to(ROOT).as_posix()}/", f"Purpose: {purpose}", ""])

        lines.append("Files:")
        if summaries:
            for summary in summaries:
                lines.append(f"- `{summary.path}`")
        else:
            lines.append("- No Python entry points found yet.")

        exports = sorted({export for summary in summaries for export in summary.exports})
        if exports:
            lines.extend(["", "Exported symbols:"])
            lines.extend(f"- `{symbol}`" for symbol in exports)

        classes = sorted({class_name for summary in summaries for class_name in summary.classes})
        functions = sorted({function_name for summary in summaries for function_name in summary.functions})
        if classes or functions:
            lines.extend(["", "Important classes/functions:"])
            lines.extend(f"- class `{class_name}`" for class_name in classes)
            lines.extend(f"- function `{function_name}`" for function_name in functions)

        public_apis = [summary for summary in summaries if summary.exports]
        if public_apis:
            lines.extend(["", "Public APIs:"])
            for summary in public_apis:
                lines.append(f"- `{summary.path}` -> {', '.join(f'`{item}`' for item in summary.exports)}")

        dependencies = sorted({dependency for summary in summaries for dependency in summary.dependencies})
        if dependencies:
            lines.extend(["", "Dependency edges:"])
            lines.extend(f"- `{directory.relative_to(ROOT).as_posix()}` -> `{dependency}`" for dependency in dependencies)

        tests = find_tests(name, paths)
        if tests:
            lines.extend(["", "Tests:"])
            lines.extend(f"- `{path}`" for path in tests)

        lines.extend(["", "Risk notes:"])
        lines.extend(f"- {note}" for note in risk_notes(name, summaries))
        lines.append("")

    CODEMAP.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Updated {CODEMAP.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
