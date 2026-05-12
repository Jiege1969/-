# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
CORE_PREP_JSON = OUT_DIR / "研发费用核心正式依据时效补齐准备包_最新.json"
PREVIEW_JSON = OUT_DIR / "研发费用后续比例延续政策本地证据卡补齐准备_最新.json"
PREVIEW_MD = OUT_DIR / "研发费用后续比例延续政策本地证据卡补齐准备_最新.md"
REPORT_JSON = OUT_DIR / "研发费用后续比例延续政策本地证据卡补齐准备验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用后续比例延续政策本地证据卡补齐准备验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    core_prep = load_json(CORE_PREP_JSON)
    preview = load_json(PREVIEW_JSON)
    candidates = preview.get("候选线索", [])
    checks = []

    checks.append(check("核心时效准备包存在", CORE_PREP_JSON.exists(), str(CORE_PREP_JSON)))
    checks.append(check("后续比例延续准备JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("后续比例延续准备Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("目标槽位为rd-rate-extension", preview.get("目标槽位", {}).get("槽位ID") == "rd-rate-extension", preview.get("目标槽位", {})))
    checks.append(check("证据卡字段清单不少于16项", len(preview.get("证据卡字段清单", [])) >= 16, preview.get("证据卡字段清单", [])))
    checks.append(check("入候选门禁包含哈希与有效状态", any("原文哈希" in item for item in preview.get("入候选门禁", [])) and any("有效状态" in item or "全文有效" in item for item in preview.get("入候选门禁", [])), preview.get("入候选门禁", [])))
    checks.append(check("所有候选线索均未进入当前适用依据候选", all(item.get("是否进入当前适用依据候选") is False for item in candidates), candidates))
    checks.append(check("所有候选线索均不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in candidates), candidates))
    checks.append(check("待人工复核项覆盖官方来源和适用期间", any("官方来源" in item for item in preview.get("待人工复核项", [])) and any("适用期间" in item for item in preview.get("待人工复核项", [])), preview.get("待人工复核项", [])))
    checks.append(check("下一步队列均不生成正式税务结论", all("不生成正式税务结论" in item.get("边界", "") for item in preview.get("下一步自动队列", [])), preview.get("下一步自动队列", [])))
    checks.append(check("承接核心准备包后续比例槽位", any(item.get("槽位ID") == "rd-rate-extension" for item in core_prep.get("补齐任务", [])), core_prep.get("补齐任务", [])))

    safety = preview.get("安全边界", {})
    required_false = [
        "是否联网",
        "是否下载",
        "是否覆盖原始资料",
        "是否写正式业务规则",
        "是否生成正式税务结论",
        "是否接电子税务局",
        "是否接财税软件",
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否调用模型推理",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "研发费用后续比例延续政策本地证据卡补齐准备验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 研发费用后续比例延续政策本地证据卡补齐准备验收",
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
