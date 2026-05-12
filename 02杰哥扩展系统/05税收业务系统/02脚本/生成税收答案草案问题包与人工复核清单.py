# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收答案草案问题包规则.json"
ANSWER_SAMPLE = ROOT / "03数据" / "16答案草案依据链样板" / "税收答案草案本地依据链样板_最新.json"
OUT_DIR = ROOT / "03数据" / "17问题包与人工复核清单"
OUT_JSON = OUT_DIR / "税收答案草案问题包与人工复核清单_最新.json"
OUT_MD = OUT_DIR / "税收答案草案问题包与人工复核清单_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def text_blob(answer: dict) -> str:
    return json.dumps(answer, ensure_ascii=False)


def matched_sample(question: dict, samples: list[dict]) -> dict | None:
    best = None
    best_score = 0
    for sample in samples:
        blob = text_blob(sample)
        score = sum(1 for keyword in question.get("关键词", []) if keyword and keyword in blob)
        if score > best_score:
            best = sample
            best_score = score
    return best if best_score > 0 else None


def make_review_item(question: dict, sample: dict | None) -> dict:
    can_judge = bool(sample and sample.get("是否可形成当前适用判断") is True)
    formal_count = 0
    auxiliary_count = 0
    if sample:
        formal_count = len(sample.get("正式依据", [])) + len(sample.get("正式依据候选", []))
        auxiliary_count = len(sample.get("辅助材料", []))
    blockers = []
    if not sample:
        blockers.append("尚未生成答案草案样板。")
    if formal_count < int(question.get("最低正式依据数量", 1)):
        blockers.append("可匹配正式依据数量不足。")
    if not can_judge:
        blockers.append("当前不能形成适用判断，需按降级条件复核。")

    return {
        "问题ID": question.get("问题ID"),
        "问题": question.get("问题"),
        "适用税种": question.get("适用税种"),
        "关键词": question.get("关键词", []),
        "最低正式依据数量": question.get("最低正式依据数量", 1),
        "已匹配正式依据数量": formal_count,
        "已匹配辅助材料数量": auxiliary_count,
        "是否已有答案草案样板": sample is not None,
        "能否形成当前适用判断": can_judge,
        "判断策略": question.get("判断策略"),
        "降级条件": question.get("降级条件", []),
        "当前阻断原因": blockers,
        "人工复核清单": {
            "事实条件是否齐备": "待复核",
            "正式依据是否全文有效": "待复核",
            "是否存在已修改或废止文件": "待复核",
            "附件是否已解析": "待复核",
            "地方口径是否需要核验": "待复核",
            "复核人": "",
            "复核结论": "",
            "复核时间": "",
        },
        "详情路径": str(ANSWER_SAMPLE) if sample else "",
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rule = load_json(RULE)
    sample_pack = load_json(ANSWER_SAMPLE)
    samples = sample_pack.get("答案草案", [])
    review_items = [
        make_review_item(question, matched_sample(question, samples))
        for question in rule.get("问题包", [])
    ]

    result = {
        "名称": "税收答案草案问题包与人工复核清单",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change_configurable_question_pack",
        "规则文件": str(RULE),
        "问题数量": len(review_items),
        "可形成判断数量": sum(1 for item in review_items if item["能否形成当前适用判断"]),
        "需降级或待补数量": sum(1 for item in review_items if not item["能否形成当前适用判断"]),
        "问题包复核清单": review_items,
        "安全边界": rule.get("安全边界", {}),
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收答案草案问题包与人工复核清单",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change_configurable_question_pack",
        f"- 问题数量：{result['问题数量']}",
        f"- 可形成判断数量：{result['可形成判断数量']}",
        f"- 需降级或待补数量：{result['需降级或待补数量']}",
        "",
        "## 问题包复核清单",
        "",
    ]
    for item in review_items:
        lines.extend([
            f"### {item['问题']}",
            f"- 问题ID：{item['问题ID']}",
            f"- 适用税种：{item['适用税种']}",
            f"- 已匹配正式依据数量：{item['已匹配正式依据数量']}",
            f"- 已匹配辅助材料数量：{item['已匹配辅助材料数量']}",
            f"- 能否形成当前适用判断：{item['能否形成当前适用判断']}",
            f"- 当前阻断原因：{'；'.join(item['当前阻断原因']) if item['当前阻断原因'] else '无'}",
            f"- 降级条件：{'；'.join(item['降级条件'])}",
            "",
        ])
    lines.extend(["## 安全边界", ""])
    for key, value in result["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "问题数量": len(review_items), "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
