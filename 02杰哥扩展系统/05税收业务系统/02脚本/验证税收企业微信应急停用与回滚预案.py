# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PLAN_JSON = OUT_DIR / "税收企业微信应急停用与回滚预案_最新.json"
PLAN_MD = OUT_DIR / "税收企业微信应急停用与回滚预案_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信应急停用与回滚预案验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信应急停用与回滚预案验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plan = load_json(PLAN_JSON)
    safety = plan.get("安全边界", {})
    required_fields = ["回滚负责人", "异常联系人", "备用通知方式", "停用确认人", "恢复确认人", "最近一次演练时间"]
    checks = [
        check("回滚预案JSON存在", PLAN_JSON.exists(), str(PLAN_JSON)),
        check("回滚预案Markdown存在", PLAN_MD.exists(), str(PLAN_MD)),
        check("预案默认pending", plan.get("预案状态") == "pending", plan.get("预案状态")),
        check("紧急停用状态为false", plan.get("紧急停用状态") is False, plan.get("紧急停用状态")),
        check("触发停用情形不少于5项", len(plan.get("触发停用情形", [])) >= 5, plan.get("触发停用情形", [])),
        check("上线前必填字段齐备", all(field in plan.get("上线前必填", {}) for field in required_fields), plan.get("上线前必填", {})),
        check("停用步骤包含dry_run和放行关闭", any("dry_run_only" in item for item in plan.get("应急停用步骤", [])) and any("真实发送放行改为false" in item for item in plan.get("应急停用步骤", [])), plan.get("应急停用步骤", [])),
        check("恢复条件要求重新验收", any("重新验收通过" in item for item in plan.get("恢复发送前条件", [])), plan.get("恢复发送前条件", [])),
        check("禁止删除审计和绕过门禁", any("删除历史审计台账" in item for item in plan.get("禁止动作", [])) and any("绕过门禁" in item for item in plan.get("禁止动作", [])), plan.get("禁止动作", [])),
        check("未联网未发送未改入口", safety.get("是否联网") is False and safety.get("是否企业微信真实发送") is False and safety.get("是否修改入口状态") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信应急停用与回滚预案验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信应急停用与回滚预案验收",
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
