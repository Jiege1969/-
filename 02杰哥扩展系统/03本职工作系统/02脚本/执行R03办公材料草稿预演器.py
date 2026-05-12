# -*- coding: utf-8 -*-
"""
名称：执行R03办公材料草稿预演器.py
作用：执行R03办公材料草稿预演器联检，确认计划、草稿目录、门禁、最终闸口、执行窗口和许可令状态。
触发方式：python 执行R03办公材料草稿预演器.py
依赖：Python 标准库；R03办公材料草稿预演执行规则.json；办公材料本地生成门禁报告；真实小流量闸口、窗口、许可令文件。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只生成office_draft_dry_run预演报告；不输出正式文档；不覆盖原文件；不联网；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建R03办公材料草稿预演器联检脚本。
标识：r03-office-draft-executor
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_json_if_exists(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [item for item in root.glob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def find_task(items: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    for item in items:
        if item.get("任务编号") == task_id:
            return item
    return {}


def main() -> int:
    root = module_root()
    v3 = system_root()
    rule_path = root / "01配置" / "R03办公材料草稿预演执行规则.json"
    rules = load_json(rule_path)
    source = rules.get("联检来源", {})
    boundary = rules.get("路径边界", {})
    plan_dir = Path(boundary.get("计划目录", ""))
    draft_dir = Path(boundary.get("草稿目录", ""))
    gate_dir = Path(boundary.get("门禁目录", ""))
    local_gate_path = Path(source.get("本地生成门禁报告", ""))
    final_gate_path = Path(source.get("最终闸口", ""))
    window_path = Path(source.get("执行窗口", ""))
    permit_path = Path(source.get("许可令", ""))
    local_gate = load_json_if_exists(local_gate_path)
    final_gate = load_json_if_exists(final_gate_path)
    window_report = load_json_if_exists(window_path)
    permit_report = load_json_if_exists(permit_path)
    r03_window = find_task(window_report.get("执行窗口", []), "R03")
    r03_permit = find_task(permit_report.get("许可令", []), "R03")
    switches = rules.get("默认开关", {})
    allow_final_output = (
        switches.get("允许正式文档输出") is True
        and final_gate.get("是否允许真实动作") is True
        and r03_window.get("允许真实动作") is True
        and r03_permit.get("是否允许执行") is True
    )
    checks = {
        "规则文件存在": rule_path.exists(),
        "计划目录存在": plan_dir.exists(),
        "草稿目录存在": draft_dir.exists(),
        "门禁目录存在": gate_dir.exists(),
        "本地生成门禁报告存在": local_gate_path.exists(),
        "最终闸口存在": final_gate_path.exists(),
        "执行窗口存在": window_path.exists(),
        "许可令存在": permit_path.exists(),
        "正式文档输出关闭": switches.get("允许正式文档输出") is False,
        "覆盖原文件关闭": switches.get("允许覆盖原文件") is False,
        "最终闸口未放行": final_gate.get("是否允许真实动作") is False,
        "R03窗口未开放": r03_window.get("允许真实动作") is False,
        "R03许可令未签发": r03_permit.get("是否允许执行") is False,
        "旧系统写入关闭": switches.get("允许旧系统写入") is False,
        "税收业务关闭": switches.get("允许税收业务") is False,
    }
    latest_plan = latest_file(plan_dir, "办公材料计划_*.json") if plan_dir.exists() else None
    latest_draft = latest_file(draft_dir, "办公材料草稿框架_*.json") if draft_dir.exists() else None
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行模式": rules.get("执行模式"),
        "系统根目录": str(v3),
        "规则文件": str(rule_path),
        "联检来源": source,
        "路径边界": boundary,
        "联检结果": checks,
        "最新计划": str(latest_plan) if latest_plan else "",
        "最新草稿": str(latest_draft) if latest_draft else "",
        "本地门禁摘要": local_gate.get("汇总", {}),
        "是否输出正式文档": False,
        "是否允许进入正式输出": allow_final_output,
        "执行器状态": "就绪但冻结",
        "阻断原因": "正式文档输出开关、最终闸口、执行窗口和许可令均未同时放行。",
        "当前结论": "R03办公材料草稿预演器联检完成；当前不输出正式文档，不覆盖原文件。",
    }
    output_dir = root / "03数据" / "04本地生成门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"R03办公材料草稿预演器联检_{timestamp}.json"
    latest = output_dir / "R03办公材料草稿预演器联检_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否输出正式文档": report["是否输出正式文档"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
