# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SRC_JSON = DATA_DIR / "税收企业微信批量分析契约输入包_最新.json"
SRC_MD = DATA_DIR / "税收企业微信批量分析契约输入包_最新.md"
PACKAGE_JSON = DATA_DIR / "分析契约输入包" / "税收企业微信批量分析契约输入包_预演.json"
OUT_JSON = DATA_DIR / "税收企业微信批量分析契约输入包验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信批量分析契约输入包验收_最新.md"


REQUIRED_FIELDS = [
    "输入包ID",
    "来源流转ID",
    "消息ID",
    "来源机器人",
    "输入包状态",
    "业务事项",
    "适用税种",
    "政策依据候选主题",
    "依据层级",
    "业务事实摘要",
    "资料缺口",
    "风险点",
    "置信度",
    "人工复核项",
    "禁止动作",
    "下一步建议",
    "是否写正式业务库",
    "是否生成正式税务结论",
]
ALLOWED_STATUSES = {"pending_review_input", "pending_fact_completion", "blocked_sensitive_unmasked"}
FORBIDDEN_TERMS = ["confirmed_conclusion", "auto_filed", "auto_declared"]


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, passed: bool, detail) -> dict:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = load(SRC_JSON)
    package_data = load(PACKAGE_JSON)
    text = SRC_MD.read_text(encoding="utf-8", errors="ignore") if SRC_MD.exists() else ""
    packages = data.get("输入包", [])
    rejected = data.get("拒绝承接留痕", [])
    boundaries = data.get("安全边界", {})

    checks = [
        check("主JSON存在", SRC_JSON.exists(), str(SRC_JSON)),
        check("主Markdown存在", SRC_MD.exists(), str(SRC_MD)),
        check("预演输入包JSON存在", PACKAGE_JSON.exists(), str(PACKAGE_JSON)),
        check("主JSON可解析", bool(data), data.get("名称", "未解析")),
        check("预演输入包JSON可解析", bool(package_data), package_data.get("名称", "未解析")),
        check("输入包数量为5", len(packages) == 5 and data.get("输入包数量") == 5, len(packages)),
        check("拒绝承接数量为1", len(rejected) == 1 and data.get("拒绝承接数量") == 1, len(rejected)),
        check("输入包字段齐备", all(all(field in item for field in REQUIRED_FIELDS) for item in packages), [item.get("输入包ID") for item in packages if not all(field in item for field in REQUIRED_FIELDS)]),
        check("输入包状态均允许", all(item.get("输入包状态") in ALLOWED_STATUSES for item in packages), [item.get("输入包状态") for item in packages]),
        check("包含待事实补充输入包", any(item.get("输入包状态") == "pending_fact_completion" for item in packages), [item.get("输入包状态") for item in packages]),
        check("全部输入包来源杰哥工作秘书", all(item.get("来源机器人") == "杰哥工作秘书" for item in packages), [item.get("输入包ID") for item in packages if item.get("来源机器人") != "杰哥工作秘书"]),
        check("全部输入包有政策候选主题", all(item.get("政策依据候选主题") for item in packages), [item.get("输入包ID") for item in packages if not item.get("政策依据候选主题")]),
        check("全部输入包有资料缺口", all(item.get("资料缺口") for item in packages), [item.get("输入包ID") for item in packages if not item.get("资料缺口")]),
        check("全部输入包有风险点", all(item.get("风险点") for item in packages), [item.get("输入包ID") for item in packages if not item.get("风险点")]),
        check("全部输入包有人工复核项", all(item.get("人工复核项") for item in packages), [item.get("输入包ID") for item in packages if not item.get("人工复核项")]),
        check("全部输入包不写正式库", all(item.get("是否写正式业务库") is False for item in packages), "是否写正式业务库=False"),
        check("全部输入包不生成正式结论", all(item.get("是否生成正式税务结论") is False for item in packages), "是否生成正式税务结论=False"),
        check("输入包状态未使用禁用状态词", not any(item.get("输入包状态") in FORBIDDEN_TERMS for item in packages), [item.get("输入包状态") for item in packages]),
        check("硬边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("Markdown声明不是正式业务库和税务结论", "不是正式业务库" in text and "不是税务结论" in text, "资产身份声明"),
    ]

    failed = [item for item in checks if item["结果"] != "通过"]
    result = {
        "名称": "税收企业微信批量分析契约输入包验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信批量分析契约输入包验收",
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
