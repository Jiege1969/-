"""
名称：生成稳定中台异常诊断预案.py
作用：读取稳定中台心跳快照，生成异常诊断预案和人工处置建议；心跳正常时生成备用诊断策略。
触发方式：python 生成稳定中台异常诊断预案.py
依赖：Python 标准库；稳定中台心跳_最新.json；稳定中台心跳规则.json。
所属系统：00杰哥系统总管
安全边界：只读取心跳快照并写入诊断预案；不自动修复、不重启服务、不触发n8n、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台异常诊断预案脚本。
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


def build_plan(alert: dict[str, Any]) -> dict[str, Any]:
    name = alert.get("异常", "未知异常")
    target = alert.get("对象", "未知对象")
    level = alert.get("等级", "中")
    return {
        "异常": name,
        "对象": target,
        "等级": level,
        "诊断步骤": [
            "读取最新心跳快照和相关验收日志",
            "确认异常是否连续出现",
            "定位异常影响范围",
            "形成原因判断和人工处置建议"
        ],
        "禁止动作": [
            "自动重启服务",
            "自动删除或覆盖文件",
            "自动关闭旧系统",
            "自动触发企业微信发送",
            "自动恢复税收业务施工"
        ],
        "人工介入建议": "高风险异常需人工确认处置；中低风险异常先连续观察两轮。",
    }


def main() -> int:
    root = v3_root()
    heartbeat_path = root / "00杰哥系统总管" / "03数据" / "状态快照" / "稳定中台心跳_最新.json"
    heartbeat = load_json(heartbeat_path)
    alerts = heartbeat.get("异常列表", [])
    plans = [build_plan(alert) for alert in alerts]
    if not plans:
        plans = [
            {
                "异常": "当前无异常",
                "对象": "稳定中台",
                "等级": "观察",
                "诊断步骤": [
                    "保持心跳快照定期生成",
                    "保留最近验收日志",
                    "真实接入前再次运行总体验收",
                    "异常出现时先生成诊断预案再决定是否修复"
                ],
                "禁止动作": [
                    "为优化而优化",
                    "无异常时新增补丁",
                    "无确认时触发真实业务"
                ],
                "人工介入建议": "当前无需人工处置，继续推进稳定中台建设。",
            }
        ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-diagnosis-plan",
        "来源心跳": str(heartbeat_path),
        "心跳通过": heartbeat.get("心跳通过"),
        "异常数量": len(alerts),
        "诊断预案": plans,
        "执行开关": {
            "是否自动修复": False,
            "是否重启服务": False,
            "是否删除文件": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否恢复税收业务": False
        },
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "稳定中台"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / "stable-hub-diagnosis-plan-最新.json"
    latest = output_dir / "stable-hub-diagnosis-plan-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"异常数量": len(alerts), "预案数量": len(plans), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
