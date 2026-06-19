# Custom LLM Client for Graphiti via Claude Proxy

## Problem

graphiti-core uses OpenAI's Responses API (`client.responses.parse()`) which most
proxy endpoints don't support. Additionally, Claude models via proxy have specific
quirks that break standard OpenAI SDK patterns.

## Solution: ChatCompletionsClient

File: `/home/enzo/Documents/Hermes_Agent/Memory/graphiti-bridge/src/llm_client.py`

### Key Design Decisions

1. **Override `_create_structured_completion`** — uses `chat.completions.create()` 
   instead of `beta.chat.completions.parse()` or `responses.parse()`

2. **Always `stream=False`** — proxy defaults to SSE streaming for Claude models.
   Without explicit `stream=False`, the SDK receives chunked SSE data instead of
   a complete JSON response object.

3. **No `response_format` param** — proxy ignores `{"type": "json_object"}` for
   Claude. Instead, JSON schema is injected directly into the system prompt:
   ```
   IMPORTANT: You MUST respond with ONLY a valid JSON object (no markdown, 
   no code blocks, no explanation) matching this exact schema:
   {schema}
   Output ONLY the raw JSON object.
   ```

4. **`_extract_json()` helper** — Claude sometimes wraps JSON in markdown code
   blocks despite instructions. Extraction priority:
   - Raw JSON (starts with `{` or `[`)
   - Regex extract from ```json...``` blocks
   - Find first `{` to last `}` as last resort

5. **`_handle_structured_response` override** — reads from
   `response.choices[0].message.content` (Chat Completions format) instead of
   `response.output_text` (Responses API format)

### LLMConfig Requirements

```python
llm_config = LLMConfig(
    api_key=API_KEY,
    base_url="http://127.0.0.1:20128/v1",
    model="kr/claude-opus-4.6",
    small_model="kr/claude-opus-4.6",  # MUST set — default gpt-4.1-nano doesn't exist
)
```

### Testing a new model works

```bash
curl -s -X POST http://127.0.0.1:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <KEY>" \
  -d '{
    "model": "<MODEL>",
    "messages": [{"role": "user", "content": "Return JSON: {\"status\": \"ok\"}. Output ONLY raw JSON."}],
    "stream": false,
    "max_tokens": 50
  }'
```

If response is valid JSON with `choices[0].message.content` containing raw JSON → model works.
If response is SSE chunks (`data: {...}`) → `stream: false` not being honored (proxy issue).
If response wraps in ```json...``` → `_extract_json()` handles it.

### Companion Components

- `src/embedder.py` — `HashEmbedder`: local deterministic embeddings (no API)
- `src/reranker.py` — `LocalReranker`: word-overlap Jaccard scoring (no API)

Together these three files eliminate ALL external API dependencies except the
chat completions endpoint for LLM reasoning.
