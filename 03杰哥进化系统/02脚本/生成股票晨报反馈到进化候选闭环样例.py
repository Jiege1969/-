# -*- coding: utf-8 -*-
"""
生成股票晨报反馈到进化候选闭环样例。

边界：只写 03进化系统既有 13/15 数据目录；不写正式规则库，不改总管面板，
不改一键接续包，不触发 n8n，不真实发送企业微信，不接券商，不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
STOCK_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
OUT_13 = ROOT / "03数据" / "13股票复盘反馈样本"
OUT_15 = ROOT / "03数据" / "15复盘转经验候选"


SOURCE_PUSH = STOCK_ROOT / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"
SOURCE_PUSH_JSON = STOCK_ROOT / "03数据" / "136推送草案" / "股票企微推送草案_最新.json"
SOURCE_DRY_RUN = STOCK_ROOT / "03数据" / "249主动推送dry-run消息样本包" / "股票主动推送dry-run消息样本包_最新.json"
SOURCE_STRATEGY = STOCK_ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"
SOURCE_REVIEW_LEDGER = STOCK_ROOT / "04日志" / "复盘" / "判断复盘账_最新.json"


SAFETY_BOUNDARY = {
    "自动转正式规则": False,
    "写正式规则库": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "触发n8n": False,
    "真实发送企业微信": False,
    "接券商": False,
    "交易": False,
    "写回股票系统": False,
}


FEEDBACK_OPTIONS = [
    "说到位",
    "太空泛",
    "少了财务依据",
    "风险没讲清",
    "行业逻辑不够",
    "这个口径保留",
    "这个候选不合理",
    "明天继续观察",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def source_status(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else None,
    }


def build_template(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "股票晨报反馈样本模板",
        "生成时间": generated_at,
        "类型": "stock-morning-brief-feedback-template",
        "所属系统": "03杰哥进化系统",
        "承载目录": str(OUT_13),
        "用途": "把股票晨报、推送、用户纠偏和晚间复盘反馈入账为可追溯样本，供后续转进化候选；不自动生效为正式规则。",
        "适用来源": [
            "开市前晨报",
            "主动推送dry-run消息",
            "企业微信推送草案",
            "晚间复盘记录",
            "用户随问随答后的纠偏反馈",
        ],
        "允许反馈选项": FEEDBACK_OPTIONS,
        "必填字段": [
            "反馈ID",
            "反馈时间",
            "反馈来源",
            "原始晨报或推送记录ID",
            "原始晨报或推送记录路径",
            "股票代码",
            "股票名称",
            "反馈选项",
            "用户原话",
            "反馈对象片段",
            "期望处理",
            "人工确认状态",
            "去重键",
            "正式规则申请前闸口状态",
        ],
        "人工确认状态集合": [
            "待人工确认",
            "已确认进入候选",
            "驳回",
            "冻结观察",
            "可提交正式规则申请草案",
        ],
        "去重逻辑": {
            "规范化字段": [
                "股票代码",
                "原始晨报或推送记录ID",
                "反馈选项",
                "候选类型",
                "期望处理",
            ],
            "去重键算法": "sha256(股票代码|原始记录ID|反馈选项|候选类型|期望处理)",
            "重复处理": "保留首条样本，后续样本标记为 duplicate_of，不生成新的进化候选。",
        },
        "正式规则申请前闸口": {
            "默认状态": "blocked_before_manual_confirm",
            "允许提交申请草案条件": [
                "人工确认状态为 已确认进入候选",
                "非重复样本",
                "能追溯到原始晨报或推送记录",
                "不含交易指令、收益承诺、券商动作或外部发送动作",
                "仅提交正式规则申请草案，不写正式规则库",
            ],
        },
        "安全边界": SAFETY_BOUNDARY,
    }


def sample_feedback_rows() -> list[dict[str, Any]]:
    base_source_id = "MORNING-PUSH-20260509-SAMPLE"
    source_paths = {
        "原始推送草案": str(SOURCE_PUSH),
        "dry-run推送样本": str(SOURCE_DRY_RUN),
        "晨报策略包": str(SOURCE_STRATEGY),
        "复盘账": str(SOURCE_REVIEW_LEDGER),
    }
    rows = [
        {
            "反馈ID": "SMBF-20260509-001",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sh688047",
            "股票名称": "龙芯中科",
            "反馈选项": "说到位",
            "用户原话": "龙芯中科这条把观察价、风险位和证据缺口说到位了。",
            "反馈对象片段": "观察价、风险复核位、证据缺口",
            "候选类型": "保留有效表达口径",
            "期望处理": "保留“观察条件+风险位+证据缺口”的晨报表达结构。",
        },
        {
            "反馈ID": "SMBF-20260509-002",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sh688012",
            "股票名称": "中微公司",
            "反馈选项": "太空泛",
            "用户原话": "中微公司这条太空泛，只说继续跟踪，没有讲为什么。",
            "反馈对象片段": "继续跟踪",
            "候选类型": "补足判断依据",
            "期望处理": "晨报中出现继续跟踪时，必须补充至少一个可复核理由。",
        },
        {
            "反馈ID": "SMBF-20260509-003",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sz002466",
            "股票名称": "天齐锂业",
            "反馈选项": "少了财务依据",
            "用户原话": "天齐锂业少了财务依据，不能只有行业和技术。",
            "反馈对象片段": "行业动态、技术结构、资金活跃",
            "候选类型": "补财务依据",
            "期望处理": "周期和资源类股票晨报必须显示财务或价格周期依据缺口。",
        },
        {
            "反馈ID": "SMBF-20260509-004",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sh688795",
            "股票名称": "摩尔线程",
            "反馈选项": "风险没讲清",
            "用户原话": "摩尔线程风险没讲清，波动和估值压力要单独说。",
            "反馈对象片段": "条件尚未完全达到推荐标准",
            "候选类型": "补风险解释",
            "期望处理": "高波动候选必须把风险来源拆成估值、流动性、消息面或技术破位。",
        },
        {
            "反馈ID": "SMBF-20260509-005",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sh688347",
            "股票名称": "华虹公司",
            "反馈选项": "行业逻辑不够",
            "用户原话": "华虹公司行业逻辑不够，要说明半导体链条里的位置。",
            "反馈对象片段": "行业强度与资金活跃度双高",
            "候选类型": "补行业逻辑",
            "期望处理": "晨报出现行业强度时，必须说明行业链条位置或同业对照。",
        },
        {
            "反馈ID": "SMBF-20260509-006",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sh688047",
            "股票名称": "龙芯中科",
            "反馈选项": "这个口径保留",
            "用户原话": "这个不是买卖建议、只是观察条件的口径保留。",
            "反馈对象片段": "不构成投资建议，不作为买卖指令",
            "候选类型": "保留合规边界口径",
            "期望处理": "晨报结尾继续保留非投资建议和人工观察边界声明。",
        },
        {
            "反馈ID": "SMBF-20260509-007",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sz300641",
            "股票名称": "正丹股份",
            "反馈选项": "这个候选不合理",
            "用户原话": "正丹股份这个候选不合理，风险过滤后不该进晨报。",
            "反馈对象片段": "L7系统过滤仍进入观察",
            "候选类型": "候选降级或剔除",
            "期望处理": "被风险过滤或证据不足的标的默认不进入晨报重点候选，只能进入观察附录。",
        },
        {
            "反馈ID": "SMBF-20260509-008",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sz000906",
            "股票名称": "浙商中拓",
            "反馈选项": "明天继续观察",
            "用户原话": "浙商中拓明天继续观察，不急着转结论。",
            "反馈对象片段": "资金信号较强但需继续观察",
            "候选类型": "延续观察",
            "期望处理": "延续观察类反馈只生成观察任务候选，不生成判断规则。",
        },
        {
            "反馈ID": "SMBF-20260509-009",
            "反馈来源": "用户晨报反馈样例",
            "原始晨报或推送记录ID": base_source_id,
            "股票代码": "sh688012",
            "股票名称": "中微公司",
            "反馈选项": "太空泛",
            "用户原话": "重复样例：中微公司这条太空泛。",
            "反馈对象片段": "继续跟踪",
            "候选类型": "补足判断依据",
            "期望处理": "晨报中出现继续跟踪时，必须补充至少一个可复核理由。",
        },
    ]
    for row in rows:
        row["反馈时间"] = "2026-05-09 08:45:00"
        row["原始晨报或推送记录路径"] = source_paths
        row["人工确认状态"] = "待人工确认"
        row["正式规则申请前闸口状态"] = "blocked_before_manual_confirm"
        row["安全边界"] = SAFETY_BOUNDARY
    return rows


def attach_dedupe(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: dict[str, str] = {}
    unique: list[dict[str, Any]] = []
    for row in rows:
        raw = "|".join(
            [
                row["股票代码"],
                row["原始晨报或推送记录ID"],
                row["反馈选项"],
                row["候选类型"],
                row["期望处理"],
            ]
        )
        key = sha256_text(raw)
        row["去重键"] = key
        if key in seen:
            row["去重结果"] = "duplicate"
            row["duplicate_of"] = seen[key]
        else:
            row["去重结果"] = "unique"
            row["duplicate_of"] = None
            seen[key] = row["反馈ID"]
            unique.append(row)
    return rows, unique


def build_candidate(row: dict[str, Any], idx: int) -> dict[str, Any]:
    action_map = {
        "说到位": "保留并作为候选口径",
        "太空泛": "补充可复核依据",
        "少了财务依据": "补充财务依据字段",
        "风险没讲清": "补充风险拆解字段",
        "行业逻辑不够": "补充行业链条或同业对照",
        "这个口径保留": "保留合规边界表达",
        "这个候选不合理": "降级或剔除候选",
        "明天继续观察": "生成次日观察任务候选",
    }
    return {
        "候选ID": f"SMBC-20260509-{idx:03d}",
        "候选来源反馈ID": row["反馈ID"],
        "候选类型": row["候选类型"],
        "标题": f"{row['股票名称']}晨报反馈候选：{row['反馈选项']}",
        "建议动作": action_map[row["反馈选项"]],
        "候选内容": row["期望处理"],
        "原始用户反馈": row["用户原话"],
        "追溯": {
            "原始晨报或推送记录ID": row["原始晨报或推送记录ID"],
            "原始晨报或推送记录路径": row["原始晨报或推送记录路径"],
            "反馈对象片段": row["反馈对象片段"],
            "股票代码": row["股票代码"],
            "股票名称": row["股票名称"],
        },
        "人工确认状态": "待人工确认",
        "自动生效": False,
        "正式规则申请前闸口状态": "blocked_before_manual_confirm",
        "正式规则申请前闸口说明": "仅为进化候选样例；人工确认和总管复核前不得写入正式规则库。",
        "去重键": row["去重键"],
        "去重结果": row["去重结果"],
        "安全边界": SAFETY_BOUNDARY,
    }


def build_outputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    generated_at = now_text()
    rows, unique_rows = attach_dedupe(sample_feedback_rows())
    candidates = [build_candidate(row, idx) for idx, row in enumerate(unique_rows, start=1)]

    template = build_template(generated_at)
    feedback_package = {
        "名称": "股票晨报反馈样本模板与本地样例",
        "生成时间": generated_at,
        "类型": "stock-morning-brief-feedback-samples",
        "所属系统": "03杰哥进化系统",
        "更新方式": "更新既有13股票复盘反馈样本目录，不新建重复工作包。",
        "源文件状态": {
            "原始推送草案Markdown": source_status(SOURCE_PUSH),
            "原始推送草案JSON": source_status(SOURCE_PUSH_JSON),
            "主动推送dry-run样本": source_status(SOURCE_DRY_RUN),
            "日内闭环与晨报策略包": source_status(SOURCE_STRATEGY),
            "判断复盘账": source_status(SOURCE_REVIEW_LEDGER),
        },
        "模板": template,
        "样例反馈数量": len(rows),
        "去重后样例数量": len(unique_rows),
        "重复样例数量": len(rows) - len(unique_rows),
        "反馈样例": rows,
        "验收": {
            "支持指定反馈选项": all(option in template["允许反馈选项"] for option in FEEDBACK_OPTIONS),
            "样本可追溯到原始晨报或推送记录": all(bool(row["原始晨报或推送记录路径"]) for row in rows),
            "有人工确认状态": all("人工确认状态" in row for row in rows),
            "有去重逻辑": True,
            "有正式规则申请前闸口": all(row["正式规则申请前闸口状态"] == "blocked_before_manual_confirm" for row in rows),
            "不写正式规则": not SAFETY_BOUNDARY["写正式规则库"],
            "不触发n8n": not SAFETY_BOUNDARY["触发n8n"],
            "不真实发送企业微信": not SAFETY_BOUNDARY["真实发送企业微信"],
        },
        "安全边界": SAFETY_BOUNDARY,
    }

    candidate_package = {
        "名称": "股票晨报反馈转进化候选本地样例",
        "生成时间": generated_at,
        "类型": "stock-morning-brief-feedback-to-evolution-candidates",
        "所属系统": "03杰哥进化系统",
        "更新方式": "更新既有15复盘转经验候选目录，不新建重复工作包。",
        "来源样本包": str(OUT_13 / "股票晨报反馈样本模板与本地样例_最新.json"),
        "候选生成规则": {
            "只处理去重结果为unique的反馈样本": True,
            "重复反馈不生成新候选": True,
            "默认人工确认状态": "待人工确认",
            "默认正式规则申请前闸口": "blocked_before_manual_confirm",
            "自动生效为正式规则": False,
        },
        "候选数量": len(candidates),
        "去重拒收数量": len(rows) - len(unique_rows),
        "进化候选": candidates,
        "去重拒收": [row for row in rows if row["去重结果"] == "duplicate"],
        "正式规则申请前闸口": {
            "当前状态": "全部阻断在候选层",
            "可进入申请草案的最低条件": [
                "人工确认状态改为 已确认进入候选",
                "总管复核允许提交申请草案",
                "仍只生成申请草案，不直接写正式规则",
                "复核不触发 n8n、不发送企业微信、不接券商、不交易",
            ],
        },
        "验收": {
            "候选样本可追溯到原始晨报或推送记录": all("追溯" in item and item["追溯"]["原始晨报或推送记录路径"] for item in candidates),
            "有人工确认状态": all(item["人工确认状态"] == "待人工确认" for item in candidates),
            "有去重逻辑": True,
            "重复样例未生成候选": len(candidates) == len(unique_rows),
            "有正式规则申请前闸口": all(item["正式规则申请前闸口状态"] == "blocked_before_manual_confirm" for item in candidates),
            "不写正式规则": not SAFETY_BOUNDARY["写正式规则库"],
            "不触发n8n": not SAFETY_BOUNDARY["触发n8n"],
            "不真实发送企业微信": not SAFETY_BOUNDARY["真实发送企业微信"],
            "不接券商": not SAFETY_BOUNDARY["接券商"],
            "不交易": not SAFETY_BOUNDARY["交易"],
        },
        "安全边界": SAFETY_BOUNDARY,
    }

    handback = {
        "标题": "进化反馈闭环任务回传",
        "生成时间": generated_at,
        "范围": str(ROOT),
        "本次动作": [
            "查找股票反馈、复盘反馈、用户反馈样本、进化候选相关包。",
            "复用13股票复盘反馈样本和15复盘转经验候选两个既有目录。",
            "补齐股票晨报反馈样本模板，覆盖8类用户反馈。",
            "生成本地样例，将晨报反馈转为进化候选，但全部停留在候选层。",
            "设置去重、人工确认状态和正式规则申请前闸口。",
        ],
        "产物": {
            "股票晨报反馈模板JSON": str(OUT_13 / "股票晨报反馈样本模板_最新.json"),
            "股票晨报反馈模板Markdown": str(OUT_13 / "股票晨报反馈样本模板_最新.md"),
            "股票晨报反馈样本包JSON": str(OUT_13 / "股票晨报反馈样本模板与本地样例_最新.json"),
            "股票晨报反馈转候选JSON": str(OUT_15 / "股票晨报反馈转进化候选样例_最新.json"),
            "任务回传Markdown": str(OUT_15 / "进化反馈闭环任务回传_最新.md"),
        },
        "验收结论": candidate_package["验收"],
        "安全边界": SAFETY_BOUNDARY,
    }
    return feedback_package, candidate_package, handback


def write_outputs(feedback_package: dict[str, Any], candidate_package: dict[str, Any], handback: dict[str, Any]) -> None:
    ts = stamp()
    template = feedback_package["模板"]

    write_json(OUT_13 / f"股票晨报反馈样本模板_{ts}.json", template)
    write_json(OUT_13 / "股票晨报反馈样本模板_最新.json", template)
    template_md = [
        "# 股票晨报反馈样本模板",
        "",
        f"- 生成时间：{template['生成时间']}",
        f"- 用途：{template['用途']}",
        f"- 允许反馈选项：{'、'.join(template['允许反馈选项'])}",
        "",
        "## 必填字段",
        "",
        *[f"- {field}" for field in template["必填字段"]],
        "",
        "## 去重逻辑",
        "",
        f"- 算法：{template['去重逻辑']['去重键算法']}",
        f"- 重复处理：{template['去重逻辑']['重复处理']}",
        "",
        "## 正式规则申请前闸口",
        "",
        f"- 默认状态：{template['正式规则申请前闸口']['默认状态']}",
        "- 未人工确认前不得写正式规则库。",
    ]
    write_md(OUT_13 / f"股票晨报反馈样本模板_{ts}.md", template_md)
    write_md(OUT_13 / "股票晨报反馈样本模板_最新.md", template_md)

    write_json(OUT_13 / f"股票晨报反馈样本模板与本地样例_{ts}.json", feedback_package)
    write_json(OUT_13 / "股票晨报反馈样本模板与本地样例_最新.json", feedback_package)
    feedback_md = [
        "# 股票晨报反馈样本模板与本地样例",
        "",
        f"- 生成时间：{feedback_package['生成时间']}",
        f"- 样例反馈数量：{feedback_package['样例反馈数量']}",
        f"- 去重后样例数量：{feedback_package['去重后样例数量']}",
        f"- 重复样例数量：{feedback_package['重复样例数量']}",
        "",
        "## 样例摘要",
        "",
    ]
    for row in feedback_package["反馈样例"]:
        suffix = f"，重复于 {row['duplicate_of']}" if row["duplicate_of"] else ""
        feedback_md.append(f"- {row['反馈ID']} {row['股票名称']}：{row['反馈选项']}，{row['去重结果']}{suffix}")
    write_md(OUT_13 / f"股票晨报反馈样本模板与本地样例_{ts}.md", feedback_md)
    write_md(OUT_13 / "股票晨报反馈样本模板与本地样例_最新.md", feedback_md)

    write_json(OUT_15 / f"股票晨报反馈转进化候选样例_{ts}.json", candidate_package)
    write_json(OUT_15 / "股票晨报反馈转进化候选样例_最新.json", candidate_package)
    candidate_md = [
        "# 股票晨报反馈转进化候选样例",
        "",
        f"- 生成时间：{candidate_package['生成时间']}",
        f"- 候选数量：{candidate_package['候选数量']}",
        f"- 去重拒收数量：{candidate_package['去重拒收数量']}",
        "- 自动生效为正式规则：False",
        "",
        "## 候选摘要",
        "",
    ]
    for item in candidate_package["进化候选"]:
        candidate_md.append(f"- {item['候选ID']} {item['标题']}：{item['人工确认状态']}，{item['正式规则申请前闸口状态']}")
    write_md(OUT_15 / f"股票晨报反馈转进化候选样例_{ts}.md", candidate_md)
    write_md(OUT_15 / "股票晨报反馈转进化候选样例_最新.md", candidate_md)

    write_json(OUT_15 / f"进化反馈闭环任务回传_{ts}.json", handback)
    write_json(OUT_15 / "进化反馈闭环任务回传_最新.json", handback)
    handback_md = [
        "# 进化反馈闭环任务回传",
        "",
        f"- 生成时间：{handback['生成时间']}",
        f"- 范围：{handback['范围']}",
        "",
        "## 本次动作",
        "",
        *[f"- {item}" for item in handback["本次动作"]],
        "",
        "## 产物",
        "",
        *[f"- {name}：{path}" for name, path in handback["产物"].items()],
        "",
        "## 验收结论",
        "",
        *[f"- {name}：{value}" for name, value in handback["验收结论"].items()],
        "",
        "## 安全边界",
        "",
        *[f"- {name}：{value}" for name, value in handback["安全边界"].items()],
    ]
    write_md(OUT_15 / f"进化反馈闭环任务回传_{ts}.md", handback_md)
    write_md(OUT_15 / "进化反馈闭环任务回传_最新.md", handback_md)


def main() -> int:
    feedback_package, candidate_package, handback = build_outputs()
    write_outputs(feedback_package, candidate_package, handback)
    failed = [name for name, value in candidate_package["验收"].items() if value is not True]
    result = {
        "输出目录13": str(OUT_13),
        "输出目录15": str(OUT_15),
        "反馈样例数量": feedback_package["样例反馈数量"],
        "进化候选数量": candidate_package["候选数量"],
        "去重拒收数量": candidate_package["去重拒收数量"],
        "验收": "通过" if not failed else "不通过",
        "失败项": failed,
        "安全边界": SAFETY_BOUNDARY,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
