"""
名称：生成n8n启用后只读观测方案.py
作用：生成第一批n8n工作流未来启用后的只读观测方案，明确观测项、日志路径和异常回滚原则。
触发方式：python 生成n8n启用后只读观测方案.py
依赖：Python标准库；需已有单工作流启用准入表。
所属系统：00杰哥系统总管
安全边界：只生成观测方案；不启用工作流、不触发Webhook、不读取业务数据、不发送企业微信、不接入税收业务。
创建/修改记录：2026-04-27 创建n8n启用后只读观测方案脚本。
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
    gate_path = root / "00杰哥系统总管" / "03数据" / "灰度接入" / "n8n单工作流启用准入表_最新.json"
    gate = load_json(gate_path)
    observation_items = []
    for item in gate.get("准入表", []):
        observation_items.append(
            {
                "工作流名": item.get("工作流名", ""),
                "工作流ID": item.get("工作流ID", ""),
                "观测状态": "待未来启用后观察",
                "只读观测项": [
                    "active状态",
                    "最近一次执行是否成功",
                    "最近一次执行耗时",
                    "错误日志摘要",
                    "是否出现外发动作",
                    "是否出现未授权写入",
                ],
                "异常处理": "任一异常立即执行批量或单工作流active=false回滚，不删除工作流。",
            }
        )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "n8n启用后只读观测方案",
        "来源": str(gate_path),
        "观测对象数量": len(observation_items),
        "观测对象": observation_items,
        "是否启用工作流": False,
        "是否触发Webhook": False,
        "是否读取业务数据": False,
        "是否发送企业微信": False,
        "是否接入税收业务": False,
        "结论": "已生成未来启用后的只读观测方案；当前不启用任何工作流。",
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "n8n启用后只读观测方案_最新.json"
    latest = output_dir / "n8n启用后只读观测方案_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"观测对象数量": len(observation_items), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
