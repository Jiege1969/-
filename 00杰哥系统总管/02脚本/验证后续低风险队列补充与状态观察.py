# -*- coding: utf-8 -*-
"""
名称：验证后续低风险队列补充与状态观察.py
作用：验收后续低风险候选清单是否覆盖四条主线、阻断正式入口替换并保持安全边界。
触发方式：python 验证后续低风险队列补充与状态观察.py
安全边界：只读候选清单；只写验收报告；不触发执行器；不触发n8n；不发送企业微信；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "后续低风险队列补充与状态观察_最新.json"
REPORT_MD = OUT_DIR / "后续低风险队列补充与状态观察_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
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
    report = load_json(REPORT_JSON)
    md = load_text(REPORT_MD)
    text = json.dumps(report, ensure_ascii=False) + "\n" + md
    candidates = report.get("候选任务", [])
    candidate_codes = [item.get("编号") for item in candidates]
    safety = report.get("安全边界", {})

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "候选清单 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(all(code in candidate_codes for code in ["LR001", "LR002", "LR003", "LR004"]), "覆盖企业微信/知识库/执行器/进化四条主线", ",".join(candidate_codes)),
        check("BLOCK001" in candidate_codes, "正式入口替换阻断项存在", ""),
        check("必须停下报告" in text and "正式微信短文生成器替换运行入口" in text, "正式入口替换继续阻断", ""),
        check(report.get("可自动候选数量", 0) >= 1, "至少存在一个可自动低风险候选", str(report.get("可自动候选数量"))),
        check("用户重负载" in text or "重负载" in text or report.get("当前调度状态"), "记录当前调度状态", str(report.get("当前调度状态"))),
        check("不启动批量问答或入库" in text or "避免模型重任务" in text, "重负载下知识库降载口径明确", ""),
        check("不触发执行器" in text or "触发执行器" in json.dumps(safety, ensure_ascii=False), "不触发执行器边界明确", ""),
        check(all(value is False for value in safety.values()), "安全边界全部为False", json.dumps(safety, ensure_ascii=False)),
        check("不发送企业微信" in text or "发送企业微信" in json.dumps(safety, ensure_ascii=False), "不真实发送企业微信边界明确", ""),
        check("不自动交易" in text or "自动交易" in json.dumps(safety, ensure_ascii=False), "不自动交易边界明确", ""),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    validation = {
        "名称": "后续低风险队列补充与状态观察验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "触发执行器": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "重启19300": False,
            "重启19302": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "后续低风险队列补充与状态观察验收_最新.json"
    latest_md = OUT_DIR / "后续低风险队列补充与状态观察验收_最新.md"
    lines = [
        "# 后续低风险队列补充与状态观察验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, validation)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": validation["结论"],
        "通过数量": validation["通过数量"],
        "失败数量": validation["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
