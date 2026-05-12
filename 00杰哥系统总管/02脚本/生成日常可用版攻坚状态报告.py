# -*- coding: utf-8 -*-
"""
名称：生成日常可用版攻坚状态报告.py
作用：汇总当前总体验收、首批执行器、调度适配、n8n禁用工作流和真实动作闸口，生成日常可用版攻坚状态报告。
触发方式：python 生成日常可用版攻坚状态报告.py
依赖：Python 标准库；最新v3总体验收、当前总体进度报告、首批执行器就绪总表、调度适配表、n8n禁用工作流草案汇总。
所属系统：00杰哥系统总管
安全边界：只读取状态并生成报告；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建日常可用版攻坚状态报告脚本。
标识：daily-usable-assault-status-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_json_if_exists(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {}


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [item for item in root.rglob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    acceptance_path = latest_file(manager / "04日志" / "acceptance", "v3-acceptance-最新.json")
    progress_path = manager / "03数据" / "阶段判定" / "当前总体进度报告_最新.json"
    executor_table_path = manager / "03数据" / "小流量只读执行" / "首批执行器就绪总表_最新.json"
    adapter_path = manager / "03数据" / "小流量只读执行" / "首批执行器调度适配表_最新.json"
    workflow_summary_path = root / "01杰哥智能系统" / "03数据" / "工作流草案" / "首批执行器禁用工作流" / "首批执行器n8n禁用工作流草案汇总_最新.json"
    final_gate_path = manager / "03数据" / "小流量只读执行" / "真实小流量动作最终闸口报告_最新.json"
    acceptance = load_json_if_exists(acceptance_path) if acceptance_path else {}
    progress = load_json_if_exists(progress_path)
    executor_table = load_json_if_exists(executor_table_path)
    adapter = load_json_if_exists(adapter_path)
    workflow_summary = load_json_if_exists(workflow_summary_path)
    final_gate = load_json_if_exists(final_gate_path)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "日常可用版攻坚状态",
        "总体进度": progress.get("进度估算", {}),
        "总体验收": {
            "路径": str(acceptance_path) if acceptance_path else "",
            "汇总": acceptance.get("summary", {}),
        },
        "首批执行器": executor_table.get("汇总", {}),
        "调度适配": adapter.get("汇总", {}),
        "n8n禁用工作流草案": workflow_summary.get("汇总", {}),
        "最终闸口": {
            "路径": str(final_gate_path),
            "是否允许真实动作": final_gate.get("是否允许真实动作"),
        },
        "已具备": [
            "R01/R02/R03冻结执行器",
            "首批执行器就绪总表",
            "调度适配表",
            "n8n禁用工作流草案",
            "总体验收闭环"
        ],
        "仍未开放": [
            "真实联网",
            "正式库写入",
            "正式文档输出",
            "n8n真实触发",
            "企业微信真实发送",
            "税收业务",
            "旧系统写入"
        ],
        "下一步施工面": [
            "生成真实动作前最小样本包",
            "生成只读请求沙箱日志结构",
            "完善企业微信沙箱消息回环",
            "继续保持税收业务暂停"
        ],
        "当前结论": "日常可用版攻坚状态已可量化追踪；真实动作仍默认关闭。",
    }
    output_dir = manager / "03数据" / "阶段判定"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "日常可用版攻坚状态报告_最新.json"
    latest = output_dir / "日常可用版攻坚状态报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"阶段": report["阶段"], "最终闸口允许": report["最终闸口"]["是否允许真实动作"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
