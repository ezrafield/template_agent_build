---
name: graphiti-memory-integration
description: "Integrate Graphiti temporal knowledge graph with TencentDB Agent Memory for dual-write + unified search."
version: 0.1.0
author: enzo
tags: [graphiti, knowledge-graph, memory, falkordb, dual-write, unified-search]
---

# Graphiti + TencentDB Memory Integration

## Trigger
When setting up or maintaining the dual-write memory system that combines TencentDB (flat L0-L3 memories) with Graphiti (temporal knowledge graph with entities and relationships).

## Architecture Overview

```
Hermes Agent → TencentDB Gateway (port 8420)
                  ├── TdaiCore (L0→L1→L2→L3) [flat memories]
                  ├── Dual-write → Graphiti Bridge (port 8421) [knowledge graph]
                  └── Unified recall: merge TdaiCore + Graphiti results
                  
Graphiti Bridge (Python FastAPI) → FalkorDB (Docker, port 6379)
```

## Key Components

- **FalkorDB**: Redis-based graph DB in Docker (`graphiti-falkordb` container)
- **Graphiti Bridge**: Python FastAPI sidecar at port 8421, wraps graphiti-core
- **TencentDB Gateway**: Node.js server at port 8420, calls Bridge for dual-write
- **Shared .env**: `/home/enzo/Documents/Hermes_Agent/.env` — ALL services read from here

## File Locations

- Bridge service: `/home/enzo/Documents/Hermes_Agent/Memory/graphiti-bridge/`
- Bridge client (TS): `TencentDB-Agent-Memory/src/gateway/graphiti-bridge-client.ts`
- Gateway server (modified): `TencentDB-Agent-Memory/src/gateway/server.ts`
- Plugin tools: `TencentDB-Agent-Memory/hermes-plugin/memory/memory_tencentdb/__init__.py`
- Plugin HTTP client: `TencentDB-Agent-Memory/hermes-plugin/memory/memory_tencentdb/client.py`

## Critical Pitfalls

### 1. Graphiti uses OpenAI Responses API (not Chat Completions)
- graphiti-core v0.29.0 uses `client.responses.parse()` with `output_text` response format
- Most proxy endpoints (like local routers) don't support this
- **Solution**: Custom `ChatCompletionsClient` in `src/llm_client.py` overriding `_create_structured_completion` and `_handle_structured_response`

### 2. Claude via proxy — stream and JSON issues (CRITICAL)
- **`stream=False` is MANDATORY** — proxy defaults to streaming SSE for Claude, which breaks OpenAI Python SDK's non-streaming response parsing. Always pass `stream=False` in `chat.completions.create()`
- **`response_format={"type": "json_object"}` is IGNORED** by proxy for Claude — do NOT rely on it. Instead inject JSON schema into system prompt with explicit instruction: "Output ONLY the raw JSON object, no markdown, no code blocks"
- **Claude wraps JSON in markdown code blocks** (```json...```) even when told not to — `_handle_structured_response` must extract JSON via regex fallback (`_extract_json()` helper)
- **`small_model` must be set explicitly** in LLMConfig to same value as main model — Graphiti defaults to `gpt-4.1-nano` for dedup calls which doesn't exist on proxy → 404 error after extraction succeeds

### 3. Model selection
- `kr/claude-opus-4.6` works with the custom ChatCompletionsClient (stream=False + JSON extraction)
- `gh/gpt-4o` also works (native json_object support)
- Do NOT use `response_format` param — rely on prompt-based JSON enforcement

### 4. Embedding — no API available via proxy
- Proxy does NOT serve embedding models (text-embedding-3-small etc. → 403/404)
- **Solution**: Local `HashEmbedder` in `src/embedder.py` (deterministic hash-based vectors via character n-gram + word hashing)
- Lexical only (not semantic) but sufficient because FalkorDB fulltext search provides primary retrieval
- `EmbedderClient.create()` returns `list[float]` (single vector), `create_batch()` returns `list[list[float]]` — different signatures
- For production: install Ollama with `nomic-embed-text` or similar

### 5. Reranker — no API available via proxy
- `OpenAIRerankerClient` calls OpenAI API directly → 404 on proxy
- **Solution**: Local `LocalReranker` in `src/reranker.py` using word overlap (Jaccard) scoring

### 6. FalkorDB fulltext search syntax
- Group IDs with hyphens cause RediSearch syntax errors — use underscores: `hermes_default` NOT `hermes-default`
- Docker requires sudo: `sudo docker compose up -d`
- Health check: `sudo docker exec graphiti-falkordb redis-cli ping`

### 7. Gateway dual-write is fire-and-forget
- `GraphitiBridgeClient.sendEpisode()` is async non-blocking
- Circuit breaker: 5 failures → 60s cooldown
- Bridge unavailability does NOT block main capture path

### 8. graphiti-core API notes (v0.29.0)
- `add_episode()` returns `AddEpisodeResults` with: `.episode`, `.nodes`, `.edges`, `.episodic_edges`, `.communities`
- `EntityEdge` has `.name` (relation name), `.fact`, `.source_node_uuid`, `.target_node_uuid`, `.valid_at`, `.invalid_at` — NO `.relation_type` or `.source_node_name`
- `search()` accepts `num_results` param, returns `list[EntityEdge]`
- `LLMConfig(api_key, model, base_url, temperature, max_tokens, small_model)`

## Hermes Plugin Tools Added

| Tool | Endpoint | Purpose |
|------|----------|---------|
| `memory_tencentdb_graph_search` | POST /search/graph | Search knowledge graph facts |
| `memory_tencentdb_entity_search` | POST /graph/entities | Lookup entities |

## Startup Order

1. FalkorDB Docker: `sudo docker compose -f graphiti-bridge/docker-compose.yml up -d`
2. Graphiti Bridge: `cd graphiti-bridge && ./start.sh`
3. TencentDB Gateway: (managed by Hermes supervisor)

## Environment Variables (ALL in shared .env at /home/enzo/Documents/Hermes_Agent/.env)

**IMPORTANT**: All services MUST read from the single shared .env file. Do NOT create per-service .env files. Each service's start script should `source /home/enzo/Documents/Hermes_Agent/.env`.

```bash
# === TencentDB Gateway (port 8420) ===
TDAI_LLM_API_KEY=<api-key>
TDAI_LLM_BASE_URL=http://127.0.0.1:20128/v1
TDAI_LLM_MODEL=gh/claude-sonnet-4
TDAI_GATEWAY_PORT=8420
TDAI_GATEWAY_HOST=127.0.0.1

# === FalkorDB ===
FALKORDB_HOST=localhost
FALKORDB_PORT=6379

# === Graphiti Bridge (port 8421) ===
GRAPHITI_LLM_BASE_URL=http://127.0.0.1:20128/v1
GRAPHITI_LLM_API_KEY=${TDAI_LLM_API_KEY}
GRAPHITI_LLM_MODEL=kr/claude-opus-4.6
GRAPHITI_EMBEDDING_BASE_URL=http://127.0.0.1:20128/v1
GRAPHITI_EMBEDDING_API_KEY=${TDAI_LLM_API_KEY}
GRAPHITI_EMBEDDING_MODEL=text-embedding-3-small
GRAPHITI_EMBEDDING_DIM=1024
GRAPHITI_BRIDGE_HOST=127.0.0.1
GRAPHITI_BRIDGE_PORT=8421
GRAPHITI_BRIDGE_ENABLED=true
GRAPHITI_GROUP_ID=hermes_default
```

### Migration checklist (per-service .env → shared .env)

1. Consolidate all vars into `/home/enzo/Documents/Hermes_Agent/.env`
2. Delete per-service .env files: `graphiti-bridge/.env`, any `TencentDB-Agent-Memory/.env`
3. Update `graphiti-bridge/start.sh` to source shared .env
4. Update Hermes `.hermes/.env` to source or symlink shared .env
5. Update `GatewaySupervisor` in Python plugin to pass shared .env path to Node.js subprocess
6. Verify: each service reads vars correctly after migration

## Status: Complete ✓

All components tested end-to-end (2026-05-20):
- Episode creation with `kr/claude-opus-4.6` via proxy: 4-5 nodes, 3 edges per episode
- Search returns structured facts with relation names
- Dual-write from Gateway capture → Bridge episode creation works
- Unified recall merges TdaiCore + Graphiti results
- HashEmbedder + LocalReranker eliminate external API dependencies

## References

- See `references/graphiti-api-signatures.md` for detailed API docs
- See `references/architecture-decisions.md` for design rationale
- See `references/proxy-claude-llm-client.md` for the custom LLM client pattern
- See `references/testing-verification.md` for stress test results and verification commands
