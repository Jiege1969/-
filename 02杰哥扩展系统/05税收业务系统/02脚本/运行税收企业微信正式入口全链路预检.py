# -*- coding: utf-8 -*-
"""
名称：运行税收企业微信正式入口全链路预检.py
作用：按固定顺序运行企业微信正式入口的全链路预检和验收。
安全边界：只运行本地dry-run预检链路；入口未放行时不会真实发送；不修改正式配置。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信正式入口全链路预检_最新.json"
OUT_MD = OUT_DIR / "税收企业微信正式入口全链路预检_最新.md"


STEPS = [
    ("生成机器人终端绑定报告", "生成税收企业微信机器人终端绑定报告.py"),
    ("验证机器人终端绑定报告", "验证税收企业微信机器人终端绑定报告.py"),
    ("生成公共组件对齐核实报告", "生成税收企业微信公共组件对齐核实报告.py"),
    ("验证公共组件对齐核实报告", "验证税收企业微信公共组件对齐核实报告.py"),
    ("生成输入消息契约样例", "生成税收企业微信输入消息契约样例.py"),
    ("验证输入消息契约样例", "验证税收企业微信输入消息契约样例.py"),
    ("生成消息接收服务设计报告", "生成税收企业微信消息接收服务设计报告.py"),
    ("验证消息接收服务设计报告", "验证税收企业微信消息接收服务设计报告.py"),
    ("生成本地输入队列预演", "生成税收企业微信本地输入队列预演.py"),
    ("验证本地输入队列预演", "验证税收企业微信本地输入队列预演.py"),
    ("生成输入队列证据匹配影子流转", "生成税收企业微信输入队列证据匹配影子流转.py"),
    ("验证输入队列证据匹配影子流转", "验证税收企业微信输入队列证据匹配影子流转.py"),

    ("生成证据匹配到分析契约输入包", "生成税收企业微信证据匹配到分析契约输入包.py"),
    ("验证证据匹配到分析契约输入包", "验证税收企业微信证据匹配到分析契约输入包.py"),
    ("生成分析契约输入包到待复核草案骨架", "生成税收企业微信分析契约输入包到待复核草案骨架.py"),
    ("验证分析契约输入包到待复核草案骨架", "验证税收企业微信分析契约输入包到待复核草案骨架.py"),
    ("生成待复核草案骨架到分析摘要预演", "生成税收企业微信待复核草案骨架到分析摘要预演.py"),
    ("验证待复核草案骨架到分析摘要预演", "验证税收企业微信待复核草案骨架到分析摘要预演.py"),

    ("生成消息预演", "生成税收企业微信正式入口消息预演.py"),
    ("验证消息预演", "验证税收企业微信正式入口消息预演.py"),
    ("生成消息合规审查", "生成税收企业微信消息合规审查报告.py"),
    ("验证消息合规审查", "验证税收企业微信消息合规审查报告.py"),
    ("生成凭据接入预检", "生成税收企业微信凭据接入预检.py"),
    ("验证凭据接入预检", "验证税收企业微信凭据接入预检.py"),
    ("生成接收范围与消息分级", "生成税收企业微信接收范围与消息分级.py"),
    ("验证接收范围与消息分级", "验证税收企业微信接收范围与消息分级.py"),
    ("生成应急停用与回滚预案", "生成税收企业微信应急停用与回滚预案.py"),
    ("验证应急停用与回滚预案", "验证税收企业微信应急停用与回滚预案.py"),
    ("生成真实发送准备清单", "生成税收企业微信真实发送准备清单.py"),
    ("验证真实发送准备清单", "验证税收企业微信真实发送准备清单.py"),
    ("生成真实发送上线变更单", "生成税收企业微信真实发送上线变更单.py"),
    ("验证真实发送上线变更单", "验证税收企业微信真实发送上线变更单.py"),
    ("运行发送门禁", "税收企业微信正式入口发送器.py"),
    ("验证发送门禁", "验证税收企业微信正式入口发送门禁.py"),
    ("生成发送审计台账汇总", "生成税收企业微信发送审计台账汇总.py"),
    ("验证发送审计台账汇总", "验证税收企业微信发送审计台账汇总.py"),
    ("生成上线就绪度矩阵", "生成税收企业微信上线就绪度矩阵.py"),
    ("验证上线就绪度矩阵", "验证税收企业微信上线就绪度矩阵.py"),
    ("生成门禁反事实演练", "生成税收企业微信门禁反事实演练.py"),
    ("验证门禁反事实演练", "验证税收企业微信门禁反事实演练.py"),
    ("生成入口配置一致性巡检", "生成税收企业微信入口配置一致性巡检.py"),
    ("验证入口配置一致性巡检", "验证税收企业微信入口配置一致性巡检.py"),
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_step(name: str, script_name: str) -> dict[str, Any]:
    script = ROOT / "02脚本" / script_name
    start = datetime.now()
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    end = datetime.now()
    return {
        "步骤": name,
        "脚本": str(script),
        "返回码": completed.returncode,
        "是否通过": completed.returncode == 0,
        "开始时间": start.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": end.strftime("%Y-%m-%d %H:%M:%S"),
        "标准输出摘要": completed.stdout.strip()[-1000:],
        "错误输出摘要": completed.stderr.strip()[-1000:],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hard_stop = config.get("入口状态") == "real_send_enabled" or config.get("真实发送放行") is True
    steps: list[dict[str, Any]] = []
    if hard_stop:
        result = {
            "步骤": "全链路预检安全前置检查",
            "脚本": str(CONFIG),
            "返回码": 2,
            "是否通过": False,
            "开始时间": now,
            "结束时间": now,
            "标准输出摘要": "",
            "错误输出摘要": "入口状态或真实发送放行已打开；为避免预检链路误触发真实发送，本编排器拒绝继续。",
        }
        steps.append(result)
    else:
        for name, script_name in STEPS:
            steps.append(run_step(name, script_name))
            if not steps[-1]["是否通过"]:
                break

    passed = sum(1 for item in steps if item["是否通过"])
    failed = len(steps) - passed
    send_gate = load_json(OUT_DIR / "税收企业微信正式入口发送门禁_最新.json")
    matrix = load_json(OUT_DIR / "税收企业微信上线就绪度矩阵_最新.json")
    report = {
        "名称": "税收企业微信正式入口全链路预检",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "步骤数量": len(steps),
        "通过数量": passed,
        "失败数量": failed,
        "步骤结果": steps,
        "发送门禁结论": send_gate.get("结论", "缺失"),
        "是否真实发送": send_gate.get("是否真实发送", False),
        "上线矩阵结论": matrix.get("上线结论", "缺失"),
        "安全边界": {
            "是否联网": False,
            "是否读取凭据": False,
            "是否企业微信真实发送": bool(send_gate.get("是否真实发送", False)),
            "是否修改正式配置": False,
            "是否生成正式税务结论": False,
            "是否触发n8n": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信正式入口全链路预检",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 步骤数量：{report['步骤数量']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        f"- 发送门禁结论：{report['发送门禁结论']}",
        f"- 是否真实发送：{report['是否真实发送']}",
        f"- 上线矩阵结论：{report['上线矩阵结论']}",
        "",
        "## 步骤结果",
        "",
    ]
    for item in steps:
        lines.append(f"- {item['步骤']}：通过={item['是否通过']}，返回码={item['返回码']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "步骤数量": len(steps), "失败数量": failed, "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
