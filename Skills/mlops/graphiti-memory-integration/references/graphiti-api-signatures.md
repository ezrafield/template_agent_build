# Graphiti Core v0.29.0 — API Signatures Reference

## Initialization

```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

driver = FalkorDriver(host="localhost", port=6379)

llm_config = LLMConfig(
    api_key="...",
    base_url="http://127.0.0.1:20128/v1",
    model="gh/gpt-4o",
    # temperature: float = 1.0 (DEFAULT_TEMPERATURE)
    # max_tokens: int = 16384 (DEFAULT_MAX_TOKENS)
    # small_model: str | None = None
)

embedder_config = OpenAIEmbedderConfig(
    api_key="...",
    base_url="http://127.0.0.1:20128/v1",
    embedding_model="text-embedding-3-small",  # NOT 'model'
    embedding_dim=1024,  # default from env EMBEDDING_DIM or 1024
)

client = Graphiti(
    graph_driver=driver,
    llm_client=llm_client,
    embedder=OpenAIEmbedder(config=embedder_config),
    cross_encoder=reranker,
)
await client.build_indices_and_constraints()
```

## AddEpisodeResults

```python
class AddEpisodeResults(BaseModel):
    episode: EpisodicNode
    episodic_edges: list[EpisodicEdge]
    nodes: list[EntityNode]
    edges: list[EntityEdge]
    communities: list[CommunityNode]
    community_edges: list[CommunityEdge]
```

## EntityEdge (from edges.py)

Base `Edge`:
- uuid: str
- group_id: str
- source_node_uuid: str
- target_node_uuid: str
- created_at: datetime

`EntityEdge(Edge)` adds:
- name: str — relation name (SCREAMING_SNAKE_CASE)
- fact: str — natural language fact
- fact_embedding: list[float] | None
- episodes: list[str] — episode UUIDs
- expired_at: datetime | None
- valid_at: datetime | None
- invalid_at: datetime | None
- reference_time: datetime | None
- attributes: dict[str, Any]

**NO** `relation_type`, `source_node_name`, `target_node_name` attributes.

## EntityNode

- uuid: str
- name: str
- name_embedding: list[float] | None
- group_id: str
- summary: str
- labels: list[str]
- attributes: dict[str, Any]
- created_at: datetime

## search() — Simple

```python
async def search(
    self,
    query: str,
    center_node_uuid: str | None = None,
    group_ids: list[str] | None = None,
    num_results=10,  # DEFAULT_SEARCH_LIMIT
    search_filter: SearchFilters | None = None,
    driver: GraphDriver | None = None,
) -> list[EntityEdge]:
```

## search_() — Advanced

```python
async def search_(
    self,
    query: str,
    config: SearchConfig = COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    group_ids: list[str] | None = None,
    center_node_uuid: str | None = None,
    bfs_origin_node_uuids: list[str] | None = None,
    search_filter: SearchFilters | None = None,
    driver: GraphDriver | None = None,
) -> SearchResults:
```

## SearchResults

```python
class SearchResults(BaseModel):
    edges: list[EntityEdge]
    edge_reranker_scores: list[float]
    nodes: list[EntityNode]
    node_reranker_scores: list[float]
    episodes: list[EpisodicNode]
    episode_reranker_scores: list[float]
    communities: list[CommunityNode]
    community_reranker_scores: list[float]
```

## EpisodeType enum

- EpisodeType.message
- EpisodeType.text
- EpisodeType.json
- EpisodeType.fact_triple

## Graph Database Backends

| Backend | Class | Requires Server |
|---------|-------|-----------------|
| Neo4j | (default, uri-based) | Yes |
| FalkorDB | FalkorDriver(host, port) | Yes (Docker) |
| Kùzu | KuzuDriver(db=':memory:' or path) | No (embedded) |
| Neptune | NeptuneDriver(...) | Yes (AWS) |

## Search Config Recipes (from search_config_recipes.py)

- COMBINED_HYBRID_SEARCH_RRF
- COMBINED_HYBRID_SEARCH_CROSS_ENCODER
- EDGE_HYBRID_SEARCH_NODE_DISTANCE
- NODE_HYBRID_SEARCH_RRF
