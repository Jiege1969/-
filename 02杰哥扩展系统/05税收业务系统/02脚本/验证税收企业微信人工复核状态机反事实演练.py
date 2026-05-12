# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = BASE_DIR / "税收企业微信人工复核状态机反事实演练_最新.json"
PREVIEW_MD = BASE_DIR / "税收企业微信人工复核状态机反事实演练_最新.md"
REPORT_JSON = BASE_DIR / "税收企业微信人工复核状态机反事实演练验收_最新.json"
REPORT_MD = BASE_DIR / "税收企业微信人工复核状态机反事实演练验收_最新.md"

SAFETY_FALSE_KEYS = [
    "是否接收真实企业微信回调",
    "是否联网",
    "是否读取凭据",
    "是否企业微信真实发送",
    "是否修改公共企业微信接入配置",
    "是否修改19310",
    "是否触发n8n",
    "是否写正式业务库",
    "是否写草案源文件",
    "是否真实回写状态",
    "是否调用模型推理",
    "是否接电子税务局",
    "是否接财税软件",
    "是否生成正式税务结论",
    "是否形成正式复核结论",
    "是否覆盖历史资料",
    "是否删除历史审计记录",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains(data: Any, keyword: str) -> bool:
    return keyword in json.dumps(data, ensure_ascii=False)


def main() -> int:
    data = load_json(PREVIEW_JSON)
    results = data.get("演练结果", [])
    safety = data.get("安全边界", {})
    target_counts = data.get("目标状态统计", {})

    checks = [
        check("反事实演练JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("反事实演练Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明为dry-run", contains(data.get("资产身份", ""), "dry-run"), data.get("资产身份", "")),
        check("演练结论通过", data.get("结论") == "通过", data.get("结论")),
        check("演练场景不少于7个", data.get("演练场景数量", 0) >= 7, data.get("演练场景数量", 0)),
        check("误升级数量为0", data.get("误升级数量") == 0, data.get("误升级数量")),
        check("没有场景误升级为evidence_ready", all(item.get("是否误升级为evidence_ready") is False for item in results), results),
        check("没有场景误升级为human_reviewed", all(item.get("是否误升级为human_reviewed") is False for item in results), results),
        check("反事实包含pending_review结果", int(target_counts.get("pending_review", 0)) >= 1, target_counts),
        check("反事实包含blocked结果", int(target_counts.get("blocked", 0)) >= 1, target_counts),
        check("仅全部门禁满足时可预演evidence_ready", int(target_counts.get("evidence_ready", 0)) == 1, target_counts),
        check("每条记录均不真实回写", all(item.get("是否真实回写状态") is False for item in results), results),
        check("每条记录均不写正式业务库", all(item.get("是否写正式业务库") is False for item in results), results),
        check("每条记录均不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in results), results),
        check("下一步队列指向整改清单", contains(data.get("下一步低风险队列", []), "整改清单"), data.get("下一步低风险队列", [])),
        check("安全边界全部关闭", all(safety.get(key) is False for key in SAFETY_FALSE_KEYS), safety),
    ]

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核状态机反事实演练验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核状态机反事实演练验收",
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
