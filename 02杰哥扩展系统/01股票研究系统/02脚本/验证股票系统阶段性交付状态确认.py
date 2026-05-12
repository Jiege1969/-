# -*- coding: utf-8 -*-
"""
名称：验证股票系统阶段性交付状态确认.py
作用：验收 243 股票系统阶段性交付状态确认。
安全边界：只读取状态确认包，只写验收结果；不发送企业微信，不触发 n8n，不调用券商接口，不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "243股票系统阶段性交付状态确认"
REPORT_JSON = OUT_DIR / "股票系统阶段性交付状态确认_最新.json"


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
    safety = data.get("不改变的安全边界", {})
    checks = [
        check(REPORT_JSON.exists(), "状态确认包存在", str(REPORT_JSON)),
        check(data.get("结论") == "通过", "状态确认结论通过", data.get("结论")),
        check(data.get("当前状态") == "阶段性交付完成", "当前状态正确", data.get("当前状态")),
        check(data.get("状态口径") == "可验收、可回滚、可接正式口径", "状态口径正确", data.get("状态口径")),
        check(data.get("主线归类") == "不再归类为正在搭建主线", "主线归类正确", data.get("主线归类")),
        check("优化和灰度监控" in data.get("工时口径", ""), "工时口径正确", data.get("工时口径")),
        check(len(data.get("状态依据", [])) >= 4, "状态依据完整", data.get("状态依据", [])),
        check(len(data.get("后续工作口径", [])) >= 4, "后续工作口径完整", data.get("后续工作口径", [])),
        check(safety.get("触发n8n") is False, "n8n仍关闭", safety),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False and safety.get("下单") is False, "券商/交易/下单仍关闭", safety),
        check(safety.get("写正式库") is False and safety.get("重启正式服务") is False, "正式库/正式服务边界不变", safety),
        check(safety.get("修改总管代码") is False and safety.get("修改知识库代码") is False and safety.get("修改进化系统代码") is False, "未扩散修改非股票系统", safety),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "股票系统阶段性交付状态确认验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
    }
    write_json(OUT_DIR / "股票系统阶段性交付状态确认验收_最新.json", result)
    write_text(
        OUT_DIR / "股票系统阶段性交付状态确认验收_最新.md",
        "\n".join([
            "# 股票系统阶段性交付状态确认验收",
            "",
            f"- 结论：{result['结论']}",
            f"- 通过数量：{result['通过数量']}",
            f"- 失败数量：{result['失败数量']}",
            "",
        ]),
    )
    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
