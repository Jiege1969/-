# -*- coding: utf-8 -*-
"""
名称：验证股票历史K线东方财富成交额影子回补探测.py
作用：验收226东方财富历史K线成交额影子回补探测是否拿到正式成交额、未覆盖正式快照、未触发发送或交易。
安全边界：只读226探测包；只写验收报告；不覆盖历史K线最新快照、不改入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "226历史K线东方财富成交额影子回补探测"
REPORT_JSON = OUT_DIR / "股票历史K线东方财富成交额影子回补探测_最新.json"
REPORT_MD = OUT_DIR / "股票历史K线东方财富成交额影子回补探测_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票历史K线东方财富成交额影子回补探测验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    data = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    text = json.dumps(data, ensure_ascii=False) + "\n" + md
    result = data.get("探测结果", {})
    request = data.get("探测请求", {})
    compare = data.get("近5日正式成交额对照", []) or []
    safety = data.get("安全边界", {})
    backfilled = [item for item in compare if item.get("可回补") is True]

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "226探测 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "股票历史K线东方财富成交额影子回补探测", "报告名称正确", str(data.get("名称"))),
        check(data.get("样本股票", {}).get("名称") == "新易盛", "样本股票为新易盛", json.dumps(data.get("样本股票", {}), ensure_ascii=False)),
        check(request.get("接口") == "东方财富公开历史K线接口", "请求接口为东方财富历史K线", json.dumps(request, ensure_ascii=False)),
        check(all(name in request.get("请求头增强", []) for name in ["User-Agent", "Referer", "Accept", "Connection: close"]), "请求头增强记录完整", json.dumps(request.get("请求头增强", []), ensure_ascii=False)),
        check(result.get("是否成功") is True and result.get("返回记录数", 0) >= 5, "东方财富返回足够历史记录", json.dumps(result, ensure_ascii=False)),
        check(len(compare) == 5 and len(backfilled) == 5, "近5日正式成交额完整可回补", f"{len(backfilled)}/{len(compare)}"),
        check(result.get("正式近5日均额") != "缺失" and result.get("正式近5日均额1.2倍") != "缺失", "正式均额和1.2倍阈值已计算", json.dumps(result, ensure_ascii=False)),
        check(result.get("是否可解除样本估算降级") is True, "样本估算降级可进入影子解除", json.dumps(result, ensure_ascii=False)),
        check("不直接覆盖" in text or "不直接覆盖 `重点关注池历史K线快照_最新.json`" in text, "明确不覆盖历史K线最新快照", ""),
        check("生成重点关注池历史K线快照.py" in text and "重试" in text, "脚本增强建议存在", ""),
        check(safety.get("联网只读公开接口") is True, "本轮仅联网只读公开接口", json.dumps(safety, ensure_ascii=False)),
        check(all(value is False for key, value in safety.items() if key != "联网只读公开接口"), "除联网只读外安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("覆盖历史K线最新快照") is False and safety.get("修改历史K线生成脚本") is False, "未覆盖快照且未改脚本", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "股票历史K线东方财富成交额影子回补探测验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "联网只读公开接口": True,
            "覆盖历史K线最新快照": False,
            "修改历史K线生成脚本": False,
            "修改220口径": False,
            "修改221短文": False,
            "修改222影子分支": False,
            "修改正式短回复生成器": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "股票历史K线东方财富成交额影子回补探测验收_最新.json"
    latest_md = OUT_DIR / "股票历史K线东方财富成交额影子回补探测验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
