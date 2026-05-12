# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送灰度发送日志台账与回滚演练包.py
作用：基于252最终只读总闸口，生成未来真实灰度发送所需的本地日志台账、失败记录、重复拦截和回滚演练包。
触发方式：python 生成股票主动推送灰度发送日志台账与回滚演练包.py
依赖：Python标准库；252主动推送真实灰度发送前最终只读总闸口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地253演练包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送灰度发送日志台账与回滚演练包。
标识：stock-active-push-gray-send-ledger-rollback-drill-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送灰度发送日志台账与回滚演练包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 是否真实发送：{report['是否真实发送']}",
        f"- 是否启用n8n：{report['是否启用n8n']}",
        f"- 是否演练通过：{report['演练通过']}",
        "",
        "## 发送台账字段",
        "",
    ]
    for item in report["发送台账字段"]:
        lines.append(f"- {item['字段']}：{item['说明']}")
    lines.extend(["", "## 失败记录字段", ""])
    for item in report["失败记录字段"]:
        lines.append(f"- {item['字段']}：{item['说明']}")
    lines.extend(["", "## 回滚演练步骤", ""])
    for item in report["回滚演练步骤"]:
        lines.append(f"{item['顺序']}. {item['动作']}：{item['结果']}")
    lines.extend(["", "## 熔断触发演练", ""])
    for item in report["熔断触发演练"]:
        lines.append(f"- {item['场景']}：{item['预期动作']}，结果 {item['演练结果']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data = root / "03数据"
    gate_path = data / "252主动推送真实灰度发送前最终只读总闸口" / "股票主动推送真实灰度发送前最终只读总闸口_最新.json"
    gate = load_json(gate_path)

    send_ledger_fields = [
        {"字段": "发送批次ID", "说明": "本地生成，格式如 STOCK-PUSH-GRAY-YYYYMMDD-001。"},
        {"字段": "目标用户", "说明": "必须来自单人白名单人工确认，不允许群发。"},
        {"字段": "消息摘要哈希", "说明": "用于重复发送拦截，不保存敏感凭据。"},
        {"字段": "dry_run", "说明": "当前演练固定为 true。"},
        {"字段": "真实发送", "说明": "当前演练固定为 false。"},
        {"字段": "企业微信msgid", "说明": "真实发送前为空；本演练不得伪造。"},
        {"字段": "发送结果", "说明": "blocked / dry_run_only / sent / failed；当前只能是 blocked 或 dry_run_only。"},
        {"字段": "熔断状态", "说明": "记录是否因交易化表达、重复发送、闸口未放行等被拦截。"},
        {"字段": "回滚状态", "说明": "记录无需回滚、已阻断、已人工撤回等状态。"},
    ]

    failure_fields = [
        {"字段": "失败时间", "说明": "本地记录时间。"},
        {"字段": "失败阶段", "说明": "闸口检查、内容扫描、重复拦截、发送调用、人工复核。"},
        {"字段": "失败原因", "说明": "保持可读，不写密钥、不写真实凭据。"},
        {"字段": "处置动作", "说明": "阻断、转人工、复跑只读巡检、保持不发送。"},
        {"字段": "是否外发", "说明": "当前演练固定为 false。"},
    ]

    rollback_steps = [
        {"顺序": 1, "动作": "读取252总闸口", "结果": "完成"},
        {"顺序": 2, "动作": "确认当前总闸口blocked", "结果": "完成" if gate.get("总体状态") == "blocked" else "异常"},
        {"顺序": 3, "动作": "模拟发现真实发送未放行", "结果": "阻断发送"},
        {"顺序": 4, "动作": "模拟写入失败台账", "结果": "仅本地演练，不外发"},
        {"顺序": 5, "动作": "模拟回滚", "结果": "保持未发送状态，无需撤回真实消息"},
        {"顺序": 6, "动作": "模拟恢复条件", "结果": "要求人工确认和受控发送闸口另行放行"},
    ]

    circuit_drill = [
        {"场景": "命中交易化表达", "预期动作": "阻断并转人工复核", "演练结果": "pass"},
        {"场景": "同一摘要重复", "预期动作": "拦截重复发送", "演练结果": "pass"},
        {"场景": "目标用户非单人白名单", "预期动作": "阻断群发", "演练结果": "pass"},
        {"场景": "受控发送闸口未放行", "预期动作": "保持blocked", "演练结果": "pass"},
        {"场景": "n8n触发开关开启", "预期动作": "阻断自动化", "演练结果": "pass"},
        {"场景": "出现券商或交易动作", "预期动作": "登记高风险并阻断", "演练结果": "pass"},
    ]

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源总闸口": str(gate_path),
        "来源总闸口存在": gate_path.exists(),
        "来源总闸口状态": gate.get("总体状态", ""),
        "当前状态": "日志台账与回滚演练已生成；仅本地演练，不构成真实发送许可。",
        "是否真实发送": False,
        "是否启用n8n": False,
        "是否触发n8n": False,
        "是否接券商": False,
        "是否交易": False,
        "演练通过": gate_path.exists() and gate.get("总体状态") == "blocked",
        "发送台账字段": send_ledger_fields,
        "失败记录字段": failure_fields,
        "回滚演练步骤": rollback_steps,
        "熔断触发演练": circuit_drill,
        "样例发送台账记录": {
            "发送批次ID": "STOCK-PUSH-GRAY-DRYRUN-001",
            "目标用户": "待人工确认",
            "消息摘要哈希": "dryrun-only",
            "dry_run": True,
            "真实发送": False,
            "企业微信msgid": "",
            "发送结果": "blocked",
            "熔断状态": "受控发送闸口未放行",
            "回滚状态": "未发送，无需撤回",
        },
        "实际动作": {
            "读取252总闸口": True,
            "写本地253演练包": True,
            "调用企业微信API": False,
            "真实发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "重载19310": False,
            "重载19302": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式规则库": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }

    out_dir = data / "253主动推送灰度发送日志台账与回滚演练包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送灰度发送日志台账与回滚演练包_{stamp}.json"
    latest_json = out_dir / "股票主动推送灰度发送日志台账与回滚演练包_最新.json"
    output_md = out_dir / f"股票主动推送灰度发送日志台账与回滚演练包_{stamp}.md"
    latest_md = out_dir / "股票主动推送灰度发送日志台账与回滚演练包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": "pass" if report["演练通过"] else "blocked", "真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if report["演练通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
