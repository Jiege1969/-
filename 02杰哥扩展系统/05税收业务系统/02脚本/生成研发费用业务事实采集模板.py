# -*- coding: utf-8 -*-
"""
名称：生成研发费用业务事实采集模板.py
作用：生成研发费用加计扣除分析前的业务事实采集模板，供人工补充事实。
安全边界：只生成空白采集模板；不联网、不下载、不测算金额、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "30研发费用业务事实采集模板"
OUT_JSON = OUT_DIR / "研发费用业务事实采集模板_最新.json"
OUT_MD = OUT_DIR / "研发费用业务事实采集模板_最新.md"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def field(name: str, category: str, required: bool, reason: str, value: str = "") -> dict[str, Any]:
    return {
        "字段": name,
        "类别": category,
        "必填": required,
        "填写值": value,
        "采集目的": reason,
        "人工核验状态": "待填写",
    }


def build_template() -> dict[str, Any]:
    fields = [
        field("企业名称", "主体信息", True, "确认纳税主体。"),
        field("纳税人识别号", "主体信息", True, "与申报主体、辅助账、留存资料匹配。"),
        field("纳税人类型", "主体信息", True, "确认是否为居民企业、是否查账征收。"),
        field("适用地区", "主体信息", True, "识别是否需要地方口径或主管税务机关复核。"),
        field("所属年度", "期间信息", True, "匹配政策适用期间和申报期间。"),
        field("申报场景", "期间信息", True, "区分预缴、汇算清缴、追溯享受或更正申报。"),
        field("研发项目名称", "项目事实", True, "建立项目级判断对象。"),
        field("项目研发目标", "项目事实", True, "核验是否具有明确研发目标。"),
        field("拟突破核心技术", "项目事实", True, "核验技术不确定性和创新性。"),
        field("研发组织形式", "项目事实", True, "核验系统组织形式和研发团队情况。"),
        field("研发成果或阶段成果", "项目事实", False, "辅助判断项目结果和资料闭环。"),
        field("是否存在专家鉴定", "项目事实", False, "有争议或政策要求时作为人工复核依据。"),
        field("研发费用总额", "费用信息", True, "采集金额口径，但本模板不测算税额。"),
        field("人员人工费用", "费用信息", False, "匹配研发费用归集范围。"),
        field("直接投入费用", "费用信息", False, "匹配研发费用归集范围。"),
        field("折旧费用", "费用信息", False, "匹配研发费用归集范围。"),
        field("无形资产摊销", "费用信息", False, "匹配研发费用归集范围。"),
        field("其他相关费用", "费用信息", False, "核验限额和归集口径。"),
        field("委托研发情况", "特殊事项", False, "核验委托研发、境外委托和关联方资料。"),
        field("合作或集中研发情况", "特殊事项", False, "核验费用分摊和项目归属。"),
        field("是否涉及不适用行业", "排除事项", True, "核验行业限制。"),
        field("是否涉及不适用活动", "排除事项", True, "核验常规升级、直接应用、简单改变等排除情形。"),
        field("研发支出辅助账", "资料清单", True, "确认留存备查资料。"),
        field("项目立项资料", "资料清单", True, "确认研发活动证据链。"),
        field("费用归集明细", "资料清单", True, "确认费用和生产经营费用是否分别核算。"),
        field("留存备查资料目录", "资料清单", True, "支撑后续人工复核。"),
        field("主管税务机关沟通记录", "资料清单", False, "识别地方口径或争议处理。"),
    ]
    return {
        "名称": "研发费用业务事实采集模板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模板状态": "draft",
        "用途": "供研发费用加计扣除涉税业务分析前人工补充事实，不形成正式税务结论。",
        "字段数量": len(fields),
        "必填字段数量": sum(1 for item in fields if item["必填"]),
        "字段": fields,
        "放行规则": [
            "必填字段未补齐时，不得生成适用判断。",
            "政策链仍为pending_review时，只能生成待复核分析草案。",
            "金额字段只采集事实口径，不自动测算可扣除金额或税额影响。",
            "项目创新性、技术不确定性和费用归集准确性必须人工复核。",
        ],
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否测算金额": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 研发费用业务事实采集模板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 模板状态：{report['模板状态']}",
        f"- 字段数量：{report['字段数量']}",
        f"- 必填字段数量：{report['必填字段数量']}",
        f"- 用途：{report['用途']}",
        "",
        "## 字段",
        "",
    ]
    for item in report.get("字段", []):
        required = "必填" if item["必填"] else "选填"
        lines.append(f"- [{required}] {item['类别']} / {item['字段']}：{item['采集目的']}")
    lines.extend(["", "## 放行规则", ""])
    for item in report.get("放行规则", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_template()
    write_json(OUT_JSON, report)
    write_text(OUT_MD, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "字段数量": report["字段数量"],
        "必填字段数量": report["必填字段数量"],
        "输出": str(OUT_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
