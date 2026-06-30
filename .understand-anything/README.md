# Understand Anything

This directory documents the local source-code knowledge graph workflow.

Generated graph outputs are ignored by default. The committed files here are setup and policy files only.

Understand Anything remains an agent/plugin runtime integration. The project-local agent-tool bootstrap stores compatible setup notes and verification helpers, but it does not install the Understand Anything runtime or generate graph data.

## Generate The Graph

Use the installed Understand Anything runtime:

```bash
/understand
```

Or use the project command placeholder:

```bash
make understand
```

## Search The Graph

```bash
make understand-search QUERY="api route"
```

## Open Dashboard

```bash
make understand-dashboard
```

## Committed Files

- `README.md`
- `.understandignore`
- `config.example.json`

## Ignored Generated Files

- `knowledge-graph.json`
- `meta.json`
- `intermediate/`
- `tmp/`
- `*knowledge-graph*.json`

Commit generated graph files only if the team explicitly decides the benefits outweigh repository noise.
