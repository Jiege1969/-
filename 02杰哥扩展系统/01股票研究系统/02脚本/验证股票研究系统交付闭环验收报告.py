# -*- coding: utf-8 -*-
"""
名称：验证股票研究系统交付闭环验收报告.py
作用：验收 237 股票研究系统交付闭环验收报告的证据完整性和安全边界。
安全边界：只读 237 报告和引用产物；只写 237 验收报告；不发企业微信、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "237股票研究系统交付闭环验收"
REPORT_JSON = OUT_DIR / "股票研究系统交付闭环验收报告_最新.json"
REPORT_MD = OUT_DIR / "股票研究系统交付闭环验收报告_最新.md"


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


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票研究系统交付闭环验收报告验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    data = load_json(REPORT_JSON)
    safety = data.get("安全边界", {})
    validations = data.get("验收结果", []) or []
    rollback = data.get("回滚证据", []) or []
    evidence = data.get("正式成交额证据", {})
    generated_paths = data.get("生成或修改的文件路径", []) or []

    pending_self_outputs = (
        "股票研究系统交付闭环验收报告验收_最新.json",
        "股票研究系统交付闭环验收报告验收_最新.md",
    )
    preexisting_paths = [
        path for path in generated_paths
        if path.endswith((".json", ".md", ".py"))
        and not path.endswith(pending_self_outputs)
    ]

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "237报告 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(data.get("总结论") == "通过", "总结论通过", str(data.get("总结论"))),
        check(len(validations) >= 13, "验收链路数量完整", f"数量={len(validations)}"),
        check(all(item.get("结论") == "通过" and item.get("失败数量") == 0 for item in validations), "所有引用验收均通过且失败为0", ""),
        check("19/19" in str(evidence.get("227影子增强快照", "")), "227保留19/19正式成交额证据", str(evidence.get("227影子增强快照", ""))),
        check("123" in str(evidence.get("233正式刷新后统计", "")) and "含正式成交额数量" in str(evidence.get("233正式刷新后统计", "")), "233保留正式底座全量成交额证据", str(evidence.get("233正式刷新后统计", ""))),
        check(any(item.get("名称") == "233历史K线刷新前备份" and item.get("存在") is True for item in rollback), "233刷新前备份存在", json.dumps(rollback, ensure_ascii=False)),
        check(any(item.get("存在") is True and "237" in item.get("路径", "") for item in rollback), "237本轮影子/对照备份存在", json.dumps(rollback, ensure_ascii=False)),
        check(all(Path(path).exists() for path in preexisting_paths), "报告列出的关键文件存在", ""),
        check(safety.get("发送企业微信") is False, "未发送企业微信", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("触发n8n") is False, "未触发n8n", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False and safety.get("下单") is False, "未调用券商接口且未自动交易/下单", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("重启正式服务") is False, "未重启正式服务", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("修改总管代码") is False and safety.get("修改知识库代码") is False and safety.get("修改进化系统代码") is False, "未修改非股票系统代码", json.dumps(safety, ensure_ascii=False)),
        check(data.get("股票系统剩余有效工时估算") == "0小时；后续仅为可选优化、灰度发送方案或维护增强。", "剩余工时估算明确", str(data.get("股票系统剩余有效工时估算"))),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票研究系统交付闭环验收报告验收",
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
            "下单": False,
            "写正式库": False,
            "重启正式服务": False,
            "修改总管代码": False,
            "修改知识库代码": False,
            "修改进化系统代码": False,
        },
    }
    write_json(OUT_DIR / "股票研究系统交付闭环验收报告验收_最新.json", report)
    write_text(OUT_DIR / "股票研究系统交付闭环验收报告验收_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "输出": str(OUT_DIR / "股票研究系统交付闭环验收报告验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
