# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信应急停用与回滚预案.py
作用：生成企业微信正式入口的应急停用、异常处置和回滚预案。
安全边界：只生成本地预案；不读取凭据、不联网、不真实发送、不修改入口状态。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信应急停用与回滚预案_最新.json"
OUT_MD = OUT_DIR / "税收企业微信应急停用与回滚预案_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    rollback_config = config.get("应急停用与回滚", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plan = {
        "名称": "税收企业微信应急停用与回滚预案",
        "生成时间": now,
        "配置来源": str(CONFIG),
        "预案状态": rollback_config.get("默认状态", "pending"),
        "紧急停用状态": rollback_config.get("紧急停用状态", False),
        "触发停用情形": rollback_config.get("触发停用情形", []),
        "上线前必填": {
            "回滚负责人": "",
            "异常联系人": "",
            "备用通知方式": "",
            "停用确认人": "",
            "恢复确认人": "",
            "最近一次演练时间": "",
            "备注": ""
        },
        "应急停用步骤": [
            "将税收企业微信正式入口配置中的入口状态改回dry_run_only。",
            "将真实发送放行改为false。",
            "撤销人工放行清单approved状态，改回pending或paused。",
            "撤销接收范围approved状态，改回pending或paused。",
            "重新运行发送门禁脚本，确认结论为已阻断。",
            "保留发送审计台账和异常说明，不删除历史审计记录。"
        ],
        "恢复发送前条件": [
            "异常原因已定位并记录。",
            "消息预演、凭据预检、接收范围、人工放行、发送门禁全部重新验收通过。",
            "人工确认不会发送正式税务意见或确定性适用结论。",
            "至少保留一次恢复前dry-run阻断报告。"
        ],
        "禁止动作": [
            "删除历史审计台账",
            "直接修改发送脚本绕过门禁",
            "把凭据写入配置、报告或日志",
            "在异常未复盘前恢复真实发送",
            "将待复核草案解释为正式税务意见"
        ],
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": False,
            "是否修改入口状态": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False
        }
    }
    OUT_JSON.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信应急停用与回滚预案",
        "",
        f"- 生成时间：{now}",
        f"- 预案状态：{plan['预案状态']}",
        f"- 紧急停用状态：{plan['紧急停用状态']}",
        "",
        "## 触发停用情形",
        "",
    ]
    for item in plan["触发停用情形"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 上线前必填", ""])
    for key, value in plan["上线前必填"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 应急停用步骤", ""])
    for item in plan["应急停用步骤"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 恢复发送前条件", ""])
    for item in plan["恢复发送前条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 禁止动作", ""])
    for item in plan["禁止动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in plan["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "预案状态": plan["预案状态"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
