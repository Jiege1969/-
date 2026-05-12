# -*- coding: utf-8 -*-
"""
名称：验证模型路由与审稿能力只读审计.py
作用：验收模型路由与审稿能力只读审计报告是否完整、边界是否安全。
触发方式：python 验证模型路由与审稿能力只读审计.py
安全边界：只读审计报告；只写验收报告；不运行模型；不改配置；不重启服务；不触发n8n；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
AUDIT_JSON = OUT_DIR / "模型路由与审稿能力只读审计_最新.json"
AUDIT_MD = OUT_DIR / "模型路由与审稿能力只读审计_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    audit = load_json(AUDIT_JSON)
    md = load_text(AUDIT_MD)
    text = json.dumps(audit, ensure_ascii=False) + "\n" + md
    config = audit.get("配置解析", {})
    routes = audit.get("路由覆盖", [])
    safety = audit.get("安全边界", {})
    review = audit.get("审稿能力", {})
    route_text = json.dumps(routes, ensure_ascii=False)

    checks = [
        check(AUDIT_JSON.exists() and AUDIT_MD.exists(), "审计 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(config.get("模型资源池存在") and config.get("模型路由策略存在") and config.get("双系统Ollama治理存在"), "核心模型配置存在且已解析", ""),
        check(config.get("预计模型数量", 0) >= 8, "预计模型清单数量充足", str(config.get("预计模型数量"))),
        check(config.get("任务路由数量", 0) >= 8, "任务路由数量充足", str(config.get("任务路由数量"))),
        check(all(keyword in route_text for keyword in ["股票研究", "知识库问答", "代码维护", "普通聊天"]), "关键任务路由覆盖股票/知识库/代码/聊天", ""),
        check("生产切换" in text and ("必须人工确认" in text or "不切换生产配置" in text), "生产切换边界明确", ""),
        check(review.get("sidecar验收记录") not in ("", "缺失"), "审稿sidecar验收记录存在", review.get("sidecar验收记录", "")),
        check(review.get("低负载闸口记录") not in ("", "缺失"), "低负载闸口验收记录存在", review.get("低负载闸口记录", "")),
        check(all(value is False for value in safety.values()), "安全边界全部为False", json.dumps(safety, ensure_ascii=False)),
        check("不运行批量模型任务" in text or "未执行模型推理" in text, "明确不运行批量模型任务", ""),
        check("不拉取模型" in text or "拉取模型" in json.dumps(safety, ensure_ascii=False), "明确不拉取模型", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "模型路由与审稿能力只读审计验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "拉取模型": False,
            "删除模型": False,
            "运行批量推理": False,
            "切换生产配置": False,
            "重启服务": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "模型路由与审稿能力只读审计验收_最新.json"
    latest_md = OUT_DIR / "模型路由与审稿能力只读审计验收_最新.md"
    lines = [
        "# 模型路由与审稿能力只读审计验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, report)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
