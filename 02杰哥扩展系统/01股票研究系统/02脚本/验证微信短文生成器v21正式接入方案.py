# -*- coding: utf-8 -*-
"""
名称：验证微信短文生成器v21正式接入方案.py
作用：验收微信短文生成器 v2.1 正式接入方案是否覆盖字段、阶段、回滚和安全边界。
触发方式：python 验证微信短文生成器v21正式接入方案.py
安全边界：只读方案产物；只写验收报告；不改正式入口；不重启服务；不发送企业微信；不触发 n8n；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "217微信短文生成器v21接入方案"
PLAN_JSON = OUT_DIR / "微信短文生成器v21正式接入方案_最新.json"
PLAN_MD = OUT_DIR / "微信短文生成器v21正式接入方案_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    plan = load_json(PLAN_JSON) if PLAN_JSON.exists() else {}
    md = load_text(PLAN_MD) if PLAN_MD.exists() else ""
    text = json.dumps(plan, ensure_ascii=False) + "\n" + md
    mapping = plan.get("字段映射", [])
    steps = plan.get("分阶段接入步骤", [])
    safety = plan.get("安全边界", {})
    forbidden = "\n".join(plan.get("禁止动作", []))

    required_fields = ["股票名称和一句话结论", "逻辑", "财务", "观察条件", "转强条件", "失败条件", "风险", "详情路径"]
    checks = [
        check(PLAN_JSON.exists() and PLAN_MD.exists(), "方案 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(all(any(row.get("目标字段") == field for row in mapping) for field in required_fields), "字段映射覆盖6+1短文和详情路径", ",".join(required_fields)),
        check(len(steps) >= 4 and steps[0].get("名称") == "影子生成器接入", "接入步骤从影子生成器开始", ""),
        check("特性开关" in text and "默认关闭" in text, "正式接入要求特性开关默认关闭", ""),
        check("回滚" in text and "旧模板" in text, "回滚路径明确", ""),
        check("成交额若为估算口径" in text and "不得装作精确事实" in text, "成交额估算降级规则明确", ""),
        check("不得输出强推荐" in text, "数据缺失时不得强推荐", ""),
        check("不得重启 `19300`" in forbidden and "不得重启 `19302`" in forbidden, "正式入口重启被禁止", ""),
        check("不得发送企业微信真实消息" in forbidden and "不得触发 n8n 正式工作流" in forbidden, "真实发送和 n8n 被禁止", ""),
        check("不得调用券商接口" in forbidden and "自动交易" in forbidden, "交易动作被禁止", ""),
        check(all(value is False for value in safety.values()), "安全边界全部为False", json.dumps(safety, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文生成器v21正式接入方案验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        },
    }
    latest_json = OUT_DIR / "微信短文生成器v21正式接入方案验收_最新.json"
    latest_md = OUT_DIR / "微信短文生成器v21正式接入方案验收_最新.md"
    lines = [
        "# 微信短文生成器 v2.1 正式接入方案验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, report)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
