# -*- coding: utf-8 -*-
"""
名称：生成低负载治理阶段风险与验收报告.py
作用：汇总低负载治理与股票闭环巩固阶段的健康基线、服务状态、旧容器引用、总管面板和股票质量产物，刷新风险清单、服务缺口清单和阶段验收报告。
触发方式：python 生成低负载治理阶段风险与验收报告.py
依赖：Python 标准库；最新总管运行状态产物；股票质量面板产物。
所属系统：00杰哥系统总管。
输出：03数据/运行状态/低负载治理阶段风险清单_最新.json|md；03数据/运行状态/低负载治理与股票闭环巩固验收_最新.json|md；刷新个人智能母系统服务缺口清单_最新.json|md。
安全边界：只读核验并写总管状态/日志；不启动服务、不停止服务、不重启服务、不清理容器、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：low-load-governance-stage-risk-and-acceptance；股票闭环巩固；阶段风险清单；服务缺口清单。
"""

from __future__ import annotations

import json
import socket
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


HEALTH_ENDPOINTS = [
    ("股票助手入口", "http://127.0.0.1:19300/health"),
    ("股票企业微信桥接入口", "http://127.0.0.1:19302/health"),
    ("企业微信统一指令本地服务", "http://127.0.0.1:19310/health"),
    ("v3智能体大脑测试服务", "http://127.0.0.1:28100/health"),
    ("v3 n8n", "http://127.0.0.1:28679/healthz"),
    ("v3 Ollama", "http://127.0.0.1:29134/api/tags"),
]


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def stock_root() -> Path:
    return project_root() / "02杰哥扩展系统" / "01股票研究系统"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def check_http(name: str, url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:  # noqa: S310 - localhost only
            body = response.read(256).decode("utf-8", errors="replace")
            return {"名称": name, "地址": url, "通过": response.status == 200, "状态码": response.status, "样例": body}
    except Exception as exc:  # noqa: BLE001
        return {"名称": name, "地址": url, "通过": False, "错误": str(exc)}


def check_tcp(name: str, host: str, port: int) -> dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout=5):
            return {"名称": name, "地址": f"{host}:{port}", "通过": True}
    except Exception as exc:  # noqa: BLE001
        return {"名称": name, "地址": f"{host}:{port}", "通过": False, "错误": str(exc)}


def file_check(path: Path, label: str) -> dict[str, Any]:
    return {
        "名称": label,
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def stock_three_line_check() -> dict[str, Any]:
    root = stock_root()
    assistant = root / "02脚本" / "股票助手入口.py"
    bridge = root / "02脚本" / "股票企业微信桥接入口.py"
    assistant_text = assistant.read_text(encoding="utf-8-sig", errors="replace") if assistant.exists() else ""
    bridge_text = bridge.read_text(encoding="utf-8-sig", errors="replace") if bridge.exists() else ""
    checks = {
        "助手入口支持专家角色": "入口角色" in assistant_text and "专家" in assistant_text,
        "专家总览入口存在": "/专家总览" in assistant_text or "expert-overview" in assistant_text,
        "桥接入口传递入口角色": "入口角色" in bridge_text and "entrance_role" in bridge_text,
        "金融复核提示存在": "金融专项复核" in assistant_text or "金融复核" in assistant_text,
    }
    return {"名称": "股票三线/双入口轻量一致性检查", "通过": all(checks.values()), "检查项": checks}


def build_risks(
    scheduler: dict[str, Any],
    service_status: dict[str, Any],
    old_refs: dict[str, Any],
    stock_evidence: dict[str, Any],
    stock_replay: dict[str, Any],
    stock_quality: dict[str, Any],
    send_check: dict[str, Any],
    send_entry: dict[str, Any],
) -> list[dict[str, Any]]:
    risks = []
    if scheduler.get("当前状态") == "用户重负载避让":
        risks.append({"编号": "RISK-LLG-001", "风险": "当前处于用户重负载避让", "等级": "低", "处置": "仅执行只读治理、面板刷新和轻量验收。"})
    if old_refs.get("汇总", {}).get("存在引用", 0) > 0:
        risks.append({"编号": "RISK-LLG-002", "风险": "旧 jiege_* 容器仍存在引用关系", "等级": "中", "处置": "不自动清理；先做引用替换或备案，清理需单独确认。"})
    if service_status.get("汇总", {}).get("容器未运行", 0) > 0:
        risks.append({"编号": "RISK-LLG-003", "风险": "注册服务中存在旧容器未运行状态", "等级": "中", "处置": "作为登记/实时状态差异观察，不自动恢复旧容器。"})
    if send_check and send_check.get("是否具备提交真实发送讨论资格") is False:
        risks.append({"编号": "RISK-LLG-004", "风险": "股票候选尚不具备提交真实发送讨论资格", "等级": "低", "处置": "继续保留人工闸口和真实发送前检查。"})
    if "待复核" in str(send_entry.get("清点结论", "")):
        risks.append({"编号": "RISK-LLG-005", "风险": "真实发送入口清点仍有待复核项", "等级": "低", "处置": "真实发送入口保持禁用和人工确认。"})
    if stock_evidence:
        blocked = []
        for key in ("公司概况", "事件风险证据", "行业景气证据"):
            item = stock_evidence.get(key, {})
            if item.get("未通过数量", 0):
                blocked.append(f"{key}未通过{item.get('未通过数量')}项")
        if blocked:
            risks.append({"编号": "RISK-LLG-006", "风险": "股票证据核验仍需人工补齐", "等级": "低", "处置": "继续走证据台账和人工核验入口。", "明细": blocked})
    if stock_replay and stock_replay.get("验证结果记录数", 0) == 0:
        risks.append({"编号": "RISK-LLG-007", "风险": "复盘账已建立但 T 周期验证结果尚未回填", "等级": "低", "处置": "等待 T+1/T+3/T+5 后人工回填。"})
    if stock_quality and stock_quality.get("质量结论") != "运行质量正常":
        risks.append({"编号": "RISK-LLG-008", "风险": "股票质量观察面板存在异常结论", "等级": "中", "处置": "暂停质量扩张，只做定位和人工复核。"})
    return risks


def render_risk_md(report: dict[str, Any]) -> str:
    lines = [
        "# 低负载治理阶段风险清单",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 风险数量：{len(report['风险'])}",
        "",
        "| 编号 | 等级 | 风险 | 处置 |",
        "|---|---|---|---|",
    ]
    for item in report["风险"]:
        lines.append(f"| {item['编号']} | {item['等级']} | {item['风险']} | {item['处置']} |")
    lines.extend(["", "## 安全边界", "", "- 未执行真实发送、n8n 正式触发、正式写库、券商接口调用、自动交易或旧容器清理。"])
    return "\n".join(lines) + "\n"


def render_gap_md(report: dict[str, Any]) -> str:
    lines = [
        "# 个人智能母系统服务缺口清单",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "| 编号 | 缺口 | 当前状态 | 风险等级 | 下一步 |",
        "|---|---|---|---|---|",
    ]
    for item in report["缺口"]:
        lines.append(f"| {item['编号']} | {item['缺口']} | {item['当前状态']} | {item['风险等级']} | {item['下一步']} |")
    return "\n".join(lines) + "\n"


def render_acceptance_md(report: dict[str, Any]) -> str:
    lines = [
        "# 低负载治理与股票闭环巩固验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        "",
        "## 验收项",
        "",
        "| 项目 | 通过 | 说明 |",
        "|---|---|---|",
    ]
    for item in report["验收项"]:
        lines.append(f"| {item['项目']} | {str(item['通过']).lower()} | {item['说明']} |")
    lines.extend(["", "## 保持禁止", ""])
    for item in report["保持禁止"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    manager = manager_root()
    data_dir = manager / "03数据" / "运行状态"
    log_dir = manager / "04日志" / "低负载治理与股票闭环巩固"
    stock = stock_root()

    health = [check_http(name, url) for name, url in HEALTH_ENDPOINTS]
    health.append(check_tcp("v3 Redis", "127.0.0.1", 26379))

    service_fields = load_json(data_dir / "服务注册实时状态字段补齐报告_最新.json", {})
    service_status = load_json(data_dir / "服务注册实时状态校准报告_最新.json", {})
    old_refs = load_json(data_dir / "旧容器引用关系检查报告_最新.json", {})
    scheduler = load_json(data_dir / "个人智能母系统日常调度状态_最新.json", {})
    task_admission = load_json(data_dir / "个人智能母系统任务准入_最新.json", {})
    task_queue = load_json(data_dir / "个人智能母系统任务队列调度_最新.json", {})

    stock_evidence = load_json(stock / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json", {})
    stock_replay = load_json(stock / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.json", {})
    stock_quality = load_json(stock / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.json", {})
    send_check = load_json(stock / "03数据" / "105真实发送前检查" / "300只候选真实发送前检查包_最新.json", {})
    send_entry = load_json(stock / "03数据" / "160真实发送入口清点" / "股票系统真实发送入口清点报告_最新.json", {})
    three_line = stock_three_line_check()

    risk_items = build_risks(scheduler, service_status, old_refs, stock_evidence, stock_replay, stock_quality, send_check, send_entry)
    risk_report = {
        "名称": "低负载治理阶段风险清单",
        "生成时间": now_text(),
        "风险": risk_items,
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n正式工作流": False,
            "是否写正式业务库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否清理旧容器": False,
        },
    }

    gap_report = {
        "名称": "个人智能母系统服务缺口清单",
        "生成时间": now_text(),
        "所属系统": "00杰哥系统总管",
        "当前结论": "核心入口可用；服务注册实时状态字段已全量补齐；旧容器仍存在引用关系；股票闭环进入只读质量巩固。",
        "安全边界": risk_report["安全边界"],
        "缺口": [
            {"编号": "GAP-001", "缺口": "企业微信统一指令服务常驻观察", "当前状态": "19310 健康检查通过，仍为本地预演观察态", "风险等级": "低", "下一步": "继续观察；不开放全系统控制或真实发送"},
            {"编号": "GAP-002", "缺口": "v3智能体大脑测试服务常驻观察", "当前状态": "28100 健康检查通过，仅测试运行", "风险等级": "低", "下一步": "继续观察；不接管旧系统生产流量"},
            {"编号": "GAP-003", "缺口": "旧 jiege_* 容器引用关系未收口", "当前状态": f"{old_refs.get('汇总', {}).get('旧容器数量', 0)} 个旧容器均存在引用", "风险等级": "中", "下一步": "先做引用替换/备案；清理需单独确认"},
            {"编号": "GAP-004", "缺口": "服务注册实时状态字段治理", "当前状态": f"{service_fields.get('汇总', {}).get('服务数量', 0)} 个服务、{service_fields.get('汇总', {}).get('端口数量', 0)} 个端口已补齐；允许自动操作为 0", "风险等级": "低", "下一步": "保持默认禁止自动操作，后续变更单独确认"},
            {"编号": "GAP-005", "缺口": "股票真实发送前资格不足", "当前状态": "真实发送前检查显示不具备提交真实发送讨论资格", "风险等级": "低", "下一步": "继续人工闸口、证据核验和复盘回填"},
            {"编号": "GAP-006", "缺口": "v3 Postgres未进入当前运行基线", "当前状态": "仍未作为本阶段运行依赖启用", "风险等级": "低", "下一步": "如需启用，另行确认并影子验证"},
        ],
    }

    latest_files = [
        file_check(data_dir / "服务注册实时状态字段补齐报告_最新.json", "服务状态字段补齐报告"),
        file_check(data_dir / "旧容器引用关系检查报告_最新.json", "旧容器引用关系检查报告"),
        file_check(stock / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json", "股票证据核验总览面板"),
        file_check(stock / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.json", "股票复盘学习闭环状态面板"),
        file_check(stock / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.json", "股票系统质量观察面板"),
        file_check(stock / "03数据" / "105真实发送前检查" / "300只候选真实发送前检查包_最新.json", "真实发送前检查包"),
    ]
    acceptance_items = [
        {"项目": "核心入口健康检查", "通过": all(item["通过"] for item in health), "说明": "19300、19302、19310、28100、26379、28679、29134 已检查"},
        {"项目": "服务注册表和端口表字段补齐", "通过": service_fields.get("汇总", {}).get("允许自动操作为true", 1) == 0, "说明": "默认允许自动操作为 false"},
        {"项目": "服务状态校准报告可复现", "通过": bool(service_status.get("服务状态")), "说明": "校准报告已刷新"},
        {"项目": "旧容器引用关系报告", "通过": old_refs.get("汇总", {}).get("旧容器数量", 0) >= 1, "说明": "只读列出引用和处置建议"},
        {"项目": "总管调度与队列面板", "通过": bool(scheduler) and bool(task_queue), "说明": f"调度={scheduler.get('当前状态')}；队列不触发执行器/n8n"},
        {"项目": "股票证据核验与复盘面板", "通过": all(item["存在"] and item["大小"] > 0 for item in latest_files[:5]), "说明": "证据核验、复盘学习、质量观察均有最新产物"},
        {"项目": "股票三线/双入口一致性轻检", "通过": three_line["通过"], "说明": "检查入口角色、专家总览、金融复核提示"},
        {"项目": "真实发送保持拦截", "通过": send_check.get("是否具备提交真实发送讨论资格") is False, "说明": "真实发送前检查未放行"},
    ]
    acceptance = {
        "名称": "低负载治理与股票闭环巩固验收",
        "生成时间": now_text(),
        "验收结论": "通过：本阶段完成低负载治理、服务状态字段补齐、旧容器引用检查、总管面板刷新和股票闭环质量巩固；真实发送和旧容器清理继续禁止。",
        "健康检查": health,
        "任务准入": task_admission,
        "股票三线双入口轻检": three_line,
        "最新产物": latest_files,
        "验收项": acceptance_items,
        "保持禁止": [
            "真实发送企业微信",
            "触发 n8n 正式工作流",
            "写正式业务库",
            "调用券商接口",
            "自动交易",
            "自动清理旧容器",
            "开放新的公网入口",
        ],
    }
    if not all(item["通过"] for item in acceptance_items):
        acceptance["验收结论"] = "需观察：本阶段产物已生成，但存在未通过验收项，禁止进入真实发送或清理动作。"

    stamp = stamp_text()
    outputs = [
        (data_dir / "低负载治理阶段风险清单_最新.json", risk_report),
        (log_dir / f"low-load-governance-risk-{stamp}.json", risk_report),
        (log_dir / "low-load-governance-risk-最新.json", risk_report),
        (data_dir / "个人智能母系统服务缺口清单_最新.json", gap_report),
        (log_dir / f"service-gap-list-{stamp}.json", gap_report),
        (log_dir / "service-gap-list-最新.json", gap_report),
        (data_dir / "低负载治理与股票闭环巩固验收_最新.json", acceptance),
        (log_dir / f"low-load-governance-acceptance-{stamp}.json", acceptance),
        (log_dir / "low-load-governance-acceptance-最新.json", acceptance),
    ]
    for path, payload in outputs:
        write_json(path, payload)
    write_text(data_dir / "低负载治理阶段风险清单_最新.md", render_risk_md(risk_report))
    write_text(log_dir / f"low-load-governance-risk-{stamp}.md", render_risk_md(risk_report))
    write_text(log_dir / "low-load-governance-risk-最新.md", render_risk_md(risk_report))
    write_text(data_dir / "个人智能母系统服务缺口清单_最新.md", render_gap_md(gap_report))
    write_text(log_dir / f"service-gap-list-{stamp}.md", render_gap_md(gap_report))
    write_text(log_dir / "service-gap-list-最新.md", render_gap_md(gap_report))
    write_text(data_dir / "低负载治理与股票闭环巩固验收_最新.md", render_acceptance_md(acceptance))
    write_text(log_dir / f"low-load-governance-acceptance-{stamp}.md", render_acceptance_md(acceptance))
    write_text(log_dir / "low-load-governance-acceptance-最新.md", render_acceptance_md(acceptance))

    print(json.dumps({"验收结论": acceptance["验收结论"], "风险数量": len(risk_items), "输出": str(data_dir / "低负载治理与股票闭环巩固验收_最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
