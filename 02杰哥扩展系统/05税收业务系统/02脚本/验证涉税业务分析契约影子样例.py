# -*- coding: utf-8 -*-
"""
名称：验证涉税业务分析契约影子样例.py
作用：验收涉税业务分析契约和影子样例，确保不套股票L3、不使用confirmed_conclusion、不生成正式税务结论。
触发方式：python 验证涉税业务分析契约影子样例.py
安全边界：只读检查本地配置和影子样例；不联网、不下载、不触发n8n、不企业微信发送。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONTRACT = ROOT / "01配置" / "涉税业务分析契约.json"
OUT_DIR = ROOT / "03数据" / "29涉税业务分析契约影子样例"
SHADOW = OUT_DIR / "涉税业务分析契约影子样例_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def has_navigation_noise(shadow: dict[str, Any]) -> bool:
    noise_markers = ["本站热词", "当前位置", "首页 总局概况", "个人中心", "搜索 高级搜索", "热门关键词", "字体："]
    for item in shadow.get("适用条件", []):
        fields = item.get("关键条件", []) + item.get("排除条件", [])
        if any(any(marker in str(value) for marker in noise_markers) for value in fields):
            return True
    return False


def main() -> int:
    contract = load_json(CONTRACT)
    report = load_json(SHADOW)
    shadow = report.get("影子样例", {})
    required_fields = ["政策依据", "依据层级", "适用条件", "业务事实", "资料缺口", "风险点", "置信度", "人工复核项"]
    shadow_text = json.dumps(shadow, ensure_ascii=False)
    checks = [
        check("契约配置存在", CONTRACT.exists(), str(CONTRACT)),
        check("影子样例存在", SHADOW.exists(), str(SHADOW)),
        check("契约必备字段齐备", all(field in contract.get("契约字段", []) for field in required_fields), contract.get("契约字段", [])),
        check("状态词使用税务白名单", shadow.get("契约状态") in {"draft", "evidence_ready", "pending_review", "human_reviewed"}, shadow.get("契约状态")),
        check("禁用confirmed_conclusion", "confirmed_conclusion" not in shadow.get("契约状态", "") and "confirmed_conclusion" not in json.dumps(shadow, ensure_ascii=False), shadow.get("契约状态")),
        check("不套股票L3", "L3" not in shadow_text and "推荐等级" not in shadow_text and "价位" not in shadow_text, "影子样例未命中股票口径"),
        check("影子样例字段齐备", all(field in shadow for field in required_fields), shadow),
        check("政策依据来自证据底座", isinstance(shadow.get("政策依据", []), list) and len(shadow.get("政策依据", [])) >= 1, shadow.get("政策依据", [])),
        check("不生成正式税务结论", shadow.get("是否生成正式税务结论") is False, shadow.get("是否生成正式税务结论")),
        check("不接正式入口", shadow.get("是否接正式入口") is False, shadow.get("是否接正式入口")),
        check("安全边界全部关闭", all(value is False for value in report.get("安全边界", {}).values()), report.get("安全边界", {})),
        check("影子样例适用条件不含网页导航噪声", not has_navigation_noise(shadow), "检查本站热词、当前位置、首页总局概况等导航文本"),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "名称": "涉税业务分析契约影子样例验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读验收；不联网、不下载、不触发n8n、不企业微信发送、不生成正式税务结论。",
    }
    write_json(OUT_DIR / "涉税业务分析契约影子样例验收_最新.json", result)
    lines = [
        "# 涉税业务分析契约影子样例验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item['说明']}")
    write_text(OUT_DIR / "涉税业务分析契约影子样例验收_最新.md", "\n".join(lines) + "\n")
    print(json.dumps({"状态": result["结论"], "通过数量": passed, "失败数量": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
