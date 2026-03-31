"""Smoke test script for Meilisearch embedding write and retrieval quality."""

import argparse
import time
from typing import Any

from meilisearch_settings import ensure_hybrid_settings
from search_service import hybrid_search


def evaluate_hit_rank(hits: list[dict[str, Any]], expected_id: str) -> int:
    """Return one-based rank for expected_id; -1 when absent."""
    for idx, hit in enumerate(hits, start=1):
        if str(hit.get("id", "")) == expected_id:
            return idx
    return -1


def _extract_task_uid(task_result: Any) -> int | None:
    if isinstance(task_result, dict):
        task_uid = task_result.get("taskUid")
        if task_uid is None:
            task_uid = task_result.get("uid")
        return task_uid
    return getattr(task_result, "task_uid", None)


def _wait_task(client: Any, task_result: Any, timeout_ms: int = 120000):
    task_uid = _extract_task_uid(task_result)
    if task_uid is None:
        return
    client.wait_for_task(task_uid, timeout_in_ms=timeout_ms)


def _build_demo_docs(workspace: str) -> list[dict[str, str]]:
    return [
        {
            "id": "doc-uht",
            "workspace": workspace,
            "title": "超高压灭菌饮料的货架期提升",
            "summary": "通过超高压灭菌与冷链结合提升果汁稳定性",
            "cleaned_content": "超高压灭菌可以在低温条件下抑制微生物，减少风味损失，并显著延长饮料货架期。",
            "raw_content": "超高压灭菌可以在低温条件下抑制微生物，减少风味损失，并显著延长饮料货架期。",
        },
        {
            "id": "doc-packaging",
            "workspace": workspace,
            "title": "食品包装材料升级趋势",
            "summary": "可降解包装材料在休闲食品中的应用",
            "cleaned_content": "文章讨论包装薄膜、阻隔性和环保法规，不涉及超高压灭菌。",
            "raw_content": "文章讨论包装薄膜、阻隔性和环保法规，不涉及超高压灭菌。",
        },
        {
            "id": "doc-cold-chain",
            "workspace": workspace,
            "title": "冷链配送优化实践",
            "summary": "生鲜物流路由与温控策略",
            "cleaned_content": "本文聚焦冷链运输过程中的温区管理和车队调度，不讨论灭菌工艺。",
            "raw_content": "本文聚焦冷链运输过程中的温区管理和车队调度，不讨论灭菌工艺。",
        },
    ]


def _build_openai_rest_embedder(hybrid_cfg: dict[str, Any]) -> dict[str, Any] | None:
    endpoint = hybrid_cfg.get("endpoint")
    api_key = hybrid_cfg.get("api_key")
    model = hybrid_cfg.get("model", "text-embedding-3-small")
    dimensions = int(hybrid_cfg.get("dimensions", 1536))
    document_template = hybrid_cfg.get(
        "document_template", "{{doc.title}}\n{{doc.summary}}\n{{doc.cleaned_content}}"
    )
    if not endpoint or not api_key:
        return None
    return {
        "source": "rest",
        "url": endpoint,
        "dimensions": dimensions,
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        "request": {
            "model": model,
            "input": ["{{text}}", "{{..}}"],
            "encoding_format": "float",
        },
        "response": {
            "data": [
                {
                    "embedding": "{{embedding}}",
                },
                "{{..}}",
            ]
        },
        "documentTemplate": document_template,
    }


def _print_hits(title: str, hits: list[dict[str, Any]], top_k: int):
    print(f"\n{title} Top-{top_k}:")
    if not hits:
        print("  (no hits)")
        return
    for i, hit in enumerate(hits[:top_k], start=1):
        doc_id = hit.get("id", "")
        doc_title = hit.get("title", "")
        score = hit.get("_rankingScore")
        score_text = f" score={score:.4f}" if isinstance(score, (float, int)) else ""
        print(f"  {i}. {doc_id} | {doc_title}{score_text}")


def main() -> int:
    import meilisearch

    from app_config import load_app_config

    parser = argparse.ArgumentParser(
        description="Test embedding write and hybrid retrieval in Meilisearch"
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--query", default="超高压灭菌饮料保鲜")
    parser.add_argument("--expected-id", default="doc-uht")
    parser.add_argument("--workspace", default="embedding-eval")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--semantic-ratio", type=float, default=0.7)
    parser.add_argument("--index-uid", default=f"embedding_eval_{int(time.time())}")
    parser.add_argument("--keep-index", action="store_true")
    args = parser.parse_args()

    config = load_app_config(env_file=args.env_file)
    meili_config = config.get("meilisearch_config", {})
    hybrid_cfg = meili_config.get("hybrid_search", {})


    print(f"[INFO] hybrid cfg: {hybrid_cfg}", hybrid_cfg)

    if not meili_config.get("url"):
        print("[ERROR] Missing MEILI_URL in env")
        return 2
    if not hybrid_cfg.get("enabled"):
        print("[ERROR] MEILI_HYBRID_ENABLED is false; cannot test embedding retrieval")
        return 2

    embedder_name = hybrid_cfg.get("embedder_name", "openai-emb")
    embedder_settings = hybrid_cfg.get("embedder") or _build_openai_rest_embedder(
        hybrid_cfg
    )
    if not embedder_settings:
        print("[ERROR] Hybrid embedder config is incomplete")
        return 2

    client = meilisearch.Client(meili_config["url"], meili_config.get("api_key", ""))
    index_uid = args.index_uid
    should_delete = not args.keep_index

    try:
        print(f"[INFO] Creating test index: {index_uid}")
        task = client.create_index(index_uid, {"primaryKey": "id"})
        _wait_task(client, task)

        ensure_hybrid_settings(
            client=client,
            index_uids=[index_uid],
            embedder_name=embedder_name,
            embedder_settings=embedder_settings,
            searchable_attrs=["title", "summary", "cleaned_content", "raw_content"],
            filterable_attrs=["workspace"],
        )

        docs = _build_demo_docs(args.workspace)
        print(f"[INFO] Writing {len(docs)} demo documents")
        task = client.index(index_uid).update_documents(docs)
        _wait_task(client, task)

        filter_expr = f'workspace = "{args.workspace}"'
        lexical_result = client.index(index_uid).search(
            args.query,
            {"limit": args.top_k, "filter": filter_expr},
        )
        lexical_hits = lexical_result.get("hits", [])
        lexical_rank = evaluate_hit_rank(lexical_hits, args.expected_id)
        _print_hits("Lexical Search", lexical_hits, args.top_k)

        hybrid_result = hybrid_search(
            client=client,
            index_uid=index_uid,
            query=args.query,
            embedder_name=embedder_name,
            semantic_ratio=args.semantic_ratio,
            limit=args.top_k,
            filter_expr=filter_expr,
        )
        hybrid_hits = hybrid_result.get("hits", [])
        hybrid_rank = evaluate_hit_rank(hybrid_hits, args.expected_id)
        _print_hits("Hybrid Search", hybrid_hits, args.top_k)

        print("\n[RESULT]")
        print(f"  expected_id={args.expected_id}")
        print(f"  lexical_rank={lexical_rank}")
        print(f"  hybrid_rank={hybrid_rank}")

        if hybrid_rank == -1:
            print("[FAIL] Expected document not found in hybrid search results")
            return 1
        if lexical_rank == -1 or hybrid_rank <= lexical_rank:
            print("[PASS] Hybrid retrieval is effective for this sample")
            return 0
        print("[WARN] Hybrid found expected doc but rank is not better than lexical")
        return 0
    finally:
        if should_delete:
            try:
                task = client.delete_index(index_uid)
                _wait_task(client, task)
                print(f"[INFO] Deleted test index: {index_uid}")
            except Exception as e:
                print(f"[WARN] Failed to delete index {index_uid}: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
