"""
名称：生成小流量只读执行前快照.py
作用：汇总小流量只读执行前的总体验收、总闸门、执行方案、旧系统保护和禁用态完成度，生成执行前基线快照。
触发方式：python 生成小流量只读执行前快照.py
依赖：Python 标准库；小流量只读执行前快照规则.json；相关验收日志。
所属系统：00杰哥系统总管
安全边界：只读取日志并生成快照；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读执行前快照脚本；2026-04-30 将v3总体验收设为观察项，避免总体验收内部自我引用导致循环失败。
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


def latest_summary(log_root: Path, name: str, pattern: str) -> dict[str, Any]:
    path = latest_file(log_root, pattern)
    if not path:
        return {"名称": name, "存在": False, "通过": False, "日志": "", "汇总": {}}
    data = load_json(path)
    summary = data.get("汇总") or data.get("summary") or {}
    failed = summary.get("失败", summary.get("failed", 0))
    return {"名称": name, "存在": True, "通过": failed == 0, "日志": str(path), "汇总": summary}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    log_root = manager / "04日志"
    rules = load_json(manager / "01配置" / "小流量只读执行前快照规则.json")
    checks = [
        latest_summary(log_root, "v3总体验收", "v3-acceptance-最新.json"),
        latest_summary(log_root, "真实接入总闸门", "real-access-master-gate-verify-*.json"),
        latest_summary(log_root, "小流量只读执行方案", "readonly-execution-plan-verify-*.json"),
        latest_summary(log_root, "旧系统保护", "old-system-protection-verify-*.json"),
        latest_summary(log_root, "小流量禁用态完成度", "readonly-disabled-completion-verify-*.json"),
    ]
    blocking_checks = [item for item in checks if item["名称"] != "v3总体验收"]
    failed_items = [item for item in blocking_checks if not item["通过"]]
    snapshot = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "快照项目": rules.get("快照项目", []),
        "检查结果": checks,
        "真实动作关闭开关": rules.get("真实动作关闭开关", {}),
        "汇总": {
            "项目总数": len(checks),
            "通过": len(checks) - len([item for item in checks if not item["通过"]]),
            "失败": len(failed_items),
            "观察项失败": len([item for item in checks if item["名称"] == "v3总体验收" and not item["通过"]]),
        },
        "当前结论": "执行前快照已生成；真实动作仍保持关闭。" if not failed_items else "执行前快照存在未通过项目，禁止进入真实动作。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "小流量只读执行前快照_最新.json"
    latest = output_dir / "小流量只读执行前快照_最新.json"
    write_json(output, snapshot)
    write_json(latest, snapshot)
    print(json.dumps({"通过": snapshot["汇总"]["通过"], "失败": snapshot["汇总"]["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
