# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
MATRIX_JSON = OUT_DIR / "税收企业微信上线就绪度矩阵_最新.json"
MATRIX_MD = OUT_DIR / "税收企业微信上线就绪度矩阵_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信上线就绪度矩阵验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信上线就绪度矩阵验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix = load_json(MATRIX_JSON)
    rows = matrix.get("门禁矩阵", [])
    names = {item.get("门禁") for item in rows}
    required_names = {
        "机器人终端绑定",
        "入口状态与发送放行",
        "消息预演",
        "消息合规审查",
        "上线变更单",
        "凭据接入预检",
        "接收范围与消息分级",
        "应急停用与回滚预案",
        "人工放行准备清单",
        "发送门禁与审计",
    }
    safety = matrix.get("安全边界", {})
    checks = [
        check("上线矩阵JSON存在", MATRIX_JSON.exists(), str(MATRIX_JSON)),
        check("上线矩阵Markdown存在", MATRIX_MD.exists(), str(MATRIX_MD)),
        check("门禁矩阵包含10项", len(rows) >= 10 and required_names.issubset(names), rows),
        check("当前结论不得真实发送", matrix.get("上线结论") == "不得真实发送" and matrix.get("真实发送允许") is False, {"结论": matrix.get("上线结论"), "真实发送允许": matrix.get("真实发送允许")}),
        check("存在阻断门禁", matrix.get("阻断门禁数量", 0) >= 1, matrix.get("当前阻断", [])),
        check("机器人终端绑定已通过", any(item.get("门禁") == "机器人终端绑定" and item.get("是否通过") is True for item in rows), rows),
        check("消息预演和合规审查已通过", all(item.get("是否通过") for item in rows if item.get("门禁") in {"消息预演", "消息合规审查"}), rows),
        check("变更单、凭据、接收范围、回滚或人工放行至少一项阻断", any(not item.get("是否通过") for item in rows if item.get("门禁") in {"上线变更单", "凭据接入预检", "接收范围与消息分级", "应急停用与回滚预案", "人工放行准备清单", "入口状态与发送放行"}), rows),
        check("发送门禁保持已阻断但验收通过", any(item.get("门禁") == "发送门禁与审计" and item.get("是否通过") is True and "已阻断" in item.get("状态", "") for item in rows), rows),
        check("未联网未读取凭据未真实发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信上线就绪度矩阵验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信上线就绪度矩阵验收",
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
