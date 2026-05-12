# -*- coding: utf-8 -*-
"""
名称：验证总管小流量执行器只读门禁复核.py
作用：验收总管小流量执行器只读门禁复核报告是否完整，确认未触发执行器和真实动作。
触发方式：python 验证总管小流量执行器只读门禁复核.py
安全边界：只读门禁复核报告；只写验收报告；不触发执行器；不触发n8n；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "总管小流量执行器只读门禁复核_最新.json"
REPORT_MD = OUT_DIR / "总管小流量执行器只读门禁复核_最新.md"


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
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "复核 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "复核结论通过", report.get("结论", "")),
        check(len(runs) >= 4 and all(item.get("退出码") == 0 for item in runs), "四个只读门禁脚本全部通过", str(len(runs))),
        check(summary.get("执行器数量") == 3 and summary.get("就绪但冻结数量") == 3, "首批执行器均就绪但冻结", json.dumps(summary, ensure_ascii=False)),
        check(summary.get("真实动作数量") == 0, "真实动作数量为零", str(summary.get("真实动作数量"))),
        check(summary.get("执行批次数量", 0) >= 3, "小流量只读执行批次存在", str(summary.get("执行批次数量"))),
        check(summary.get("执行前快照失败数") == 0, "执行前快照无失败", str(summary.get("执行前快照失败数"))),
        check(summary.get("后观测项目数量", 0) >= 6, "执行后观测模板完整", str(summary.get("后观测项目数量"))),
        check(summary.get("计划开关全部关闭") is True, "只读方案和前快照开关全部关闭", ""),
        check(summary.get("后观测默认状态全部关闭") is True, "后观测默认状态全部关闭", ""),
        check(all(value is False for value in safety.values()), "安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check("不触发执行器" in text and "不触发n8n" in text and "不自动交易" in text, "文本记录关键禁止动作", ""),
        check(all(Path(str(path)).exists() for path in refs.values()), "引用产物均存在", json.dumps(refs, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    validation = {
        "名称": "总管小流量执行器只读门禁复核验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "触发执行器": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "总管小流量执行器只读门禁复核验收_最新.json"
    latest_md = OUT_DIR / "总管小流量执行器只读门禁复核验收_最新.md"
    lines = [
        "# 总管小流量执行器只读门禁复核验收",
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
