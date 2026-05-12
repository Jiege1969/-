# -*- coding: utf-8 -*-
"""
名称：验证企业微信真实发送人工确认令受控写入.py
作用：验证公共受控发送器人工确认令当天有效且范围受控。
安全边界：只读确认令和写入报告；只写验收报告；不发送企业微信、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
CONFIRMATION = COMMON_ROOT / "01配置" / "企业微信真实发送人工确认令.json"
OUT_DIR = ROOT / "03数据" / "240企业微信真实发送人工确认令受控写入"


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
    data = load_json(CONFIRMATION)
    report = load_json(OUT_DIR / "企业微信真实发送人工确认令受控写入_最新.json")
    today = datetime.now().strftime("%Y-%m-%d")
    checks = [
        check(CONFIRMATION.exists(), "确认令文件存在", str(CONFIRMATION)),
        check(data.get("确认状态") == "已人工确认", "确认状态为已人工确认", data.get("确认状态")),
        check(data.get("允许真实发送") is True, "允许真实发送为True", data.get("允许真实发送")),
        check(data.get("有效日期") == today, "有效日期为今天", data.get("有效日期")),
        check(data.get("确认令") == f"ALLOW_WECOM_REAL_SEND_{datetime.now().strftime('%Y%m%d')}", "确认令匹配当天", data.get("确认令")),
        check(data.get("允许接收人") == ["ChenXiaoJie"], "仅允许本人白名单", data.get("允许接收人")),
        check(set(data.get("允许消息类型", [])) == {"text", "markdown"}, "仅允许text和markdown", data.get("允许消息类型")),
        check(data.get("允许n8n") is False, "禁止n8n", data.get("允许n8n")),
        check(data.get("允许自动交易") is False, "禁止自动交易", data.get("允许自动交易")),
        check(report.get("结论") == "完成", "写入报告存在且完成", report.get("结论")),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "企业微信真实发送人工确认令受控写入验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式库": False,
            "重启正式服务": False,
        },
    }
    write_json(OUT_DIR / "企业微信真实发送人工确认令受控写入验收_最新.json", result)
    lines = [
        "# 企业微信真实发送人工确认令受控写入验收",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
    ]
    write_text(OUT_DIR / "企业微信真实发送人工确认令受控写入验收_最新.md", "\n".join(lines))
    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
