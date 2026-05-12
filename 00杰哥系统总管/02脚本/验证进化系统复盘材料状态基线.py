# -*- coding: utf-8 -*-
"""
名称：验证进化系统复盘材料状态基线.py
作用：验收进化系统复盘材料状态基线是否完整，并确认候选经验未自动固化为正式规则。
触发方式：python 验证进化系统复盘材料状态基线.py
安全边界：只读状态基线报告；只写验收报告；不生成正式经验卡片；不固化规则；不触发n8n；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "进化系统复盘材料状态基线_最新.json"
REPORT_MD = OUT_DIR / "进化系统复盘材料状态基线_最新.md"


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
    report = load_json(REPORT_JSON)
    md = load_text(REPORT_MD)
    text = json.dumps(report, ensure_ascii=False) + "\n" + md
    summary = report.get("汇总", {})
    runs = report.get("脚本执行", [])
    safety = report.get("安全边界", {})
    refs = report.get("引用产物", {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "基线 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "基线结论通过", report.get("结论", "")),
        check(len(runs) >= 3 and all(item.get("退出码") == 0 for item in runs), "三个进化材料脚本全部通过", str(len(runs))),
        check(summary.get("进化系统状态") == "healthy", "进化系统状态 healthy", json.dumps(summary, ensure_ascii=False)),
        check(int(summary.get("经验卡片数量", 0) or 0) >= 1, "复盘报告包含经验卡片", str(summary.get("经验卡片数量"))),
        check(int(summary.get("方法资产候选数量", 0) or 0) >= 1, "复盘报告包含方法资产候选", str(summary.get("方法资产候选数量"))),
        check(int(summary.get("巡检候选数量", 0) or 0) >= 5, "巡检经验候选数量充足", str(summary.get("巡检候选数量"))),
        check(summary.get("正式经验卡片数量") == 0, "未生成正式经验卡片", str(summary.get("正式经验卡片数量"))),
        check(summary.get("自动固化规则数量") == 0, "未自动固化规则", str(summary.get("自动固化规则数量"))),
        check(summary.get("删除样本数量") == 0 and summary.get("写旧系统数量") == 0, "未删除样本且未写旧系统", json.dumps(summary, ensure_ascii=False)),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check("不写总纲规则" in text and "不自动固化规则" in text and "不触发n8n" in text, "文本记录关键禁止动作", ""),
        check(all(Path(str(path)).exists() for path in refs.values()), "引用产物均存在", json.dumps(refs, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    validation = {
        "名称": "进化系统复盘材料状态基线验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "生成正式经验卡片": False,
            "自动固化规则": False,
            "写总纲规则": False,
            "触发n8n": False,
            "发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "进化系统复盘材料状态基线验收_最新.json"
    latest_md = OUT_DIR / "进化系统复盘材料状态基线验收_最新.md"
    lines = [
        "# 进化系统复盘材料状态基线验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, validation)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": validation["结论"],
        "通过数量": validation["通过数量"],
        "失败数量": validation["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
