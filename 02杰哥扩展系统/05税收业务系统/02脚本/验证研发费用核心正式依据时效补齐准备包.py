# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
SOURCE_JSON = OUT_DIR / "研发费用加计扣除核心正式依据时效补齐预演_最新.json"
PREVIEW_JSON = OUT_DIR / "研发费用核心正式依据时效补齐准备包_最新.json"
PREVIEW_MD = OUT_DIR / "研发费用核心正式依据时效补齐准备包_最新.md"
REPORT_JSON = OUT_DIR / "研发费用核心正式依据时效补齐准备包验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用核心正式依据时效补齐准备包验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = load_json(SOURCE_JSON)
    preview = load_json(PREVIEW_JSON)
    slots = source.get("核心依据时效矩阵", [])
    tasks = preview.get("补齐任务", [])
    checks = []

    checks.append(check("时效预演来源存在", SOURCE_JSON.exists(), str(SOURCE_JSON)))
    checks.append(check("准备包JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("准备包Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("槽位数量一致", preview.get("槽位数量") == len(slots), {"准备包": preview.get("槽位数量"), "来源": len(slots)}))
    checks.append(check("每个槽位均形成补齐任务", len(tasks) == len(slots), len(tasks)))
    checks.append(check("待补齐槽位数量不少于来源缺口数量", preview.get("待补齐槽位数量", 0) >= source.get("仍需补齐槽位数量", 0), {"准备包": preview.get("待补齐槽位数量"), "来源": source.get("仍需补齐槽位数量")}))
    checks.append(check("所有任务均不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in tasks), tasks))
    checks.append(check("未放行槽位保持pending_review", all(item.get("处理状态") in {"pending_review", "evidence_ready_pending_review"} for item in tasks), tasks))
    checks.append(check("下一步队列指向后续比例延续政策证据卡准备", any("后续比例延续政策本地证据卡补齐准备" in item.get("事项", "") for item in preview.get("下一步自动队列", [])), preview.get("下一步自动队列", [])))

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
        "名称": "研发费用核心正式依据时效补齐准备包验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 研发费用核心正式依据时效补齐准备包验收",
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
