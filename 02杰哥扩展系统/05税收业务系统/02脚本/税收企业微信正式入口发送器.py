# -*- coding: utf-8 -*-
"""
名称：税收企业微信正式入口发送器.py
作用：企业微信正式入口的发送门禁脚本。
安全边界：默认只做dry-run阻断检查；只有配置、凭据、验收和人工放行全部满足时才允许真实发送。
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
PREVIEW = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口消息预演_最新.json"
TERMINAL_BINDING = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信机器人终端绑定报告_最新.json"
TERMINAL_BINDING_VALIDATION = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信机器人终端绑定报告验收_最新.json"
VALIDATION = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口消息预演验收_最新.json"
MESSAGE_COMPLIANCE = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信消息合规审查报告_最新.json"
MESSAGE_COMPLIANCE_VALIDATION = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信消息合规审查报告验收_最新.json"
APPROVAL = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信真实发送准备清单_最新.json"
RECIPIENT_SCOPE = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信接收范围与消息分级_最新.json"
ROLLBACK_PLAN = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信应急停用与回滚预案_最新.json"
CHANGE_REQUEST = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信真实发送上线变更单_最新.json"
CREDENTIAL_PRECHECK = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信凭据接入预检_最新.json"
CREDENTIAL_VALIDATION = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信凭据接入预检验收_最新.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
AUDIT_DIR = OUT_DIR / "发送审计"
REPORT_JSON = OUT_DIR / "税收企业微信正式入口发送门禁_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信正式入口发送门禁_最新.md"
LEDGER_JSON = OUT_DIR / "税收企业微信正式入口发送审计台账_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    audit_path = AUDIT_DIR / f"税收企业微信正式入口发送门禁_{report['审计编号']}.json"
    audit_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ledger = load_json(LEDGER_JSON, {"名称": "税收企业微信正式入口发送审计台账", "记录": []})
    ledger.setdefault("记录", []).append({
        "审计编号": report["审计编号"],
        "生成时间": report["生成时间"],
        "结论": report["结论"],
        "是否真实发送": report["是否真实发送"],
        "报告路径": str(audit_path),
    })
    LEDGER_JSON.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信正式入口发送门禁",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 审计编号：{report['审计编号']}",
        f"- 结论：{report['结论']}",
        f"- 是否真实发送：{report['是否真实发送']}",
        "",
        "## 门禁结果",
        "",
    ]
    for item in report.get("门禁结果", []):
        lines.append(f"- {item['门禁']}：{item['状态']}。{item['说明']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gate(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"门禁": name, "状态": "通过" if ok else "未通过", "说明": detail}


def main() -> int:
    config = load_json(CONFIG)
    preview = load_json(PREVIEW)
    terminal_binding = load_json(TERMINAL_BINDING)
    terminal_binding_validation = load_json(TERMINAL_BINDING_VALIDATION)
    validation = load_json(VALIDATION)
    message_compliance = load_json(MESSAGE_COMPLIANCE)
    message_compliance_validation = load_json(MESSAGE_COMPLIANCE_VALIDATION)
    approval = load_json(APPROVAL)
    recipient_scope = load_json(RECIPIENT_SCOPE)
    rollback_plan = load_json(ROLLBACK_PLAN)
    change_request = load_json(CHANGE_REQUEST)
    credential_precheck = load_json(CREDENTIAL_PRECHECK)
    credential_validation = load_json(CREDENTIAL_VALIDATION)
    webhook_var = config.get("凭据配置", {}).get("机器人Webhook环境变量", "TAX_WECOM_WEBHOOK_URL")
    webhook = os.environ.get(webhook_var, "")
    approval_status = approval.get("放行状态", "missing")
    allowed_status = set(config.get("人工放行", {}).get("允许状态", ["approved"]))
    scope_status = recipient_scope.get("接收范围状态", "missing")
    scope_allowed_status = set(config.get("接收范围治理", {}).get("允许状态", ["approved"]))
    rollback_status = rollback_plan.get("预案状态", "missing")
    rollback_allowed_status = set(config.get("应急停用与回滚", {}).get("允许状态", ["approved"]))
    emergency_stop = rollback_plan.get("紧急停用状态", config.get("应急停用与回滚", {}).get("紧急停用状态", False))
    change_status = change_request.get("变更状态", "missing")
    change_allowed_status = set(config.get("上线变更管理", {}).get("允许状态", ["approved"]))
    gates = [
        gate("机器人终端", terminal_binding.get("机器人名称") == "杰哥工作秘书" and terminal_binding_validation.get("结论") == "通过", f"机器人名称：{terminal_binding.get('机器人名称')}；验收：{terminal_binding_validation.get('结论')}"),
        gate("入口状态", config.get("入口状态") == "real_send_enabled", f"当前入口状态：{config.get('入口状态')}"),
        gate("真实发送放行", config.get("真实发送放行") is True, f"当前真实发送放行：{config.get('真实发送放行')}"),
        gate("上线变更单", change_status in change_allowed_status, f"当前变更状态：{change_status}"),
        gate("人工放行", approval_status in allowed_status, f"当前人工放行状态：{approval_status}"),
        gate("接收范围", scope_status in scope_allowed_status and bool(recipient_scope.get("接收范围白名单")), f"当前接收范围状态：{scope_status}；白名单数量：{len(recipient_scope.get('接收范围白名单', []))}"),
        gate("应急停用与回滚", rollback_status in rollback_allowed_status and emergency_stop is False, f"当前预案状态：{rollback_status}；紧急停用状态：{emergency_stop}"),
        gate("企业微信凭据", bool(webhook), f"环境变量{webhook_var}是否存在：{bool(webhook)}"),
        gate("凭据预检", credential_precheck.get("是否具备真实发送凭据条件") is True and credential_validation.get("结论") == "通过", f"预检条件：{credential_precheck.get('凭据预检结论')}；验收：{credential_validation.get('结论')}"),
        gate("消息预演验收", validation.get("结论") == "通过", f"当前验收结论：{validation.get('结论')}"),
        gate("消息合规审查", message_compliance.get("审查结论") == "通过" and message_compliance_validation.get("结论") == "通过", f"审查结论：{message_compliance.get('审查结论')}；验收：{message_compliance_validation.get('结论')}"),
        gate("预演未越界", preview.get("消息预演", {}).get("是否真实发送") is False, "预演阶段必须保持未发送记录。"),
    ]
    can_send = all(item["状态"] == "通过" for item in gates)
    sent = False
    error = ""

    if can_send:
        payload = {
            "msgtype": preview.get("消息预演", {}).get("消息类型", "markdown"),
            "markdown": {"content": preview.get("消息预演", {}).get("企业微信拟发送消息", "")},
        }
        try:
            request = urllib.request.Request(
                webhook,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8", errors="ignore")
            sent = True
            gates.append(gate("企业微信返回", True, body[:300]))
        except Exception as exc:  # pragma: no cover - real send path is manually gated.
            error = str(exc)
            gates.append(gate("企业微信返回", False, error))

    report = {
        "名称": "税收企业微信正式入口发送门禁",
        "审计编号": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "已发送" if sent else "已阻断",
        "是否真实发送": sent,
        "门禁结果": gates,
        "错误": error,
        "安全边界": {
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否写向量库": False,
            "是否企业微信真实发送": sent,
        },
    }
    write_report(report)
    print(json.dumps({"状态": report["结论"], "是否真实发送": sent, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not sent else 0


if __name__ == "__main__":
    raise SystemExit(main())
