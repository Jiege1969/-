# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
SCOPE_JSON = OUT_DIR / "税收企业微信接收范围与消息分级_最新.json"
SCOPE_MD = OUT_DIR / "税收企业微信接收范围与消息分级_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信接收范围与消息分级验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信接收范围与消息分级验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scope = load_json(SCOPE_JSON)
    safety = scope.get("安全边界", {})
    levels = scope.get("消息分级", [])
    required_fields = ["接收对象类型", "接收对象名称", "接收对象标识", "用途说明", "负责人", "启用时间", "停用时间"]
    checks = [
        check("接收范围JSON存在", SCOPE_JSON.exists(), str(SCOPE_JSON)),
        check("接收范围Markdown存在", SCOPE_MD.exists(), str(SCOPE_MD)),
        check("接收范围默认pending", scope.get("接收范围状态") == "pending", scope.get("接收范围状态")),
        check("白名单当前为空等待人工配置", scope.get("接收范围白名单") == [], scope.get("接收范围白名单")),
        check("待配置字段齐备", all(field in scope.get("待配置字段", []) for field in required_fields), scope.get("待配置字段", [])),
        check("消息分级不少于3类", len(levels) >= 3, levels),
        check("每个消息分级都有禁止内容", all(item.get("禁止内容") for item in levels), levels),
        check("当前消息分级为待复核草案", scope.get("当前消息分级建议", {}).get("等级") == "L2_review_request", scope.get("当前消息分级建议", {})),
        check("禁止范围包含全员和外部群", any("全员" in item or "@all" in item for item in scope.get("禁止接收范围", [])) and any("外部" in item or "客户群" in item for item in scope.get("禁止接收范围", [])), scope.get("禁止接收范围", [])),
        check("未真实发送未读取凭据", safety.get("是否企业微信真实发送") is False and safety.get("是否读取凭据") is False, safety),
        check("禁止全员群发和外部客户群", safety.get("是否允许全员群发") is False and safety.get("是否允许外部客户群") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信接收范围与消息分级验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信接收范围与消息分级验收",
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
