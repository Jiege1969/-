# -*- coding: utf-8 -*-
"""
名称：生成真实小流量执行窗口登记.py
作用：根据真实小流量执行窗口登记规则，生成首批候选动作的冻结窗口登记表。
触发方式：python 生成真实小流量执行窗口登记.py
依赖：Python 标准库；真实小流量执行窗口登记规则.json；最新真实小流量动作最终闸口报告。
所属系统：00杰哥系统总管
安全边界：只生成窗口登记表；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实小流量执行窗口登记脚本。
标识：real-execution-window-register
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
    files = [item for item in root.rglob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def normalize_window(item: dict[str, Any], final_gate_allowed: bool) -> dict[str, Any]:
    return {
        "任务编号": item.get("任务编号"),
        "任务名称": item.get("任务名称"),
        "所属模块": item.get("所属模块"),
        "动作类型": item.get("动作类型"),
        "窗口状态": item.get("窗口状态", "冻结"),
        "允许真实动作": bool(item.get("允许真实动作")) and final_gate_allowed,
        "释放条件": item.get("释放条件", []),
        "当前处理方式": "登记并冻结，等待后续真实执行闸口统一放行",
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "真实小流量执行窗口登记规则.json"
    rules = load_json(rule_path)
    final_gate_path = manager / "03数据" / "小流量只读执行" / "真实小流量动作最终闸口报告_最新.json"
    final_gate = load_json(final_gate_path) if final_gate_path.exists() else {}
    acceptance_path = latest_file(manager / "04日志" / "acceptance", "v3-acceptance-最新.json")
    final_gate_allowed = final_gate.get("是否允许真实动作") is True
    windows = [normalize_window(item, final_gate_allowed) for item in rules.get("登记窗口", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "最新总体验收": str(acceptance_path) if acceptance_path else "",
        "最终闸口": {
            "路径": str(final_gate_path),
            "是否允许真实动作": final_gate.get("是否允许真实动作"),
        },
        "默认开关": rules.get("默认开关", {}),
        "执行窗口": windows,
        "汇总": {
            "登记窗口数": len(windows),
            "开放窗口数": sum(1 for item in windows if item.get("允许真实动作") is True),
            "冻结窗口数": sum(1 for item in windows if item.get("允许真实动作") is not True),
        },
        "禁止项": rules.get("禁止项", []),
        "当前结论": "首批真实小流量执行窗口已登记；因最终闸口未放行，全部窗口保持冻结。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "真实小流量执行窗口登记_最新.json"
    latest = output_dir / "真实小流量执行窗口登记_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"登记窗口数": report["汇总"]["登记窗口数"], "开放窗口数": report["汇总"]["开放窗口数"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
