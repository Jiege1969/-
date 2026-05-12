# -*- coding: utf-8 -*-
"""
验证股票自动交易屏蔽加固报告。

安全边界：
- 只读加固报告、配置、脚本编译状态。
- 只写验收报告。
"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT.parents[1]
MANAGER = SYSTEM_ROOT / "00杰哥系统总管"
OUT_DIR = ROOT / "03数据" / "243股票自动交易屏蔽加固"

REPORT_JSON = OUT_DIR / "股票自动交易屏蔽加固报告_最新.json"
REPORT_MD = OUT_DIR / "股票自动交易屏蔽加固报告_最新.md"
VERIFY_JSON = OUT_DIR / "股票自动交易屏蔽加固验收_最新.json"
VERIFY_MD = OUT_DIR / "股票自动交易屏蔽加固验收_最新.md"

SCRIPTS = [
    ROOT / "02脚本" / "股票助手入口.py",
    ROOT / "02脚本" / "模拟企业微信股票查询.py",
    ROOT / "02脚本" / "验证股票交易指令拦截.py",
    ROOT / "02脚本" / "生成股票自动交易屏蔽加固报告.py",
    ROOT / "02脚本" / "验证股票自动交易屏蔽加固报告.py",
]

CONFIGS = [
    ROOT / "01配置" / "股票分析系统硬闸门配置.json",
    ROOT / "01配置" / "L7可交易过滤池规则.json",
    MANAGER / "01配置" / "股票分析非交易边界规则.json",
    MANAGER / "01配置" / "股票自动交易屏蔽总闸门规则.json",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def compile_ok(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    report = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    compile_results = []
    for script in SCRIPTS:
        ok, error = compile_ok(script)
        compile_results.append({"脚本": str(script), "通过": ok, "错误": error})
    config_results = []
    for config in CONFIGS:
        data = load_json(config)
        config_results.append({"配置": str(config), "可解析": bool(data)})
    checks = [
        check(all(item["通过"] for item in compile_results), "关键脚本均可编译", compile_results),
        check(all(item["可解析"] for item in config_results), "关键配置均可解析", config_results),
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "加固报告JSON和Markdown存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "加固报告结论通过", report.get("结论")),
        check(not report.get("阻断项"), "加固报告无阻断项", report.get("阻断项")),
        check("只分析、不交易" in report.get("分析系统标准", ""), "分析系统标准写明只分析不交易", report.get("分析系统标准")),
        check("不调用券商接口" in md and "不自动交易" in md and "不下单" in md, "Markdown安全边界完整", ""),
        check(all(value is False for value in report.get("安全边界", {}).values()), "报告安全边界全部为false", report.get("安全边界", {})),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "股票自动交易屏蔽加固验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
            "写正式库": False,
        },
    }
    write_json(VERIFY_JSON, result)
    lines = [
        "# 股票自动交易屏蔽加固验收",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", "- 未发企业微信，未触发 n8n，未调用券商接口，未自动交易，未下单，未写正式库。", ""])
    write_text(VERIFY_MD, "\n".join(lines))
    print(json.dumps({"结果": result["结论"], "通过": result["通过数量"], "失败": result["失败数量"], "输出": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
