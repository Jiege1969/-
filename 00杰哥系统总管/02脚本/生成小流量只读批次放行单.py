"""
名称：生成小流量只读批次放行单.py
作用：根据小流量只读批次放行规则和观测闭环状态，生成批次放行单。
触发方式：python 生成小流量只读批次放行单.py
依赖：Python 标准库；小流量只读批次放行规则.json；小流量只读执行观测闭环汇总_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成批次放行单；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读批次放行单脚本。
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
    rules = load_json(manager / "01配置" / "小流量只读批次放行规则.json")
    loop_path = manager / "03数据" / "小流量只读执行" / "小流量只读执行观测闭环汇总_最新.json"
    loop = load_json(loop_path) if loop_path.exists() else {}
    batches = []
    for item in rules.get("候选批次", []):
        batches.append({
            **item,
            "当前是否放行": False,
            "阻断原因": "默认不放行；需要用户明确确认具体批次后才可进入真实小流量动作。",
            "观测闭环完成度": loop.get("完成度百分比"),
        })
    form = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "观测闭环": {"路径": str(loop_path), "完成度": loop.get("完成度百分比")},
        "批次放行单": batches,
        "全局禁止": rules.get("全局禁止", []),
        "是否允许批量放行": False,
        "是否允许跳过人工确认": False,
        "是否允许真实动作": False,
        "当前结论": "批次放行单已生成；所有批次默认不放行。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "小流量只读批次放行单_最新.json"
    latest = output_dir / "小流量只读批次放行单_最新.json"
    write_json(output, form)
    write_json(latest, form)
    print(json.dumps({"批次数": len(batches), "是否允许真实动作": form["是否允许真实动作"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
