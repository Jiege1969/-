# -*- coding: utf-8 -*-
"""
名称：验证微信短文正式成交额口径影子重跑.py
作用：验收229微信短文正式成交额口径影子重跑是否移除估算降级、保留安全边界。
安全边界：只读229影子重跑；只写验收报告；不覆盖221/222、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "229微信短文正式成交额口径影子重跑"
REPORT_JSON = OUT_DIR / "微信短文正式成交额口径影子重跑_最新.json"
REPORT_MD = OUT_DIR / "微信短文正式成交额口径影子重跑_最新.md"


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
        "# 微信短文正式成交额口径影子重跑验收",
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
    short = str(data.get("微信短文", ""))
    safety = data.get("安全边界", {})
    required = data.get("关键字段命中", {})
    banned = data.get("禁用交易词命中", {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "229影子重跑 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "微信短文正式成交额口径影子重跑", "报告名称正确", str(data.get("名称"))),
        check(data.get("样本股票", {}).get("名称") == "新易盛", "样本股票为新易盛", json.dumps(data.get("样本股票", {}), ensure_ascii=False)),
        check(data.get("口径状态", {}).get("228验收通过") is True, "228上游验收通过", json.dumps(data.get("口径状态", {}), ensure_ascii=False)),
        check("250.85亿元" in short and "301.02亿元" in short, "短文使用正式阈值", short),
        check("估算口径" not in short and "待正式成交额源回补" not in short, "短文移除估算降级", short),
        check("东方财富历史K线正式成交额影子口径" in short, "短文标明正式成交额影子口径", short),
        check(all(required.values()), "短文关键字段完整", json.dumps(required, ensure_ascii=False)),
        check(not any(banned.values()), "短文未命中交易动作禁用词", json.dumps(banned, ensure_ascii=False)),
        check("不自动交易" in short, "短文保留不自动交易声明", ""),
        check(300 <= int(data.get("短文长度", 0)) <= 700, "短文长度适合微信端", str(data.get("短文长度"))),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("覆盖221原文件") is False and safety.get("覆盖222影子分支") is False, "未覆盖221/222", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文正式成交额口径影子重跑验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "覆盖221原文件": False,
            "覆盖222影子分支": False,
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
    latest_json = OUT_DIR / "微信短文正式成交额口径影子重跑验收_最新.json"
    latest_md = OUT_DIR / "微信短文正式成交额口径影子重跑验收_最新.md"
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
