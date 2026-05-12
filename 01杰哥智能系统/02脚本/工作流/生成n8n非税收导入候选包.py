"""
名称：生成n8n非税收导入候选包.py
作用：基于n8n工作流草案清单和当前候选规则，生成排除税收业务的低风险导入候选包。
触发方式：python 生成n8n非税收导入候选包.py
依赖：Python 标准库；需已有n8n工作流草案清单。
所属系统：01杰哥智能系统
安全边界：只生成本地候选包；不调用n8n API、不导入工作流、不启用Webhook、不触发真实工作流。
创建/修改记录：2026-04-27 创建n8n非税收低风险导入候选包脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    return v3_root() / "01杰哥智能系统" / "01配置"


def draft_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "03数据" / "工作流草案"
    target.mkdir(parents=True, exist_ok=True)
    return target


def review_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "03数据" / "工作流导入审查"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_drafts() -> Path:
    latest = draft_dir() / "n8n工作流草案清单_最新.json"
    if latest.exists():
        return latest
    script = Path(__file__).resolve().parent / "生成n8n工作流草案.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def evaluate(draft: dict[str, Any], allowed: set[str], excluded: set[str]) -> dict[str, Any]:
    name = draft.get("名称", "")
    webhook = draft.get("Webhook草案", {})
    reasons = []
    if name in excluded or "税收" in name or "税收" in str(draft.get("归属系统", "")):
        reasons.append("用户已暂停税收业务搭建，当前候选包排除")
    if name not in allowed:
        reasons.append("不在当前允许候选清单")
    if draft.get("是否允许自动触发") is not False:
        reasons.append("自动触发未关闭")
    if webhook.get("是否启用") is not False:
        reasons.append("Webhook未关闭")
    is_candidate = len(reasons) == 0
    return {
        "工作流名": name,
        "归属系统": draft.get("归属系统"),
        "草案文件": draft.get("草案文件"),
        "Webhook路径": webhook.get("路径"),
        "是否候选": is_candidate,
        "阻断原因": reasons,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
    }


def build_package() -> dict[str, Any]:
    rules = load_json(config_dir() / "n8n非税收导入候选规则.json")
    manifest_path = ensure_drafts()
    manifest = load_json(manifest_path)
    allowed = set(rules.get("允许候选", []))
    excluded = set(rules.get("明确排除", []))
    evaluated = [evaluate(item, allowed, excluded) for item in manifest.get("工作流草案", [])]
    candidates = [item for item in evaluated if item["是否候选"]]
    blocked = [item for item in evaluated if not item["是否候选"]]
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则来源": str(config_dir() / "n8n非税收导入候选规则.json"),
        "草案来源": str(manifest_path),
        "候选工作流": candidates,
        "阻断工作流": blocked,
        "统计": {
            "候选数量": len(candidates),
            "阻断数量": len(blocked),
            "总数量": len(evaluated),
        },
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否包含税收业务": any("税收" in item.get("工作流名", "") for item in candidates),
        "安全说明": "本候选包只用于人工审查，不导入n8n，不启用Webhook；税收相关工作流已排除。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = review_dir() / f"n8n非税收导入候选包_{timestamp}.json"
    latest = review_dir() / "n8n非税收导入候选包_最新.json"
    text = json.dumps(package, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "blocked_count": len(blocked), "output": str(output)}, ensure_ascii=True))
    return package


def main() -> int:
    build_package()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
