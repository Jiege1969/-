# -*- coding: utf-8 -*-
"""
名称：验证L3企业微信短答桥接dry_run.py
作用：通过本地企业微信桥接入口dry-run验证L3短答能被桥接拿到。
触发方式：python 验证L3企业微信短答桥接dry_run.py
安全边界：real_send=false；不真实回传企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SAMPLES = [
    ("分析云南锗业", "云南锗业", "sz002428"),
    ("分析天齐锂业", "天齐锂业", "sz002466"),
    ("分析华虹公司", "华虹公司", "sh688347"),
    ("分析浙商中拓", "浙商中拓", "sz000906"),
    ("分析正丹股份", "正丹股份", "sz300641"),
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def post_bridge(text: str) -> dict[str, Any]:
    body = json.dumps({"text": text, "real_send": False}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:19302/wecom-bot/message",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def validate(question: str, name: str, code: str, result: dict[str, Any]) -> dict[str, Any]:
    content = str(result.get("企业微信内容") or result.get("回复") or "")
    body = "\n".join(line for line in content.splitlines() if not line.strip().startswith("!["))
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    why_line = next((line for line in lines if line.startswith("为什么：")), "")
    checks = {
        "assistant_completed": result.get("股票助手状态") == "完成",
        "real_send_false": result.get("真实回传") is False,
        "has_analysis_object": f"分析对象：{name}（{code}）" in body,
        "has_conclusion": "结论：" in body,
        "has_missing": "缺口：" in body,
        "not_old_template": "操作策略：" not in content and "关注条件：" not in content,
        "no_trade_words": all(word not in content for word in ["买入", "卖出", "下单", "加仓", "减仓", "满仓", "止盈", "目标价"]),
        "frontend_reply_not_too_long": len(body) <= 560,
        "frontend_line_count_controlled": len(lines) <= 10,
        "why_line_is_compressed": bool(why_line) and len(why_line) <= 150,
    }
    blocking = [key for key, ok in checks.items() if not ok]
    return {
        "question": question,
        "expected": f"分析对象：{name}（{code}）",
        "checks": checks,
        "blocking": blocking,
        "passed": not blocking,
        "reply_length": len(body),
        "line_count": len(lines),
        "why_line_length": len(why_line),
        "real_send": result.get("真实回传"),
        "reply_preview": content[:700],
    }


def markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['question']} | {'通过' if item['passed'] else '失败'} | {item['reply_length']} | {'无' if not item['blocking'] else '、'.join(item['blocking'])} |"
        for item in report["samples"]
    ]
    return "\n".join([
        "# L3企业微信短答桥接 dry-run 验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体结论：{report['overall']['conclusion']}",
        "",
        "| 问题 | 结果 | 长度 | 阻断项 |",
        "|---|---:|---:|---|",
        *rows,
        "",
        "## 边界",
        "",
        "- real_send=false",
        "- 不真实回传企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "",
    ])


def main() -> int:
    root = module_root()
    samples: list[dict[str, Any]] = []
    for question, name, code in SAMPLES:
        try:
            result = post_bridge(question)
            samples.append(validate(question, name, code, result))
        except Exception as exc:  # noqa: BLE001
            samples.append({
                "question": question,
                "passed": False,
                "blocking": ["bridge_request_failed"],
                "error": str(exc),
            })
    passed = sum(1 for item in samples if item.get("passed"))
    report = {
        "名称": "L3企业微信短答桥接dry-run验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if passed == len(samples) else "failed",
        "samples": samples,
        "overall": {
            "sample_count": len(samples),
            "passed_count": passed,
            "conclusion": "桥接dry-run通过" if passed == len(samples) else "桥接dry-run存在阻断项",
        },
        "safety_boundary": {
            "real_send": False,
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    out_dir = root / "03数据" / "245L3评分基础资产"
    json_path = out_dir / "L3企业微信短答桥接dry_run验收_20260507.json"
    md_path = out_dir / "L3企业微信短答桥接dry_run验收_20260507.md"
    write_json(json_path, report)
    write_text(md_path, markdown(report))
    print(json.dumps({"status": report["status"], "passed_count": passed, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
