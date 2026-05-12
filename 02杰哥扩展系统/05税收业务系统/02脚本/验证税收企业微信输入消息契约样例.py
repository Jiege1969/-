# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONTRACT = ROOT / "01配置" / "税收企业微信输入消息契约.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
SAMPLE_JSON = OUT_DIR / "税收企业微信输入消息契约样例_最新.json"
SAMPLE_MD = OUT_DIR / "税收企业微信输入消息契约样例_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信输入消息契约样例验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信输入消息契约样例验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract = load_json(CONTRACT)
    sample = load_json(SAMPLE_JSON)
    item = sample.get("输入样例", {})
    safety = sample.get("安全边界", {})
    required = set(contract.get("必填字段", []))
    present = set(item.keys())
    missing = sorted(required - present)
    checks = [
        check("输入契约存在", CONTRACT.exists(), str(CONTRACT)),
        check("输入样例JSON存在", SAMPLE_JSON.exists(), str(SAMPLE_JSON)),
        check("输入样例Markdown存在", SAMPLE_MD.exists(), str(SAMPLE_MD)),
        check("机器人名称为杰哥工作秘书", item.get("机器人名称") == "杰哥工作秘书", item.get("机器人名称")),
        check("必填字段齐备", not missing, missing),
        check("输入状态合法", item.get("输入状态") in contract.get("输入状态词", []), item.get("输入状态")),
        check("未使用禁用状态词", item.get("输入状态") not in contract.get("禁用状态词", []), item.get("输入状态")),
        check("进入证据匹配待处理状态", item.get("输入状态") == "pending_evidence_match", item.get("输入状态")),
        check("脱敏状态已标记", item.get("脱敏状态") == "masked", item.get("脱敏状态")),
        check("业务事实和附件提示齐备", isinstance(item.get("业务事实"), dict) and isinstance(item.get("附件提示"), dict), {"业务事实": item.get("业务事实"), "附件提示": item.get("附件提示")}),
        check("禁止动作包含办税执行和正式意见", any("申报" in action or "退税" in action or "开票" in action for action in item.get("禁止动作", [])) and any("正式税务意见" in action for action in item.get("禁止动作", [])), item.get("禁止动作", [])),
        check("未接真实回调未发送", safety.get("是否接收真实企业微信回调") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未联网未读取凭据", safety.get("是否联网") is False and safety.get("是否读取凭据") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for row in checks if row["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信输入消息契约样例验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信输入消息契约样例验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for row in checks:
        lines.append(f"- {row['检查项']}：{row['结果']}。{row['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
