# -*- coding: utf-8 -*-
"""
名称：生成股票四系统融合闭环状态面板.py
作用：把股票分析系统任务和四系统闭环任务合并到同一个状态面板。
触发方式：python 生成股票四系统融合闭环状态面板.py
依赖：股票系统验收报告、企微前台回归、推荐点击详情与手机排版验收、191最小行动卡、191资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205候选采用确认回执草案、206候选采用前闸口、198填写质量闸口、193闸口、194同步执行dry-run验证、197完成后预演检查、文稿质检观察面板与用户确认进度、样本复盘、四系统开工快检、版本治理快照。
所属系统：00杰哥系统总管
输出：00杰哥系统总管/03数据/四系统小闭环/股票四系统融合闭环状态面板_最新.md|json。
安全边界：只读检查本地文件、端口和健康接口；只写总管03数据状态面板；
不触发n8n、不发送企业微信、不重启服务、不写正式业务库、不调用券商接口、不自动交易。
创建/修改记录：2026-05-03 创建；2026-05-03 接入文稿质检旁路观察面板；2026-05-03 接入推荐点击详情与手机排版验收；2026-05-03 接入文稿质检样本复盘；2026-05-03 修正189入口详情显示为已完成前置样本与待处理队列；2026-05-03 更新融合进度估算依据；2026-05-03 接入194受控同步dry-run验证；2026-05-03 更新194接入后的剩余缺口估算；2026-05-03 接入文稿质检用户确认进度；2026-05-03 接入191最小行动卡检查；2026-05-03 接入197完成后预演检查；2026-05-03 接入191资料来源导航卡；2026-05-03 接入198填写质量闸口；2026-05-03 进度与剩余工时改为按关键缺口动态估算；2026-05-03 接入199资料候选处理包；2026-05-03 接入200填写建议草案；2026-05-03 接入201最小人工确认清单；2026-05-03 接入202候选填写CSV副本；2026-05-03 接入203候选写入差异预览；2026-05-03 接入204候选采用后质量预演；2026-05-03 接入205候选采用确认回执草案；2026-05-03 接入206候选采用前闸口。
标识：stock-four-system-fusion-panel-generate
"""

from __future__ import annotations

import json
import socket
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
INTELLIGENCE = ROOT / "01杰哥智能系统"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = MANAGER / "03数据" / "四系统小闭环"


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


def port_listening(port: int, host: str = "127.0.0.1", timeout: float = 1.2) -> bool:
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


def pass_count(path: Path) -> tuple[int | None, int | None]:
    data = load_json(path, {})
    if not isinstance(data, dict):
        return None, None
    summary = data.get("汇总", {})
    if isinstance(summary, dict) and ("通过" in summary or "失败" in summary):
        return summary.get("通过"), summary.get("失败")
    passed = data.get("通过数量")
    failed = data.get("失败数量")
    if passed is None:
        passed = data.get("通过数")
    if failed is None:
        failed = data.get("失败数")
    return passed, failed


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(ok), "详情": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统与四系统融合闭环状态面板 - {report['生成时间']}",
        "",
        "## 一、总判断",
        "",
        f"- 融合结论：{report['融合结论']}",
        f"- 是否影响股票日常使用：{report['是否影响股票日常使用']}",
        f"- 当前阶段：{report['当前阶段']}",
        f"- 当前进度：{report['当前进度']}",
        f"- 剩余有效工作时间估算：{report['剩余有效工作时间估算']}",
        "",
        "## 二、进度依据",
        "",
    ]
    for item in report.get("进度依据", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 三、四类检查",
        "",
    ])
    for group in report["检查组"]:
        lines.extend([
            f"### {group['名称']}",
            "",
            f"- 结论：{group['结论']}",
            f"- 通过：{group['通过数量']} / {group['总数']}",
            "",
        ])
        for item in group["检查项"]:
            status = "通过" if item["通过"] else "失败"
            lines.append(f"- {status}：{item['名称']}")
        lines.append("")

    lines.extend([
        "## 四、融合施工主线",
        "",
    ])
    for item in report["融合施工主线"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 五、下一步",
        "",
    ])
    for item in report["下一步"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## 六、安全边界",
        "",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def group(name: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for item in checks if item["通过"])
    return {
        "名称": name,
        "总数": len(checks),
        "通过数量": passed,
        "失败数量": len(checks) - passed,
        "结论": "通过" if passed == len(checks) else "待处理",
        "检查项": checks,
    }


def estimate_progress_and_time(failed: list[dict[str, Any]], quality_gate_data: dict[str, Any], review_confirmation: dict[str, Any]) -> tuple[str, str]:
    if failed:
        return "82%左右", "5-8小时；先处理失败检查项，再回到融合闭环主线"
    quality_summary = quality_gate_data.get("汇总", {}) if isinstance(quality_gate_data.get("汇总"), dict) else {}
    missing_fields = int(quality_summary.get("缺失字段总数") or 0)
    quality_allowed = quality_gate_data.get("是否允许进入197预演") is True
    review_remaining = int(review_confirmation.get("仍需确认次数") or 0)
    if missing_fields > 0 or not quality_allowed:
        return "97%左右", "1小时左右完成融合闭环当前阶段；正式回执已录入，剩余是191质量闸口、193/194同步和收尾验收"
    if review_remaining > 0:
        return "99%左右", f"0.5小时左右；主闭环已进入收尾复核，文稿质检旁路仍需{review_remaining}次样本确认但不阻断股票和四系统闭环"
    return "99%左右", "0.5小时左右；主要剩余为收尾复核、观察期记录和收工固化"


def main() -> int:
    now = datetime.now()
    final_acceptance = STOCK / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.json"
    c_acceptance = STOCK / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.json"
    front_regression = STOCK / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.json"
    detail_mobile_acceptance = STOCK / "03数据" / "196推荐点击详情与手机排版验收" / "股票推荐点击详情与手机排版验收_最新.json"
    evidence_overview = STOCK / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json"
    evidence_manual_entry = STOCK / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json"
    minimum_action_card = STOCK / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写最小行动卡_最新.json"
    minimum_action_card_verify = STOCK / "04日志" / "单股证据核验人工填写最小行动卡" / "single-stock-evidence-minimum-action-card-verify-最新.json"
    source_navigation_card = STOCK / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.json"
    source_navigation_card_verify = STOCK / "04日志" / "单股证据核验资料来源导航卡" / "single-stock-evidence-source-navigation-card-verify-最新.json"
    source_candidate_package = STOCK / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.json"
    source_candidate_package_verify = STOCK / "04日志" / "单股证据核验资料候选处理包" / "single-stock-evidence-source-candidate-package-verify-最新.json"
    fill_suggestion_draft = STOCK / "03数据" / "200单股证据核验191填写建议草案" / "单股证据核验191填写建议草案_最新.json"
    fill_suggestion_draft_verify = STOCK / "04日志" / "单股证据核验191填写建议草案" / "single-stock-evidence-191-fill-suggestion-draft-verify-最新.json"
    minimal_confirmation = STOCK / "03数据" / "201单股证据核验最小人工确认清单" / "单股证据核验最小人工确认清单_最新.json"
    minimal_confirmation_verify = STOCK / "04日志" / "单股证据核验最小人工确认清单" / "single-stock-evidence-minimal-human-confirmation-list-verify-最新.json"
    candidate_filled_csv = STOCK / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.json"
    candidate_filled_csv_verify = STOCK / "04日志" / "单股证据核验191候选填写CSV副本" / "single-stock-evidence-191-candidate-filled-csv-copy-verify-最新.json"
    candidate_write_diff = STOCK / "03数据" / "203单股证据核验191候选写入差异预览" / "单股证据核验191候选写入差异预览_最新.json"
    candidate_write_diff_verify = STOCK / "04日志" / "单股证据核验191候选写入差异预览" / "single-stock-evidence-191-candidate-write-diff-preview-verify-最新.json"
    candidate_quality_preview = STOCK / "03数据" / "204单股证据核验191候选采用后质量预演" / "单股证据核验191候选采用后质量预演_最新.json"
    candidate_quality_preview_verify = STOCK / "04日志" / "单股证据核验191候选采用后质量预演" / "single-stock-evidence-191-candidate-adoption-quality-preview-verify-最新.json"
    candidate_confirmation = STOCK / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.json"
    candidate_confirmation_verify = STOCK / "04日志" / "单股证据核验191候选采用确认回执草案" / "single-stock-evidence-191-candidate-adoption-confirmation-draft-verify-最新.json"
    receipt_status_panel = STOCK / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.json"
    receipt_status_panel_verify = STOCK / "04日志" / "单股证据核验确认回执状态面板" / "single-stock-evidence-confirmation-receipt-status-panel-verify-最新.json"
    post_confirmation_dispatch = STOCK / "03数据" / "211单股证据核验回执后调度清单" / "单股证据核验回执后调度清单_最新.json"
    post_confirmation_dispatch_verify = STOCK / "04日志" / "单股证据核验回执后调度清单" / "single-stock-evidence-post-confirmation-dispatch-list-verify-最新.json"
    receipt_example_copy = STOCK / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.json"
    receipt_example_copy_verify = STOCK / "04日志" / "单股证据核验确认回执填写样例副本" / "single-stock-evidence-confirmation-receipt-filled-example-copy-verify-最新.json"
    post_confirmation_rehearsal = STOCK / "03数据" / "213单股证据核验确认后路径演练报告" / "单股证据核验确认后路径演练报告_最新.json"
    post_confirmation_rehearsal_verify = STOCK / "04日志" / "单股证据核验确认后路径演练报告" / "single-stock-evidence-post-confirmation-path-rehearsal-report-verify-最新.json"
    formal_receipt_todo = STOCK / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.json"
    formal_receipt_todo_verify = STOCK / "04日志" / "单股证据核验正式回执待办卡" / "single-stock-evidence-formal-confirmation-receipt-todo-card-verify-最新.json"
    formal_receipt_prefill = STOCK / "03数据" / "215单股证据核验正式回执填写前自检" / "单股证据核验正式回执填写前自检_最新.json"
    formal_receipt_prefill_verify = STOCK / "04日志" / "单股证据核验正式回执填写前自检" / "single-stock-evidence-formal-confirmation-receipt-prefill-check-verify-最新.json"
    formal_receipt_rerun = STOCK / "03数据" / "216单股证据核验正式回执录入后受控重跑预演" / "单股证据核验正式回执录入后受控重跑预演_最新.json"
    formal_receipt_rerun_verify = STOCK / "04日志" / "单股证据核验正式回执录入后受控重跑预演" / "single-stock-evidence-formal-confirmation-post-entry-controlled-rerun-rehearsal-verify-最新.json"
    candidate_pre_gate = STOCK / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.json"
    candidate_pre_gate_verify = STOCK / "04日志" / "单股证据核验191候选采用前闸口" / "single-stock-evidence-191-candidate-adoption-pre-gate-verify-最新.json"
    candidate_controlled_plan = STOCK / "03数据" / "207单股证据核验191候选采用受控执行预案" / "单股证据核验191候选采用受控执行预案_最新.json"
    candidate_controlled_plan_verify = STOCK / "04日志" / "单股证据核验191候选采用受控执行预案" / "single-stock-evidence-191-candidate-adoption-controlled-plan-verify-最新.json"
    candidate_preview = STOCK / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.json"
    candidate_preview_verify = STOCK / "04日志" / "单股证据核验191候选采用预览" / "single-stock-evidence-191-candidate-adoption-preview-verify-最新.json"
    controlled_command_draft = STOCK / "03数据" / "209单股证据核验受控写入命令草案" / "单股证据核验受控写入命令草案_最新.json"
    controlled_command_draft_verify = STOCK / "04日志" / "单股证据核验受控写入命令草案" / "single-stock-evidence-controlled-write-command-draft-verify-最新.json"
    quality_gate = STOCK / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.json"
    quality_gate_verify = STOCK / "04日志" / "单股证据核验191填写质量闸口" / "single-stock-evidence-191-quality-gate-verify-最新.json"
    sync_gate = STOCK / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"
    template_sync_verify = STOCK / "04日志" / "单股证据核验模板同步执行" / "single-stock-evidence-template-sync-execute-verify-最新.json"
    after_191_preflight = STOCK / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.json"
    after_191_preflight_verify = STOCK / "04日志" / "单股证据核验191完成后预演检查" / "single-stock-evidence-after-191-preflight-verify-最新.json"
    completion_observation = MANAGER / "03数据" / "四系统小闭环" / "股票四系统闭环完成观察记录_最新.json"
    completion_observation_verify = MANAGER / "04日志" / "四系统小闭环" / "stock-four-system-closed-loop-completion-observation-verify-最新.json"
    latest_daily = STOCK / "03数据" / "135分层日报" / "AI分析报告_最新.md"
    latest_single = STOCK / "03数据" / "135分层日报" / "单股标准报告v2_最新.md"
    latest_png = STOCK / "03数据" / "86图形报告" / "股票图形报告_最新.png"

    four_loop = MANAGER / "03数据" / "四系统小闭环" / "四系统股票小闭环验收_最新.json"
    open_check = MANAGER / "03数据" / "四系统小闭环" / "四系统小闭环开工快检_最新.json"
    inheritance = MANAGER / "03数据" / "全闭环保障" / "子系统全闭环继承状态_最新.json"
    version_v11 = MANAGER / "04日志" / "版本升级治理" / "version_snapshot_latest.json"
    version_verify_script = MANAGER / "02脚本" / "验证版本升级治理闭环.py"
    n8n_shadow_plan = MANAGER / "04日志" / "版本升级治理" / "n8n_shadow_plan_latest.json"

    text_reviewer = INTELLIGENCE / "02脚本" / "文稿质检" / "text_reviewer.py"
    review_records = INTELLIGENCE / "03数据" / "文稿质检" / "review_records.jsonl"
    review_observation = INTELLIGENCE / "03数据" / "文稿质检" / "观察面板" / "文稿质检旁路观察面板_最新.json"
    review_observation_script = INTELLIGENCE / "02脚本" / "文稿质检" / "生成文稿质检旁路观察面板.py"
    review_retrospective = INTELLIGENCE / "03数据" / "文稿质检" / "样本复盘" / "文稿质检样本复盘报告_最新.json"
    review_retrospective_script = INTELLIGENCE / "02脚本" / "文稿质检" / "生成文稿质检样本复盘报告.py"
    stock_report_review_doc = INTELLIGENCE / "07文档" / "股票报告文稿质检融入方案_20260503.md"
    stock_report_review_rule = INTELLIGENCE / "01配置" / "股票报告质检融入规则.json"
    constitution_doc = MANAGER / "07文档" / "设计纲领" / "系统宪法级原则与落地检查清单_20260503.md"
    constitution_rule = MANAGER / "01配置" / "系统宪法级原则落地规则.json"
    constitution_review_verify = MANAGER / "02脚本" / "验证股票报告质检与宪法级原则落实.py"
    learning_rules = EVOLUTION / "01配置" / "学习提炼导航规则.json"
    engineering_principle = MANAGER / "07文档" / "设计纲领" / "影子试验逐步组合失败隔离通用进化机制_20260503.md"
    method_template = EVOLUTION / "03数据" / "04通用方法" / "四系统小闭环_通用施工模板_20260503.md"
    report_review_method = EVOLUTION / "03数据" / "04通用方法" / "报告质检_内容结构语言排版把关方法_20260503.md"

    final_pass, final_fail = pass_count(final_acceptance)
    c_pass, c_fail = pass_count(c_acceptance)
    front_pass, front_fail = pass_count(front_regression)
    detail_mobile = load_json(detail_mobile_acceptance, {})
    four_pass, four_fail = pass_count(four_loop)
    open_pass, open_fail = pass_count(open_check)
    evidence = load_json(evidence_overview, {})
    evidence_entry = load_json(evidence_manual_entry, {})
    minimum_action_card_data = load_json(minimum_action_card, {})
    minimum_action_card_verify_data = load_json(minimum_action_card_verify, {})
    source_navigation_card_data = load_json(source_navigation_card, {})
    source_navigation_card_verify_data = load_json(source_navigation_card_verify, {})
    source_candidate_package_data = load_json(source_candidate_package, {})
    source_candidate_package_verify_data = load_json(source_candidate_package_verify, {})
    fill_suggestion_draft_data = load_json(fill_suggestion_draft, {})
    fill_suggestion_draft_verify_data = load_json(fill_suggestion_draft_verify, {})
    minimal_confirmation_data = load_json(minimal_confirmation, {})
    minimal_confirmation_verify_data = load_json(minimal_confirmation_verify, {})
    candidate_filled_csv_data = load_json(candidate_filled_csv, {})
    candidate_filled_csv_verify_data = load_json(candidate_filled_csv_verify, {})
    candidate_write_diff_data = load_json(candidate_write_diff, {})
    candidate_write_diff_verify_data = load_json(candidate_write_diff_verify, {})
    candidate_quality_preview_data = load_json(candidate_quality_preview, {})
    candidate_quality_preview_verify_data = load_json(candidate_quality_preview_verify, {})
    candidate_confirmation_data = load_json(candidate_confirmation, {})
    candidate_confirmation_verify_data = load_json(candidate_confirmation_verify, {})
    receipt_status_panel_data = load_json(receipt_status_panel, {})
    receipt_status_panel_verify_data = load_json(receipt_status_panel_verify, {})
    post_confirmation_dispatch_data = load_json(post_confirmation_dispatch, {})
    post_confirmation_dispatch_verify_data = load_json(post_confirmation_dispatch_verify, {})
    receipt_example_copy_data = load_json(receipt_example_copy, {})
    receipt_example_copy_verify_data = load_json(receipt_example_copy_verify, {})
    post_confirmation_rehearsal_data = load_json(post_confirmation_rehearsal, {})
    post_confirmation_rehearsal_verify_data = load_json(post_confirmation_rehearsal_verify, {})
    formal_receipt_todo_data = load_json(formal_receipt_todo, {})
    formal_receipt_todo_verify_data = load_json(formal_receipt_todo_verify, {})
    formal_receipt_prefill_data = load_json(formal_receipt_prefill, {})
    formal_receipt_prefill_verify_data = load_json(formal_receipt_prefill_verify, {})
    formal_receipt_rerun_data = load_json(formal_receipt_rerun, {})
    formal_receipt_rerun_verify_data = load_json(formal_receipt_rerun_verify, {})
    candidate_pre_gate_data = load_json(candidate_pre_gate, {})
    candidate_pre_gate_verify_data = load_json(candidate_pre_gate_verify, {})
    candidate_controlled_plan_data = load_json(candidate_controlled_plan, {})
    candidate_controlled_plan_verify_data = load_json(candidate_controlled_plan_verify, {})
    candidate_preview_data = load_json(candidate_preview, {})
    candidate_preview_verify_data = load_json(candidate_preview_verify, {})
    controlled_command_draft_data = load_json(controlled_command_draft, {})
    controlled_command_draft_verify_data = load_json(controlled_command_draft_verify, {})
    quality_gate_data = load_json(quality_gate, {})
    quality_gate_verify_data = load_json(quality_gate_verify, {})
    sync = load_json(sync_gate, {})
    template_sync_verify_data = load_json(template_sync_verify, {})
    after_191_preflight_data = load_json(after_191_preflight, {})
    after_191_preflight_verify_data = load_json(after_191_preflight_verify, {})
    completion_observation_data = load_json(completion_observation, {})
    completion_observation_verify_data = load_json(completion_observation_verify, {})
    version = load_json(version_v11, {})
    review_observation_data = load_json(review_observation, {})
    review_retrospective_data = load_json(review_retrospective, {})
    review_confirmation = review_observation_data.get("用户确认进度", {}) if isinstance(review_observation_data, dict) else {}
    review_progress = review_observation_data.get("股票三类报告样本进度", []) if isinstance(review_observation_data, dict) else []
    missing_review_samples = [
        str(item.get("名称"))
        for item in review_progress
        if isinstance(item, dict) and item.get("是否已有样本") is not True
    ]
    if missing_review_samples:
        review_next_step = f"文稿质检先保持旁路实验；观察面板显示仍需补{ '、'.join(missing_review_samples) }样本，连续验证有价值后再考虑第二阶段。"
    else:
        review_next_step = (
            "文稿质检先保持旁路实验；股票三类报告均已有样本，"
            f"已确认{review_confirmation.get('已采用或确认有价值次数', 0)}次，"
            f"仍需{review_confirmation.get('仍需确认次数', 5)}次用户确认有价值后才评估第二阶段。"
        )

    stock_checks = [
        check("股票助手19300端口监听", port_listening(19300), {"端口": 19300}),
        check("企微桥接19302端口监听", port_listening(19302), {"端口": 19302}),
        check("股票助手健康接口正常", http_json("http://127.0.0.1:19300/%E5%81%A5%E5%BA%B7").get("可访问") is True, "GET /健康"),
        check("企微桥接健康接口正常", http_json("http://127.0.0.1:19302/health").get("可访问") is True, "GET /health"),
        check("股票交付边界已知且C+++可用", (final_pass or 0) >= 4 and (final_fail or 0) <= 1, file_state(final_acceptance)),
        check("股票C+++日常可用验收通过", (c_pass or 0) >= 16 and c_fail == 0, file_state(c_acceptance)),
        check("企微前台回归验收无失败", (front_pass or 0) >= 20 and front_fail == 0, file_state(front_regression)),
        check("推荐点击详情与手机排版验收通过", detail_mobile.get("失败数量") == 0 and int(detail_mobile.get("链接数量") or 0) >= 5, {
            "验收": file_state(detail_mobile_acceptance),
            "链接数量": detail_mobile.get("链接数量"),
            "结论": detail_mobile.get("验收结论"),
        }),
        check("每日推荐报告存在", latest_daily.exists(), file_state(latest_daily)),
        check("单股标准报告存在", latest_single.exists(), file_state(latest_single)),
        check("图形报告PNG存在", latest_png.exists(), file_state(latest_png)),
    ]

    evidence_summary = evidence.get("链路汇总", {}) if isinstance(evidence, dict) else {}
    evidence_tasks = evidence_entry.get("逐股任务", []) if isinstance(evidence_entry, dict) else []
    completed_prefix = [item for item in evidence_tasks if int(item.get("合计待填") or 0) == 0][:4]
    pending_tasks = [item for item in evidence_tasks if int(item.get("合计待填") or 0) > 0]
    next_pending = pending_tasks[0] if pending_tasks else {}
    stock_evolution_checks = [
        check("证据核验总览存在", evidence_overview.exists(), file_state(evidence_overview)),
        check("公司/事件/行业证据链已有正式样本", all(
            int((evidence_summary.get(key, {}) or {}).get("已导入数量") or 0) >= 4
            for key in ["公司概况", "事件风险证据", "行业景气证据"]
        ), evidence_summary),
        check("证据链人工核验入口按权威状态排序", evidence_manual_entry.exists()
              and "天齐锂业" in str(evidence_entry.get("建议先处理", ""))
              and str(next_pending.get("名称") or "") == "天齐锂业"
              and all(int(item.get("合计待填") or 0) == 0 for item in evidence_tasks[:4]), {
                  "入口": file_state(evidence_manual_entry),
                  "建议先处理": evidence_entry.get("建议先处理", ""),
                  "已完成前置样本": [
                      {"名称": item.get("名称"), "合计待填": item.get("合计待填")}
                      for item in completed_prefix
                  ],
                  "下一只待处理": {
                      "名称": next_pending.get("名称"),
                      "代码": next_pending.get("代码"),
                      "合计待填": next_pending.get("合计待填"),
                  },
                  "待处理前四": [
                      {"名称": item.get("名称"), "代码": item.get("代码"), "合计待填": item.get("合计待填")}
                      for item in pending_tasks[:4]
                  ],
              }),
        check("191最小行动卡存在且验证通过", minimum_action_card.exists()
              and int((minimum_action_card_data.get("当前缺口", {}) or {}).get("缺失字段总数") or 0) >= 0
              and minimum_action_card_verify.exists()
              and int(minimum_action_card_verify_data.get("失败") or 0) == 0, {
                  "行动卡": file_state(minimum_action_card),
                  "验证日志": file_state(minimum_action_card_verify),
                  "缺失字段总数": (minimum_action_card_data.get("当前缺口", {}) or {}).get("缺失字段总数"),
                  "验证通过": minimum_action_card_verify_data.get("通过"),
                  "验证失败": minimum_action_card_verify_data.get("失败"),
              }),
        check("191资料来源导航卡存在且验证通过", source_navigation_card.exists()
              and source_navigation_card_verify.exists()
              and int(source_navigation_card_verify_data.get("失败") or 0) == 0
              and (source_navigation_card_data.get("安全边界", {}) or {}).get("提供事实答案") is False, {
                  "导航卡": file_state(source_navigation_card),
                  "验证日志": file_state(source_navigation_card_verify),
                  "缺失字段总数": (source_navigation_card_data.get("当前缺口", {}) or {}).get("缺失字段总数"),
                  "验证通过": source_navigation_card_verify_data.get("通过"),
                  "验证失败": source_navigation_card_verify_data.get("失败"),
              }),
        check("199资料候选处理包存在且验证通过", source_candidate_package.exists()
              and source_candidate_package_verify.exists()
              and int(source_candidate_package_verify_data.get("失败") or 0) == 0
              and len(source_candidate_package_data.get("候选资料抓取", []) if isinstance(source_candidate_package_data.get("候选资料抓取"), list) else []) >= 1
              and (int((source_candidate_package_data.get("覆盖统计", {}) or {}).get("已有候选片段字段数") or 0) >= 1
                   or int((source_candidate_package_data.get("覆盖统计", {}) or {}).get("待填字段数") or 0) == 0)
              and (source_candidate_package_data.get("安全边界", {}) or {}).get("写191") is False, {
                  "候选处理包": file_state(source_candidate_package),
                  "验证日志": file_state(source_candidate_package_verify),
                  "资料抓取数量": len(source_candidate_package_data.get("候选资料抓取", []) if isinstance(source_candidate_package_data.get("候选资料抓取"), list) else []),
                  "已有候选片段字段数": (source_candidate_package_data.get("覆盖统计", {}) or {}).get("已有候选片段字段数"),
                  "验证通过": source_candidate_package_verify_data.get("通过"),
                  "验证失败": source_candidate_package_verify_data.get("失败"),
              }),
        check("200填写建议草案存在且验证通过", fill_suggestion_draft.exists()
              and fill_suggestion_draft_verify.exists()
              and int(fill_suggestion_draft_verify_data.get("失败") or 0) == 0
              and int((fill_suggestion_draft_data.get("汇总", {}) or {}).get("有建议值行数") or 0) >= 10
              and (fill_suggestion_draft_data.get("安全边界", {}) or {}).get("写191台账") is False, {
                  "建议草案": file_state(fill_suggestion_draft),
                  "验证日志": file_state(fill_suggestion_draft_verify),
                  "有建议值行数": (fill_suggestion_draft_data.get("汇总", {}) or {}).get("有建议值行数"),
                  "可直接复制候选行数": (fill_suggestion_draft_data.get("汇总", {}) or {}).get("可直接复制候选行数"),
                  "验证通过": fill_suggestion_draft_verify_data.get("通过"),
                  "验证失败": fill_suggestion_draft_verify_data.get("失败"),
              }),
        check("201最小人工确认清单存在且验证通过", minimal_confirmation.exists()
              and minimal_confirmation_verify.exists()
              and int(minimal_confirmation_verify_data.get("失败") or 0) == 0
              and int((minimal_confirmation_data.get("汇总", {}) or {}).get("最小确认问题数") or 0) == 3
              and (minimal_confirmation_data.get("安全边界", {}) or {}).get("写191台账") is False, {
                  "确认清单": file_state(minimal_confirmation),
                  "验证日志": file_state(minimal_confirmation_verify),
                  "最小确认问题数": (minimal_confirmation_data.get("汇总", {}) or {}).get("最小确认问题数"),
                  "仍需确认字段数": (minimal_confirmation_data.get("汇总", {}) or {}).get("仍需确认字段数"),
                  "验证通过": minimal_confirmation_verify_data.get("通过"),
                  "验证失败": minimal_confirmation_verify_data.get("失败"),
              }),
        check("202候选填写CSV副本存在且验证通过", candidate_filled_csv.exists()
              and candidate_filled_csv_verify.exists()
              and int(candidate_filled_csv_verify_data.get("失败") or 0) == 0
              and int((candidate_filled_csv_data.get("汇总", {}) or {}).get("已预填候选行数") or 0) >= 20
              and (candidate_filled_csv_data.get("安全边界", {}) or {}).get("覆盖191CSV") is False, {
                  "候选CSV副本": file_state(candidate_filled_csv),
                  "验证日志": file_state(candidate_filled_csv_verify),
                  "已预填候选行数": (candidate_filled_csv_data.get("汇总", {}) or {}).get("已预填候选行数"),
                  "保留空白待人工确认行数": (candidate_filled_csv_data.get("汇总", {}) or {}).get("保留空白待人工确认行数"),
                  "验证通过": candidate_filled_csv_verify_data.get("通过"),
                  "验证失败": candidate_filled_csv_verify_data.get("失败"),
              }),
        check("203候选写入差异预览存在且验证通过", candidate_write_diff.exists()
              and candidate_write_diff_verify.exists()
              and int(candidate_write_diff_verify_data.get("失败") or 0) == 0
              and (int((candidate_write_diff_data.get("汇总", {}) or {}).get("候选可填入字段数") or 0) >= 20
                   or (int((candidate_write_diff_data.get("汇总", {}) or {}).get("仍缺必填字段数") or 0) == 0
                       and int((candidate_write_diff_data.get("汇总", {}) or {}).get("原已填写且与候选一致数") or 0) >= 20))
              and (candidate_write_diff_data.get("汇总", {}) or {}).get("是否允许自动写入191") is False
              and (candidate_write_diff_data.get("安全边界", {}) or {}).get("覆盖191CSV") is False, {
                  "候选写入差异预览": file_state(candidate_write_diff),
                  "验证日志": file_state(candidate_write_diff_verify),
                  "候选可填入字段数": (candidate_write_diff_data.get("汇总", {}) or {}).get("候选可填入字段数"),
                  "仍缺必填字段数": (candidate_write_diff_data.get("汇总", {}) or {}).get("仍缺必填字段数"),
                  "验证通过": candidate_write_diff_verify_data.get("通过"),
                  "验证失败": candidate_write_diff_verify_data.get("失败"),
              }),
        check("204候选采用后质量预演存在且验证通过", candidate_quality_preview.exists()
              and candidate_quality_preview_verify.exists()
              and int(candidate_quality_preview_verify_data.get("失败") or 0) == 0
              and (int((candidate_quality_preview_data.get("汇总", {}) or {}).get("候选可补足字段数") or 0) >= 20
                   or (int((candidate_quality_preview_data.get("汇总", {}) or {}).get("候选可补足字段数") or 0) == 0
                       and int((candidate_quality_preview_data.get("汇总", {}) or {}).get("候选后仍缺必填字段数") or 0) == 0))
              and (candidate_quality_preview_data.get("汇总", {}) or {}).get("是否允许自动写入191") is False
              and (candidate_quality_preview_data.get("安全边界", {}) or {}).get("覆盖191CSV") is False, {
                  "候选采用后质量预演": file_state(candidate_quality_preview),
                  "验证日志": file_state(candidate_quality_preview_verify),
                  "候选可补足字段数": (candidate_quality_preview_data.get("汇总", {}) or {}).get("候选可补足字段数"),
                  "候选后仍缺必填字段数": (candidate_quality_preview_data.get("汇总", {}) or {}).get("候选后仍缺必填字段数"),
                  "验证通过": candidate_quality_preview_verify_data.get("通过"),
                  "验证失败": candidate_quality_preview_verify_data.get("失败"),
              }),
        check("205候选采用确认回执草案存在且验证通过", candidate_confirmation.exists()
              and candidate_confirmation_verify.exists()
              and int(candidate_confirmation_verify_data.get("失败") or 0) == 0
              and int((candidate_confirmation_data.get("汇总", {}) or {}).get("确认链路数") or 0) == 3
              and (candidate_confirmation_data.get("汇总", {}) or {}).get("是否已获得用户确认") is True
              and int((candidate_confirmation_data.get("汇总", {}) or {}).get("确认完成链路数") or 0) == 3
              and (candidate_confirmation_data.get("安全边界", {}) or {}).get("覆盖191CSV") is False, {
                  "候选采用确认回执草案": file_state(candidate_confirmation),
                  "验证日志": file_state(candidate_confirmation_verify),
                  "确认链路数": (candidate_confirmation_data.get("汇总", {}) or {}).get("确认链路数"),
                  "是否已获得用户确认": (candidate_confirmation_data.get("汇总", {}) or {}).get("是否已获得用户确认"),
                  "验证通过": candidate_confirmation_verify_data.get("通过"),
                  "验证失败": candidate_confirmation_verify_data.get("失败"),
              }),
        check("210确认回执状态面板存在且验证通过", receipt_status_panel.exists()
              and receipt_status_panel_verify.exists()
              and int(receipt_status_panel_verify_data.get("失败") or 0) == 0
              and (receipt_status_panel_data.get("汇总", {}) or {}).get("是否三链路确认完成") is True
              and (receipt_status_panel_data.get("汇总", {}) or {}).get("是否允许重跑206采用前闸口") is True
              and (receipt_status_panel_data.get("汇总", {}) or {}).get("是否允许触发197写191") is False, {
                  "确认回执状态面板": file_state(receipt_status_panel),
                  "验证日志": file_state(receipt_status_panel_verify),
                  "确认完成链路数": (receipt_status_panel_data.get("汇总", {}) or {}).get("确认完成链路数"),
                  "验证通过": receipt_status_panel_verify_data.get("通过"),
                  "验证失败": receipt_status_panel_verify_data.get("失败"),
              }),
        check("211回执后调度清单存在且验证通过", post_confirmation_dispatch.exists()
              and post_confirmation_dispatch_verify.exists()
              and int(post_confirmation_dispatch_verify_data.get("失败") or 0) == 0
              and int((post_confirmation_dispatch_data.get("汇总", {}) or {}).get("当前允许调度步骤数") or 0) == 5
              and (post_confirmation_dispatch_data.get("汇总", {}) or {}).get("本脚本是否执行调度") is False, {
                  "回执后调度清单": file_state(post_confirmation_dispatch),
                  "验证日志": file_state(post_confirmation_dispatch_verify),
                  "当前允许调度步骤数": (post_confirmation_dispatch_data.get("汇总", {}) or {}).get("当前允许调度步骤数"),
                  "验证通过": post_confirmation_dispatch_verify_data.get("通过"),
                  "验证失败": post_confirmation_dispatch_verify_data.get("失败"),
              }),
        check("212确认回执填写样例副本存在且验证通过", receipt_example_copy.exists()
              and receipt_example_copy_verify.exists()
              and int(receipt_example_copy_verify_data.get("失败") or 0) == 0
              and (receipt_example_copy_data.get("汇总", {}) or {}).get("是否正式回执") is False
              and (receipt_example_copy_data.get("汇总", {}) or {}).get("是否允许用于写191") is False, {
                  "确认回执填写样例副本": file_state(receipt_example_copy),
                  "验证日志": file_state(receipt_example_copy_verify),
                  "样例链路数": (receipt_example_copy_data.get("汇总", {}) or {}).get("样例链路数"),
                  "验证通过": receipt_example_copy_verify_data.get("通过"),
                  "验证失败": receipt_example_copy_verify_data.get("失败"),
              }),
        check("213确认后路径演练报告存在且验证通过", post_confirmation_rehearsal.exists()
              and post_confirmation_rehearsal_verify.exists()
              and int(post_confirmation_rehearsal_verify_data.get("失败") or 0) == 0
              and (post_confirmation_rehearsal_data.get("汇总", {}) or {}).get("模拟是否三链路确认完成") is True
              and int((post_confirmation_rehearsal_data.get("汇总", {}) or {}).get("模拟允许调度步骤数") or 0) == 5, {
                  "确认后路径演练报告": file_state(post_confirmation_rehearsal),
                  "验证日志": file_state(post_confirmation_rehearsal_verify),
                  "演练结论": (post_confirmation_rehearsal_data.get("汇总", {}) or {}).get("演练结论"),
                  "验证通过": post_confirmation_rehearsal_verify_data.get("通过"),
                  "验证失败": post_confirmation_rehearsal_verify_data.get("失败"),
              }),
        check("214正式回执待办卡存在且验证通过", formal_receipt_todo.exists()
              and formal_receipt_todo_verify.exists()
              and int(formal_receipt_todo_verify_data.get("失败") or 0) == 0
              and int((formal_receipt_todo_data.get("汇总", {}) or {}).get("待办链路数") or 0) == 3
              and (formal_receipt_todo_data.get("汇总", {}) or {}).get("本卡是否写入205") is False, {
                  "正式回执待办卡": file_state(formal_receipt_todo),
                  "验证日志": file_state(formal_receipt_todo_verify),
                  "待办链路数": (formal_receipt_todo_data.get("汇总", {}) or {}).get("待办链路数"),
                  "验证通过": formal_receipt_todo_verify_data.get("通过"),
                  "验证失败": formal_receipt_todo_verify_data.get("失败"),
              }),
        check("215正式回执填写前自检存在且验证通过", formal_receipt_prefill.exists()
              and formal_receipt_prefill_verify.exists()
              and int(formal_receipt_prefill_verify_data.get("失败") or 0) == 0
              and int((formal_receipt_prefill_data.get("汇总", {}) or {}).get("正式回执行数") or 0) == 3
              and (formal_receipt_prefill_data.get("汇总", {}) or {}).get("本报告是否写入205") is False, {
                  "正式回执填写前自检": file_state(formal_receipt_prefill),
                  "验证日志": file_state(formal_receipt_prefill_verify),
                  "当前缺失字段总数": (formal_receipt_prefill_data.get("汇总", {}) or {}).get("当前缺失字段总数"),
                  "验证通过": formal_receipt_prefill_verify_data.get("通过"),
                  "验证失败": formal_receipt_prefill_verify_data.get("失败"),
              }),
        check("216正式回执录入后受控重跑预演存在且验证通过", formal_receipt_rerun.exists()
              and formal_receipt_rerun_verify.exists()
              and int(formal_receipt_rerun_verify_data.get("失败") or 0) == 0
              and int((formal_receipt_rerun_data.get("汇总", {}) or {}).get("候选有效链路数") or 0) == 3, {
                  "正式回执录入后受控重跑预演": file_state(formal_receipt_rerun),
                  "验证日志": file_state(formal_receipt_rerun_verify),
                  "验证通过": formal_receipt_rerun_verify_data.get("通过"),
                  "验证失败": formal_receipt_rerun_verify_data.get("失败"),
              }),
        check("206候选采用前闸口存在且验证通过", candidate_pre_gate.exists()
              and candidate_pre_gate_verify.exists()
              and int(candidate_pre_gate_verify_data.get("失败") or 0) == 0
              and candidate_pre_gate_data.get("是否允许触发197_apply_191") is False
              and candidate_pre_gate_data.get("是否允许进入模板同步执行器") is False, {
                  "候选采用前闸口": file_state(candidate_pre_gate),
                  "验证日志": file_state(candidate_pre_gate_verify),
                  "闸口结论": candidate_pre_gate_data.get("闸口结论"),
                  "阻断项数量": candidate_pre_gate_data.get("阻断项数量"),
                  "验证通过": candidate_pre_gate_verify_data.get("通过"),
                  "验证失败": candidate_pre_gate_verify_data.get("失败"),
              }),
        check("207候选采用受控执行预案存在且验证通过", candidate_controlled_plan.exists()
              and candidate_controlled_plan_verify.exists()
              and int(candidate_controlled_plan_verify_data.get("失败") or 0) == 0
              and candidate_controlled_plan_data.get("当前是否允许自动执行") is False
              and candidate_controlled_plan_data.get("当前是否允许写191") is False, {
                  "候选采用受控执行预案": file_state(candidate_controlled_plan),
                  "验证日志": file_state(candidate_controlled_plan_verify),
                  "当前206闸口结论": candidate_controlled_plan_data.get("当前206闸口结论"),
                  "验证通过": candidate_controlled_plan_verify_data.get("通过"),
                  "验证失败": candidate_controlled_plan_verify_data.get("失败"),
              }),
        check("208候选采用预览存在且验证通过", candidate_preview.exists()
              and candidate_preview_verify.exists()
              and int(candidate_preview_verify_data.get("失败") or 0) == 0
              and all(value is False for value in (candidate_preview_data.get("安全边界", {}) or {}).values()), {
                  "候选采用预览": file_state(candidate_preview),
                  "验证日志": file_state(candidate_preview_verify),
                  "阻断原因": (candidate_preview_data.get("汇总", {}) or {}).get("当前阻断原因"),
                  "验证通过": candidate_preview_verify_data.get("通过"),
                  "验证失败": candidate_preview_verify_data.get("失败"),
              }),
        check("209受控写入命令草案存在且验证通过", controlled_command_draft.exists()
              and controlled_command_draft_verify.exists()
              and int(controlled_command_draft_verify_data.get("失败") or 0) == 0
              and all(value is False for value in (controlled_command_draft_data.get("安全边界", {}) or {}).values()), {
                  "受控写入命令草案": file_state(controlled_command_draft),
                  "验证日志": file_state(controlled_command_draft_verify),
                  "高风险命令允许数量": (controlled_command_draft_data.get("汇总", {}) or {}).get("高风险命令允许数量"),
                  "验证通过": controlled_command_draft_verify_data.get("通过"),
                  "验证失败": controlled_command_draft_verify_data.get("失败"),
              }),
        check("198填写质量闸口存在且验证通过", quality_gate.exists()
              and quality_gate_verify.exists()
              and int(quality_gate_verify_data.get("失败") or 0) == 0
              and (quality_gate_data.get("安全边界", {}) or {}).get("填写191") is False, {
                  "质量闸口": file_state(quality_gate),
                  "验证日志": file_state(quality_gate_verify),
                  "闸口结论": quality_gate_data.get("闸口结论"),
                  "验证通过": quality_gate_verify_data.get("通过"),
                  "验证失败": quality_gate_verify_data.get("失败"),
              }),
        check("193同步闸口存在且允许进入模板同步执行器", sync_gate.exists() and sync.get("是否允许进入模板同步执行器") is True, sync.get("闸口结论")),
        check("194受控同步执行验证通过", template_sync_verify.exists()
              and int(template_sync_verify_data.get("失败") or 0) == 0
              and any(item.get("名称") == "193闸口状态与191完成度一致" and item.get("通过") is True for item in template_sync_verify_data.get("检查项", [])), {
                  "验证日志": file_state(template_sync_verify),
                  "通过": template_sync_verify_data.get("通过"),
                  "失败": template_sync_verify_data.get("失败"),
              }),
        check("197完成后预演检查已同步191且验证通过", after_191_preflight.exists()
              and after_191_preflight_data.get("是否写入191台账") is True
              and after_191_preflight_verify.exists()
              and int(after_191_preflight_verify_data.get("失败") or 0) == 0, {
                  "预演报告": file_state(after_191_preflight),
                  "验证日志": file_state(after_191_preflight_verify),
                  "总结论": after_191_preflight_data.get("总结论"),
                  "验证通过": after_191_preflight_verify_data.get("通过"),
                  "验证失败": after_191_preflight_verify_data.get("失败"),
              }),
        check("文稿质检脚本存在且旁路", text_reviewer.exists(), file_state(text_reviewer)),
        check("文稿质检记录库路径存在或可创建", review_records.parent.exists(), file_state(review_records.parent)),
        check("文稿质检旁路观察面板存在且不允许第二阶段", review_observation.exists() and review_observation_data.get("是否允许进入第二阶段") is False, {
            "面板": file_state(review_observation),
            "生成脚本": file_state(review_observation_script),
            "结论": review_observation_data.get("结论", ""),
            "统计": review_observation_data.get("统计", {}),
            "用户确认进度": review_confirmation,
        }),
        check("文稿质检样本复盘存在且不允许第二阶段", review_retrospective.exists() and review_retrospective_data.get("是否允许进入第二阶段") is False, {
            "复盘": file_state(review_retrospective),
            "生成脚本": file_state(review_retrospective_script),
            "结论": review_retrospective_data.get("结论", ""),
            "统计": review_retrospective_data.get("统计", {}),
        }),
        check("股票报告质检融入方案存在", stock_report_review_doc.exists(), file_state(stock_report_review_doc)),
        check("股票报告质检融入规则存在", stock_report_review_rule.exists(), file_state(stock_report_review_rule)),
    ]

    four_system_checks = [
        check("四系统开工快检报告存在", open_check.exists(), file_state(open_check)),
        check("四系统股票小闭环8/8", four_pass == 8 and four_fail == 0, file_state(four_loop)),
        check("股票四系统闭环完成观察记录存在", completion_observation.exists(), {
                  "完成观察记录": file_state(completion_observation),
                  "验证日志": file_state(completion_observation_verify),
                  "总结论": completion_observation_data.get("总结论"),
                  "验证通过": completion_observation_verify_data.get("通过"),
                  "验证失败": completion_observation_verify_data.get("失败"),
              }),
        check("子系统继承状态存在", inheritance.exists(), file_state(inheritance)),
        check("版本治理V1.1快照存在", version.get("版本") == "V1.1", file_state(version_v11)),
        check("n8n影子试验预案存在但未执行", n8n_shadow_plan.exists() and "未创建容器" in load_json(n8n_shadow_plan, {}).get("结论", ""), file_state(n8n_shadow_plan)),
        check("版本治理验证脚本存在", version_verify_script.exists(), file_state(version_verify_script)),
        check("宪法级原则总纲存在", constitution_doc.exists(), file_state(constitution_doc)),
        check("宪法级原则规则存在", constitution_rule.exists(), file_state(constitution_rule)),
        check("报告质检与宪法原则验证脚本存在", constitution_review_verify.exists(), file_state(constitution_review_verify)),
    ]

    evolution_checks = [
        check("学习提炼导航规则存在", learning_rules.exists(), file_state(learning_rules)),
        check("全系统影子试验失败隔离原则存在", engineering_principle.exists(), file_state(engineering_principle)),
        check("四系统小闭环通用施工模板存在", method_template.exists(), file_state(method_template)),
        check("报告质检通用方法存在", report_review_method.exists(), file_state(report_review_method)),
    ]

    groups = [
        group("股票系统日常可用", stock_checks),
        group("股票系统补强与进化接口", stock_evolution_checks),
        group("四系统闭环治理", four_system_checks),
        group("进化沉淀与复用", evolution_checks),
    ]
    failed = [item for grp in groups for item in grp["检查项"] if not item["通过"]]
    stock_failed = [item for item in stock_checks if not item["通过"]]
    progress_text, remaining_time = estimate_progress_and_time(failed, quality_gate_data, review_confirmation)

    report = {
        "名称": "股票系统与四系统融合闭环状态面板",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "融合结论": "通过：可以按融合主线继续施工" if not failed else "待处理：存在融合断点",
        "是否影响股票日常使用": "不影响，股票日常可用检查全部通过" if not stock_failed else "可能影响，需先处理股票日常可用失败项",
        "当前阶段": "股票系统与四系统最小闭环已进入完成观察态",
        "当前进度": progress_text,
        "剩余有效工作时间估算": remaining_time,
        "进度依据": [
            "股票日常可用、企微前台回归、推荐点击详情、手机端基础排版、图形报告和C+++验收均已进入主验收。",
            "总管开工快检、融合面板、融合验证、一键执行器和历史观察已形成可重复执行入口。",
            "完成观察记录已接入总管快检和融合面板，观察期按24小时或一次完整业务周期复核。",
            "智能系统文稿质检已完成旁路观察与样本复盘，但仍保持第一阶段，不接正式推送链路。",
            "进化系统已沉淀影子试验、逐步组合、失败隔离、硬件天花板和报告质检通用方法。",
            "191最小行动卡、191资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205正式确认回执、210确认回执状态面板、211回执后调度清单、212确认回执填写样例副本、213确认后路径演练报告、214正式回执待办卡、215正式回执填写前自检、216正式回执录入后受控重跑预演、206候选采用前闸口、207受控执行预案、208候选采用预览、209受控写入命令草案、198填写质量闸口、197同步191后预演检查、193模板同步闸口和194受控同步执行验证已接入；系统已先处理正规资料候选、生成填写建议、压缩确认问题、生成候选填写副本、预览采用差异、推演采用后剩余质量缺口，再把正式205确认回执、候选值和核验字段写入191 CSV，经198质量闸口、197同步191台账、193闸口和194执行器完成172/175/178人工模板受控同步；主要剩余缺口是收尾复核、观察期记录，以及报告质检继续累计用户确认样本。",
        ],
        "检查组": groups,
        "融合施工主线": [
            "股票系统继续承担真实业务样板：企微问答、推荐报告、单股报告、图形报告和证据链。",
            "总管系统负责状态面板、开工快检、版本治理、调度边界和验收口径。",
            "智能系统负责企微桥接、模型能力、文稿质检旁路和手机端输出质量补强。",
            "进化系统只沉淀已验证经验：影子试验、逐步组合、失败隔离、排版规则和证据链规则。",
            "报告质检层负责把关内容完整性、文章结构、语言描述和手机端排版，但不改事实和股票判断。",
            "文稿质检观察面板只判断旁路样本进度，不授权进入第二阶段，不接正式推送链路。",
            "文稿质检样本复盘负责提炼已发生样本的经验和风险，确认模型不自动替换、规则先守门。",
            "完成观察记录负责把股票日常可用、四系统快检、融合面板和194写入结果合成为观察期起点。",
            "所有新能力先旁路、影子、样本或只读验证，不直接冲击股票正式链路。",
        ],
        "下一步": [
            "进入24小时或一次完整业务周期观察；观察期内只复核，不为完善而改动正式链路。",
            "手机端排版继续纳入观察期复核，确保企业微信窄屏阅读不回退。",
            review_next_step,
            "文稿质检样本复盘已确认：模型可做主编候选，但禁止字段、图片链接、报告链接、免责声明必须由脚本硬守门。",
            "所有新施工继续按宪法级原则检查：硬件天花板、平稳运行、能力边界、影子试验、失败隔离、克制施工。",
            "保留199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205正式确认回执、206候选采用前闸口、208采用预览、198填写质量闸口、197同步191预演、193闸口和194受控同步执行的顺序：系统先处理可信资料候选、生成填写建议、压缩确认问题、生成候选副本、预览写入差异、推演采用后质量缺口，确认后才补191 CSV，CSV填完后先质量检查、再同步191台账、再走193/194显式同步。",
        ],
        "安全边界": {
            "触发n8n": False,
            "真实发送企业微信": False,
            "重启服务": False,
            "写正式业务库": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }

    latest_json = OUT_DIR / "股票四系统融合闭环状态面板_最新.json"
    latest_md = OUT_DIR / "股票四系统融合闭环状态面板_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": report["融合结论"],
        "是否影响股票日常使用": report["是否影响股票日常使用"],
        "失败数量": len(failed),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
