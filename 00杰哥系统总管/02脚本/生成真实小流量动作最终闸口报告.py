"""
名称：生成真实小流量动作最终闸口报告.py
作用：根据最终闸口规则和首批预检总表，生成真实小流量动作最终闸口报告。
触发方式：python 生成真实小流量动作最终闸口报告.py
依赖：Python 标准库；真实小流量动作最终闸口规则.json；首批小流量批次预检总表_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成最终闸口报告；不联网；不写库；不生成正式文档；不触发n8n；不真实发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实小流量动作最终闸口报告脚本。
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


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    log_root = manager / "04日志"
    rules = load_json(manager / "01配置" / "真实小流量动作最终闸口规则.json")
    preflight_path = manager / "03数据" / "小流量只读执行" / "首批小流量批次预检总表_最新.json"
    preflight = load_json(preflight_path) if preflight_path.exists() else {}
    acceptance_path = latest_file(log_root / "acceptance", "v3-acceptance-最新.json")
    gate_path = latest_file(log_root, "real-access-master-gate-verify-*.json")
    design_path = latest_file(log_root, "readonly-execution-design-stage-verify-*.json")
    checks = {
        "v3总体验收通过": acceptance_path is not None,
        "真实接入总闸门通过": gate_path is not None,
        "小流量只读执行设计阶段通过": design_path is not None,
        "首批小流量批次预检总表通过": preflight.get("汇总", {}).get("失败") == 0,
        "用户明确指定放行批次": False,
        "用户明确确认执行窗口": False
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "默认开关": rules.get("默认开关", {}),
        "放行前置条件": checks,
        "首批预检总表": str(preflight_path),
        "是否允许真实动作": False,
        "阻断原因": "缺少用户明确指定放行批次和执行窗口；默认不放行真实动作。",
        "当前结论": "最终闸口报告已生成；真实小流量动作未放行。"
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "真实小流量动作最终闸口报告_最新.json"
    latest = output_dir / "真实小流量动作最终闸口报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"是否允许真实动作": report["是否允许真实动作"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
