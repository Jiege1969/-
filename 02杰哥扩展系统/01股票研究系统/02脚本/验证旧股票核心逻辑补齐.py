"""
名称：验证旧股票核心逻辑补齐.py
作用：离线验证新股票助手已吸收旧系统的股票识别接口和技术分析接口核心逻辑。
触发方式：python 验证旧股票核心逻辑补齐.py
依赖：Python标准库；股票助手入口.py；旧股票系统核心逻辑吸收差异报告.md。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读验证新系统文件；不启动服务；不刷新行情；不触发n8n；不发送企业微信；不写旧系统；不接交易接口。
创建/修改记录：2026-04-28 创建，用于验证旧系统核心逻辑吸收落地。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_PATH = ROOT / "02脚本" / "股票助手入口.py"
DIFF_REPORT_PATH = ROOT / "03数据" / "08草案吸收" / "旧股票系统核心逻辑吸收差异报告.md"


def load_assistant_module():
    spec = importlib.util.spec_from_file_location("stock_assistant_entry", ASSISTANT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载股票助手入口模块")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_assistant_module()
    source = ASSISTANT_PATH.read_text(encoding="utf-8")

    checks: list[dict[str, object]] = []

    recognition = module.build_recognition("分析新易盛")
    checks.append({
        "项目": "股票识别核心函数",
        "通过": recognition.get("状态") == "完成" and bool(recognition.get("识别结果")),
        "摘要": recognition,
    })

    technical = module.build_technical_analysis("新易盛", refresh=False)
    checks.append({
        "项目": "技术分析核心函数",
        "通过": technical.get("状态") == "完成" and bool(technical.get("技术指标")),
        "摘要": {
            "状态": technical.get("状态"),
            "股票": technical.get("股票"),
            "技术指标状态": (technical.get("技术指标") or {}).get("状态"),
            "分层": (technical.get("规则判断") or {}).get("分层"),
        },
    })

    checks.append({
        "项目": "识别接口路径",
        "通过": '"/识别", "/recognize"' in source,
        "摘要": "入口文件包含识别接口路径",
    })
    checks.append({
        "项目": "技术分析接口路径",
        "通过": '"/技术分析", "/technical"' in source,
        "摘要": "入口文件包含技术分析接口路径",
    })
    checks.append({
        "项目": "差异报告",
        "通过": DIFF_REPORT_PATH.exists(),
        "摘要": str(DIFF_REPORT_PATH),
    })

    passed = sum(1 for item in checks if item["通过"])
    report = {
        "标识": "old-stock-core-logic-assimilation-diff-verify",
        "检查数": len(checks),
        "通过数": passed,
        "结果": checks,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
