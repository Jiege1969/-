# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
CORE_PREP_JSON = OUT_DIR / "研发费用核心正式依据时效补齐准备包_最新.json"
CORE_MATRIX_JSON = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.json"
POLICY_CHAIN_JSON = OUT_DIR / "研发费用加计扣除政策链补齐预演_最新.json"
OUT_JSON = OUT_DIR / "研发费用后续比例延续政策本地证据卡补齐准备_最新.json"
OUT_MD = OUT_DIR / "研发费用后续比例延续政策本地证据卡补齐准备_最新.md"

TARGET_SLOT_ID = "rd-rate-extension"
FIELD_CHECKLIST = [
    "资料编号",
    "资料类型",
    "标题",
    "文号",
    "发布机关",
    "发布日期",
    "施行日期",
    "有效状态",
    "适用税种",
    "适用对象",
    "适用地区",
    "适用期间",
    "依据层级",
    "资料角色",
    "来源名称",
    "来源链接",
    "最终链接",
    "抓取或登记时间",
    "原文哈希",
    "本地原文路径",
    "本地解析文本路径",
    "本地元数据路径",
    "适用主体",
    "适用事项",
    "关键条件",
    "排除条件",
    "所需资料",
    "待人工复核项",
]
SEARCH_TERMS = [
    "研发费用 加计扣除 比例",
    "研究开发费用 税前加计扣除 提高",
    "研发费用 加计扣除 延续",
    "研发费用 加计扣除 行业范围",
    "集成电路 工业母机 研发费用 加计扣除",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def text_blob(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def classify_candidate(item: dict[str, Any]) -> str:
    text = text_blob(item)
    if any(keyword in text for keyword in ["比例", "提高", "延续", "行业", "集成电路", "工业母机"]):
        return "后续比例/延续/行业范围候选线索"
    if "A107012" in text or "预缴" in text or "年度纳税申报" in text:
        return "申报表配套候选，不能替代比例延续政策"
    return "其他研发费用候选线索"


def candidate_stub(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "标题": item.get("标题"),
        "文号": item.get("文号"),
        "依据层级": item.get("依据层级"),
        "资料角色": item.get("资料角色"),
        "发布日期": item.get("发布日期"),
        "文件时效": item.get("文件时效"),
        "来源名称": item.get("来源名称"),
        "来源链接": item.get("来源链接"),
        "候选分类": classify_candidate(item),
        "当前处理状态": item.get("处理状态", "本地线索，尚未形成补齐证据卡"),
        "阻断原因": item.get("阻断原因", []) or [
            "尚未形成后续比例/延续政策本地证据卡。",
            "尚未核验全文有效、适用期间、行业范围和上下位关系。",
        ],
        "是否进入当前适用依据候选": False,
        "是否生成正式税务结论": False,
    }


def find_target_slot(matrix: dict[str, Any]) -> dict[str, Any]:
    for slot in matrix.get("核心依据时效矩阵", []):
        if slot.get("槽位ID") == TARGET_SLOT_ID:
            return slot
    return {}


def find_target_task(prep: dict[str, Any]) -> dict[str, Any]:
    for task in prep.get("补齐任务", []):
        if task.get("槽位ID") == TARGET_SLOT_ID:
            return task
    return {}


def write_md(report: dict[str, Any]) -> None:
    lines = [
        "# 研发费用后续比例延续政策本地证据卡补齐准备",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 候选线索数量：{report['候选线索数量']}",
        f"- 证据卡字段数量：{len(report['证据卡字段清单'])}",
        "",
        "## 目标槽位",
        "",
        f"- 槽位ID：{report['目标槽位'].get('槽位ID')}",
        f"- 槽位名称：{report['目标槽位'].get('槽位名称')}",
        f"- 当前状态：{report['目标槽位'].get('槽位状态')}",
        "",
        "## 候选线索",
        "",
    ]
    for item in report["候选线索"]:
        lines.extend([
            f"### {item.get('标题')}",
            f"- 文号：{item.get('文号')}",
            f"- 分类：{item.get('候选分类')}",
            f"- 文件时效：{item.get('文件时效')}",
            f"- 当前处理状态：{item.get('当前处理状态')}",
            f"- 是否进入当前适用依据候选：{item.get('是否进入当前适用依据候选')}",
            "",
        ])
    if not report["候选线索"]:
        lines.append("- 无。需等待人工提供或后续受控下载候选。")

    lines.extend(["## 证据卡字段清单", ""])
    for field in report["证据卡字段清单"]:
        lines.append(f"- {field}")

    lines.extend(["", "## 待人工复核项", ""])
    for item in report["待人工复核项"]:
        lines.append(f"- {item}")

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
    core_prep = load_json(CORE_PREP_JSON)
    core_matrix = load_json(CORE_MATRIX_JSON)
    policy_chain = load_json(POLICY_CHAIN_JSON)

    target_slot = find_target_slot(core_matrix)
    target_task = find_target_task(core_prep)
    source_candidates = []
    source_candidates.extend(target_slot.get("官方查询候选", []))
    source_candidates.extend(target_task.get("官方查询候选", []))
    source_candidates.extend(policy_chain.get("官方查询候选", []))
    candidate_lines = [candidate_stub(item) for item in source_candidates]

    target_like = [item for item in candidate_lines if item["候选分类"] == "后续比例/延续/行业范围候选线索"]
    review_items = [
        "人工确认后续比例、延续和行业范围政策的官方来源入口，优先国家级部门官方网站或政策法规库。",
        "人工核验标题、文号、发布机关、发布日期、施行日期、全文有效状态和适用期间。",
        "人工区分一般研发费用政策、特定行业比例提高政策、申报表配套公告和政策解读，不得混层。",
        "仅有查询候选或标题线索时，不得进入当前适用依据候选。",
        "形成本地原文、原文哈希、解析文本和元数据后，再进入下一轮时效核验。",
    ]
    for item in target_task.get("人工复核项", []):
        if item not in review_items:
            review_items.append(item)

    report = {
        "名称": "研发费用后续比例延续政策本地证据卡补齐准备",
        "生成时间": now,
        "资产身份": "政策证据底座补齐准备包，不是税务结论库，不是办税执行系统。",
        "来源文件": {
            "核心时效准备包": str(CORE_PREP_JSON),
            "核心时效矩阵": str(CORE_MATRIX_JSON),
            "政策链补齐预演": str(POLICY_CHAIN_JSON),
        },
        "结论": "完成，后续比例/延续政策仍需人工提供或后续受控下载后形成本地证据卡",
        "目标槽位": target_slot,
        "目标补齐任务": target_task,
        "搜索关键词建议": SEARCH_TERMS,
        "候选线索数量": len(candidate_lines),
        "命中后续比例延续线索数量": len(target_like),
        "候选线索": candidate_lines,
        "证据卡字段清单": FIELD_CHECKLIST,
        "入候选门禁": [
            "必须存在官方来源链接或人工提供的官方原文。",
            "必须生成本地原文路径、解析文本路径、元数据路径和原文哈希。",
            "有效状态必须为全文有效或人工确认有效。",
            "依据层级必须为财税文件或税务规范性文件等正式依据层，不得用政策解读或案例替代。",
            "不得自动生成适用结论、享受判断、金额测算或申报指令。",
        ],
        "待人工复核项": review_items,
        "下一步自动队列": [
            {
                "优先级": "L2",
                "事项": "涉税业务分析契约影子样例复核",
                "原因": "政策证据底座补齐准备已推进，分析契约样例需要继续保持只输出待复核分析草案的边界。",
                "是否可自动推进": True,
                "边界": "只复核影子样例和契约字段，不调用模型，不生成正式税务结论，不接电子税务局或财税软件。",
            },
            {
                "优先级": "L2",
                "事项": "税收企业微信正式入口dry-run链路复检",
                "原因": "企业微信终端已纳入入口，但真实发送和凭据仍阻断，需要定期复检dry-run门禁和合规输出。",
                "是否可自动推进": True,
                "边界": "只运行本地dry-run和验收脚本，不读取凭据，不启动服务，不真实发送，不生成正式税务结论。",
            },
        ],
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否覆盖原始资料": False,
            "是否写正式业务规则": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用模型推理": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(report)
    print(json.dumps({"状态": "完成", "候选线索数量": len(candidate_lines), "命中后续比例延续线索数量": len(target_like), "输出": str(OUT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
