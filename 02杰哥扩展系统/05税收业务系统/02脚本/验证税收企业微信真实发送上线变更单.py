# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
CHANGE_JSON = OUT_DIR / "税收企业微信真实发送上线变更单_最新.json"
CHANGE_MD = OUT_DIR / "税收企业微信真实发送上线变更单_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信真实发送上线变更单验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信真实发送上线变更单验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    change = load_json(CHANGE_JSON)
    safety = change.get("安全边界", {})
    required_fields = ["变更申请人", "申请时间", "上线窗口", "影响范围", "接收范围确认人", "人工复核负责人", "回滚负责人", "审批人", "审批时间", "审批意见"]
    evidence = change.get("验收依据", [])
    checks = [
        check("上线变更单JSON存在", CHANGE_JSON.exists(), str(CHANGE_JSON)),
        check("上线变更单Markdown存在", CHANGE_MD.exists(), str(CHANGE_MD)),
        check("变更状态默认pending", change.get("变更状态") == "pending", change.get("变更状态")),
        check("上线前必填字段齐备", all(field in change.get("上线前必填", {}) for field in required_fields), change.get("上线前必填", {})),
        check("验收依据不少于7项且均存在", len(evidence) >= 7 and all(item.get("是否存在") is True for item in evidence), evidence),
        check("上线前确认不少于6项", len(change.get("上线前确认", [])) >= 6, change.get("上线前确认", [])),
        check("禁止动作包含未审批改状态和绕过门禁", any("未审批" in item and "real_send_enabled" in item for item in change.get("禁止动作", [])) and any("绕过发送门禁" in item for item in change.get("禁止动作", [])), change.get("禁止动作", [])),
        check("变更单不自动放行入口", change.get("当前入口状态") != "real_send_enabled" and change.get("当前真实发送放行") is False, {"入口状态": change.get("当前入口状态"), "真实发送放行": change.get("当前真实发送放行")}),
        check("未联网未读取凭据未发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未修改入口状态", safety.get("是否修改入口状态") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信真实发送上线变更单验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信真实发送上线变更单验收",
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
