"""
Meilisearch indexing tasks and flow for Prefect
将爬取的 cleaned_content 经 LLM 结构化后写入 Meilisearch 各 index
"""

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import litellm
import meilisearch
from prefect import flow, task

from meilisearch_settings import ensure_hybrid_settings
from markdown_cleaner import clean_markdown_content
from utils import DEFAULT_WORKSPACE, OUTPUT_ROOT, load_prompts

COMPETITOR_PROFILE_DTYPES = {"products", "cases", "solutions", "technologies"}

# index prompt 的 key 与 prompts/ 目录下文件名对应
_PROMPT_KEY = {
    "news": "index_competitor_news",
    "industry_news": "index_industry_news",
    "trade_show": "index_trade_show",
    "profile": "index_competitor_profile",
    "pre_filter": "index_pre_filter",
}


def _parse_keep_flag(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "keep"}
    if isinstance(value, (int, float)):
        return bool(value)
    return True


def _collect_json_sidecars(
    workspace: str,
    date: str,
    json_paths: list[str] | None = None,
) -> list[Path]:
    if json_paths:
        files: list[Path] = []
        for raw_path in dict.fromkeys(json_paths):
            jf = Path(raw_path)
            if not jf.exists():
                print(f"  [警告] sidecar 文件不存在，跳过: {jf}")
                continue
            if jf.suffix.lower() != ".json":
                print(f"  [警告] 非 JSON sidecar，跳过: {jf}")
                continue
            files.append(jf)
        print(f"  使用上游传入的 {len(files)} 个 JSON sidecar 文件")
        return files

    scan_root = OUTPUT_ROOT / workspace / date
    if not scan_root.exists():
        print(f"  [跳过] 目录不存在: {scan_root}")
        return []
    files = list(scan_root.rglob("*.json"))
    print(f"  扫描到 {len(files)} 个 JSON sidecar 文件")
    return files


def _build_openai_rest_embedder(hybrid_cfg: dict) -> dict | None:
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


def _ensure_hybrid_search_if_configured(client: meilisearch.Client, meili_config: dict):
    hybrid_cfg = meili_config.get("hybrid_search", {})
    if not hybrid_cfg.get("enabled", False):
        return

    embedder_name = hybrid_cfg.get("embedder_name", "openai-emb")
    index_uids = hybrid_cfg.get(
        "indexes", ["industry_news", "competitor_news", "trade_shows"]
    )
    embedder_settings = hybrid_cfg.get("embedder") or _build_openai_rest_embedder(
        hybrid_cfg
    )
    if not embedder_settings:
        print(
            "  [警告] hybrid_search 已启用但 embedder 配置不完整，跳过 settings 初始化"
        )
        return

    ensure_hybrid_settings(
        client=client,
        index_uids=index_uids,
        embedder_name=embedder_name,
        embedder_settings=embedder_settings,
    )
    print(f"  [index] hybrid settings updated for {len(index_uids)} indexes")


# ─── LLM 调用 ────────────────────────────────────────────────────────────────


def call_llm(llm_cfg: dict, system_prompt: str, user_content: str) -> dict:
    """调用 LLM，返回解析后的 JSON dict"""
    response = litellm.completion(
        model=llm_cfg["provider"],
        api_key=llm_cfg["api_token"],
        api_base=llm_cfg.get("base_url"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # fallback：从文本中提取 JSON 块
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


# ─── 工具函数 ────────────────────────────────────────────────────────────────


def get_meili_client(config: dict) -> meilisearch.Client:
    url = config.get("url", "http://localhost:7700")
    api_key = config.get("api_key", "")
    return meilisearch.Client(url, api_key)


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


# ─── Index Tasks ─────────────────────────────────────────────────────────────


@task(name="index_competitor_news_doc", tags=["index"])
def index_competitor_news_task(
    client: meilisearch.Client,
    llm_cfg: dict,
    prompts: dict,
    meta: dict,
    cleaned_content: str,
    raw_content: str,
):
    """LLM 提取字段后写入 competitor_news"""
    system_prompt = prompts[_PROMPT_KEY["news"]]["instruction"]
    try:
        extracted = call_llm(llm_cfg, system_prompt, cleaned_content)
    except Exception as e:
        print(f"  [警告] LLM 提取失败 [{meta['url']}]: {e}")
        return

    doc = {
        "id": _url_hash(meta["url"]),
        "workspace": meta["workspace"],
        "competitor_id": meta["competitor_id"],
        "competitor_name": meta["site_name"],
        "url": meta["url"],
        "crawled_at": meta["crawled_at"],
        "source_section": meta["section_name"],
        "raw_content": raw_content,
        **extracted,
    }
    client.index("competitor_news").update_documents([doc])
    print(f"  [index] competitor_news: {meta['url']}")


@task(name="index_industry_news_doc", tags=["index"])
def index_industry_news_task(
    client: meilisearch.Client,
    llm_cfg: dict,
    prompts: dict,
    meta: dict,
    cleaned_content: str,
    raw_content: str,
):
    """LLM 提取字段后写入 industry_news"""
    system_prompt = prompts[_PROMPT_KEY["industry_news"]]["instruction"]
    try:
        extracted = call_llm(llm_cfg, system_prompt, cleaned_content)
    except Exception as e:
        print(f"  [警告] LLM 提取失败 [{meta['url']}]: {e}")
        return

    doc = {
        "id": _url_hash(meta["url"]),
        "workspace": meta["workspace"],
        "url": meta["url"],
        "crawled_at": meta["crawled_at"],
        "raw_content": raw_content,
        **extracted,
    }
    client.index("industry_news").update_documents([doc])
    print(f"  [index] industry_news: {meta['url']}")


@task(name="index_trade_show_doc", tags=["index"])
def index_trade_show_task(
    client: meilisearch.Client,
    llm_cfg: dict,
    prompts: dict,
    meta: dict,
    cleaned_content: str,
    raw_content: str,
):
    """LLM 提取字段后写入 trade_shows"""
    system_prompt = prompts[_PROMPT_KEY["trade_show"]]["instruction"]
    try:
        extracted = call_llm(llm_cfg, system_prompt, cleaned_content)
    except Exception as e:
        print(f"  [警告] LLM 提取失败 [{meta['url']}]: {e}")
        return

    name = extracted.get("name", "")
    year = extracted.get("year") or datetime.now().year
    doc = {
        "id": _url_hash(f"{name}{year}"),
        "workspace": meta["workspace"],
        "crawled_at": meta["crawled_at"],
        "raw_content": raw_content,
        **extracted,
    }
    client.index("trade_shows").update_documents([doc])
    print(f"  [index] trade_shows: {name} {year}")


@task(name="upsert_competitor_profile", tags=["index"])
def upsert_competitor_profile_task(
    client: meilisearch.Client,
    llm_cfg: dict,
    prompts: dict,
    workspace: str,
    competitor_id: str,
    site_name: str,
    new_items: list[dict],
):
    """
    LLM 负责合并竞争对手档案：
    - 获取现有 profile（或创建空档案）
    - 将现有 profile + 所有新内容传给 LLM
    - LLM 返回合并后的完整档案
    - Upsert 到 Meilisearch
    同一 url 的内容视为更新（内容已重新爬取），由 LLM 处理替换逻辑
    """
    doc_id = f"{workspace}_{competitor_id}"
    idx = client.index("competitor_profiles")

    # 获取现有档案
    try:
        existing = dict(idx.get_document(doc_id))
    except Exception:
        existing = {
            "id": doc_id,
            "workspace": workspace,
            "competitor_id": competitor_id,
            "name": site_name,
            "website": "",
            "country": "",
            "updated_at": "",
            "products": [],
            "cases": [],
            "solutions": [],
            "technologies": [],
        }

    user_content = json.dumps(
        {"existing_profile": existing, "new_items": new_items},
        ensure_ascii=False,
    )

    system_prompt = prompts[_PROMPT_KEY["profile"]]["instruction"]
    try:
        updated = call_llm(llm_cfg, system_prompt, user_content)
    except Exception as e:
        print(f"  [警告] LLM 合并失败 [{competitor_id}]: {e}")
        return

    # 确保必要的 meta 字段不被 LLM 遗漏
    updated["id"] = doc_id
    updated["workspace"] = workspace
    updated["competitor_id"] = competitor_id
    updated["updated_at"] = datetime.now(timezone.utc).isoformat()

    idx.update_documents([updated])
    print(
        f"  [index] competitor_profiles: upserted {competitor_id} ({len(new_items)} new items)"
    )


@task(name="pre_index_filter_doc", tags=["index", "filter"])
def pre_index_filter_task(
    llm_cfg: dict,
    prompts: dict,
    meta: dict,
    cleaned_content: str,
) -> tuple[bool, str]:
    """预留的内容过滤任务：在写入 Meilisearch 前做 LLM 判定。"""
    prompt_cfg = prompts.get(_PROMPT_KEY["pre_filter"], {})
    system_prompt = prompt_cfg.get("instruction", "").strip()
    if not system_prompt:
        return True, "index_pre_filter prompt 未配置，默认保留"

    user_content = json.dumps(
        {
            "meta": meta,
            "cleaned_content": cleaned_content,
            "rule": "判断该内容是否值得写入检索库，输出 keep(boolean) 与 reason(string)",
        },
        ensure_ascii=False,
    )
    try:
        verdict = call_llm(llm_cfg, system_prompt, user_content)
    except Exception as e:
        return True, f"过滤任务调用失败，默认保留: {e}"

    keep = _parse_keep_flag(verdict.get("keep", True))
    reason = str(verdict.get("reason", ""))
    return keep, reason


# ─── Index Flow ───────────────────────────────────────────────────────────────


@flow(name="index_workspace", log_prints=True)
def index_workspace_flow(
    workspace: str = DEFAULT_WORKSPACE,
    date: str | None = None,
    meili_config: dict | None = None,
    llm_config: dict | None = None,
    json_paths: list[str] | None = None,
):
    """
    扫描 output/{workspace}/{date}/ 下所有 .json sidecar，
    以 cleaned_content 为输入，经 LLM 结构化后写入对应 Meilisearch index。
    date 默认为今天（格式 YYYYMMDD）。
    """
    from datetime import date as date_cls

    if not meili_config:
        print("  [跳过] 未配置 meilisearch_config，跳过 indexing")
        return
    if not llm_config:
        print("  [跳过] 未配置 llm_config，跳过 indexing")
        return

    if date is None:
        date = date_cls.today().strftime("%Y%m%d")

    client = get_meili_client(meili_config)
    _ensure_hybrid_search_if_configured(client, meili_config)
    prompts = load_prompts()

    # 按 competitor_id 归集 profile 类数据
    # {competitor_id: {"site_name": str, "items": [{"data_type":..., "url":..., "cleaned_content":..., "raw_content":...}]}}
    profiles: dict = defaultdict(lambda: {"site_name": "", "items": []})

    json_files = _collect_json_sidecars(workspace, date, json_paths)
    if not json_files:
        return

    for jf in json_files:
        try:
            payload = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [警告] 读取失败 {jf}: {e}")
            continue

        meta = payload.get("meta", {})
        raw_content = payload.get("raw_content", "")
        # cleaned_content = payload.get("cleaned_content", "")
        data_type = meta.get("data_type")
        competitor_id = meta.get("competitor_id")

        if not raw_content:
            print(f"  [跳过] raw_content 为空: {jf.name}")
            continue

        # if not cleaned_content:
        #     cleaned_content = clean_markdown_content(raw_content)

        # keep, reason = pre_index_filter_task(llm_config, prompts, meta, cleaned_content)
        # if not keep:
        #     print(f"  [过滤] 跳过 {jf.name}: {reason}")
        #     continue

        if data_type in COMPETITOR_PROFILE_DTYPES and competitor_id:
            if not profiles[competitor_id]["site_name"]:
                profiles[competitor_id]["site_name"] = meta["site_name"]
            profiles[competitor_id]["items"].append(
                {
                    "data_type": data_type,
                    "url": meta["url"],
                    # "cleaned_content": cleaned_content,
                    "raw_content": raw_content,
                }
            )

        elif data_type == "news" and competitor_id:
            index_competitor_news_task(
                client, llm_config, prompts, meta, raw_content
            )

        elif data_type == "industry_news":
            index_industry_news_task(
                client, llm_config, prompts, meta, raw_content
            )

        elif data_type == "trade_show":
            index_trade_show_task(
                client, llm_config, prompts, meta, raw_content
            )

        else:
            print(f"  [跳过] data_type={data_type!r}, file={jf.name}")

    # competitor_profiles：每个竞争对手一次 LLM 合并调用
    for competitor_id, data in profiles.items():
        upsert_competitor_profile_task(
            client,
            llm_config,
            prompts,
            workspace,
            competitor_id,
            data["site_name"],
            data["items"],
        )

    print(f"\n  Indexing 完成 [workspace={workspace}, date={date}]")
