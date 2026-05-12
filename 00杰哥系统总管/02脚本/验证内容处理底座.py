"""
名称：验证内容处理底座.py
作用：验证内容处理系统配置、素材索引、批处理计划和转换预演是否满足第一阶段底座要求。
触发方式：python 验证内容处理底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只运行内容处理系统本地脚本；不改写、不删除、不移动素材，不执行真实批量转码。
创建/修改记录：2026-04-27 创建内容处理底座验收脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "04内容处理系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "内容处理验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "内容处理配置.json")
    rules = load_json(root / "01配置" / "内容批处理规则.json")
    switches = config.get("处理边界", {})
    index_script = root / "02脚本" / "生成内容素材索引.py"
    plan_script = root / "02脚本" / "生成内容批处理计划.py"
    preview_script = root / "02脚本" / "生成内容转换预演.py"
    index_result = run_script(index_script)
    plan_result = run_script(plan_script)
    preview_result = run_script(preview_script)

    latest_index = root / "03数据" / "02登记索引" / "内容素材索引_最新.json"
    latest_plan = root / "03数据" / "03批处理计划" / "内容批处理计划_最新.json"
    latest_preview = root / "03数据" / "04转换预演" / "内容转换预演_最新.json"
    index_data = load_json(latest_index) if latest_index.exists() else {}
    plan_data = load_json(latest_plan) if latest_plan.exists() else {}
    preview_data = load_json(latest_preview) if latest_preview.exists() else {}

    checks = [
        check("内容处理配置", "素材类型" in config and "处理边界" in config, config.get("阶段")),
        check("内容批处理规则", "任务类型" in rules and "阻断规则" in rules, [item.get("名称") for item in rules.get("任务类型", [])]),
        check("禁止改写原文件", switches.get("允许改写原文件") is False, switches),
        check("禁止删除原文件", switches.get("允许删除原文件") is False, switches),
        check("禁止移动原文件", switches.get("允许移动原文件") is False, switches),
        check("禁止批量转码", switches.get("允许批量转码") is False, switches),
        check("素材索引脚本执行", index_result.returncode == 0, (index_result.stdout or "").strip() or (index_result.stderr or "").strip()),
        check("批处理计划脚本执行", plan_result.returncode == 0, (plan_result.stdout or "").strip() or (plan_result.stderr or "").strip()),
        check("转换预演脚本执行", preview_result.returncode == 0, (preview_result.stdout or "").strip() or (preview_result.stderr or "").strip()),
        check("最新素材索引存在", latest_index.exists(), str(latest_index)),
        check("素材索引结构", "素材" in index_data and index_data.get("素材数量", 0) >= 1, index_data.get("统计")),
        check("最新批处理计划存在", latest_plan.exists(), str(latest_plan)),
        check("批处理计划结构", "任务" in plan_data and plan_data.get("是否允许真实处理") is False, {"任务数量": plan_data.get("任务数量")}),
        check("最新转换预演存在", latest_preview.exists(), str(latest_preview)),
        check(
            "转换预演结构",
            "预演" in preview_data
            and preview_data.get("是否执行真实转换") is False
            and preview_data.get("是否改写原文件") is False
            and preview_data.get("是否删除原文件") is False,
            {"预演数量": preview_data.get("预演数量")},
        ),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "content-processing-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"content-processing-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "content-processing-base-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
