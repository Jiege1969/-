# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信上线就绪度矩阵.py
作用：汇总企业微信正式入口各项门禁，生成上线就绪度矩阵。
安全边界：只读配置和本地验收报告；不读取凭据、不联网、不真实发送。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
SOURCES = {
    "机器人终端绑定": OUT_DIR / "税收企业微信机器人终端绑定报告_最新.json",
    "机器人终端绑定验收": OUT_DIR / "税收企业微信机器人终端绑定报告验收_最新.json",
    "消息预演": OUT_DIR / "税收企业微信正式入口消息预演验收_最新.json",
    "消息合规审查": OUT_DIR / "税收企业微信消息合规审查报告验收_最新.json",
    "上线变更单": OUT_DIR / "税收企业微信真实发送上线变更单_最新.json",
    "上线变更单验收": OUT_DIR / "税收企业微信真实发送上线变更单验收_最新.json",
    "凭据接入预检": OUT_DIR / "税收企业微信凭据接入预检_最新.json",
    "凭据预检验收": OUT_DIR / "税收企业微信凭据接入预检验收_最新.json",
    "接收范围与消息分级": OUT_DIR / "税收企业微信接收范围与消息分级_最新.json",
    "接收范围验收": OUT_DIR / "税收企业微信接收范围与消息分级验收_最新.json",
    "应急停用与回滚预案": OUT_DIR / "税收企业微信应急停用与回滚预案_最新.json",
    "应急停用与回滚验收": OUT_DIR / "税收企业微信应急停用与回滚预案验收_最新.json",
    "真实发送准备清单": OUT_DIR / "税收企业微信真实发送准备清单_最新.json",
    "真实发送准备清单验收": OUT_DIR / "税收企业微信真实发送准备清单验收_最新.json",
    "发送门禁": OUT_DIR / "税收企业微信正式入口发送门禁_最新.json",
    "发送门禁验收": OUT_DIR / "税收企业微信正式入口发送门禁验收_最新.json",
}
OUT_JSON = OUT_DIR / "税收企业微信上线就绪度矩阵_最新.json"
OUT_MD = OUT_DIR / "税收企业微信上线就绪度矩阵_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def row(name: str, status: str, can_pass: bool, blocker: str, source: Path) -> dict[str, Any]:
    return {
        "门禁": name,
        "状态": status,
        "是否通过": can_pass,
        "阻断原因": blocker,
        "来源": str(source),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    data = {name: load_json(path) for name, path in SOURCES.items()}
    terminal_ready = data["机器人终端绑定"].get("机器人名称") == "杰哥工作秘书" and data["机器人终端绑定验收"].get("结论") == "通过"
    message_ok = data["消息预演"].get("结论") == "通过"
    compliance_ok = data["消息合规审查"].get("结论") == "通过"
    change_ready = data["上线变更单"].get("变更状态") == "approved" and data["上线变更单验收"].get("结论") == "通过"
    credential_ready = data["凭据接入预检"].get("是否具备真实发送凭据条件") is True and data["凭据预检验收"].get("结论") == "通过"
    scope_ready = data["接收范围与消息分级"].get("接收范围状态") == "approved" and bool(data["接收范围与消息分级"].get("接收范围白名单"))
    scope_validation_ok = data["接收范围验收"].get("结论") == "通过"
    rollback_ready = data["应急停用与回滚预案"].get("预案状态") == "approved" and data["应急停用与回滚预案"].get("紧急停用状态") is False
    rollback_validation_ok = data["应急停用与回滚验收"].get("结论") == "通过"
    approval_ready = data["真实发送准备清单"].get("放行状态") == "approved"
    approval_validation_ok = data["真实发送准备清单验收"].get("结论") == "通过"
    config_ready = config.get("入口状态") == "real_send_enabled" and config.get("真实发送放行") is True
    send_gate_blocked = data["发送门禁"].get("结论") == "已阻断" and data["发送门禁"].get("是否真实发送") is False
    send_gate_validation_ok = data["发送门禁验收"].get("结论") == "通过"

    rows = [
        row("机器人终端绑定", data["机器人终端绑定"].get("绑定状态", "缺失"), terminal_ready, "杰哥工作秘书终端绑定缺失或验收未通过。", SOURCES["机器人终端绑定"]),
        row("入口状态与发送放行", f"入口状态={config.get('入口状态')}；真实发送放行={config.get('真实发送放行')}", config_ready, "入口状态或真实发送放行未打开。", CONFIG),
        row("消息预演", data["消息预演"].get("结论", "缺失"), message_ok, "消息预演验收未通过。", SOURCES["消息预演"]),
        row("消息合规审查", data["消息合规审查"].get("结论", "缺失"), compliance_ok, "消息合规审查未通过。", SOURCES["消息合规审查"]),
        row("上线变更单", data["上线变更单"].get("变更状态", "缺失"), change_ready, "上线变更单未approved或验收未通过。", SOURCES["上线变更单"]),
        row("凭据接入预检", data["凭据接入预检"].get("凭据预检结论", "缺失"), credential_ready, "未发现可用企业微信凭据形态，或凭据预检验收未通过。", SOURCES["凭据接入预检"]),
        row("接收范围与消息分级", data["接收范围与消息分级"].get("接收范围状态", "缺失"), scope_ready and scope_validation_ok, "接收范围未approved或白名单为空。", SOURCES["接收范围与消息分级"]),
        row("应急停用与回滚预案", data["应急停用与回滚预案"].get("预案状态", "缺失"), rollback_ready and rollback_validation_ok, "回滚预案未approved或紧急停用状态打开。", SOURCES["应急停用与回滚预案"]),
        row("人工放行准备清单", data["真实发送准备清单"].get("放行状态", "缺失"), approval_ready and approval_validation_ok, "人工放行状态未approved。", SOURCES["真实发送准备清单"]),
        row("发送门禁与审计", data["发送门禁"].get("结论", "缺失"), send_gate_blocked and send_gate_validation_ok, "发送门禁报告缺失或验收失败。", SOURCES["发送门禁"]),
    ]
    hard_blockers = [item for item in rows if not item["是否通过"]]
    real_send_allowed = not hard_blockers and config_ready
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信上线就绪度矩阵",
        "生成时间": now,
        "上线结论": "允许真实发送" if real_send_allowed else "不得真实发送",
        "真实发送允许": real_send_allowed,
        "通过门禁数量": len(rows) - len(hard_blockers),
        "阻断门禁数量": len(hard_blockers),
        "门禁矩阵": rows,
        "当前阻断": hard_blockers,
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信上线就绪度矩阵",
        "",
        f"- 生成时间：{now}",
        f"- 上线结论：{report['上线结论']}",
        f"- 真实发送允许：{real_send_allowed}",
        f"- 通过门禁数量：{report['通过门禁数量']}",
        f"- 阻断门禁数量：{report['阻断门禁数量']}",
        "",
        "## 门禁矩阵",
        "",
    ]
    for item in rows:
        lines.append(f"- {item['门禁']}：通过={item['是否通过']}；状态={item['状态']}；阻断={item['阻断原因']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "上线结论": report["上线结论"], "阻断门禁数量": report["阻断门禁数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
