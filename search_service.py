from typing import Any


def hybrid_search(
    client: Any,
    index_uid: str,
    query: str,
    *,
    embedder_name: str,
    semantic_ratio: float = 0.4,
    limit: int = 20,
    offset: int = 0,
    filter_expr: str | list[str] | None = None,
    attributes_to_retrieve: list[str] | None = None,
):
    """Run Meilisearch hybrid search using configured embedder."""
    options: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
        "hybrid": {
            "embedder": embedder_name,
            "semanticRatio": semantic_ratio,
        },
    }
    if filter_expr is not None:
        options["filter"] = filter_expr
    if attributes_to_retrieve is not None:
        options["attributesToRetrieve"] = attributes_to_retrieve
    return client.index(index_uid).search(query, options)
