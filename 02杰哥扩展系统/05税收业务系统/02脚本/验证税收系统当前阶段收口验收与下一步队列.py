# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "21当前阶段收口"
PREVIEW_JSON = OUT_DIR / "税收系统当前阶段收口验收与下一步队列_最新.json"
PREVIEW_MD = OUT_DIR / "税收系统当前阶段收口验收与下一步队列_最新.md"
REPORT_JSON = OUT_DIR / "税收系统当前阶段收口验收与下一步队列验收_最新.json"
REPORT_MD = OUT_DIR / "税收系统当前阶段收口验收与下一步队列验收_最新.md"

REQUIRED_REPORT_KEYWORDS = [
    "智能政策下载管道",
    "研发费用加计扣除政策链补齐预演",
    "研发费用加计扣除核心正式依据时效补齐预演",
    "研发费用核心正式依据时效补齐准备包",
    "研发费用后续比例延续政策本地证据卡补齐准备",
    "研发费用加计扣除专项人工复核清单",
    "政策证据底座字段补齐预演复核",
    "政策证据底座字段缺口补强预演",
    "涉税业务分析契约影子样例",
    "涉税业务分析契约影子样例复核",
    "研发费用业务事实采集模板",
    "研发费用分析准备度门禁",
    "税收企业微信公共组件对齐核实",
    "税收企业微信正式入口全链路预检",
    "税收企业微信入口配置一致性巡检",
    "税收企业微信dry-run阶段收口索引",
    "税收企业微信脱敏提问样例扩展包",
    "税收企业微信脱敏样例批量入队影子流转",
    "税收企业微信批量分析契约输入包",
    "税收企业微信待复核草案骨架批量预演",
    "税收企业微信待复核分析摘要批量预演",
    "税收企业微信待复核摘要批量消息合规审查",
    "税收企业微信人工复核阅读包批量预演",
    "税收企业微信人工复核回执空白模板批量预演",
    "税收企业微信复核回执到草案状态回写预演",
    "税收企业微信人工复核填写规范与状态机规则",
    "税收企业微信人工复核回执填报校验器预演",
    "税收企业微信人工复核状态机反事实演练",
    "税收企业微信人工复核校验失败整改清单",
    "税收企业微信待复核分析草案出入口状态索引",
    "税收企业微信人工复核整改后再校验样例模板",
    "税收企业微信待复核分析草案出入口索引反事实校验",
    "税收企业微信人工复核样例敏感信息复扫报告",
    "税收企业微信人工复核链路阶段收口索引",
    "税收企业微信人工复核链路一键本地预检",
    "税收企业微信人工复核链路阶段总回传记录",
    "税收企业微信人工复核链路持续巡检规则",
    "税收企业微信人工复核链路持续巡检样例演练",
    "税收企业微信人工复核链路巡检失败整改模板",
    "税收企业微信人工复核链路巡检整改后再校验清单",
    "税收企业微信人工复核链路巡检整改闭环阶段收口索引",
    "税收企业微信人工复核链路巡检整改闭环阶段总回传记录",
    "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明",
]
COMPLETED_QUEUE_KEYWORDS = [
    "税收政策证据底座字段缺口补强预演",
    "税收研发费用加计扣除核心正式依据时效补齐",
    "税收研发费用加计扣除后续比例延续政策本地证据卡补齐准备",
    "涉税业务分析契约影子样例",
    "税收企业微信人工复核回执填报校验器预演",
    "税收企业微信人工复核状态机反事实演练",
    "税收企业微信人工复核校验失败整改清单",
    "税收企业微信待复核分析草案出入口状态索引",
    "税收企业微信人工复核整改后再校验样例模板",
    "税收企业微信待复核分析草案出入口索引反事实校验",
    "税收企业微信人工复核样例敏感信息复扫报告",
    "税收企业微信人工复核链路阶段收口索引",
    "税收企业微信人工复核链路一键本地预检",
    "税收企业微信人工复核链路阶段总回传记录",
    "税收企业微信人工复核链路持续巡检规则",
    "税收企业微信人工复核链路持续巡检样例演练",
    "税收企业微信人工复核链路巡检失败整改模板",
    "税收企业微信人工复核链路巡检整改后再校验清单",
    "税收企业微信人工复核链路巡检整改闭环阶段收口索引",
    "税收企业微信人工复核链路巡检整改闭环阶段总回传记录",
    "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明",
]
REQUIRED_QUEUE_KEYWORDS = [
    "税收企业微信正式入口dry-run",
    "税收企业微信人工复核链路巡检整改闭环一键本地预检",
]
STOP_KEYWORDS = ["正式文档解析器", "真实发送凭据接入", "RAG正式问答链路"]
SAFETY_FALSE_KEYS = [
    "是否触发n8n",
    "是否企业微信真实发送",
    "是否写向量库",
    "是否调用模型推理",
    "是否生成正式税务结论",
    "是否新增端口",
    "是否重启服务",
    "是否影响股票系统",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def value_by_keywords(data: dict[str, Any], keywords: list[str], default: Any = None) -> Any:
    for key, value in data.items():
        if any(keyword in str(key) for keyword in keywords):
            return value
    return default


def report_name(item: dict[str, Any]) -> str:
    return str(value_by_keywords(item, ["名称", "鍚嶇О"], ""))


def report_exists(item: dict[str, Any]) -> bool:
    value = value_by_keywords(item, ["是否存在", "瀛樺湪"], False)
    return value is True


def report_passed(item: dict[str, Any]) -> bool:
    value = value_by_keywords(item, ["是否通过", "閫氳繃"], False)
    return value is True


def queue_item_name(item: dict[str, Any]) -> str:
    return str(value_by_keywords(item, ["事项", "浜嬮」"], ""))


def queue_priority(item: dict[str, Any]) -> str:
    return str(value_by_keywords(item, ["优先级", "浼樺厛绾"], ""))


def queue_auto(item: dict[str, Any]) -> Any:
    return value_by_keywords(item, ["是否可自动推进", "鍙嚜鍔ㄦ帹杩"], None)


def contains_any(items: list[Any], keyword: str) -> bool:
    return any(keyword in json.dumps(item, ensure_ascii=False) for item in items)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON)
    reports = value_by_keywords(preview, ["验收报告状态", "楠屾敹鎶ュ憡鐘"], [])
    queue = value_by_keywords(preview, ["下一步队列", "涓嬩竴姝ラ槦鍒"], [])
    blockers = value_by_keywords(preview, ["当前阻断", "褰撳墠闃绘柇"], [])
    safety = value_by_keywords(preview, ["安全边界", "瀹夊叏杈圭晫"], {})

    checks = [
        check("收口JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("收口Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("验收报告数量不少于72", len(reports) >= 72, len(reports)),
        check("所有验收报告存在", all(report_exists(item) for item in reports), [report_name(item) for item in reports if not report_exists(item)]),
        check("所有验收报告通过", all(report_passed(item) for item in reports), [report_name(item) for item in reports if not report_passed(item)]),
    ]

    for keyword in REQUIRED_REPORT_KEYWORDS:
        checks.append(check(f"当前报告包含：{keyword}", contains_any(reports, keyword), keyword))

    for keyword in COMPLETED_QUEUE_KEYWORDS:
        checks.append(check(f"下一步队列不再包含已完成项：{keyword}", not contains_any(queue, keyword), keyword))

    for keyword in REQUIRED_QUEUE_KEYWORDS:
        checks.append(check(f"下一步队列保留可自动推进项：{keyword}", contains_any(queue, keyword), keyword))

    checks.append(check("STOP事项均不可自动推进", all(queue_auto(item) is False for item in queue if queue_priority(item) == "STOP"), [item for item in queue if queue_priority(item) == "STOP"]))
    for keyword in STOP_KEYWORDS:
        checks.append(check(f"STOP队列包含：{keyword}", contains_any(queue, keyword), keyword))

    checks.append(check("阻断项包含RAG和企业微信真实发送", contains_any(blockers, "RAG") and contains_any(blockers, "真实发送"), blockers))
    checks.append(check("阻断项包含正式税务结论边界", contains_any(blockers, "正式税务结论"), blockers))
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in SAFETY_FALSE_KEYS), safety))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收系统当前阶段收口验收与下一步队列验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收系统当前阶段收口验收与下一步队列验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
