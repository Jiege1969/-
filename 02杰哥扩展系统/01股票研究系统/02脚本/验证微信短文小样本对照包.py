# -*- coding: utf-8 -*-
"""
名称：验证微信短文小样本对照包.py
作用：验收224微信短文小样本对照包是否完成旧草稿/v21/成交额门禁对照，并保持正式入口阻断。
安全边界：只读224对照包；只写验收报告；不改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "224微信短文小样本对照包"
REPORT_JSON = OUT_DIR / "微信短文小样本对照包_最新.json"
REPORT_MD = OUT_DIR / "微信短文小样本对照包_最新.md"


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
        "# 微信短文小样本对照包验收",
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
    gates = data.get("准入门禁", {})
    samples = data.get("样本对照", []) or []
    safety = data.get("安全边界", {})
    first = samples[0] if samples else {}
    v21_hits = first.get("v21关键字段命中", {})
    old_hits = first.get("旧话术命中", {})
    v21_banned = first.get("v21禁用交易词命中", {})

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "224对照包 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "微信短文小样本对照包", "报告名称正确", str(data.get("名称"))),
        check(data.get("样本数量") == 1 and len(samples) == 1, "小样本数量明确", f"样本数量={data.get('样本数量')}, 列表={len(samples)}"),
        check(first.get("名称") == "新易盛", "样本股票为新易盛", str(first.get("名称"))),
        check(gates.get("221验收通过") is True and gates.get("222验收通过") is True and gates.get("223验收通过") is True, "221/222/223上游验收均通过", json.dumps(gates, ensure_ascii=False)),
        check(all(v21_hits.values()), "v21短文关键字段完整", json.dumps(v21_hits, ensure_ascii=False)),
        check(not any(v21_banned.values()), "v21短文未命中禁用交易动作词", json.dumps(v21_banned, ensure_ascii=False)),
        check(any(old_hits.values()), "旧草稿旧话术已被识别", json.dumps(old_hits, ensure_ascii=False)),
        check(gates.get("历史成交额可解除估算降级") is False, "历史成交额未正式化时门禁保持阻断", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("允许设计正式可控开关") is False, "正式可控开关未被放行", json.dumps(gates, ensure_ascii=False)),
        check("估算口径" in text and "待正式成交额源回补" in text, "v21仍保留成交额估算降级说明", ""),
        check("不允许替换正式发送模板" in text or "正式替换模板" in text, "明确不替换正式发送模板", ""),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文小样本对照包验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "修改正式短回复生成器": False,
            "修改股票企业微信桥接入口": False,
            "修改股票助手入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "微信短文小样本对照包验收_最新.json"
    latest_md = OUT_DIR / "微信短文小样本对照包验收_最新.md"
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
