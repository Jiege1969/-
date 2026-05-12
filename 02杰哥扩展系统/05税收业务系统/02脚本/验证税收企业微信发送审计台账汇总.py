# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
SUMMARY_JSON = OUT_DIR / "税收企业微信发送审计台账汇总_最新.json"
SUMMARY_MD = OUT_DIR / "税收企业微信发送审计台账汇总_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信发送审计台账汇总验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信发送审计台账汇总验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = load_json(SUMMARY_JSON)
    safety = summary.get("安全边界", {})
    latest = summary.get("最近一次审计", {})
    checks = [
        check("审计汇总JSON存在", SUMMARY_JSON.exists(), str(SUMMARY_JSON)),
        check("审计汇总Markdown存在", SUMMARY_MD.exists(), str(SUMMARY_MD)),
        check("台账记录不少于1条", summary.get("台账记录数量", 0) >= 1, summary.get("台账记录数量")),
        check("可读取审计报告不少于1份", summary.get("可读取审计报告数量", 0) >= 1, summary.get("可读取审计报告数量")),
        check("当前无真实发送记录", summary.get("真实发送数量", 999) == 0 and summary.get("是否存在真实发送") is False, {"真实发送数量": summary.get("真实发送数量"), "是否存在真实发送": summary.get("是否存在真实发送")}),
        check("存在阻断记录", summary.get("阻断数量", 0) >= 1, summary.get("阻断数量")),
        check("最近一次审计为已阻断", latest.get("结论") == "已阻断" and latest.get("是否真实发送") is False, latest),
        check("最近一次有未通过门禁", len(latest.get("未通过门禁", [])) >= 1, latest.get("未通过门禁", [])),
        check("未命中敏感信息", summary.get("敏感信息命中报告") == [], summary.get("敏感信息命中报告")),
        check("未联网未读取凭据未发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未修改审计台账", safety.get("是否修改审计台账") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信发送审计台账汇总验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信发送审计台账汇总验收",
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
