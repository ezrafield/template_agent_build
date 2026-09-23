# Module: Models

## Responsibility
Owns domain data structures and model-level behavior.

## Key Files
- `src/models/example.py`: sample domain model

## Public Interfaces
- Model classes and constructors exported from `src/models`

## Rules
- Keep transport-specific request and response objects out of models.
- Keep persistence decisions aligned with `docs/agent/module-cards/database.md`.
- Update tests when model invariants change.

## Common Tasks
- Add model: define and export it when needed; test meaningful invariants.
- Change validation: update model tests and related API/service callers.

## Known Pitfalls
- Avoid placing workflow logic in models when it belongs in services.
