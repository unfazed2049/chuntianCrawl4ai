from typing import Any


def ensure_hybrid_settings(
    client: Any,
    index_uids: list[str],
    embedder_name: str,
    embedder_settings: dict,
    searchable_attrs: list[str] | None = None,
    filterable_attrs: list[str] | None = None,
    sortable_attrs: list[str] | None = None,
):
    """Ensure hybrid retrieval settings exist on target indexes."""
    if not index_uids:
        return
    if not embedder_name or not embedder_settings:
        return

    for index_uid in index_uids:
        payload = {
            "embedders": {
                embedder_name: embedder_settings,
            }
        }
        if searchable_attrs is not None:
            payload["searchableAttributes"] = searchable_attrs
        if filterable_attrs is not None:
            payload["filterableAttributes"] = filterable_attrs
        if sortable_attrs is not None:
            payload["sortableAttributes"] = sortable_attrs

        client.index(index_uid).update_settings(payload)
