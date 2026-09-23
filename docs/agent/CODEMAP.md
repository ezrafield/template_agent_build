# Code Map

Generated from the current `src/` directory by `scripts/generate_codemap.py`.

Use this for quick orientation, then confirm with Semble, `rg`, module cards, and source reads.

## src/api/
Purpose: HTTP routes, request validation, response shaping, and transport boundaries.

Files:
- `src/api/__init__.py`
- `src/api/dependencies.py`
- `src/api/routes.py`

Exported symbols:
- `get_settings`
- `health`

Important classes/functions:
- function `get_settings`
- function `health`

Public APIs:
- `src/api/dependencies.py` -> `get_settings`
- `src/api/routes.py` -> `health`

Dependency edges:
- `src/api` -> `src/core/config`
- `src/api` -> `src/services/example_service`

Tests:
- `tests/integration/test_api.py`

Risk notes:
- Public exports may be imported by other modules; confirm references before renaming.
- Public API or schema changes should be reflected in specs and tests.
- Dependency edges are import hints, not a full call graph; verify behavior in source.

## src/core/
Purpose: Configuration, application setup, and cross-cutting primitives.

Files:
- `src/core/__init__.py`
- `src/core/config.py`

Exported symbols:
- `Settings`
- `load_settings`

Important classes/functions:
- class `Settings`
- function `load_settings`

Public APIs:
- `src/core/config.py` -> `Settings`, `load_settings`

Risk notes:
- Public exports may be imported by other modules; confirm references before renaming.

## src/models/
Purpose: Domain models and persistence-facing data structures.

Files:
- `src/models/__init__.py`
- `src/models/example.py`

Exported symbols:
- `Example`

Important classes/functions:
- class `Example`

Public APIs:
- `src/models/example.py` -> `Example`

Risk notes:
- Public exports may be imported by other modules; confirm references before renaming.
- Public API or schema changes should be reflected in specs and tests.

## src/services/
Purpose: Business workflows and application logic.

Files:
- `src/services/__init__.py`
- `src/services/example_service.py`

Exported symbols:
- `ExampleService`

Important classes/functions:
- class `ExampleService`

Public APIs:
- `src/services/example_service.py` -> `ExampleService`

Risk notes:
- Public exports may be imported by other modules; confirm references before renaming.

## src/utils/
Purpose: Small shared helpers with no business ownership.

Files:
- `src/utils/__init__.py`
- `src/utils/strings.py`

Exported symbols:
- `normalize_name`

Important classes/functions:
- function `normalize_name`

Public APIs:
- `src/utils/strings.py` -> `normalize_name`

Risk notes:
- Public exports may be imported by other modules; confirm references before renaming.
