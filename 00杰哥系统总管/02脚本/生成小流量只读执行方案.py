"""
名称：生成小流量只读执行方案.py
作用：根据小流量只读执行方案规则和禁用态完成度汇总，生成真实动作前的小流量只读执行方案。
触发方式：python 生成小流量只读执行方案.py
依赖：Python 标准库；小流量只读执行方案规则.json；小流量只读接入禁用态完成度汇总_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成执行方案；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读执行方案生成脚本。
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


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rules = load_json(manager / "01配置" / "小流量只读执行方案规则.json")
    disabled_summary_path = manager / "03数据" / "真实攻坚队列" / "小流量只读接入禁用态完成度汇总_最新.json"
    disabled_summary = load_json(disabled_summary_path) if disabled_summary_path.exists() else {}
    switches = rules.get("默认开关", {})
    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "禁用态完成度": disabled_summary.get("完成度百分比"),
        "默认开关": switches,
        "执行批次": rules.get("执行批次", []),
        "观测要求": rules.get("观测要求", []),
        "执行前必须通过": [
            "v3总体验收",
            "真实接入总闸门",
            "小流量只读接入禁用态完成度",
            "对应业务人工确认单"
        ],
        "当前结论": "方案已生成；真实动作未放行。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "小流量只读执行方案_最新.json"
    latest = output_dir / "小流量只读执行方案_最新.json"
    write_json(output, plan)
    write_json(latest, plan)
    print(json.dumps({"批次数": len(plan["执行批次"]), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
