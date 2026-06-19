# Testing & Verification Reference

## Stress Test Results (2026-05-20)

Model: `kr/claude-opus-4.6` via proxy at `127.0.0.1:20128/v1`

| # | Description | Nodes | Edges | Time | Status |
|---|-------------|-------|-------|------|--------|
| 1 | PostgreSQL + read replicas | 2 | 1 | 12.8s | PASS |
| 2 | Auth service (JWT, OAuth2) | 5 | 4 | 16.9s | PASS |
| 3 | CI/CD optimization (GitHub Actions) | 2 | 1 | 9.6s | PASS |
| 4 | WebSockets (FastAPI, React, Redis) | 5 | 5 | 17.5s | PASS |
| 5 | Search engine (Elasticsearch, Meilisearch) | 2 | 0 | 10.7s | PASS |

Average: ~13s/episode, 2-5 nodes, 0-5 edges.

## Verification Commands

```bash
# 1. Health checks
curl -s http://127.0.0.1:8420/health  # Gateway — expect graphiti_bridge: true
curl -s http://127.0.0.1:8421/health  # Bridge — expect graphiti_ready: true

# 2. Episode creation (use @file to avoid shell quoting)
cat > /tmp/test_ep.json << 'EOF'
{
  "name": "verify_test",
  "content": "User: Testing the knowledge graph.\nAssistant: Graph is working.",
  "source": "message",
  "source_description": "verification",
  "group_id": "hermes_default",
  "reference_time": "2026-05-20T00:00:00Z"
}
EOF
curl -s -X POST http://127.0.0.1:8421/episode \
  -H "Content-Type: application/json" -d @/tmp/test_ep.json

# 3. Search
curl -s -X POST http://127.0.0.1:8421/search \
  -H "Content-Type: application/json" \
  -d '{"query": "knowledge graph", "group_ids": ["hermes_default"], "num_results": 5}'

# 4. Entity lookup
curl -s -X POST http://127.0.0.1:8421/entities \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "group_ids": ["hermes_default"], "limit": 10}'

# 5. Dual-write via Gateway
curl -s -X POST http://127.0.0.1:8420/capture \
  -H "Content-Type: application/json" \
  -d '{"user_content": "Test message", "assistant_content": "Test reply", "session_key": "verify"}'
# Wait 30-60s, then search Bridge for the content
```

## Shell Quoting Pitfall

When testing via curl with JSON containing single quotes or special chars:
- **DON'T**: inline JSON in shell command with single-quote wrapping
- **DO**: write JSON to temp file, use `curl -d @/tmp/file.json`

This is NOT a code bug — the Gateway/Bridge receive proper HTTP POST bodies from real clients.

## Performance Expectations

- Episode extraction: 10-18s (depends on content complexity and LLM response time)
- Search: <1s
- Entity lookup: <1s
- Health check: <100ms
- Dual-write overhead on Gateway capture: ~0ms (fire-and-forget, non-blocking)
