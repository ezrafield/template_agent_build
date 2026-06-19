# Hermes Data Skills — Inventory

Listing of data-related skills available in the Hermes install at `/home/enzo/.hermes/skills/`: scraping, extraction, processing, evaluation, storage. This is an **index** — full content is loaded via `skill_view(name)` or read directly at the path.

Categorized by relevance:
- **Primary** — dedicated data skills, load directly for data work.
- **Supporting** — related data skills (storage, query, format).
- **Indirect** — supporting skills (context window, multi-agent, evaluation, format conversion).

---

## 1. Primary data skills

### 1.1 `data-scraping-frameworks`
- **Path:** `/home/enzo/.hermes/skills/software-development/data-scraping-frameworks/SKILL.md`
- **Category:** software-development
- **Tags:** scraping, firecrawl, scrapingant, data-collection, enrichment, lead-generation
- **Description:** Build multi-source data scraping frameworks with Firecrawl v2 + ScrapingAnt. Domain-specific scrapers, enrichment pipelines, structured extraction, lead scoring.
- **Use when:** Collecting structured data from multiple web sources (trade data, company directory, rate table), lead gen pipelines, price intelligence.
- **Key tools:** `firecrawl.FirecrawlApp` (v2 SDK: `scrape/crawl/map/search/extract`), `scrapingant_client`, `tenacity` retry, `BeautifulSoup` for CSR sites, optional Playwright.
- **Architecture pattern:** `scrapers/base.py` + `scrapers/domains/<site>.py` (1 class per source) + `enrichment.py` (post-process pipeline).
- **Notable pitfalls:** 13 listed — generic regex across sites, search returns limited metadata, LinkedIn blocks Firecrawl (use ScrapingAnt residential), CSR sites need Playwright scroll, ScrapingAnt `js_snippet` rejects async, phone cleaning must be robust.
- **Linked files:** `references/firecrawl-v2-api-signatures.md`, `references/importyeti-field-patterns.md`, `templates/csr_html_parser.py`.

### 1.2 `context-engineering`
- **Path:** `/home/enzo/.hermes/skills/software-development/context-engineering/SKILL.md`
- **Category:** software-development
- **Tags:** llm, context-window, optimization, multi-agent, tokens
- **Description:** Optimize LLM context window usage, token consumption, multi-agent architectures. Four-Bucket Strategy (Write, Select, Compress, Isolate). Key metrics, anti-patterns, degradation debugging.
- **Use when:** Designing/debugging agent systems, optimizing cost/latency, building multi-agent coordination, implementing memory.
- **Core:** Four-Bucket (Write/Compress/Select/Isolate) — especially "Select" and "Compress" for data work.
- **Key metrics:** Token utilization warning at 70%, trigger optimization at 80%, compaction 50-70% reduction.
- **Anti-patterns:** Exhaustive context, critical info in the middle (lost-in-middle), single agent for parallel tasks.
- **Hermes-specific:** Use `delegate_task` for isolation, `execute_code` to filter/reduce large output, `session_search` to recall past context.

### 1.3 `jupyter-live-kernel`
- **Path:** `/home/enzo/.hermes/skills/data-science/jupyter-live-kernel/SKILL.md`
- **Category:** data-science
- **Tags:** jupyter, notebook, repl, data-science, exploration, iterative
- **Description:** Iterative Python via live Jupyter kernel (hamelnb). Stateful REPL — variables persist.
- **Use when:** Building state incrementally, exploring APIs, inspecting DataFrames, iterating on complex code. Replaces `execute_code` when state is needed.
- **Tools:** `uv run ~/.agent-skills/hamelnb/skills/jupyter-live-kernel/scripts/jupyter_live_kernel.py` with subcommands: `servers/notebooks/execute/variables/edit/restart-run-all`.
- **Always use:** `--compact` flag to save tokens.
- **vs `execute_code`:** Jupyter = stateful, iterative, data exploration. `execute_code` = one-shot, stateless, has hermes tool access.

### 1.4 `ocr-and-documents`
- **Path:** `/home/enzo/.hermes/skills/productivity/ocr-and-documents/SKILL.md`
- **Category:** productivity
- **Tags:** PDF, Documents, Research, Arxiv, Text-Extraction, OCR
- **Description:** Extract text from PDFs/scans (pymupdf, marker-pdf). Helper scripts + decision tree.
- **Use when:** PDF needing text extraction, scanned doc needing OCR, arxiv paper, Vietnamese legal docs.
- **Decision:** URL available → `web_extract` (Firecrawl) first. Local file → pymupdf (instant, 25MB) default, marker-pdf (3-5GB, OCR + equations) when needed.
- **Scripts:** `scripts/extract_pymupdf.py`, `scripts/extract_marker.py` (with `--check` disk space).
- **Pitfall:** marker-pdf downloads ~2.5GB models on first use, check disk first.
- **Linked files:** `references/yolo-layout-detection-ensemble.md` (figure detection), `references/vietnamese-legal-documents.md` (congbao.chinhphu.vn).

### 1.5 `langgraph-enrichment-pipeline`
- **Path:** `/home/enzo/.hermes/skills/software-development/langgraph-enrichment-pipeline/SKILL.md`
- **Category:** software-development
- **Tags:** langgraph, pipeline, firecrawl, enrichment, structured-output, html-rendering, gemini
- **Description:** Build multi-node LangGraph pipelines with external API enrichment (Firecrawl, web scraping) and structured output rendering (HTML, JSON).
- **Use when:** Building LangGraph state machine with 3+ nodes, pipeline needs external data enrichment, LLM output must be structured JSON, final output is HTML/PDF.
- **Architecture:** `filter → basic_enrich → planner (LLM gate) → deep_enrich → render`.
- **Key pattern:** Two-phase enrichment — cheap broad basic crawl, LLM decides targeted deep crawl.
- **Pitfalls:** 12 listed — Gemini wraps JSON in code blocks, Firecrawl rate limits, NEVER overwrite .env, auth errors surface at `invoke()` not constructor, Gemini 503 "high demand" frequent (needs key rotation + backoff).
- **Linked files:** `references/two-phase-enrichment.md`.

### 1.6 `structured-evaluation-workflows`
- **Path:** `/home/enzo/.hermes/skills/evaluation/structured-evaluation-workflows/SKILL.md`
- **Category:** evaluation
- **Tags:** evaluation, metrics, json, ocr, extraction, iou, f1, testing
- **Description:** Class-level workflow for designing/fixing/validating evaluators that compare predicted structured output to ground truth (JSON extraction, OCR, layout IoU, precision/recall/F1, synthetic self-tests).
- **Use when:** Comparing predicted JSON to hand-annotated truth, code computes IoU/accuracy/F1, scores look suspiciously high, user requests quality measurement / benchmark.
- **Required metric shape:** Every axis must report `truth=N pred=M matched=K precision=K/M recall=K/N F1`.
- **Historical bugs:** 5 types — membership instead of multiset, recall-only IoU (doesn't penalize spam), best text match reusing same pred, dict overwrite on duplicate IDs, degenerate bbox pollution.
- **Self-test recipe:** Truth-vs-truth = 1.0, truth-vs-empty = 0.0, noisy drops predictably, bug witnesses (multiset match = 2 not 3).
- **Linked files:** `templates/test_eval_scaffold.py`, `templates/evaluator_skeleton.py`.

---

## 2. Supporting data skills (storage, query, structured records)

### 2.1 `airtable`
- **Path:** `/home/enzo/.hermes/skills/productivity/airtable/SKILL.md`
- **Category:** productivity
- **Description:** Airtable REST API via curl. Records CRUD, filters, upserts.
- **Use when:** Output data to Airtable base, sync scrape results to Airtable, manual review records in UI.

### 2.2 `notion`
- **Path:** `/home/enzo/.hermes/skills/productivity/notion/SKILL.md`
- **Category:** productivity
- **Description:** Notion API + ntn CLI: pages, databases, markdown, Workers.
- **Use when:** Store data as Notion pages/databases, integrate with team Notion workflow.

### 2.3 `linear`
- **Path:** `/home/enzo/.hermes/skills/productivity/linear/SKILL.md`
- **Category:** productivity
- **Description:** Linear: manage issues, projects, teams via GraphQL + curl.
- **Use when:** Data pipeline bug → track as Linear issue; project management for data team.

### 2.4 `google-workspace`
- **Path:** `/home/enzo/.hermes/skills/productivity/google-workspace/SKILL.md`
- **Category:** productivity
- **Description:** Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
- **Use when:** Output data to Google Sheets (non-tech user readable), trigger workflow from Sheets data.

### 2.5 `huggingface-hub`
- **Path:** `/home/enzo/.hermes/skills/mlops/huggingface-hub/SKILL.md`
- **Category:** mlops
- **Description:** HuggingFace `hf` CLI: search/download/upload models, datasets.
- **Use when:** Download dataset from Hub, upload new dataset, query dataset via SQL (`hf datasets sql`), manage parquet URLs.
- **Tools:** `hf download/upload/sync`, `hf datasets list/info/parquet`, `hf datasets sql` (DuckDB-backed).
- **Note:** `hf` command replaces deprecated `huggingface-cli`. Auth via `HF_TOKEN`.

### 2.6 `maps`
- **Path:** `/home/enzo/.hermes/skills/productivity/maps/SKILL.md`
- **Category:** productivity
- **Description:** Geocode, POIs, routes, timezones via OpenStreetMap/OSRM.
- **Use when:** Enrich data with location (geocode address → lat/lng), compute route/distance, lookup POI.

---

## 3. Indirect (data-adjacent infrastructure)

### 3.1 `llm-wiki`
- **Path:** `/home/enzo/.hermes/skills/research/llm-wiki/SKILL.md`
- **Category:** research
- **Description:** Karpathy's LLM Wiki: build/query interlinked markdown KB.
- **Use when:** Build knowledge base from research papers, link concepts, query via semantic search.

### 3.2 `llm-router-proxy-patterns`
- **Path:** `/home/enzo/.hermes/skills/software-development/llm-router-proxy-patterns/SKILL.md`
- **Category:** software-development
- **Description:** Architecture patterns for LLM API routers/proxies: rate limiting, fallback, anti-ban, proxy pools, format translation.
- **Use when:** Build data pipeline calling LLM API at volume, need rate limit + fallback across providers.

### 3.3 `blogwatcher`
- **Path:** `/home/enzo/.hermes/skills/research/blogwatcher/SKILL.md`
- **Category:** research
- **Description:** Monitor blogs and RSS/Atom feeds via blogwatcher-cli.
- **Use when:** Track industry blog updates, monitor competitor news feeds, collect data from RSS.
- **Tools:** `blogwatcher-cli add/scan/articles/read-all`; DB at `~/.blogwatcher-cli/`.

### 3.4 `arxiv`
- **Path:** `/home/enzo/.hermes/skills/research/arxiv/SKILL.md`
- **Category:** research
- **Description:** Search arXiv papers by keyword, author, category, or ID.
- **Use when:** Literature review for ML/data work, fetch paper metadata or PDF URL.

### 3.5 `polymarket`
- **Path:** `/home/enzo/.hermes/skills/research/polymarket/SKILL.md`
- **Category:** research
- **Description:** Query Polymarket: markets, prices, orderbooks, history.
- **Use when:** Prediction market data, sentiment/forecast tracking.

### 3.6 `codebase-inspection`
- **Path:** `/home/enzo/.hermes/skills/github/codebase-inspection/SKILL.md`
- **Category:** github
- **Description:** Inspect codebases w/ pygount: LOC, languages, ratios.
- **Use when:** Measure data project size (LOC), language breakdown, dead code hunt.

### 3.7 `trigram-code-search-index`
- **Path:** `/home/enzo/.hermes/skills/software-development/trigram-code-search-index/SKILL.md`
- **Category:** software-development
- **Description:** Build trigram inverted indexes for sub-millisecond code search in large codebases.
- **Use when:** Find code pattern in large repo, replace brute-force ripgrep scan.

### 3.8 `obsidian`
- **Path:** `/home/enzo/.hermes/skills/note-taking/obsidian/SKILL.md`
- **Category:** note-taking
- **Description:** Read, search, create, edit notes in Obsidian vault.
- **Use when:** Save research notes, link data findings, build offline knowledge base.

### 3.9 `nano-pdf`
- **Path:** `/home/enzo/.hermes/skills/productivity/nano-pdf/SKILL.md`
- **Category:** productivity
- **Description:** Edit PDF text/typos/titles via nano-pdf CLI (NL prompts).
- **Use when:** Fix typos in PDF text layer, change title/metadata of PDF output.

### 3.10 `powerpoint`
- **Path:** `/home/enzo/.hermes/skills/productivity/powerpoint/SKILL.md`
- **Category:** productivity
- **Description:** Create, read, edit .pptx decks, slides, notes, templates.
- **Use when:** Render data report as deck, auto-generate slides from data.

### 3.11 `youtube-content`
- **Path:** `/home/enzo/.hermes/skills/media/youtube-content/SKILL.md`
- **Category:** media
- **Description:** YouTube transcripts to summaries, threads, blogs.
- **Use when:** Extract transcript as text data, summarize video content as structured data.

### 3.12 `songsee`
- **Path:** `/home/enzo/.hermes/skills/media/songsee/SKILL.md`
- **Category:** media
- **Description:** Audio spectrograms/features (mel, chroma, MFCC) via CLI.
- **Use when:** Extract audio features for ML data, analyze music data.

### 3.13 `spotify`
- **Path:** `/home/enzo/.hermes/skills/media/spotify/SKILL.md`
- **Category:** media
- **Description:** Spotify: play, search, queue, manage playlists and devices.
- **Use when:** Music data (playlist, tracks) — less data-optimization, more media data.

### 3.14 `datn-backend-dev`
- **Path:** `/home/enzo/.hermes/skills/software-development/datn-backend-dev/SKILL.md`
- **Category:** software-development
- **Description:** Boot, test, extend the DATN math-platform FastAPI backend.
- **Use when:** DATN-specific FastAPI backend (project-specific), not a generic data skill.

### 3.15 `datn-ui-dark-parity`
- **Path:** `/home/enzo/.hermes/skills/software-development/datn-ui-dark-parity/SKILL.md`
- **Category:** software-development
- **Description:** Roll out dark-mode parity + taste-skill polish across DATN teacher/student/admin web UI.
- **Use when:** Project-specific UI, not a data skill — listed for completeness only.

---

## 4. Recommendations — which skill to load for which task

| Task | Load skill |
|---|---|
| Scrape multiple web sources with shared pattern | `data-scraping-frameworks` |
| Build data pipeline with LLM gate + render output | `langgraph-enrichment-pipeline` |
| Extract text from PDF / scan | `ocr-and-documents` |
| Evaluate pipeline quality (precision/recall/F1/IoU) | `structured-evaluation-workflows` |
| Optimize context window for data agent | `context-engineering` |
| Explore data interactively, stateful REPL | `jupyter-live-kernel` |
| Output records to Airtable | `airtable` |
| Output to Notion pages/Databases | `notion` |
| Output to Google Sheets | `google-workspace` |
| Download/upload dataset to HuggingFace | `huggingface-hub` |
| Geocode address / compute route | `maps` |
| Track RSS/blog updates as data source | `blogwatcher` |
| Search academic papers | `arxiv` |
| LLM API rate limit + fallback at scale | `llm-router-proxy-patterns` |
| Build knowledge base from data findings | `llm-wiki` or `obsidian` |
| Fix typo in PDF output | `nano-pdf` |
| Render data report as slides | `powerpoint` |
| Extract video transcript | `youtube-content` |
| Audio feature extraction | `songsee` |

---

## 5. How to refresh this listing

When updating (after installing new skills):

```bash
# See all skills
ls /home/enzo/.hermes/skills/*/SKILL.md

# See skills by category
ls /home/enzo/.hermes/skills/data-science/
ls /home/enzo/.hermes/skills/productivity/
ls /home/enzo/.hermes/skills/software-development/
ls /home/enzo/.hermes/skills/mlops/
ls /home/enzo/.hermes/skills/research/
ls /home/enzo/.hermes/skills/evaluation/

# Read skill frontmatter (no need to load full content)
head -20 /home/enzo/.hermes/skills/<category>/<skill>/SKILL.md
```

In Hermes runtime use `skills_list` tool for the full list + descriptions, or `skill_view(name='<skill>')` to load full content.

---

*Inventory created from the current Hermes install (`/home/enzo/.hermes/skills/`). Update when installing new skills.*
