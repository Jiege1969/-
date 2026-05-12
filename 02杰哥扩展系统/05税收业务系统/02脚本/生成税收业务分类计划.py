"""
名称：生成税收业务分类计划.py
作用：根据税收业务配置、税种分类规则和业务处理模板生成第一阶段税收业务分类计划。
触发方式：python 生成税收业务分类计划.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块配置，只写入本模块分类索引和处理计划；不抓取政策、不读取真实涉税资料、不替代正式判断。
创建/修改记录：2026-04-26 创建第一阶段税收业务分类计划脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "税收业务配置.json")
    rules = load_json(root / "01配置" / "税种分类规则.json")
    sources = load_json(root / "01配置" / "税收政策来源.json")
    template = load_json(root / "01配置" / "税收业务处理模板.json")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    classification = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "系统": "02杰哥扩展系统/05税收业务系统",
        "阶段": "第一阶段分类索引",
        "安全边界": config.get("安全边界"),
        "税种数量": len(rules.get("税种", [])),
        "税种分类": rules.get("税种", []),
        "政策来源": sources.get("官方来源", []),
    }
    plan = {
        "生成时间": classification["生成时间"],
        "处理流程": template.get("处理流程", []),
        "事实采集字段": template.get("事实采集字段", []),
        "结论输出要求": template.get("结论输出要求", {}),
        "任务列表": [
            "登记政策文件元数据",
            "按税种和业务场景分类",
            "核实政策有效状态",
            "提取适用条件和例外条款",
            "生成业务处理草案",
            "人工复核政策依据和结论"
        ],
    }

    write_json(root / "03数据" / "02分类索引" / f"税种分类索引_{timestamp}.json", classification)
    write_json(root / "03数据" / "02分类索引" / "税种分类索引_最新.json", classification)
    write_json(root / "03数据" / "04处理计划" / f"税收业务处理计划_{timestamp}.json", plan)
    write_json(root / "03数据" / "04处理计划" / "税收业务处理计划_最新.json", plan)
    print(json.dumps({"税种数量": classification["税种数量"], "输出": "税收业务处理计划_最新.json"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
