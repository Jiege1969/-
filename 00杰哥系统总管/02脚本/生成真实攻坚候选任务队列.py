"""
名称：生成真实攻坚候选任务队列.py
作用：根据真实攻坚候选任务规则和最新总体验收结果，生成真实接入攻坚候选任务队列。
触发方式：python 生成真实攻坚候选任务队列.py
依赖：Python 标准库；真实攻坚候选任务规则.json；最新v3总体验收日志。
所属系统：00杰哥系统总管
安全边界：只生成候选队列；不创建系统计划任务；不重启服务；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实攻坚候选任务队列生成脚本。
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


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = [item for item in directory.glob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rules = load_json(manager / "01配置" / "真实攻坚候选任务规则.json")
    acceptance_path = latest_file(manager / "04日志" / "acceptance", "v3-acceptance-最新.json")
    acceptance = load_json(acceptance_path) if acceptance_path else {}
    step_names = {item.get("name"): item for item in acceptance.get("steps", [])}
    summary = acceptance.get("summary", {})
    queue = []
    for item in sorted(rules.get("候选任务", []), key=lambda task: task.get("优先级", 99)):
        required = item.get("准入验收", [])
        matched = [
            name for name in required
            if any(name in (step_name or "") and step.get("ok") is True for step_name, step in step_names.items())
        ]
        missing = [name for name in required if name not in matched]
        queue.append({
            **item,
            "准入状态": "可进入预案细化" if not missing and summary.get("failed") == 0 else "继续等待验收补齐",
            "已满足验收": matched,
            "缺失验收": missing,
            "当前动作": "只允许预案、清单、回滚和人工确认设计",
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "真实接入攻坚候选任务队列",
        "总体验收": {"路径": str(acceptance_path), "汇总": summary},
        "安全边界": rules.get("安全边界", {}),
        "候选队列": queue,
        "暂停任务": rules.get("暂停任务", []),
        "结论": "候选队列已生成；当前仍按总闸门保持真实动作关闭，逐项进入预案细化。",
    }
    output_dir = manager / "03数据" / "真实攻坚队列"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "真实攻坚候选任务队列_最新.json"
    latest = output_dir / "真实攻坚候选任务队列_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"候选任务数": len(queue), "暂停任务数": len(rules.get("暂停任务", [])), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
