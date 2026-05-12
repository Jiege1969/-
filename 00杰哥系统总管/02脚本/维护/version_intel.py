# -*- coding: utf-8 -*-
"""
名称：version_intel.py
作用：版本升级治理 V1.1 只读拉取候选版本情报，供总管系统后续判断。
触发方式：python version_intel.py
依赖：upgrade_governance_common.py；GitHub/Docker Hub 等公开版本接口；网络可用时才返回情报。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/version_intel_latest.json；version_intel.jsonl。
安全边界：只读获取版本情报；不给“立即升级”建议；不下载、不安装、不升级、不停止服务。
创建/修改记录：2026-05-03 创建版本治理 V1.1 只读脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-version-intel
"""

from __future__ import annotations

import json
from typing import Any

from upgrade_governance_common import LOG_DIR, NO_ACTION_BOUNDARY, append_jsonl, http_json, now_stamp, write_json


def github_latest(repo: str) -> dict[str, Any]:
    payload = http_json(f"https://api.github.com/repos/{repo}/releases/latest", timeout=10)
    data = payload.get("data")
    if payload.get("ok") and isinstance(data, dict):
        return {
            "来源": "github",
            "仓库": repo,
            "可读取": True,
            "tag": data.get("tag_name", ""),
            "名称": data.get("name", ""),
            "发布时间": data.get("published_at", ""),
            "链接": data.get("html_url", ""),
        }
    return {"来源": "github", "仓库": repo, "可读取": False, "错误": payload.get("error", "")}


def dockerhub_tags(namespace: str, repo: str, limit: int = 5) -> dict[str, Any]:
    url = f"https://hub.docker.com/v2/repositories/{namespace}/{repo}/tags?page_size={limit}&ordering=last_updated"
    payload = http_json(url, timeout=10)
    data = payload.get("data")
    if payload.get("ok") and isinstance(data, dict):
        tags = []
        for item in data.get("results", [])[:limit]:
            tags.append({
                "name": item.get("name", ""),
                "last_updated": item.get("last_updated", ""),
                "digest": item.get("digest", ""),
            })
        return {"来源": "dockerhub", "镜像": f"{namespace}/{repo}", "可读取": True, "tags": tags}
    return {"来源": "dockerhub", "镜像": f"{namespace}/{repo}", "可读取": False, "错误": payload.get("error", "")}


def main() -> int:
    now, stamp = now_stamp()
    records = [
        github_latest("n8n-io/n8n"),
        github_latest("ollama/ollama"),
        dockerhub_tags("n8nio", "n8n"),
        dockerhub_tags("ollama", "ollama"),
        dockerhub_tags("library", "redis"),
    ]
    report = {
        "名称": "候选版本情报",
        "版本": "V1.1",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "情报": records,
        "安全边界": NO_ACTION_BOUNDARY,
        "结论": "只读情报采集；不下载、不升级、不给立即升级建议。",
    }
    path = LOG_DIR / f"version_intel_{stamp}.json"
    latest = LOG_DIR / "version_intel_latest.json"
    jsonl = LOG_DIR / "version_intel.jsonl"
    write_json(path, report)
    write_json(latest, report)
    append_jsonl(jsonl, report)
    print(json.dumps({"状态": "完成", "情报数量": len(records), "报告": str(latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
