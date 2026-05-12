# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "28政策证据底座字段补齐预演"
SOURCE_JSON = OUT_DIR / "税收政策证据底座字段补齐预演_最新.json"
OUT_JSON = OUT_DIR / "税收政策证据底座字段补齐预演复核_最新.json"
OUT_MD = OUT_DIR / "税收政策证据底座字段补齐预演复核_最新.md"

REQUIRED_FIELDS = [
    "资料ID",
    "标题",
    "文号",
    "发文机关",
    "发布日期",
    "施行日期",
    "文件时效",
    "来源名称",
    "来源链接",
    "最终链接",
    "下载时间",
    "原文哈希",
    "保存路径",
    "资产身份",
    "入库分层口径",
    "依据层级",
    "资料类别",
    "适用主体",
    "适用事项",
    "适用期间",
    "关键条件",
    "排除条件",
    "所需资料",
    "待人工复核项",
    "是否当前适用依据候选",
    "是否生成正式税务结论",
]

REVIEW_REQUIRED_WHEN_EMPTY = {
    "施行日期": ["施行日期", "生效日期", "适用年度", "适用期间"],
    "适用主体": ["适用主体", "纳税人", "企业"],
    "适用事项": ["适用事项", "事项"],
    "适用期间": ["适用期间", "适用年度", "期间"],
    "关键条件": ["关键条件", "适用条件"],
    "排除条件": ["排除条件", "废止", "失效"],
    "所需资料": ["所需资料", "附件", "资料"],
}

BAD_STATUS = {"已修改", "全文失效", "全文废止", "尚未生效", "待核验", "时效缺失", "已废止", "已失效"}
FORBIDDEN_CONCLUSION_PHRASES = [
    "该业务一定适用",
    "可以享受",
    "应纳税额",
    "退税金额",
    "无需人工复核",
    "正式税务意见",
    "结论确认",
    "confirmed_conclusion",
]
NAVIGATION_NOISE = ["当前位置", "首页 >", "上一页", "下一页", "打印本页", "关闭窗口", "分享到"]
SAFETY_FALSE_KEYS = [
    "是否联网",
    "是否下载",
    "是否覆盖原始资料",
    "是否写正式业务规则",
    "是否生成正式税务结论",
    "是否触发n8n",
    "是否企业微信真实发送",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def text_blob(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def review_items_text(row: dict[str, Any]) -> str:
    return "\n".join(str(item) for item in row.get("待人工复核项", []) if item is not None)


def has_review_for(field: str, row: dict[str, Any]) -> bool:
    review_text = review_items_text(row)
    keywords = REVIEW_REQUIRED_WHEN_EMPTY.get(field, [field])
    return any(keyword in review_text for keyword in keywords)


def title_of(row: dict[str, Any]) -> str:
    return row.get("标题") or row.get("资料ID") or "未命名资料"


def analyze_row(row: dict[str, Any]) -> dict[str, Any]:
    title = title_of(row)
    review_text = review_items_text(row)
    field_gaps = []
    field_warnings = []
    candidate_risks = []
    formal_risks = []
    noise_risks = []

    for field in REQUIRED_FIELDS:
        if field not in row or is_empty(row.get(field)):
            covered = has_review_for(field, row)
            field_gaps.append({
                "资料标题": title,
                "字段": field,
                "问题": "字段缺失或为空",
                "是否已进入待人工复核项": covered,
                "处理口径": "不直接补写为正式事实；进入待人工复核补强。",
            })

    source_link = row.get("最终链接") or row.get("来源链接")
    status = row.get("文件时效")
    category = row.get("资料类别")
    candidate = bool(row.get("是否当前适用依据候选"))
    old_candidate = bool(row.get("可作为当前适用依据"))

    allowed_candidate = (
        status == "全文有效"
        and category == "正式依据"
        and not is_empty(source_link)
        and not bool(row.get("是否生成正式税务结论"))
    )
    if candidate and not allowed_candidate:
        candidate_risks.append({
            "资料标题": title,
            "问题": "当前适用依据候选门禁不满足",
            "文件时效": status,
            "资料类别": category,
            "来源链接是否存在": not is_empty(source_link),
            "处理口径": "不得进入当前适用依据候选；应转入待核验或辅助材料。",
        })
    if old_candidate and not candidate:
        field_warnings.append({
            "资料标题": title,
            "问题": "旧字段可作为当前适用依据为真，但新字段未放行",
            "处理口径": "以后续新字段是否当前适用依据候选为准。",
        })
    if status in BAD_STATUS and candidate:
        candidate_risks.append({
            "资料标题": title,
            "问题": "非有效状态资料被标记为候选依据",
            "文件时效": status,
            "处理口径": "失效、废止、待核验或尚未生效资料不得直接参与结论。",
        })
    if status in BAD_STATUS and "时效" not in review_text and "有效" not in review_text:
        field_warnings.append({
            "资料标题": title,
            "问题": "非有效状态资料缺少时效人工复核提示",
            "处理口径": "补充待人工复核项。",
        })

    blob = text_blob(row)
    for phrase in FORBIDDEN_CONCLUSION_PHRASES:
        if phrase in blob:
            formal_risks.append({
                "资料标题": title,
                "命中短语": phrase,
                "处理口径": "政策证据底座不得生成或暗示正式税务结论。",
            })
    if row.get("是否生成正式税务结论") is not False:
        formal_risks.append({
            "资料标题": title,
            "问题": "是否生成正式税务结论未明确为False",
            "处理口径": "政策证据底座只提供证据，不提供正式税务结论。",
        })

    for section in ["关键条件", "排除条件"]:
        section_text = text_blob(row.get(section, ""))
        hits = [item for item in NAVIGATION_NOISE if item in section_text]
        if hits:
            noise_risks.append({
                "资料标题": title,
                "字段": section,
                "命中噪声": hits,
                "处理口径": "后续补强时清理页面导航噪声，只保留政策条件文本。",
            })

    return {
        "资料ID": row.get("资料ID"),
        "标题": title,
        "文件时效": status,
        "资料类别": category,
        "是否当前适用依据候选": candidate,
        "候选依据门禁是否满足": allowed_candidate,
        "字段缺口": field_gaps,
        "字段警示": field_warnings,
        "候选依据风险": candidate_risks,
        "正式结论越界风险": formal_risks,
        "页面噪声风险": noise_risks,
    }


def write_md(report: dict[str, Any]) -> None:
    lines = [
        "# 税收政策证据底座字段补齐预演复核",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 复核结论：{report['复核结论']}",
        f"- 资料数量：{report['资料数量']}",
        f"- 字段缺口数量：{report['字段缺口数量']}",
        f"- 候选依据风险数量：{report['候选依据风险数量']}",
        f"- 正式结论越界风险数量：{report['正式结论越界风险数量']}",
        f"- 安全边界风险数量：{report['安全边界风险数量']}",
        "",
        "## 字段缺口",
        "",
    ]
    for item in report["字段缺口"]:
        lines.append(f"- {item['资料标题']}：{item['字段']}，已进入复核项={item['是否已进入待人工复核项']}。{item['处理口径']}")
    if not report["字段缺口"]:
        lines.append("- 无")

    lines.extend(["", "## 候选依据风险", ""])
    for item in report["候选依据风险"]:
        lines.append(f"- {item['资料标题']}：{item['问题']}。{item['处理口径']}")
    if not report["候选依据风险"]:
        lines.append("- 无")

    lines.extend(["", "## 正式结论越界风险", ""])
    for item in report["正式结论越界风险"]:
        lines.append(f"- {item['资料标题']}：{item.get('问题') or item.get('命中短语')}。{item['处理口径']}")
    if not report["正式结论越界风险"]:
        lines.append("- 无")

    lines.extend(["", "## 下一步自动队列", ""])
    for item in report["下一步自动队列"]:
        lines.append(f"- {item['优先级']} {item['事项']}：{item['边界']}")

    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source = load_json(SOURCE_JSON)
    rows = source.get("资料", [])
    analyses = [analyze_row(row) for row in rows]

    field_gaps = [gap for item in analyses for gap in item["字段缺口"]]
    field_warnings = [gap for item in analyses for gap in item["字段警示"]]
    candidate_risks = [risk for item in analyses for risk in item["候选依据风险"]]
    formal_risks = [risk for item in analyses for risk in item["正式结论越界风险"]]
    noise_risks = [risk for item in analyses for risk in item["页面噪声风险"]]

    safety = source.get("安全边界", {})
    safety_risks = [
        {"字段": key, "当前值": safety.get(key), "期望值": False}
        for key in SAFETY_FALSE_KEYS
        if safety.get(key) is not False
    ]

    fatal_count = len(candidate_risks) + len(formal_risks) + len(safety_risks)
    if not SOURCE_JSON.exists():
        conclusion = "失败：缺少字段补齐预演来源"
    elif fatal_count:
        conclusion = "需纠偏：存在候选依据、正式结论或安全边界风险"
    elif field_gaps or field_warnings or noise_risks:
        conclusion = "通过，存在待人工复核补强项"
    else:
        conclusion = "通过"

    next_queue = []
    if field_gaps or field_warnings or noise_risks:
        next_queue.append({
            "优先级": "L1",
            "事项": "税收政策证据底座字段缺口补强预演",
            "原因": "复核已识别字段空值、字段警示或页面噪声，需要继续生成不覆盖原资料的补强预演。",
            "是否可自动推进": True,
            "边界": "只读现有政策证据和解析文本；补强结果进入待人工复核，不写正式业务规则，不生成正式税务结论。",
        })
    next_queue.append({
        "优先级": "L2",
        "事项": "税收研发费用加计扣除核心正式依据时效补齐",
        "原因": "继续补齐研发费用专题政策链的全文有效依据和适用条件。",
        "是否可自动推进": True,
        "边界": "只基于已有官方来源候选和本地证据卡准备补齐清单；不联网、不下载、不生成正式税务结论。",
    })

    report = {
        "名称": "税收政策证据底座字段补齐预演复核",
        "生成时间": now,
        "资产身份": "政策证据底座质量复核，不是税务结论库，不是办税执行系统。",
        "来源文件": str(SOURCE_JSON),
        "是否修改原始政策资料": False,
        "资料数量": len(rows),
        "复核结论": conclusion,
        "字段缺口数量": len(field_gaps),
        "字段警示数量": len(field_warnings),
        "候选依据风险数量": len(candidate_risks),
        "正式结论越界风险数量": len(formal_risks),
        "页面噪声风险数量": len(noise_risks),
        "安全边界风险数量": len(safety_risks),
        "资料复核结果": analyses,
        "字段缺口": field_gaps,
        "字段警示": field_warnings,
        "候选依据风险": candidate_risks,
        "正式结论越界风险": formal_risks,
        "页面噪声风险": noise_risks,
        "安全边界风险": safety_risks,
        "下一步自动队列": next_queue,
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否读取或保存企业微信凭据": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(report)
    print(json.dumps({"状态": "完成", "复核结论": conclusion, "字段缺口数量": len(field_gaps), "候选依据风险数量": len(candidate_risks), "输出": str(OUT_JSON)}, ensure_ascii=False))
    return 0 if SOURCE_JSON.exists() and fatal_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
