# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信单条真实灰度发送闭环报告.py
作用：验收 241 单条真实灰度发送闭环报告。
安全边界：只读报告和日志；只写验收报告；不再次发送、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "241股票企业微信单条真实灰度发送闭环"
REPORT_JSON = OUT_DIR / "股票企业微信单条真实灰度发送闭环报告_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    data = load_json(REPORT_JSON)
    evidence = data.get("关键证据", {})
    safety = data.get("安全边界", {})
    checks = [
        check(REPORT_JSON.exists(), "241报告存在", str(REPORT_JSON)),
        check(data.get("总结论") == "通过", "总结论通过", data.get("总结论")),
        check(data.get("真实发送成功") is True, "真实发送成功", data.get("真实发送成功")),
        check(data.get("目标用户") == "ChenXiaoJie", "目标用户为本人白名单", data.get("目标用户")),
        check(bool(evidence.get("企业微信msgid")), "企业微信msgid存在", evidence.get("企业微信msgid")),
        check(evidence.get("确认令有效") is True, "确认令有效", evidence.get("确认令有效")),
        check(evidence.get("计数未超限") is True, "计数未超限", data.get("当天计数")),
        check(safety.get("触发n8n") is False, "未触发n8n", safety),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False and safety.get("下单") is False, "未调用券商接口且未交易", safety),
        check(safety.get("群发") is False and safety.get("外部客户发送") is False, "未群发且未外部客户发送", safety),
        check(safety.get("输出密钥") is False, "未输出密钥", safety),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票企业微信单条真实灰度发送闭环报告验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
    }
    write_json(OUT_DIR / "股票企业微信单条真实灰度发送闭环报告验收_最新.json", report)
    write_text(OUT_DIR / "股票企业微信单条真实灰度发送闭环报告验收_最新.md", "\n".join([
        "# 股票企业微信单条真实灰度发送闭环报告验收",
        "",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
    ]))
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
