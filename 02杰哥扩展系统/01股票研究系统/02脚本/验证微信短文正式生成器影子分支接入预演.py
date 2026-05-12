# -*- coding: utf-8 -*-
"""
名称：验证微信短文正式生成器影子分支接入预演.py
作用：验收正式企业微信单股短回复生成器 shadow_v21 影子分支接入预演是否完整、安全、未改正式入口。
安全边界：只读影子预演和正式入口快照；只写验收报告；不修改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "222微信短文正式生成器影子分支接入预演"
REPORT_JSON = OUT_DIR / "微信短文正式生成器影子分支接入预演_最新.json"
REPORT_MD = OUT_DIR / "微信短文正式生成器影子分支接入预演_最新.md"


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


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 微信短文正式生成器影子分支接入预演验收",
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
    compare = data.get("对照结果", {})
    shadow_text = data.get("影子短文输出", "")
    safety = data.get("安全边界", {})
    snapshots = data.get("正式入口快照", [])
    banned = compare.get("影子短文禁用交易词命中", {})
    harmful_banned = {
        key: value
        for key, value in banned.items()
        if key != "自动交易" or ("不自动交易" not in shadow_text and "不会自动交易" not in shadow_text)
    }
    required = compare.get("影子短文关键字段命中", {})
    snapshot_ok = True
    snapshot_notes = []
    for item in snapshots:
        path = Path(item.get("路径", ""))
        current_hash = sha256(path)
        ok = item.get("存在") is True and current_hash == item.get("sha256")
        snapshot_ok = snapshot_ok and ok
        snapshot_notes.append(f"{path.name}:{'ok' if ok else 'changed'}")

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "影子分支预演 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(compare.get("221验收结论") == "通过", "上游 221 微信短文验收通过", str(compare.get("221验收结论"))),
        check(len(shadow_text) >= 300, "影子短文非空且适合微信端", f"长度={len(shadow_text)}"),
        check(all(required.values()), "影子短文覆盖观察/转强/失败/风险/详情/声明", json.dumps(required, ensure_ascii=False)),
        check(not any(harmful_banned.values()), "影子短文未命中禁用交易动作词", json.dumps(banned, ensure_ascii=False)),
        check(compare.get("影子短文披露成交额口径") is True, "影子短文披露成交额口径", ""),
        check(compare.get("影子短文保留本地详情") is True, "影子短文保留本地详情路径", ""),
        check("shadow_v21" in text and "不替换正式入口" in text, "明确为 shadow_v21 影子分支且不替换正式入口", ""),
        check(len(snapshots) == 3 and snapshot_ok, "正式入口文件哈希未变化", ";".join(snapshot_notes)),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check("发送企业微信" in safety and safety.get("发送企业微信") is False, "未发送企业微信", json.dumps(safety, ensure_ascii=False)),
        check("自动交易" in safety and safety.get("自动交易") is False, "未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文正式生成器影子分支接入预演验收",
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
    latest_json = OUT_DIR / "微信短文正式生成器影子分支接入预演验收_最新.json"
    latest_md = OUT_DIR / "微信短文正式生成器影子分支接入预演验收_最新.md"
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
