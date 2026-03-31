"""
基于 Prefect 的爬虫入口文件
使用 Prefect flows 和 tasks 来管理爬虫工作流
"""

import asyncio
import sys

from prefect_flows import crawl_sites_flow
from prefect_tasks import DEFAULT_CONFIG


async def main():
    """主入口：解析命令行参数并启动 Prefect flow"""
    # 支持命令行参数：python crawler_prefect.py [--config=<name>] [site_name] [section_name]
    config_name = DEFAULT_CONFIG
    filter_site = None
    filter_section = None

    # 解析命令行参数
    args = sys.argv[1:]
    for arg in args[:]:
        if arg.startswith("--config="):
            config_name = arg.split("=", 1)[1]
            args.remove(arg)

    if len(args) > 0:
        filter_site = args[0]
    if len(args) > 1:
        filter_section = args[1]

    # 启动 Prefect flow
    await crawl_sites_flow(
        config_name=config_name,
        filter_site=filter_site,
        filter_section=filter_section,
    )


if __name__ == "__main__":
    asyncio.run(main())
