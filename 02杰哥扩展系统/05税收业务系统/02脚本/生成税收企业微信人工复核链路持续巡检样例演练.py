# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路持续巡检样例演练"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路持续巡检样例演练.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路持续巡检样例演练.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练_最新.md"
RULE_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    if case.get("验收报告缺失"):
        findings.append("链路漂移：验收报告缺失")
    if case.get("验收失败数量", 0) > 0:
        findings.append("链路漂移：验收失败")
    if any(value is True for value in case.get("安全边界", {}).values()):
        findings.append("红线漂移：安全边界出现True")
    if case.get("出现正式结论口径"):
        findings.append("高风险漂移：出现正式税务结论口径")
    if case.get("尝试修改总管或公共配置"):
        findings.append("越权漂移：尝试修改总管或公共配置")
    if case.get("已完成项重新进入队列且无说明"):
        findings.append("施工队列漂移：已完成项回流")
    return {
        "样例ID": case["样例ID"],
        "样例名称": case["样例名称"],
        "预期结论": case["预期结论"],
        "识别结果": "通过" if not findings else "阻断",
        "命中事项": findings,
        "是否符合预期": (case["预期结论"] == "通过" and not findings) or (case["预期结论"] == "阻断" and bool(findings)),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rules = load_json(RULE_JSON)

    cases = [
        {
            "样例ID": "patrol_case_001",
            "样例名称": "健康基线样例",
            "预期结论": "通过",
            "验收报告缺失": False,
            "验收失败数量": 0,
            "安全边界": {"是否企业微信真实发送": False, "是否触发n8n": False, "是否写正式库": False},
            "出现正式结论口径": False,
            "尝试修改总管或公共配置": False,
            "已完成项重新进入队列且无说明": False,
        },
        {
            "样例ID": "patrol_case_002",
            "样例名称": "验收报告缺失样例",
            "预期结论": "阻断",
            "验收报告缺失": True,
            "验收失败数量": 0,
            "安全边界": {"是否企业微信真实发送": False, "是否触发n8n": False, "是否写正式库": False},
            "出现正式结论口径": False,
            "尝试修改总管或公共配置": False,
            "已完成项重新进入队列且无说明": False,
        },
        {
            "样例ID": "patrol_case_003",
            "样例名称": "真实发送红线漂移样例",
            "预期结论": "阻断",
            "验收报告缺失": False,
            "验收失败数量": 0,
            "安全边界": {"是否企业微信真实发送": True, "是否触发n8n": False, "是否写正式库": False},
            "出现正式结论口径": False,
            "尝试修改总管或公共配置": False,
            "已完成项重新进入队列且无说明": False,
        },
        {
            "样例ID": "patrol_case_004",
            "样例名称": "正式税务结论口径样例",
            "预期结论": "阻断",
            "验收报告缺失": False,
            "验收失败数量": 0,
            "安全边界": {"是否企业微信真实发送": False, "是否触发n8n": False, "是否写正式库": False},
            "出现正式结论口径": True,
            "尝试修改总管或公共配置": False,
            "已完成项重新进入队列且无说明": False,
        },
        {
            "样例ID": "patrol_case_005",
            "样例名称": "总管越权修改样例",
            "预期结论": "阻断",
            "验收报告缺失": False,
            "验收失败数量": 0,
            "安全边界": {"是否企业微信真实发送": False, "是否触发n8n": False, "是否写正式库": False},
            "出现正式结论口径": False,
            "尝试修改总管或公共配置": True,
            "已完成项重新进入队列且无说明": False,
        },
        {
            "样例ID": "patrol_case_006",
            "样例名称": "已完成项回流队列样例",
            "预期结论": "阻断",
            "验收报告缺失": False,
            "验收失败数量": 0,
            "安全边界": {"是否企业微信真实发送": False, "是否触发n8n": False, "是否写正式库": False},
            "出现正式结论口径": False,
            "尝试修改总管或公共配置": False,
            "已完成项重新进入队列且无说明": True,
        },
    ]
    results = [evaluate_case(case) for case in cases]
    passed = sum(1 for item in results if item["是否符合预期"])
    failed = len(results) - passed

    report = {
        "名称": "税收企业微信人工复核链路持续巡检样例演练",
        "生成时间": now,
        "资产身份": "税务线本地样例演练，不创建自动化任务，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "引用规则": str(RULE_JSON),
        "规则存在": bool(rules),
        "样例数量": len(cases),
        "符合预期数量": passed,
        "不符合预期数量": failed,
        "样例结果": results,
        "下一步建议": [
            "生成人工复核链路巡检失败整改模板，用于承接演练中识别出的缺失、失败、红线漂移和越权漂移。",
        ],
        "安全边界": {
            "是否创建自动化任务": False,
            "是否启动或重启服务": False,
            "是否新增或修改端口": False,
            "是否触发n8n": False,
            "是否读取或保存企业微信凭据": False,
            "是否企业微信真实发送": False,
            "是否修改公共企业微信配置": False,
            "是否修改总管文件": False,
            "是否写正式库": False,
            "是否生成正式税务结论": False,
            "是否删除或移动旧资产": False,
        },
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路持续巡检样例演练",
        "",
        f"- 生成时间：{now}",
        f"- 样例数量：{len(cases)}",
        f"- 符合预期数量：{passed}",
        f"- 不符合预期数量：{failed}",
        "- 资产身份：税务线本地样例演练，不创建自动化任务，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "",
        "## 样例结果",
        "",
    ]
    for item in results:
        lines.append(f"### {item['样例ID']} {item['样例名称']}")
        lines.append(f"- 预期结论：{item['预期结论']}")
        lines.append(f"- 识别结果：{item['识别结果']}")
        lines.append(f"- 是否符合预期：{item['是否符合预期']}")
        lines.append(f"- 命中事项：{'; '.join(item['命中事项']) if item['命中事项'] else '无'}")
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步建议", ""])
    for item in report["下一步建议"]:
        lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    copy_latest(OUT_JSON, LATEST_JSON)
    copy_latest(OUT_MD, LATEST_MD)
    print(json.dumps({"状态": "完成", "符合预期数量": passed, "不符合预期数量": failed, "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
