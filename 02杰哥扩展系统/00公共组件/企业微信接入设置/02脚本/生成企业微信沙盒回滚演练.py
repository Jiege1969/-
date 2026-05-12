"""
名称：生成企业微信沙盒回滚演练.py
作用：基于企业微信回滚方案生成沙盒回滚演练清单，用于真实接入前核对停用、关闭、保留日志和复盘动作。
触发方式：python 生成企业微信沙盒回滚演练.py
依赖：Python 标准库；需已有企业微信回滚方案。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只生成本地演练清单；不调用企业微信、不停用真实工作流、不修改OpenClaw、不删除日志。
创建/修改记录：2026-04-27 创建企业微信沙盒回滚演练脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def output_dir() -> Path:
    target = module_root() / "03数据" / "05回滚演练"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    rollback_path = module_root() / "01配置" / "企业微信回滚方案.json"
    rollback = load_json(rollback_path)
    actions = rollback.get("回滚动作清单", [])
    rehearsal = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "方案来源": str(rollback_path),
        "阶段": "企业微信真实接入前沙盒回滚演练",
        "触发场景": rollback.get("回滚触发条件", []),
        "演练清单": [
            {
                "序号": index,
                "动作": action,
                "演练方式": "沙盒口径人工核对",
                "是否自动执行": False,
                "是否已真实执行": False,
                "验收口径": "只确认动作顺序和责任边界，不操作真实系统",
            }
            for index, action in enumerate(actions, start=1)
        ],
        "禁止自动执行": rollback.get("禁止自动执行", []),
        "人工确认要求": rollback.get("人工确认要求"),
        "回滚后验证": [
            "重新运行企业微信接入设置底座验收",
            "重新运行统一消息出口验收",
            "重新运行OpenClaw边缘网关验收",
            "重新运行v3总体验收",
            "生成事故或演练经验卡片候选",
        ],
        "统计": {
            "动作数量": len(actions),
            "禁止自动执行数量": len(rollback.get("禁止自动执行", [])),
        },
        "是否连接企业微信": False,
        "是否停用真实n8n工作流": False,
        "是否修改OpenClaw": False,
        "是否删除日志": False,
        "是否真实执行": False,
    }
    latest = output_dir() / "企业微信沙盒回滚演练_最新.json"
    output = latest
    text = json.dumps(rehearsal, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"动作数量": len(actions), "输出": str(output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
