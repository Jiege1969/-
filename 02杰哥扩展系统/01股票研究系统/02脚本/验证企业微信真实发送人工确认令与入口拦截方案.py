# -*- coding: utf-8 -*-
"""
名称：验证企业微信真实发送人工确认令与入口拦截方案.py
作用：验收公共企业微信受控发送器在缺少有效人工确认令时，会本地阻断 --real-send，且不调用token、不发送、不触发n8n。
安全边界：只用显式不存在的确认令路径做本地阻断测试；不使用默认确认令；不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
SENDER = COMMON_ROOT / "02脚本" / "企业微信受控发送器.py"
OUT_DIR = DATA / "237企业微信真实发送人工确认令与入口拦截"
PLAN_JSON = OUT_DIR / "企业微信真实发送人工确认令与入口拦截方案_最新.json"
INVALID_CONFIRMATION = OUT_DIR / "不存在_用于验证真实发送阻断.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def parse_last_json(stdout: str) -> dict[str, Any]:
    text = str(stdout or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text.splitlines()[-1])
    except json.JSONDecodeError:
        return {"原始stdout": text}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信真实发送人工确认令与入口拦截验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item.get('说明', '')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    plan = load_json(PLAN_JSON)
    sender_text = read_text(SENDER)
    completed = subprocess.run(
        [
            sys.executable,
            str(SENDER),
            "--to",
            "ChenXiaoJie",
            "--content",
            "企业微信真实发送人工确认令拦截验证：此消息不应发送。",
            "--msgtype",
            "text",
            "--real-send",
            "--confirmation-file",
            str(INVALID_CONFIRMATION),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    stdout_json = parse_last_json(completed.stdout)
    sender_log = load_json(Path(stdout_json.get("输出", ""))) if stdout_json.get("输出") else {}
    sender_actions = sender_log.get("实际动作", {})
    confirmation = sender_log.get("真实发送人工确认令", {})
    checks = [
        check(PLAN_JSON.exists(), "237方案已生成", str(PLAN_JSON)),
        check(plan.get("公共发送器快照", {}).get("已包含确认令校验") is True, "方案记录发送器已包含确认令校验", plan.get("公共发送器快照", {})),
        check("validate_real_send_confirmation" in sender_text and "--confirmation-file" in sender_text, "公共发送器源码包含确认令入口", ""),
        check(not INVALID_CONFIRMATION.exists(), "验证使用的确认令路径不存在", str(INVALID_CONFIRMATION)),
        check(completed.returncode == 2, "缺少确认令时--real-send被阻断", {"returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}),
        check(stdout_json.get("ok") is False and stdout_json.get("allowed") is False, "发送器stdout显示不允许发送", stdout_json),
        check(sender_log.get("模式") == "real-send", "发送器进入real-send检查路径但未放行", sender_log.get("模式")),
        check(confirmation.get("有效") is False, "人工确认令无效", confirmation),
        check(sender_actions.get("调用企业微信获取token") is False and sender_actions.get("尝试发送企业微信") is False and sender_actions.get("发送企业微信成功") is False, "未调用token且未尝试发送", sender_actions),
        check(sender_actions.get("自动交易") is False and sender_log.get("实际动作", {}).get("写正式库") is False, "无交易和正式库动作", sender_actions),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信真实发送人工确认令与入口拦截验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "发送器阻断stdout": stdout_json,
        "发送器日志路径": stdout_json.get("输出", ""),
        "安全边界": {
            "使用默认确认令": False,
            "调用企业微信token接口": False,
            "尝试发送企业微信": False,
            "触发n8n": False,
            "重启服务": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信真实发送人工确认令与入口拦截验收_最新.json"
    latest_md = OUT_DIR / "企业微信真实发送人工确认令与入口拦截验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
