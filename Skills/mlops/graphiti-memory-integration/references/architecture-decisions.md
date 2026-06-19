# Architecture Decisions — Graphiti + TencentDB Dual-Write

## Why FalkorDB over Kùzu (embedded)?

- FalkorDB: production-ready, fulltext search works natively, Docker one-liner
- Kùzu: embedded (no server) but has limitations — no dynamic index creation, workaround needed for full-text search on edges via intermediate nodes
- FalkorDB is Redis-based so familiar tooling, web UI on port 3000

## Why Python FastAPI sidecar (not embedded in Node.js Gateway)?

- graphiti-core is Python — no Node.js bindings
- Sidecar pattern keeps concerns separated
- Fire-and-forget from Gateway means no latency impact on main capture path
- Circuit breaker pattern ensures Bridge failures don't cascade

## Why Chat Completions API override instead of Responses API?

- graphiti-core v0.29.0 uses `client.responses.parse()` (OpenAI Responses API)
- Local proxy at 127.0.0.1:20128 routes to GitHub Models which returns 200 but response format doesn't match what graphiti expects
- The `_handle_structured_response` in base class reads `response.output_text` which is Responses API specific
- Solution: override both `_create_structured_completion` (use json_object mode + schema in prompt) AND `_handle_structured_response` (read from `choices[0].message.content`)

## Why GPT-4o instead of Claude for Graphiti?

- Graphiti's extraction prompts are optimized for OpenAI structured output
- Claude through the proxy doesn't support the model name format Graphiti sends
- GPT-4o reliably produces valid JSON with json_object response_format

## Dual-write flow design

```
User message → Hermes → TencentDB Gateway /capture
                              │
                              ├─ TdaiCore.handleTurnCommitted() [sync, blocking]
                              │   └─ L0 record → pipeline scheduler → L1/L2/L3
                              │
                              └─ GraphitiBridgeClient.sendEpisode() [async, fire-and-forget]
                                  └─ HTTP POST to Bridge /episode
                                      └─ Graphiti add_episode() → entity extraction → graph
```

## Unified recall flow

```
/recall request
    │
    ├─ Promise.all([
    │     TdaiCore.handleBeforeRecall(),     // L1 memories + persona
    │     GraphitiBridge.searchGraph()        // knowledge graph facts
    │   ])
    │
    └─ Merge: TdaiCore context + "\n\n[Knowledge Graph — related facts]\n" + graph facts
```

## Shared .env convention

All services read from `/home/enzo/Documents/Hermes_Agent/.env`:
- Avoids key duplication across per-service .env files
- Single place to rotate API keys
- Bridge start.sh sources this file
- Gateway already reads TDAI_* vars from Hermes .env injection
- New vars: GRAPHITI_*, FALKORDB_*
