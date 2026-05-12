"""
名称：生成股票公开数据只读探测预案.py
作用：根据股票公开数据只读探测规则和真实接入总闸门状态，生成小流量公开数据只读探测预案。
触发方式：python 生成股票公开数据只读探测预案.py
依赖：Python 标准库；股票公开数据只读探测规则.json；真实接入总闸门_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成预案；不执行联网请求；不调用券商接口；不交易；不触发n8n；不发送企业微信；不写入旧系统；不接入税收。
创建/修改记录：2026-04-27 创建股票公开数据只读探测预案脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def v3_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    system_root = v3_root()
    rules = load_json(root / "01配置" / "股票公开数据只读探测规则.json")
    gate_path = system_root / "00杰哥系统总管" / "03数据" / "真实接入闸门" / "真实接入总闸门_最新.json"
    gate = load_json(gate_path) if gate_path.exists() else {}
    switches = rules.get("默认开关", {})
    enabled_sources = [item for item in rules.get("候选数据源", []) if item.get("是否默认启用") is True]
    disabled_sources = [item for item in rules.get("候选数据源", []) if item.get("是否默认启用") is not True]
    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "安全结论": "只生成预案，不执行联网抓取",
        "真实接入总闸门结论": gate.get("总闸门结论", "未找到总闸门报告"),
        "默认开关": switches,
        "请求边界": rules.get("请求边界", {}),
        "本轮允许数据源": enabled_sources,
        "待人工确认数据源": disabled_sources,
        "候选数据类型": rules.get("候选数据类型", []),
        "放行条件": rules.get("放行条件", []),
        "执行步骤": [
            "读取真实接入总闸门报告",
            "确认旧系统只读保护仍然生效",
            "确认股票研究底座验收通过",
            "人工登记具体公开URL白名单",
            "单轮最多3个请求，只写入本模块临时探测目录",
            "生成探测报告后进入人工确认队列",
            "若任一检查失败，立即停止并保留日志"
        ],
        "禁止事项": [
            "不调用券商接口",
            "不执行交易",
            "不触发n8n",
            "不发送企业微信",
            "不写入旧系统",
            "不接入税收业务",
            "不把模型输出当作买卖指令"
        ],
    }
    output_dir = root / "03数据" / "06公开数据探测"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"股票公开数据只读探测预案_{timestamp}.json"
    latest = output_dir / "股票公开数据只读探测预案_最新.json"
    write_json(output, plan)
    write_json(latest, plan)
    print(json.dumps({"本轮允许数据源": len(enabled_sources), "待确认数据源": len(disabled_sources), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
