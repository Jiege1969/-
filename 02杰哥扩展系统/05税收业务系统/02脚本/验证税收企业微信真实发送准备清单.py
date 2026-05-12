# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
CHECKLIST_JSON = OUT_DIR / "税收企业微信真实发送准备清单_最新.json"
CHECKLIST_MD = OUT_DIR / "税收企业微信真实发送准备清单_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信真实发送准备清单验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信真实发送准备清单验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checklist = load_json(CHECKLIST_JSON)
    safety = checklist.get("安全边界", {})
    required_fields = ["人工复核人", "复核时间", "接收范围", "允许发送场景", "回滚负责人", "异常联系人", "备注"]
    checks = [
        check("准备清单JSON存在", CHECKLIST_JSON.exists(), str(CHECKLIST_JSON)),
        check("准备清单Markdown存在", CHECKLIST_MD.exists(), str(CHECKLIST_MD)),
        check("当前放行状态为pending", checklist.get("放行状态") == "pending", checklist.get("放行状态")),
        check("上线前必填字段齐备", all(field in checklist.get("上线前必填", {}) for field in required_fields), checklist.get("上线前必填", {})),
        check("必须确认事项不少于5项", len(checklist.get("上线前必须确认", [])) >= 5, checklist.get("上线前必须确认", [])),
        check("不得填写内容包含凭据和电子税务局", any("Webhook" in item for item in checklist.get("不得填写内容", [])) and any("电子税务局" in item for item in checklist.get("不得填写内容", [])), checklist.get("不得填写内容", [])),
        check("当前未真实发送", safety.get("是否企业微信真实发送") is False, safety),
        check("当前未读取凭据", safety.get("是否读取凭据") is False, safety),
        check("未生成正式税务结论", safety.get("是否生成正式税务结论") is False, safety),
        check("未触发n8n或接办税系统", safety.get("是否触发n8n") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信真实发送准备清单验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信真实发送准备清单验收",
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
