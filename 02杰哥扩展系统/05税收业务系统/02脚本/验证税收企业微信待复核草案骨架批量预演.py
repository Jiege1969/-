# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SRC_JSON = DATA_DIR / "税收企业微信待复核草案骨架批量预演_最新.json"
SRC_MD = DATA_DIR / "税收企业微信待复核草案骨架批量预演_最新.md"
SKELETON_JSON = DATA_DIR / "待复核分析草案骨架" / "税收企业微信待复核草案骨架批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信待复核草案骨架批量预演验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信待复核草案骨架批量预演验收_最新.md"


REQUIRED_FIELDS = [
    "草案ID",
    "来源输入包ID",
    "消息ID",
    "契约状态",
    "业务事项",
    "业务事实",
    "政策依据",
    "依据层级",
    "适用条件",
    "资料缺口",
    "风险点",
    "置信度",
    "人工复核项",
    "输出边界",
    "禁止动作",
    "是否写正式业务库",
    "是否调用模型推理",
    "是否生成正式税务结论",
]
ALLOWED_STATUSES = {"draft", "pending_review"}
FORBIDDEN_STATUSES = {"confirmed_conclusion", "human_reviewed"}


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, passed: bool, detail) -> dict:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = load(SRC_JSON)
    skeleton_data = load(SKELETON_JSON)
    text = SRC_MD.read_text(encoding="utf-8", errors="ignore") if SRC_MD.exists() else ""
    skeletons = data.get("草案骨架", [])
    blocked = data.get("阻断留痕", [])
    boundaries = data.get("安全边界", {})

    checks = [
        check("主JSON存在", SRC_JSON.exists(), str(SRC_JSON)),
        check("主Markdown存在", SRC_MD.exists(), str(SRC_MD)),
        check("草案骨架JSON存在", SKELETON_JSON.exists(), str(SKELETON_JSON)),
        check("主JSON可解析", bool(data), data.get("名称", "未解析")),
        check("草案骨架JSON可解析", bool(skeleton_data), skeleton_data.get("名称", "未解析")),
        check("草案骨架数量为5", len(skeletons) == 5 and data.get("草案骨架数量") == 5, len(skeletons)),
        check("阻断数量为1", len(blocked) == 1 and data.get("阻断数量") == 1, len(blocked)),
        check("草案骨架字段齐备", all(all(field in item for field in REQUIRED_FIELDS) for item in skeletons), [item.get("草案ID") for item in skeletons if not all(field in item for field in REQUIRED_FIELDS)]),
        check("契约状态均允许", all(item.get("契约状态") in ALLOWED_STATUSES for item in skeletons), [item.get("契约状态") for item in skeletons]),
        check("契约状态未使用禁用状态", not any(item.get("契约状态") in FORBIDDEN_STATUSES for item in skeletons), [item.get("契约状态") for item in skeletons]),
        check("包含draft和pending_review", {"draft", "pending_review"}.issubset({item.get("契约状态") for item in skeletons}), [item.get("契约状态") for item in skeletons]),
        check("政策依据均为候选待核验", all(item.get("政策依据", {}).get("依据状态") == "candidate_only_pending_evidence_review" for item in skeletons), [item.get("草案ID") for item in skeletons if item.get("政策依据", {}).get("依据状态") != "candidate_only_pending_evidence_review"]),
        check("全部草案有依据层级", all(item.get("依据层级") for item in skeletons), [item.get("草案ID") for item in skeletons if not item.get("依据层级")]),
        check("全部草案有适用条件骨架", all(item.get("适用条件") for item in skeletons), [item.get("草案ID") for item in skeletons if not item.get("适用条件")]),
        check("全部草案有资料缺口", all(item.get("资料缺口") for item in skeletons), [item.get("草案ID") for item in skeletons if not item.get("资料缺口")]),
        check("全部草案有风险点", all(item.get("风险点") for item in skeletons), [item.get("草案ID") for item in skeletons if not item.get("风险点")]),
        check("全部草案有人工复核项", all(item.get("人工复核项") for item in skeletons), [item.get("草案ID") for item in skeletons if not item.get("人工复核项")]),
        check("输出边界明确非正式税务意见", all(any("不是正式税务意见" in boundary for boundary in item.get("输出边界", [])) for item in skeletons), "输出边界"),
        check("全部草案不写正式库", all(item.get("是否写正式业务库") is False for item in skeletons), "是否写正式业务库=False"),
        check("全部草案不调用模型推理", all(item.get("是否调用模型推理") is False for item in skeletons), "是否调用模型推理=False"),
        check("全部草案不生成正式结论", all(item.get("是否生成正式税务结论") is False for item in skeletons), "是否生成正式税务结论=False"),
        check("硬边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("Markdown声明不是正式业务库和税务结论", "不是正式业务库" in text and "不是税务结论" in text, "资产身份声明"),
    ]

    failed = [item for item in checks if item["结果"] != "通过"]
    result = {
        "名称": "税收企业微信待复核草案骨架批量预演验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信待复核草案骨架批量预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
