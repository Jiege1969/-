# -*- coding: utf-8 -*-
"""
名称：验证股票n8n企业微信终端灰度链路.py
作用：验收n8n调度、文件桥接、股票报告生成、企业微信终端口径是否已形成灰度闭环。
触发方式：python 验证股票n8n企业微信终端灰度链路.py
依赖：Docker CLI；jiege_v3_n8n；股票n8n企业微信终端桥接服务.py。
安全边界：只读n8n状态和本地输出；只写验收日志；不真实发送企业微信；不接券商；不交易；不重载19310/19302。
标识：stock-n8n-wecom-terminal-gray-link-verify
"""

from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
N8N_CONTAINER = "jiege_v3_n8n"
WORKFLOW_NAME = "股票主动研究闭环_企业微信终端灰度启用"
OLD_WORKFLOW_NAME = "股票主动研究闭环_文件桥接未激活"
BRIDGE_RESPONSE = Path(r"D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\jiege_bridge\stock_active_research_response.json")
LATEST_BRIDGE_LOG = ROOT / "04日志" / "n8n企业微信终端桥接" / "stock-n8n-wecom-terminal-bridge-run-最新.json"
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
LOG_DIR = ROOT / "04日志" / "n8n企业微信终端灰度链路"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(args: list[str], timeout: int = 60) -> dict[str, Any]:
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "命令": args,
        "返回码": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "成功": completed.returncode == 0,
    }


def port_ready(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.5):
            return True
    except OSError:
        return False


def parse_workflow_list(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        workflow_id, name = line.split("|", 1)
        result[name.strip()] = workflow_id.strip()
    return result


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n企业微信终端灰度链路验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 通过：{report['统计']['通过']}",
        f"- 失败：{report['统计']['失败']}",
        "",
        "## 结论",
        "",
        report["结论"],
        "",
        "## 检查项",
        "",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['检查项']}：{item['通过']}；{item['说明']}")
    lines.extend([
        "",
        "## 边界",
        "",
        "- 未真实发送企业微信。",
        "- 未群发。",
        "- 未接券商，未交易。",
        "- 未自动转正式规则。",
        "- 未重载19310/19302。",
    ])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    active_result = run(["docker", "exec", N8N_CONTAINER, "n8n", "list:workflow", "--active=true"])
    inactive_result = run(["docker", "exec", N8N_CONTAINER, "n8n", "list:workflow", "--active=false"])
    active = parse_workflow_list(active_result.get("stdout", ""))
    inactive = parse_workflow_list(inactive_result.get("stdout", ""))
    bridge = load_json(LATEST_BRIDGE_LOG, {})
    bridge_output = str(bridge.get("股票助手结果", {}).get("输出") or "")
    workflow_artifact = load_json(OUT_DIR / "股票n8n企业微信终端灰度工作流_最新.json", {})
    workflow_text = json.dumps(workflow_artifact, ensure_ascii=False)
    node_types = [str(node.get("type")) for node in workflow_artifact.get("nodes", []) if isinstance(node, dict)]
    executable_nodes = [
        node for node in workflow_artifact.get("nodes", [])
        if isinstance(node, dict) and str(node.get("type")) in {"n8n-nodes-base.executeCommand", "n8n-nodes-base.httpRequest"}
    ]
    executable_text = json.dumps(executable_nodes, ensure_ascii=False)

    checks = [
        check("n8n容器可读取active列表", active_result.get("成功") is True, active_result.get("stderr")),
        check("灰度工作流已active", WORKFLOW_NAME in active, active),
        check("旧文件桥接未激活骨架已退出active", OLD_WORKFLOW_NAME not in active, active),
        check("桥接服务19312在线", port_ready(19312), "127.0.0.1:19312"),
        check("工作流包含Schedule Trigger", "n8n-nodes-base.scheduleTrigger" in node_types, node_types),
        check("工作流包含手动验证触发", "n8n-nodes-base.manualTrigger" in node_types, node_types),
        check("工作流不含Webhook节点", "webhook" not in workflow_text.lower(), "无webhook"),
        check("工作流不含credentials字段", "credentials" not in workflow_text.lower(), "无credentials"),
        check("工作流不含企业微信真实发送执行节点", "http" not in executable_text.lower() and "wecom_send" not in executable_text.lower() and "企业微信发送" not in executable_text, "执行节点只写共享触发文件"),
        check("桥接输出文件存在", BRIDGE_RESPONSE.exists(), str(BRIDGE_RESPONSE)),
        check("桥接最新运行成功", bridge.get("成功") is True or bridge.get("股票助手结果", {}).get("成功") is True, bridge.get("股票助手结果", {})),
        check("报告是使用者可读晨报/观察摘要", any(term in bridge_output for term in ["股票观察晨报", "今天重点看什么", "下一步怎么观察"]), bridge_output[:300]),
        check("报告保留企业微信反馈入口", "太空泛" in bridge_output and "风险没讲清" in bridge_output, bridge_output[-500:]),
        check("安全动作全为false", all(bridge.get("安全边界", {}).get(key) is False for key in ["真实发送企业微信", "群发", "调用券商接口", "自动交易", "自动转正式规则", "重载19310", "重载19302"]), bridge.get("安全边界", {})),
        check("工作流不含危险实际动作", not any(term in executable_text for term in ["下单", "自动交易", "群发", "real_send", "broker"]), "执行节点未发现交易/群发/真实发送动作"),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票n8n企业微信终端灰度链路验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "结论": "已形成n8n定时/手动触发 -> 文件桥接 -> 股票系统生成企业微信可读报告 -> 反馈入口沉淀的灰度闭环。" if not failed else "灰度闭环仍有阻断项，详见检查项。",
        "检查项": checks,
        "统计": {"通过": len(checks) - len(failed), "失败": len(failed)},
        "active工作流": active,
        "inactive工作流相关": {name: wid for name, wid in inactive.items() if "股票" in name and "n8n" in name or name == OLD_WORKFLOW_NAME},
        "桥接日志": str(LATEST_BRIDGE_LOG),
        "桥接输出": str(BRIDGE_RESPONSE),
        "安全边界": {
            "真实发送企业微信": False,
            "群发": False,
            "调用券商接口": False,
            "自动交易": False,
            "自动转正式规则": False,
            "重载19310": False,
            "重载19302": False,
        },
    }
    output_json = LOG_DIR / f"stock-n8n-wecom-terminal-gray-link-verify-{stamp}.json"
    latest_json = LOG_DIR / "stock-n8n-wecom-terminal-gray-link-verify-最新.json"
    output_md = LOG_DIR / f"stock-n8n-wecom-terminal-gray-link-verify-{stamp}.md"
    latest_md = LOG_DIR / "stock-n8n-wecom-terminal-gray-link-verify-最新.md"
    out_report_json = OUT_DIR / "股票n8n企业微信终端灰度链路验收_最新.json"
    out_report_md = OUT_DIR / "股票n8n企业微信终端灰度链路验收_最新.md"
    markdown = build_markdown(report)
    for path in (output_json, latest_json, out_report_json):
        write_json(path, report)
    for path in (output_md, latest_md, out_report_md):
        write_text(path, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["统计"]["通过"], "失败": report["统计"]["失败"], "报告": str(out_report_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
