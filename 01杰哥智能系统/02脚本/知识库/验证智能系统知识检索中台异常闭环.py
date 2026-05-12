# -*- coding: utf-8 -*-
"""
名称：验证智能系统知识检索中台异常闭环.py
作用：验收知识检索、中台能力和异常处理闭环是否形成可追溯、可拒答、可阻断的本地闭环。
触发方式：python 验证智能系统知识检索中台异常闭环.py
依赖：Python 标准库；执行智能系统知识检索中台异常闭环.py。
所属系统：01杰哥智能系统/知识库
安全边界：只运行本地验收；不修改总管进度口径、不修改扩展系统业务脚本、不修改进化系统规则代码、不发企业微信、不触发 n8n。
标识：smart-system-knowledge-middleware-exception-loop-verify
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
GENERATOR = SMART_ROOT / "02脚本" / "知识库" / "执行智能系统知识检索中台异常闭环.py"
REPORT_JSON = SMART_ROOT / "03数据" / "知识库" / "13知识检索中台异常闭环" / "智能系统知识检索中台异常闭环_最新.json"
REPORT_MD = SMART_ROOT / "03数据" / "知识库" / "13知识检索中台异常闭环" / "智能系统知识检索中台异常闭环_最新.md"
LOG_DIR = SMART_ROOT / "04日志" / "知识库"


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
        timeout=180,
        env=env,
    )
    report = load_json(REPORT_JSON, {})
    summary = report.get("汇总", {})
    cases = report.get("用例结果", [])
    safety = report.get("安全边界", {})
    answered = [item for item in cases if item.get("闭环判定", {}).get("可追溯回答")]
    refused = [item for item in cases if item.get("闭环判定", {}).get("无证据拒答")]
    blocked = [item for item in cases if item.get("闭环判定", {}).get("高风险阻断")]

    checks: list[dict[str, Any]] = []
    add_check(checks, "执行脚本返回码为0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", REPORT_JSON.exists(), str(REPORT_JSON))
    add_check(checks, "最新Markdown存在", REPORT_MD.exists(), str(REPORT_MD))
    add_check(checks, "总体状态通过", summary.get("总体状态") == "通过", summary)
    add_check(checks, "四个闭环用例齐全", summary.get("用例数量") == 4 and len(cases) == 4, [item.get("用例ID") for item in cases])
    add_check(checks, "至少两个可追溯回答", summary.get("可追溯回答数量", 0) >= 2 and len(answered) >= 2, summary)
    add_check(checks, "至少一个无证据拒答", summary.get("无证据拒答数量", 0) >= 1 and len(refused) >= 1, summary)
    add_check(checks, "至少一个高风险阻断", summary.get("高风险阻断数量", 0) >= 1 and len(blocked) >= 1, summary)
    add_check(
        checks,
        "可追溯回答均含来源文件分块摘录",
        all(
            ref.get("来源文件存在") is True and ref.get("分块序号") and ref.get("证据摘录") and Path(ref.get("来源文件", "")).exists()
            for item in answered
            for ref in item.get("中台输出", {}).get("来源引用", [])
        ),
        answered,
    )
    add_check(
        checks,
        "拒答和阻断均不伪造来源",
        all(not item.get("中台输出", {}).get("来源引用") for item in refused + blocked),
        refused + blocked,
    )
    add_check(
        checks,
        "每个用例都有任务识别和能力规划",
        all(item.get("任务识别", {}).get("任务类型") and item.get("能力规划", {}).get("能力名") for item in cases),
        cases,
    )
    add_check(checks, "知识库索引存在且有分块", report.get("知识库状态", {}).get("索引存在") is True and report.get("知识库状态", {}).get("分块数量", 0) > 0, report.get("知识库状态", {}))
    add_check(checks, "未修改总管进度配置", safety.get("修改总管进度配置") is False, safety)
    add_check(checks, "未修改扩展系统业务脚本", safety.get("修改扩展系统业务脚本") is False, safety)
    add_check(checks, "未修改进化系统规则代码", safety.get("修改进化系统规则代码") is False, safety)
    add_check(checks, "未发送企业微信真实消息", safety.get("发送企业微信真实消息") is False and summary.get("企业微信真实发送") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False and summary.get("触发n8n") is False, safety)
    add_check(checks, "未调用券商接口且未自动交易", safety.get("调用券商接口") is False and safety.get("自动交易") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式向量库") is False and safety.get("写正式数据库") is False and summary.get("写正式库") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    now = datetime.now()
    verify = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "smart-system-knowledge-middleware-exception-loop-verify",
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "闭环报告": str(REPORT_JSON),
        "安全边界": safety,
    }
    output = LOG_DIR / "smart-system-knowledge-middleware-exception-loop-verify-最新.json"
    latest = output
    write_json(latest, verify)
    print(json.dumps({"结论": verify["结论"], "通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
