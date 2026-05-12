# -*- coding: utf-8 -*-
"""
名称：执行R01股票公开数据只读探测器.py
作用：执行R01股票公开数据只读探测器的执行前联检，确认白名单、最终闸口、执行窗口和许可令状态。
触发方式：python 执行R01股票公开数据只读探测器.py
依赖：Python 标准库；R01股票只读探测器执行规则.json；股票公开URL白名单确认单_最新.json；真实小流量闸口、窗口、许可令文件。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：默认只做联检并生成冻结报告；不联网；不抓取行情；不调用券商接口；不交易；不写旧系统；不触发n8n；不发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建R01股票只读探测器联检脚本。
标识：r01-stock-readonly-executor
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def main() -> int:
    root = module_root()
    v3 = system_root()
    rule_path = root / "01配置" / "R01股票只读探测器执行规则.json"
    rules = load_json(rule_path)
    source = rules.get("联检来源", {})
    whitelist_path = Path(source.get("URL白名单确认单", ""))
    final_gate_path = Path(source.get("最终闸口", ""))
    window_path = Path(source.get("执行窗口", ""))
    permit_path = Path(source.get("许可令", ""))
    whitelist = load_json_if_exists(whitelist_path)
    final_gate = load_json_if_exists(final_gate_path)
    window_report = load_json_if_exists(window_path)
    permit_report = load_json_if_exists(permit_path)
    confirmed_urls = whitelist.get("已确认URL", [])
    r01_window = find_task(window_report.get("执行窗口", []), "R01")
    r01_permit = find_task(permit_report.get("许可令", []), "R01")
    switches = rules.get("默认开关", {})
    allow_real = (
        switches.get("允许真实联网") is True
        and final_gate.get("是否允许真实动作") is True
        and r01_window.get("允许真实动作") is True
        and r01_permit.get("是否允许执行") is True
        and len(confirmed_urls) > 0
    )
    checks = {
        "规则文件存在": rule_path.exists(),
        "白名单确认单存在": whitelist_path.exists(),
        "最终闸口存在": final_gate_path.exists(),
        "执行窗口存在": window_path.exists(),
        "许可令存在": permit_path.exists(),
        "真实联网开关关闭": switches.get("允许真实联网") is False,
        "最终闸口未放行": final_gate.get("是否允许真实动作") is False,
        "R01窗口未开放": r01_window.get("允许真实动作") is False,
        "R01许可令未签发": r01_permit.get("是否允许执行") is False,
        "旧系统写入关闭": switches.get("允许写入旧系统") is False,
        "税收业务关闭": switches.get("允许税收业务") is False,
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行模式": rules.get("执行模式"),
        "系统根目录": str(v3),
        "规则文件": str(rule_path),
        "联检来源": source,
        "联检结果": checks,
        "已确认URL数量": len(confirmed_urls),
        "请求边界": rules.get("请求边界", {}),
        "是否执行真实联网请求": False,
        "是否允许进入真实请求": allow_real,
        "执行器状态": "就绪但冻结",
        "阻断原因": "真实联网开关、最终闸口、执行窗口和许可令均未同时放行。",
        "当前结论": "R01股票只读探测器联检完成；当前不发起任何联网请求。",
    }
    output_dir = root / "03数据" / "06公开数据探测"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"R01股票只读探测器联检_{timestamp}.json"
    latest = output_dir / "R01股票只读探测器联检_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否执行真实联网请求": report["是否执行真实联网请求"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
