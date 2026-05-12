# -*- coding: utf-8 -*-
"""
名称：验证微信短文低风险统一入口影子验收.py
作用：验收225低风险统一入口影子验收包是否完成入口源码快照、dry_run方案和正式替换阻断。
安全边界：只读225验收包和入口源码；只写验收报告；不执行入口、不改入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "225低风险统一入口影子验收"
REPORT_JSON = OUT_DIR / "微信短文低风险统一入口影子验收_最新.json"
REPORT_MD = OUT_DIR / "微信短文低风险统一入口影子验收_最新.md"


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
        "# 微信短文低风险统一入口影子验收报告",
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
    gates = data.get("上游门禁", {})
    scans = data.get("入口源码扫描", []) or []
    snapshots = data.get("入口快照", []) or []
    safety = data.get("安全边界", {})
    snapshot_ok = True
    snapshot_notes = []
    for item in snapshots:
        path = Path(item.get("路径", ""))
        current_hash = sha256(path)
        ok = item.get("存在") is True and current_hash == item.get("sha256")
        snapshot_ok = snapshot_ok and ok
        snapshot_notes.append(f"{path.name}:{'ok' if ok else 'changed'}")

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "225验收包 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("名称") == "微信短文低风险统一入口影子验收", "报告名称正确", str(data.get("名称"))),
        check(gates.get("224验收通过") is True, "224上游验收通过", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("v21短文结构通过") is True and gates.get("v21禁用交易动作词通过") is True, "v21结构和安全词门禁通过", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("历史成交额可解除估算降级") is False, "历史成交额未正式化仍阻断", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("允许正式可控开关") is False, "正式可控开关未放行", json.dumps(gates, ensure_ascii=False)),
        check(gates.get("允许dry_run影子双写方案设计") is True, "允许dry_run影子双写方案设计", json.dumps(gates, ensure_ascii=False)),
        check(len(scans) == 3 and all(item.get("存在") for item in scans), "三个入口源码扫描完整", json.dumps(scans, ensure_ascii=False)[:500]),
        check("默认行为保持不变" in text and "--shadow-v21-dry-run" in text, "影子方案要求默认关闭显式参数", ""),
        check("桥接入口" in text and "不直接引入 v21 模板" in text, "桥接和助手入口不变更", ""),
        check("正式短回复模板替换继续阻断" in text, "正式模板替换被阻断", ""),
        check(len(snapshots) == 3 and snapshot_ok, "入口文件哈希未变化", ";".join(snapshot_notes)),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("执行正式短回复生成器") is False, "未执行正式短回复生成器", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("发送企业微信") is False and safety.get("触发n8n") is False, "未发送企业微信且未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False, "未调用券商接口且未自动交易", json.dumps(safety, ensure_ascii=False)),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文低风险统一入口影子验收报告",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "执行正式短回复生成器": False,
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
    latest_json = OUT_DIR / "微信短文低风险统一入口影子验收报告_最新.json"
    latest_md = OUT_DIR / "微信短文低风险统一入口影子验收报告_最新.md"
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
