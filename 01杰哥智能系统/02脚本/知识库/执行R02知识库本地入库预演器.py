# -*- coding: utf-8 -*-
"""
名称：执行R02知识库本地入库预演器.py
作用：执行R02知识库本地入库预演器联检，确认样本路径、入库复核、最终闸口、执行窗口和许可令状态。
触发方式：python 执行R02知识库本地入库预演器.py
依赖：Python 标准库；R02知识库本地入库预演执行规则.json；知识库本地入库前复核报告；真实小流量闸口、窗口、许可令文件。
所属系统：01杰哥智能系统/知识库
安全边界：只生成local_ingest_dry_run预演报告；不写正式向量库；不联网；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建R02知识库本地入库预演器联检脚本。
标识：r02-knowledge-local-ingest-executor
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_json_if_exists(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_task(items: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    for item in items:
        if item.get("任务编号") == task_id:
            return item
    return {}


def count_sample_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def main() -> int:
    root = module_root()
    v3 = system_root()
    rule_path = root / "01配置" / "R02知识库本地入库预演执行规则.json"
    rules = load_json(rule_path)
    source = rules.get("联检来源", {})
    boundary = rules.get("路径边界", {})
    sample_root = Path(boundary.get("样本根目录", ""))
    temp_dir = Path(boundary.get("临时输出目录", ""))
    review_path = Path(source.get("入库前复核报告", ""))
    final_gate_path = Path(source.get("最终闸口", ""))
    window_path = Path(source.get("执行窗口", ""))
    permit_path = Path(source.get("许可令", ""))
    review = load_json_if_exists(review_path)
    final_gate = load_json_if_exists(final_gate_path)
    window_report = load_json_if_exists(window_path)
    permit_report = load_json_if_exists(permit_path)
    r02_window = find_task(window_report.get("执行窗口", []), "R02")
    r02_permit = find_task(permit_report.get("许可令", []), "R02")
    switches = rules.get("默认开关", {})
    allow_write = (
        switches.get("允许正式向量库写入") is True
        and final_gate.get("是否允许真实动作") is True
        and r02_window.get("允许真实动作") is True
        and r02_permit.get("是否允许执行") is True
    )
    temp_dir.mkdir(parents=True, exist_ok=True)
    checks = {
        "规则文件存在": rule_path.exists(),
        "样本根目录存在": sample_root.exists(),
        "临时输出目录存在": temp_dir.exists(),
        "入库前复核报告存在": review_path.exists(),
        "最终闸口存在": final_gate_path.exists(),
        "执行窗口存在": window_path.exists(),
        "许可令存在": permit_path.exists(),
        "正式向量库写入关闭": switches.get("允许正式向量库写入") is False,
        "最终闸口未放行": final_gate.get("是否允许真实动作") is False,
        "R02窗口未开放": r02_window.get("允许真实动作") is False,
        "R02许可令未签发": r02_permit.get("是否允许执行") is False,
        "旧系统写入关闭": switches.get("允许旧系统写入") is False,
        "税收业务关闭": switches.get("允许税收业务") is False,
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行模式": rules.get("执行模式"),
        "系统根目录": str(v3),
        "规则文件": str(rule_path),
        "联检来源": source,
        "路径边界": boundary,
        "联检结果": checks,
        "样本文件数量": count_sample_files(sample_root),
        "入库前复核摘要": review.get("汇总", {}),
        "是否写入正式向量库": False,
        "是否允许进入正式入库": allow_write,
        "执行器状态": "就绪但冻结",
        "阻断原因": "正式向量库写入开关、最终闸口、执行窗口和许可令均未同时放行。",
        "当前结论": "R02知识库本地入库预演器联检完成；当前不写入正式向量库。",
    }
    output_dir = root / "03数据" / "知识库" / "06入库前复核"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"R02知识库本地入库预演器联检_{timestamp}.json"
    latest = output_dir / "R02知识库本地入库预演器联检_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否写入正式向量库": report["是否写入正式向量库"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
