# -*- coding: utf-8 -*-
"""
名称：生成四系统股票小闭环状态面板.py
作用：汇总总管、智能系统、股票扩展系统、进化系统四个环节，生成股票样板小闭环状态面板。
触发方式：python 生成四系统股票小闭环状态面板.py
依赖：本机Python标准库、19300/19302本地健康接口、股票系统最新验收和四系统相关状态文件。
所属系统：00杰哥系统总管
输出：03数据/四系统小闭环/四系统股票小闭环状态面板_最新.json 与 .md。
安全边界：只读取本地状态文件和本机健康接口；只写00总管03数据/四系统小闭环；不重启服务；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不写正式业务库。
标识：four-system-stock-loop-panel-generate
"""

from __future__ import annotations

import json
import socket
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default if default is not None else {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def text_contains(path: Path, terms: list[str]) -> bool:
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return False
    return all(term in text for term in terms)


def port_listening(port: int, host: str = "127.0.0.1", timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_json(url: str, timeout: float = 3.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        return {"可访问": True, "数据": json.loads(raw)}
    except Exception as exc:
        return {"可访问": False, "错误": str(exc)}


def powershell_json(script: Path, timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        stdout = (completed.stdout or "").strip()
        data = json.loads(stdout) if stdout else {}
        return {
            "执行成功": completed.returncode == 0,
            "返回码": completed.returncode,
            "数据": data,
            "stderr": (completed.stderr or "").strip()[-1000:],
        }
    except Exception as exc:
        return {"执行成功": False, "返回码": -1, "数据": {}, "stderr": str(exc)}


def parse_acceptance(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    if isinstance(data, dict):
        return {
            "路径": str(path),
            "存在": path.exists(),
            "结论": data.get("验收结论") or data.get("状态") or data.get("运行结论"),
            "通过数量": data.get("通过数量") or data.get("通过数"),
            "失败数量": data.get("失败数量") if data.get("失败数量") is not None else data.get("失败数"),
        }
    return {"路径": str(path), "存在": path.exists(), "结论": "", "通过数量": None, "失败数量": None}


def check_item(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def role_status(name: str, duty: str, checks: list[dict[str, Any]], next_action: str) -> dict[str, Any]:
    failed = [item for item in checks if item["结果"] != "通过"]
    return {
        "环节": name,
        "职责": duty,
        "状态": "通过" if not failed else "待修复",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "下一步": next_action,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 四系统股票小闭环状态面板 - {report['生成时间']}",
        "",
        "## 一、闭环结论",
        "",
        f"- 总结论：{report['闭环结论']}",
        f"- 闭环成熟度：{report['闭环成熟度']}",
        f"- 通过环节：{report['通过环节数']}/{report['总环节数']}",
        f"- 当前机器状态：{report['当前机器状态']}",
        f"- 当前人工下一步：{report['当前人工下一步']}",
        f"- 下一到期日：{report['下一到期日']}",
        "",
        "## 二、四系统状态",
        "",
        "| 环节 | 职责 | 状态 | 通过 | 失败 | 下一步 |",
        "|---|---|---|---:|---:|---|",
    ]
    for role in report["四系统状态"]:
        lines.append(
            f"| {role['环节']} | {role['职责']} | {role['状态']} | {role['通过数量']} | {role['失败数量']} | {role['下一步']} |"
        )

    lines.extend(["", "## 三、闭环链路", ""])
    for index, item in enumerate(report["闭环链路"], 1):
        lines.append(f"{index}. {item}")

    lines.extend(["", "## 四、关键验收", ""])
    for item in report["关键验收"]:
        lines.append(f"- {item['检查项']}：{item['结果']}，{item['详情']}")

    lines.extend(["", "## 五、可重复执行清单", ""])
    for item in report["可重复执行清单"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 六、安全边界", ""])
    for item in report["安全边界"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = system_root()
    manager = root / "00杰哥系统总管"
    intelligence = root / "01杰哥智能系统"
    stock = root / "02杰哥扩展系统" / "01股票研究系统"
    evolution = root / "03杰哥进化系统"
    now = datetime.now()
    final_acceptance = stock / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.json"
    c_acceptance = stock / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.json"
    daily_run = stock / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.json"
    front_regression = stock / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.json"
    data_check = stock / "03数据" / "183报告数据口径检查" / "股票报告数据口径检查_最新.json"
    risk_panel = stock / "03数据" / "184风险失效条件观察面板" / "股票风险失效条件观察面板_最新.md"
    finance_coverage = stock / "03数据" / "186金融复核覆盖面板" / "推荐观察股金融复核覆盖面板_最新.json"
    replay_panel = stock / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.json"
    replay_due = stock / "03数据" / "188判断复盘到期提醒与人工填写清单" / "股票判断复盘到期提醒与人工填写清单_最新.json"
    evidence_entry = stock / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json"
    single_stock_evidence_package = stock / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.json"
    single_stock_manual_ledger = stock / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.json"
    single_stock_sync_preview = stock / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.json"
    single_stock_template_sync_gate = stock / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"
    evidence_overview = stock / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json"
    verification_pipeline_status = stock / "03数据" / "300候选核验流水线" / "300核验流水线状态_最新.json"

    final_status = parse_acceptance(final_acceptance)
    c_status = parse_acceptance(c_acceptance)
    daily_status = parse_acceptance(daily_run)
    front_status = parse_acceptance(front_regression)
    data_status = parse_acceptance(data_check)
    finance_data = load_json(finance_coverage, {})
    replay_data = load_json(replay_panel, {})
    due_data = load_json(replay_due, {})
    evidence_entry_data = load_json(evidence_entry, {})
    single_stock_evidence_package_data = load_json(single_stock_evidence_package, {})
    single_stock_manual_ledger_data = load_json(single_stock_manual_ledger, {})
    single_stock_sync_preview_data = load_json(single_stock_sync_preview, {})
    single_stock_template_sync_gate_data = load_json(single_stock_template_sync_gate, {})
    evidence_overview_data = load_json(evidence_overview, {})
    verification_pipeline_status_data = load_json(verification_pipeline_status, {})
    stock_assistant = http_json("http://127.0.0.1:19300/health")
    wework_bridge = http_json("http://127.0.0.1:19302/health")
    public_callback = powershell_json(stock / "02脚本" / "查看股票公网回调状态.ps1", timeout=90)

    manager_checks = [
        check_item("总管设计纲领存在", (manager / "07文档" / "设计纲领" / "务实闭环搭建原则与四系统小闭环方案_20260502.md").exists(), file_state(manager / "07文档" / "设计纲领" / "务实闭环搭建原则与四系统小闭环方案_20260502.md")),
        check_item("施工方向校准原则存在", (manager / "07文档" / "设计纲领" / "施工方向校准原则_埋头拉车也要抬头看路_20260502.md").exists(), file_state(manager / "07文档" / "设计纲领" / "施工方向校准原则_埋头拉车也要抬头看路_20260502.md")),
        check_item("四系统下一阶段施工方案存在", (manager / "07文档" / "设计纲领" / "四系统闭环下一阶段补充意见与施工方案_20260502.md").exists(), file_state(manager / "07文档" / "设计纲领" / "四系统闭环下一阶段补充意见与施工方案_20260502.md")),
        check_item("开工上下文接续存在", (manager / "03数据" / "开工上下文" / "AI施工接续最小包_最新.md").exists(), file_state(manager / "03数据" / "开工上下文" / "AI施工接续最小包_最新.md")),
        check_item("今日工作日志存在", (manager / "07文档" / "工作日志" / "2026-05-03.md").exists(), file_state(manager / "07文档" / "工作日志" / "2026-05-03.md")),
        check_item("接续包更新边界已写入日志", text_contains(manager / "07文档" / "工作日志" / "2026-05-03.md", ["施工过程中不要每次写入施工接续包", "只有当天收工或用户明确要新开对话时才统一更新"]), file_state(manager / "07文档" / "工作日志" / "2026-05-03.md")),
    ]
    intelligence_checks = [
        check_item("股票助手19300监听", port_listening(19300), stock_assistant),
        check_item("企微桥接19302监听", port_listening(19302), wework_bridge),
        check_item("股票助手健康接口正常", stock_assistant.get("可访问") is True and stock_assistant.get("数据", {}).get("状态") == "正常", stock_assistant),
        check_item("企微桥接健康接口正常", wework_bridge.get("可访问") is True and wework_bridge.get("数据", {}).get("状态") == "正常", wework_bridge),
        check_item("公网回调ready", public_callback.get("执行成功") is True and public_callback.get("数据", {}).get("status") == "ready", public_callback),
        check_item("智能系统运行时目录存在", (intelligence / "03数据" / "本机工具运行时").exists(), file_state(intelligence / "03数据" / "本机工具运行时")),
    ]
    stock_checks = [
        check_item("股票交付边界已知且C+++可用", (final_status.get("通过数量") or 0) >= 4 and (final_status.get("失败数量") or 0) <= 1, final_status),
        check_item("C+++日常可用验收通过", (c_status.get("通过数量") or 0) >= 16 and c_status.get("失败数量") == 0, c_status),
        check_item("日常一键失败0", daily_status.get("失败数量") == 0, daily_status),
        check_item("企微前台回归至少20项且失败0", (front_status.get("通过数量") or 0) >= 20 and front_status.get("失败数量") == 0, front_status),
        check_item("报告数据口径严重问题0", data_status.get("失败数量") in {0, None} and load_json(data_check, {}).get("严重问题数", 0) == 0, data_status),
        check_item("风险失效条件面板存在", risk_panel.exists(), file_state(risk_panel)),
        check_item("金融复核覆盖9/9", finance_data.get("执行后已覆盖数量") == 9 and finance_data.get("目标数量") == 9, finance_data),
        check_item("复盘学习状态面板存在", replay_panel.exists() and replay_data.get("企微前台回归", {}).get("失败数") == 0, replay_data),
        check_item("判断复盘到期提醒清单存在", replay_due.exists() and int(due_data.get("摘要", {}).get("验证任务数量") or 0) > 0, due_data.get("摘要", {})),
        check_item("300核验流水线状态", verification_pipeline_status.exists(), {
            "路径": str(verification_pipeline_status),
            "当前状态": verification_pipeline_status_data.get("当前状态", "缺失"),
            "是否等待人工填写": verification_pipeline_status_data.get("是否等待人工填写", False),
            "人工提示": verification_pipeline_status_data.get("人工提示", ""),
        }),
        check_item("证据链正式导入样本达到4只", evidence_overview.exists() and min(
            int(evidence_overview_data.get("链路汇总", {}).get("公司概况", {}).get("已导入数量") or 0),
            int(evidence_overview_data.get("链路汇总", {}).get("事件风险证据", {}).get("已导入数量") or 0),
            int(evidence_overview_data.get("链路汇总", {}).get("行业景气证据", {}).get("已导入数量") or 0),
        ) >= 4, {
            "路径": str(evidence_overview),
            "链路汇总": evidence_overview_data.get("链路汇总", {}),
            "下一只": (evidence_overview_data.get("L5逐股状态", [{}])[4] if len(evidence_overview_data.get("L5逐股状态", [])) > 4 else {}),
        }),
        check_item("证据链人工核验入口存在", evidence_entry.exists() and len(evidence_entry_data.get("链路入口", [])) == 3, {
            "路径": str(evidence_entry),
            "状态": evidence_entry_data.get("当前状态"),
            "建议先处理": evidence_entry_data.get("建议先处理"),
        }),
        check_item("单股证据核验工作包存在", single_stock_evidence_package.exists() and single_stock_evidence_package_data.get("目标股票", {}).get("代码"), {
            "路径": str(single_stock_evidence_package),
            "目标股票": single_stock_evidence_package_data.get("目标股票", {}),
            "待填汇总": single_stock_evidence_package_data.get("待填汇总", {}),
        }),
        check_item("单股证据核验人工填写台账存在", single_stock_manual_ledger.exists() and single_stock_manual_ledger_data.get("目标股票", {}).get("代码"), {
            "路径": str(single_stock_manual_ledger),
            "目标股票": single_stock_manual_ledger_data.get("目标股票", {}),
            "汇总": single_stock_manual_ledger_data.get("汇总", {}),
        }),
        check_item("单股证据核验台账同步预览存在", single_stock_sync_preview.exists() and single_stock_sync_preview_data.get("目标股票", {}).get("代码"), {
            "路径": str(single_stock_sync_preview),
            "目标股票": single_stock_sync_preview_data.get("目标股票", {}),
            "同步结论": single_stock_sync_preview_data.get("同步结论"),
            "汇总": single_stock_sync_preview_data.get("汇总", {}),
        }),
        check_item("单股证据核验模板同步执行闸口存在", single_stock_template_sync_gate.exists() and single_stock_template_sync_gate_data.get("目标股票", {}).get("代码"), {
            "路径": str(single_stock_template_sync_gate),
            "目标股票": single_stock_template_sync_gate_data.get("目标股票", {}),
            "闸口结论": single_stock_template_sync_gate_data.get("闸口结论"),
            "是否允许进入模板同步执行器": single_stock_template_sync_gate_data.get("是否允许进入模板同步执行器"),
        }),
    ]
    evolution_checks = [
        check_item("务实闭环方法存在", (evolution / "03数据" / "04通用方法" / "务实闭环_真实业务检验系统能力_20260502.md").exists(), file_state(evolution / "03数据" / "04通用方法" / "务实闭环_真实业务检验系统能力_20260502.md")),
        check_item("施工方向校准方法存在", (evolution / "03数据" / "04通用方法" / "施工方向校准_埋头拉车也要抬头看路_20260502.md").exists(), file_state(evolution / "03数据" / "04通用方法" / "施工方向校准_埋头拉车也要抬头看路_20260502.md")),
        check_item("机器自动与人工闸口分层方法存在", (evolution / "03数据" / "04通用方法" / "四系统闭环_机器自动与人工闸口分层_20260502.md").exists(), file_state(evolution / "03数据" / "04通用方法" / "四系统闭环_机器自动与人工闸口分层_20260502.md")),
        check_item("D盘归集经验卡片存在", (evolution / "03数据" / "历史经验" / "D盘归集后SSH私钥ACL修复经验卡片.md").exists(), file_state(evolution / "03数据" / "历史经验" / "D盘归集后SSH私钥ACL修复经验卡片.md")),
        check_item("股票候选闭环经验卡片存在", (evolution / "03数据" / "经验教训" / "20260430股票候选只读分层闭环经验卡片.md").exists(), file_state(evolution / "03数据" / "经验教训" / "20260430股票候选只读分层闭环经验卡片.md")),
        check_item("本轮四系统闭环经验卡片存在", (evolution / "03数据" / "历史经验" / "四系统股票小闭环脚本化经验卡片_20260502.md").exists(), file_state(evolution / "03数据" / "历史经验" / "四系统股票小闭环脚本化经验卡片_20260502.md")),
        check_item("学习提炼导航规则存在", (evolution / "01配置" / "学习提炼导航规则.json").exists(), file_state(evolution / "01配置" / "学习提炼导航规则.json")),
    ]

    roles = [
        role_status("00总管系统", "定方向、边界、计划、验收、接续", manager_checks, "施工中只更新工作日志；收工或新开对话时再统一更新接续包。"),
        role_status("01智能系统", "提供模型、服务、企业微信桥接和运行时底座", intelligence_checks, "保持健康检查；不重启正式服务。"),
        role_status("02扩展系统/股票", "运行真实业务、输出报告、前台问答和验收", stock_checks, "把股票证据链作为样板，不机械追求无限补股票。"),
        role_status("03进化系统", "沉淀问题、经验、规则和方法", evolution_checks, "只沉淀已验证的可复用问题，普通施工流水不入库。"),
    ]
    failed_roles = [role for role in roles if role["状态"] != "通过"]
    key_checks = manager_checks + intelligence_checks + stock_checks + evolution_checks
    failed_checks = [item for item in key_checks if item["结果"] != "通过"]
    conclusion = "通过：四系统股票小闭环可重复执行" if not failed_checks else "待修复：四系统小闭环存在断点"
    maturity = "稳定可复用雏形" if not failed_checks else "局部可用"
    due_summary = due_data.get("摘要", {}) if isinstance(due_data, dict) else {}
    if int(due_summary.get("已到期数量") or 0) > 0:
        human_next = "按188判断复盘到期提醒清单补已到期验证结果账。"
    elif int(due_summary.get("七天内到期数量") or 0) > 0:
        human_next = "准备首批T5人工复盘资料，到期后补验证结果账。"
    else:
        human_next = "等待T周期到期；同时把股票证据链样板固化为四系统小闭环验收口径。"
    machine_state = (
        "服务正常、企微可用、金融复核已覆盖、复盘提醒已排期"
        if not failed_checks
        else "存在断点，先处理失败检查项"
    )

    report = {
        "名称": "四系统股票小闭环状态面板",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成四系统股票小闭环状态面板.py",
        "闭环结论": conclusion,
        "闭环成熟度": maturity,
        "当前机器状态": machine_state,
        "当前人工下一步": human_next,
        "下一到期日": due_summary.get("最近到期日") or "",
        "总环节数": len(roles),
        "通过环节数": len(roles) - len(failed_roles),
        "失败检查数": len(failed_checks),
        "四系统状态": roles,
        "关键验收": key_checks,
        "闭环链路": [
            "00总管读取设计纲领、接续包和验收状态，确定当前用股票系统作为样板场景。",
            "01智能系统保持19300股票助手、19302企微桥接和本机运行时可用。",
            "02扩展系统以股票研究系统承载真实业务，用证据链导入、前台报告、回归验收证明业务闭环。",
            "01智能系统只在旁路提升输出质量，例如文稿质检和企微手机端排版，不接管正式推送。",
            "03进化系统只沉淀已验证的可复用经验，例如跨股票CSV残留、并行竞态、接续包更新边界。",
            "00总管施工中只写工作日志和业务数据；只有收工或新开对话时才更新接续包、接续卡片和接手包。",
        ],
        "可重复执行清单": [
            "开工：先运行 `D:\\杰哥智能化系统\\00杰哥系统总管\\06工具\\四系统小闭环开工快检.bat`，确认端口、验收、关键文件和接续边界仍正常。",
            "上下文：需要新开对话或收工时，再读取/刷新AI施工接续最小包和一键接续施工包。",
            "完整回归：必要时运行 `执行四系统股票小闭环.py --no-open`，不要把完整回归当成每次开工的默认动作。",
            "施工：用股票系统验证闭环机制，不把补股票本身当成终点。",
            "验收：跑四系统小闭环面板和验证脚本。",
            "沉淀：施工中只更新工作日志；经验进入候选前必须符合学习提炼导航。",
            "交接：只有收工或新开对话时，才刷新接续包、接续卡片和全系统AI无缝接手包。",
        ],
        "安全边界": [
            "不真实发送企业微信。",
            "不启用n8n自动触发。",
            "不调用券商接口。",
            "不自动交易。",
            "本状态面板只读，不写正式证据档案；正式导入只能通过181/195显式确认链路。",
            "施工过程中不更新接续包、接续卡片或新对话包；收工或新开对话时统一固化。",
            "不删除文件，不重启正式服务，除非用户明确确认。",
        ],
    }

    output_dir = manager / "03数据" / "四系统小闭环"
    latest_json = output_dir / "四系统股票小闭环状态面板_最新.json"
    latest_md = output_dir / "四系统股票小闭环状态面板_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "闭环结论": conclusion,
        "失败检查数": len(failed_checks),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
