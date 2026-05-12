# -*- coding: utf-8 -*-
"""
名称：验证01智能系统中台补齐清单与验收报告.py
作用：验收 01 智能系统中台补齐清单是否覆盖任务理解、能力路由、状态读取、知识/证据读取、异常处理和验收报告输出。
触发方式：python 验证01智能系统中台补齐清单与验收报告.py
依赖：Python 标准库；生成01智能系统中台补齐清单与验收报告.py。
所属系统：01杰哥智能系统/智能体大脑
安全边界：只运行本地验收；不修改总管进度口径、不修改 02 扩展系统业务脚本、不修改 03 进化系统规则代码、不发企业微信、不触发 n8n。
标识：smart-system-middleware-completion-report-verify
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SMART_ROOT = Path("D:/杰哥智能化系统/01杰哥智能系统")
GENERATOR = SMART_ROOT / "02脚本" / "智能体大脑" / "生成01智能系统中台补齐清单与验收报告.py"
REPORT_JSON = SMART_ROOT / "03数据" / "运行状态" / "01智能系统中台补齐清单与验收报告_最新.json"
REPORT_MD = SMART_ROOT / "03数据" / "运行状态" / "01智能系统中台补齐清单与验收报告_最新.md"
LOG_DIR = SMART_ROOT / "04日志" / "智能体大脑"


REQUIRED_CAPABILITIES = {"任务理解", "能力路由", "状态读取", "知识/证据读取接口", "异常处理", "验收报告输出"}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "说明": detail})


def main() -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=str(GENERATOR.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
        env=env,
    )
    report = load_json(REPORT_JSON, {})
    summary = report.get("汇总", {})
    matrix = report.get("中台最小能力矩阵", [])
    samples = report.get("小样本验收", [])
    safety = report.get("安全边界", {})
    capability_names = {item.get("能力") for item in matrix}

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码为0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", REPORT_JSON.exists(), str(REPORT_JSON))
    add_check(checks, "最新Markdown存在", REPORT_MD.exists(), str(REPORT_MD))
    add_check(checks, "总体状态通过", summary.get("总体状态") == "通过", summary)
    add_check(checks, "六项中台最小能力齐全", REQUIRED_CAPABILITIES.issubset(capability_names), list(capability_names))
    add_check(checks, "六项能力均已具备", summary.get("已具备数量") == 6 and summary.get("待补齐数量") == 0 and all(item.get("状态") == "已具备" for item in matrix), matrix)
    add_check(checks, "每项能力都有证据文件", all(item.get("当前证据") and all(Path(path).exists() for path in item.get("当前证据", []) if "最新.json" not in path or path) for item in matrix), matrix)
    add_check(checks, "小样本覆盖至少三个输入", len(samples) >= 3, samples)
    add_check(checks, "小样本均有任务识别能力规划", all(item.get("任务识别", {}).get("任务类型") and item.get("能力规划", {}).get("能力名") for item in samples), samples)
    add_check(checks, "小样本包含高风险阻断", any(item.get("异常处理", {}).get("是否高风险") is True and "阻断" in item.get("异常处理", {}).get("处理方式", "") for item in samples), samples)
    add_check(checks, "中台异常闭环验收通过", report.get("中台异常闭环验收", {}).get("returncode") == 0, report.get("中台异常闭环验收", {}))
    add_check(checks, "备份清单已生成", bool(report.get("备份", {}).get("备份目录")) and Path(report.get("备份", {}).get("备份目录", "")).exists(), report.get("备份", {}))
    add_check(checks, "读取来源均存在", all(item.get("存在") is True for item in report.get("读取来源", {}).values()), report.get("读取来源", {}))
    add_check(checks, "未修改00总管进度口径文件", safety.get("修改00总管进度口径文件") is False and summary.get("修改总管进度口径") is False, safety)
    add_check(checks, "未修改02扩展系统业务脚本", safety.get("修改02扩展系统业务脚本") is False and summary.get("修改02扩展系统业务脚本") is False, safety)
    add_check(checks, "未修改03进化系统规则文件", safety.get("修改03进化系统规则文件") is False and summary.get("修改03进化系统规则代码") is False, safety)
    add_check(checks, "未发送企业微信真实消息", safety.get("发送企业微信真实消息") is False and summary.get("企业微信真实发送") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False and summary.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口且未自动交易", safety.get("调用券商接口") is False and safety.get("自动交易") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式向量库") is False and safety.get("写正式数据库") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    now = datetime.now()
    verify = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "smart-system-middleware-completion-report-verify",
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "验收报告": str(REPORT_JSON),
        "安全边界": safety,
    }
    output = LOG_DIR / f"smart-system-middleware-completion-report-verify-{now.strftime('%Y%m%d-%H%M%S')}.json"
    latest = LOG_DIR / "smart-system-middleware-completion-report-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"结论": verify["结论"], "通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
