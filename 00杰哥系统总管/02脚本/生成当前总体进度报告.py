# -*- coding: utf-8 -*-
"""
名称：生成当前总体进度报告.py
作用：按统一进度口径汇总当前总体验收、基础可用版、股票研究系统、无人值守机制、进化清理闸口和真实动作关闭状态，生成面向总体目标的进度报告。
触发方式：python 生成当前总体进度报告.py
依赖：Python标准库；进度口径规则.json；最新v3总体验收日志；最新阶段判定日志；股票研究系统状态摘要；小流量只读执行日志。
所属系统：00杰哥系统总管
安全边界：只读取日志并生成进度报告；不联网；不写正式库；不触发n8n；不发送企业微信；不接入税收真实业务；不写入旧系统。
创建/修改记录：2026-04-27 创建当前总体进度报告脚本；2026-04-28 更新无人值守与进化清理闸口进度口径；2026-04-28 统一进度口径为范围值。
标识：current-progress-report-generate
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    files = [item for item in root.rglob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def load_if_exists(path: Path | None) -> dict[str, Any]:
    return load_json(path) if path and path.exists() else {}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    acceptance_path = latest_file(manager / "04日志" / "acceptance", "v3-acceptance-最新.json")
    stage_path = latest_file(manager / "03数据" / "阶段判定", "基础可用版完成判定_*.json")
    final_gate_path = manager / "03数据" / "小流量只读执行" / "真实小流量动作最终闸口报告_最新.json"
    executor_path = manager / "03数据" / "无人值守守护" / "无人值守任务执行器骨架报告_最新.json"
    cleanup_path = root / "03杰哥进化系统" / "03数据" / "06清理闸口" / "经验样本价值清理闸口报告_最新.json"
    progress_rule_path = manager / "01配置" / "进度口径规则.json"
    stock_status_path = root / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json"

    acceptance = load_if_exists(acceptance_path)
    stage = load_if_exists(stage_path)
    final_gate = load_if_exists(final_gate_path)
    executor = load_if_exists(executor_path)
    cleanup = load_if_exists(cleanup_path)
    progress_rules = load_if_exists(progress_rule_path)
    stock_status = load_if_exists(stock_status_path)
    current_progress = progress_rules.get("当前进度口径", {})

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体目标": "多功能智能体中台",
        "当前所在步骤": "基础可用版持续收口；股票研究系统已交付使用并完成图形化星级优化；日常入口操作索引和企业微信统一指令路由预演已纳入闭环；真实动作仍默认关闭。",
        "进度口径说明": {
            "规则文件": str(progress_rule_path),
            "核心原则": progress_rules.get("核心原则", []),
            "禁止混用": progress_rules.get("禁止混用", []),
            "说明": "以下进度均为范围值。总体进度、当前阶段进度、子系统进度分开表达，避免口径混用。"
        },
        "进度估算": {
            "多功能智能体总体": current_progress.get("多功能智能体总体", {}),
            "基础可用版阶段": current_progress.get("基础可用版阶段", {}),
            "股票研究系统": current_progress.get("股票研究系统", {}),
            "真实攻坚前门禁百分比": 100,
            "无人值守计划编排百分比": 55,
            "进化样本提炼清理百分比": 62,
            "小流量真实执行百分比": 10,
            "无人值守稳定运行百分比": 5
        },
        "时间估算": {
            "到日常可用多功能智能体还需小时": "5-16",
            "到稳定智能体中台还需小时": "36-56",
            "到多功能智能体终局还需小时": "90-150"
        },
        "最新总体验收": {
            "路径": str(acceptance_path) if acceptance_path else "",
            "汇总": acceptance.get("summary", {})
        },
        "基础阶段判定": {
            "路径": str(stage_path) if stage_path else "",
            "完成判定": stage.get("完成判定"),
            "阶段性工作进度百分比": stage.get("阶段性工作进度百分比")
        },
        "股票研究系统状态摘要": {
            "路径": str(stock_status_path),
            "重点关注池数量": stock_status.get("重点关注池数量"),
            "行情快照数量": stock_status.get("行情快照数量"),
            "候选池统计": stock_status.get("候选池统计", {}),
            "数据健康度": stock_status.get("数据健康度", {})
        },
        "最终闸口": {
            "路径": str(final_gate_path),
            "是否允许真实动作": final_gate.get("是否允许真实动作", False),
            "阻断原因": final_gate.get("阻断原因", ["真实动作总闸口默认关闭"])
        },
        "无人值守执行器骨架": {
            "路径": str(executor_path),
            "执行模式": executor.get("执行模式"),
            "汇总": executor.get("汇总", {})
        },
        "进化清理闸口": {
            "路径": str(cleanup_path),
            "生命周期原则": cleanup.get("生命周期原则"),
            "汇总": cleanup.get("汇总", {})
        },
        "仍然关闭": [
            "真实联网",
            "正式库写入",
            "正式文档输出",
            "企业微信真实发送",
            "n8n真实触发",
            "税收真实业务",
            "旧系统写入"
        ],
        "下一步": [
            "补全股票公开真实数据只读接入许可令",
            "补全低风险巡检正式启用前的人工许可令",
            "继续完善知识库、企业微信助手、内容办公和视频制作的日常可用入口",
            "推动企业微信统一指令路由从预演进入受控本地调用",
            "保持税收真实业务关闭，仅保留未来自建闸口"
        ]
    }
    output_dir = manager / "03数据" / "阶段判定"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "当前总体进度报告_最新.json"
    latest = output_dir / "当前总体进度报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"多功能智能体总体": report["进度估算"]["多功能智能体总体"], "基础可用版阶段": report["进度估算"]["基础可用版阶段"], "股票研究系统": report["进度估算"]["股票研究系统"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
