# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SRC_JSON = DATA_DIR / "税收企业微信dry-run阶段收口索引_最新.json"
SRC_MD = DATA_DIR / "税收企业微信dry-run阶段收口索引_最新.md"
OUT_JSON = DATA_DIR / "税收企业微信dry-run阶段收口索引验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信dry-run阶段收口索引验收_最新.md"


def check(name: str, passed: bool, detail) -> dict:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks: list[dict] = []
    data = {}
    text = ""

    checks.append(check("索引JSON存在", SRC_JSON.exists(), str(SRC_JSON)))
    checks.append(check("索引Markdown存在", SRC_MD.exists(), str(SRC_MD)))

    if SRC_JSON.exists():
        try:
            data = json.loads(SRC_JSON.read_text(encoding="utf-8"))
            checks.append(check("索引JSON可解析", True, "ok"))
        except json.JSONDecodeError as exc:
            checks.append(check("索引JSON可解析", False, str(exc)))
    else:
        checks.append(check("索引JSON可解析", False, "文件不存在"))

    if SRC_MD.exists():
        text = SRC_MD.read_text(encoding="utf-8", errors="ignore")

    source_status = data.get("来源报告状态", [])
    hard_boundaries = data.get("硬边界", {})
    required_fields = data.get("待复核输出最低字段", [])
    required_contract_fields = ["政策依据", "依据层级", "有效状态", "适用条件", "业务事实", "missing", "confidence", "人工复核项"]

    checks.append(check("资产身份不冒充正式入口", "不是正式入口配置" in data.get("资产身份", ""), data.get("资产身份", "")))
    checks.append(check("总体结论为dry-run待复核口径", data.get("总体结论") == "dry_run_evidence_ready_pending_human_review", data.get("总体结论")))
    checks.append(check("来源报告不少于22份", len(source_status) >= 22, len(source_status)))
    checks.append(check("来源报告无缺失", data.get("来源报告缺失数量") == 0, data.get("来源报告缺失数量")))
    checks.append(check("来源报告无失败", data.get("来源报告失败数量") == 0, data.get("来源报告失败数量")))
    checks.append(check("所有来源报告通过", all(item.get("是否通过") for item in source_status), [item for item in source_status if not item.get("是否通过")]))
    checks.append(check("硬边界全部为False", all(value is False for value in hard_boundaries.values()), hard_boundaries))
    checks.append(check("包含待复核分析契约最低字段", all(item in required_fields for item in required_contract_fields), required_fields))
    checks.append(check("明确不真实发送", data.get("硬边界", {}).get("是否企业微信真实发送") is False and "不真实发送" in text, "企业微信真实发送=False"))
    checks.append(check("明确不触发n8n", data.get("硬边界", {}).get("是否触发n8n") is False, "n8n=False"))
    checks.append(check("明确不修改公共配置", data.get("硬边界", {}).get("是否修改公共企业微信接入配置") is False, "公共配置=False"))
    checks.append(check("明确不修改总管", data.get("硬边界", {}).get("是否修改总管文件") is False, "总管=False"))
    checks.append(check("明确不生成正式税务结论", data.get("硬边界", {}).get("是否生成正式税务结论") is False and "正式税务意见" in text, "正式税务结论=False"))
    checks.append(check("需要总管整合但税收线不越权", data.get("可交付状态", {}).get("总管整合", "").startswith("需要总管只读吸收"), data.get("可交付状态", {}).get("总管整合")))

    failed = [item for item in checks if item["结果"] != "通过"]
    result = {
        "名称": "税收企业微信dry-run阶段收口索引验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": hard_boundaries,
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信dry-run阶段收口索引验收",
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
