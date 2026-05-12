# -*- coding: utf-8 -*-
"""
名称：验证微信短文正式生成器正式成交额口径对照包.py
作用：验收230正式生成器正式成交额口径对照包是否完整、安全、未改正式入口。
安全边界：只读230对照包和入口快照；只写验收报告；不改入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "230微信短文正式生成器正式成交额口径对照包"
REPORT_JSON = OUT_DIR / "微信短文正式生成器正式成交额口径对照包_最新.json"
REPORT_MD = OUT_DIR / "微信短文正式生成器正式成交额口径对照包_最新.md"


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
        "# 微信短文正式生成器正式成交额口径对照包验收",
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
    compare = data.get("对照结果", {})
    safety = data.get("安全边界", {})
    formal_text = str(data.get("正式成交额口径影子短文", ""))
    snapshots = data.get("正式入口快照", []) or []
    snapshot_ok = True
    notes = []
    for item in snapshots:
        path = Path(item.get("路径", ""))
        ok = item.get("存在") is True and sha256(path) == item.get("sha256")
        snapshot_ok = snapshot_ok and ok
        notes.append(f"{path.name}:{'ok' if ok else 'changed'}")
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "230对照包 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "微信短文正式生成器正式成交额口径对照包", "报告名称正确", str(data.get("名称"))),
        check(compare.get("222验收通过") is True and compare.get("229验收通过") is True, "222/229上游验收通过", json.dumps(compare, ensure_ascii=False)),
        check(compare.get("222当前v21已移除估算降级") is True, "222当前v21已移除估算降级", json.dumps(compare, ensure_ascii=False)),
        check(compare.get("229正式口径版移除估算降级") is True, "229正式口径版移除估算降级", json.dumps(compare, ensure_ascii=False)),
        check(compare.get("222当前v21使用正式阈值") is True, "222当前v21使用正式阈值", json.dumps(compare, ensure_ascii=False)),
        check(compare.get("229正式口径版使用阈值") is True and "250.85亿元" in formal_text and "301.02亿元" in formal_text, "229正式口径版使用正式阈值", formal_text),
        check(all(compare.get("正式口径版关键字段命中", {}).values()), "正式口径版关键字段完整", json.dumps(compare.get("正式口径版关键字段命中", {}), ensure_ascii=False)),
        check(not any(compare.get("正式口径版禁用交易词命中", {}).values()), "正式口径版未命中交易动作词", json.dumps(compare.get("正式口径版禁用交易词命中", {}), ensure_ascii=False)),
        check(compare.get("建议默认切换正式入口") is False and compare.get("建议仅实现默认关闭dry_run双写") is True, "不建议默认切换正式入口", json.dumps(compare, ensure_ascii=False)),
        check(len(snapshots) == 3 and snapshot_ok, "正式入口文件哈希未变化", ";".join(notes)),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文正式生成器正式成交额口径对照包验收",
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
    latest_json = OUT_DIR / "微信短文正式生成器正式成交额口径对照包验收_最新.json"
    latest_md = OUT_DIR / "微信短文正式生成器正式成交额口径对照包验收_最新.md"
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
