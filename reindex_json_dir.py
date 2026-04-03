"""
按目录重跑 Meilisearch 索引（基于已存在 JSON sidecar）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def collect_json_paths(target_dir: Path, recursive: bool = True) -> list[str]:
    pattern = "**/*.json" if recursive else "*.json"
    return sorted(str(path) for path in target_dir.glob(pattern) if path.is_file())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用指定目录下的 JSON sidecar 重跑索引（无需重新爬虫）"
    )
    parser.add_argument("--dir", required=True, help="JSON sidecar 目录")
    parser.add_argument(
        "--config",
        default="default",
        help="配置名，对应 config/<name>.json（默认: default）",
    )
    parser.add_argument("--workspace", default=None, help="可选：覆盖 workspace")
    parser.add_argument(
        "--date",
        default=None,
        help="可选：索引日期标签，仅用于日志展示（默认今天）",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="仅索引目录根层 JSON，不递归子目录",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印待索引文件数量，不实际写入",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target_dir = Path(args.dir)
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"[错误] 目录不存在或不是目录: {target_dir}")
        return 2

    json_paths = collect_json_paths(target_dir, recursive=not args.no_recursive)
    print(f"[info] 找到 {len(json_paths)} 个 JSON 文件")
    if not json_paths:
        return 0

    if args.dry_run:
        for path in json_paths[:20]:
            print(f"  - {path}")
        if len(json_paths) > 20:
            print(f"  ... 还有 {len(json_paths) - 20} 个")
        return 0

    from app_config import load_app_config
    from meilisearch_tasks import index_workspace_flow
    from utils import load_config

    _, config_workspace = load_config(args.config)
    workspace = args.workspace or config_workspace
    app_cfg = load_app_config()

    index_workspace_flow(
        workspace=workspace,
        date=args.date,
        meili_config=app_cfg.get("meilisearch_config"),
        llm_config=app_cfg.get("llm_config"),
        json_paths=json_paths,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
