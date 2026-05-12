# -*- coding: utf-8 -*-
"""
名称：执行四系统小闭环开工快检.py
作用：开工前快速确认股票样板小闭环是否仍可继续施工。
触发方式：手动开工快检；不由n8n自动触发。
依赖：本机Python标准库、19300/19302本地健康接口、股票和四系统最新验收产物、191最小行动卡、191资料来源导航卡、199资料候选处理包、200填写建议草案、201最小人工确认清单、202候选填写CSV副本、203候选写入差异预览、204候选采用后质量预演、205候选采用确认回执草案、216正式回执录入后受控重跑预演、206候选采用前闸口、198填写质量闸口、197完成后预演检查、194模板同步执行、文稿质检旁路观察与样本复盘产物。
所属系统：00杰哥系统总管。
输出：03数据/四系统小闭环/四系统小闭环开工快检_最新.json 与 .md。
安全边界：只读端口、健康接口和最新验收产物；只写00总管开工快检报告；
不触发n8n、不真实发送企业微信、不重启服务、不写正式业务库、不调用券商接口、不自动交易、
不更新施工接续包/接续卡片/新对话包。
标识：四系统小闭环；开工快检；只读验证；非接续包更新。
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
INTELLIGENCE = ROOT / "01杰哥智能系统"
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = MANAGER / "03数据" / "四系统小闭环"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def write_json(path: Path, data: dict[str, Any]) -> None:
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


def port_listening(port: int, host: str = "127.0.0.1", timeout: float = 1.5) -> bool:
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


def run_python(script: Path, timeout: int = 30) -> dict[str, Any]:
    if not script.exists():
        return {"路径": str(script), "返回码": 127, "成功": False, "输出": "脚本不存在"}
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(script.parent),
            capture_output=True,
            env=env,
            timeout=timeout,
        )
        stdout = decode_process_output(completed.stdout)
        stderr = decode_process_output(completed.stderr)
        return {
            "路径": str(script),
            "返回码": completed.returncode,
            "成功": completed.returncode == 0,
            "输出": stdout.strip()[-2000:],
            "错误": stderr.strip()[-1000:],
        }
    except Exception as exc:
        return {"路径": str(script), "返回码": -1, "成功": False, "输出": "", "错误": str(exc)}


def decode_process_output(raw: bytes | str | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    for encoding in ("utf-8", "gbk", "cp936"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def contains_pass(path: Path, needles: list[str]) -> bool:
    text = read_text(path)
    return path.exists() and all(needle in text for needle in needles)


def markdown_acceptance_pass(path: Path, min_pass: int) -> bool:
    text = read_text(path)
    match = re.search(r"通过：\s*(\d+)\s*/\s*(\d+)", text)
    failed = re.search(r"失败：\s*(\d+)", text)
    if not path.exists() or not match or not failed:
        return False
    return int(match.group(1)) >= min_pass and int(failed.group(1)) == 0


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 四系统小闭环开工快检 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 快检结论：{report['快检结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 二、检查项",
        "",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['名称']}：{'通过' if item['通过'] else '失败'}；{item['摘要']}")
    lines.extend([
        "",
        "## 三、下一步",
        "",
        report["下一步"],
        "",
        "## 四、安全边界",
        "",
        "- 不触发 n8n。",
        "- 不真实发送企业微信。",
        "- 不重启服务。",
        "- 不调用券商接口，不自动交易。",
        "- 不写正式业务库。",
        "- 不更新施工接续包、接续卡片、新对话包；收工或新开对话时再统一固化。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    files = {
        "当前施工面板": MANAGER / "07文档" / "当前施工面板.md",
        "四系统状态面板": OUT_DIR / "四系统股票小闭环状态面板_最新.md",
        "四系统验收": OUT_DIR / "四系统股票小闭环验收_最新.md",
        "一键执行记录": OUT_DIR / "四系统股票小闭环一键执行_最新.md",
        "子系统继承状态": MANAGER / "03数据" / "全闭环保障" / "子系统全闭环继承状态_最新.json",
        "股票完全交付验收": STOCK / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md",
        "股票C+++验收": STOCK / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md",
        "180证据总览": STOCK / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json",
        "191最小行动卡": STOCK / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写最小行动卡_最新.md",
        "191最小行动卡验证日志": STOCK / "04日志" / "单股证据核验人工填写最小行动卡" / "single-stock-evidence-minimum-action-card-verify-最新.json",
        "191资料来源导航卡": STOCK / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.md",
        "191资料来源导航卡验证日志": STOCK / "04日志" / "单股证据核验资料来源导航卡" / "single-stock-evidence-source-navigation-card-verify-最新.json",
        "199资料候选处理包": STOCK / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.md",
        "199资料候选处理包验证日志": STOCK / "04日志" / "单股证据核验资料候选处理包" / "single-stock-evidence-source-candidate-package-verify-最新.json",
        "200填写建议草案": STOCK / "03数据" / "200单股证据核验191填写建议草案" / "单股证据核验191填写建议草案_最新.md",
        "200填写建议草案验证日志": STOCK / "04日志" / "单股证据核验191填写建议草案" / "single-stock-evidence-191-fill-suggestion-draft-verify-最新.json",
        "201最小人工确认清单": STOCK / "03数据" / "201单股证据核验最小人工确认清单" / "单股证据核验最小人工确认清单_最新.md",
        "201最小人工确认清单验证日志": STOCK / "04日志" / "单股证据核验最小人工确认清单" / "single-stock-evidence-minimal-human-confirmation-list-verify-最新.json",
        "202候选填写CSV副本": STOCK / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.md",
        "202候选填写CSV副本验证日志": STOCK / "04日志" / "单股证据核验191候选填写CSV副本" / "single-stock-evidence-191-candidate-filled-csv-copy-verify-最新.json",
        "203候选写入差异预览": STOCK / "03数据" / "203单股证据核验191候选写入差异预览" / "单股证据核验191候选写入差异预览_最新.md",
        "203候选写入差异预览验证日志": STOCK / "04日志" / "单股证据核验191候选写入差异预览" / "single-stock-evidence-191-candidate-write-diff-preview-verify-最新.json",
        "204候选采用后质量预演": STOCK / "03数据" / "204单股证据核验191候选采用后质量预演" / "单股证据核验191候选采用后质量预演_最新.md",
        "204候选采用后质量预演验证日志": STOCK / "04日志" / "单股证据核验191候选采用后质量预演" / "single-stock-evidence-191-candidate-adoption-quality-preview-verify-最新.json",
        "205候选采用确认回执草案": STOCK / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.md",
        "205候选采用确认回执草案验证日志": STOCK / "04日志" / "单股证据核验191候选采用确认回执草案" / "single-stock-evidence-191-candidate-adoption-confirmation-draft-verify-最新.json",
        "210确认回执状态面板": STOCK / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.md",
        "210确认回执状态面板验证日志": STOCK / "04日志" / "单股证据核验确认回执状态面板" / "single-stock-evidence-confirmation-receipt-status-panel-verify-最新.json",
        "211回执后调度清单": STOCK / "03数据" / "211单股证据核验回执后调度清单" / "单股证据核验回执后调度清单_最新.md",
        "211回执后调度清单验证日志": STOCK / "04日志" / "单股证据核验回执后调度清单" / "single-stock-evidence-post-confirmation-dispatch-list-verify-最新.json",
        "212确认回执填写样例副本": STOCK / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.md",
        "212确认回执填写样例副本验证日志": STOCK / "04日志" / "单股证据核验确认回执填写样例副本" / "single-stock-evidence-confirmation-receipt-filled-example-copy-verify-最新.json",
        "213确认后路径演练报告": STOCK / "03数据" / "213单股证据核验确认后路径演练报告" / "单股证据核验确认后路径演练报告_最新.md",
        "213确认后路径演练报告验证日志": STOCK / "04日志" / "单股证据核验确认后路径演练报告" / "single-stock-evidence-post-confirmation-path-rehearsal-report-verify-最新.json",
        "214正式回执待办卡": STOCK / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.md",
        "214正式回执待办卡验证日志": STOCK / "04日志" / "单股证据核验正式回执待办卡" / "single-stock-evidence-formal-confirmation-receipt-todo-card-verify-最新.json",
        "215正式回执填写前自检": STOCK / "03数据" / "215单股证据核验正式回执填写前自检" / "单股证据核验正式回执填写前自检_最新.md",
        "215正式回执填写前自检验证日志": STOCK / "04日志" / "单股证据核验正式回执填写前自检" / "single-stock-evidence-formal-confirmation-receipt-prefill-check-verify-最新.json",
        "216正式回执录入后受控重跑预演": STOCK / "03数据" / "216单股证据核验正式回执录入后受控重跑预演" / "单股证据核验正式回执录入后受控重跑预演_最新.md",
        "216正式回执录入后受控重跑预演验证日志": STOCK / "04日志" / "单股证据核验正式回执录入后受控重跑预演" / "single-stock-evidence-formal-confirmation-post-entry-controlled-rerun-rehearsal-verify-最新.json",
        "206候选采用前闸口": STOCK / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.md",
        "206候选采用前闸口验证日志": STOCK / "04日志" / "单股证据核验191候选采用前闸口" / "single-stock-evidence-191-candidate-adoption-pre-gate-verify-最新.json",
        "207候选采用受控执行预案": STOCK / "03数据" / "207单股证据核验191候选采用受控执行预案" / "单股证据核验191候选采用受控执行预案_最新.md",
        "207候选采用受控执行预案验证日志": STOCK / "04日志" / "单股证据核验191候选采用受控执行预案" / "single-stock-evidence-191-candidate-adoption-controlled-plan-verify-最新.json",
        "208候选采用预览": STOCK / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.md",
        "208候选采用预览验证日志": STOCK / "04日志" / "单股证据核验191候选采用预览" / "single-stock-evidence-191-candidate-adoption-preview-verify-最新.json",
        "209受控写入命令草案": STOCK / "03数据" / "209单股证据核验受控写入命令草案" / "单股证据核验受控写入命令草案_最新.md",
        "209受控写入命令草案验证日志": STOCK / "04日志" / "单股证据核验受控写入命令草案" / "single-stock-evidence-controlled-write-command-draft-verify-最新.json",
        "198填写质量闸口": STOCK / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.md",
        "198填写质量闸口验证日志": STOCK / "04日志" / "单股证据核验191填写质量闸口" / "single-stock-evidence-191-quality-gate-verify-最新.json",
        "197完成后预演检查": STOCK / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md",
        "197完成后预演检查验证日志": STOCK / "04日志" / "单股证据核验191完成后预演检查" / "single-stock-evidence-after-191-preflight-verify-最新.json",
        "194模板同步执行报告": STOCK / "03数据" / "194单股证据核验模板同步执行" / "单股证据核验模板同步执行报告_最新.md",
        "194模板同步执行验证日志": STOCK / "04日志" / "单股证据核验模板同步执行" / "single-stock-evidence-template-sync-execute-verify-最新.json",
        "股票四系统闭环完成观察记录": MANAGER / "03数据" / "四系统小闭环" / "股票四系统闭环完成观察记录_最新.md",
        "股票四系统闭环完成观察记录验证日志": MANAGER / "04日志" / "四系统小闭环" / "stock-four-system-closed-loop-completion-observation-verify-最新.json",
        "文稿质检脚本": INTELLIGENCE / "02脚本" / "文稿质检" / "text_reviewer.py",
        "文稿质检观察面板": INTELLIGENCE / "03数据" / "文稿质检" / "观察面板" / "文稿质检旁路观察面板_最新.json",
        "文稿质检样本复盘报告": INTELLIGENCE / "03数据" / "文稿质检" / "样本复盘" / "文稿质检样本复盘报告_最新.md",
        "文稿质检样本复盘验证脚本": INTELLIGENCE / "02脚本" / "文稿质检" / "验证文稿质检样本复盘报告.py",
        "学习提炼导航规则": EVOLUTION / "01配置" / "学习提炼导航规则.json",
        "通用施工模板": EVOLUTION / "03数据" / "04通用方法" / "四系统小闭环_通用施工模板_20260503.md",
        "权威档案优先方法": EVOLUTION / "03数据" / "04通用方法" / "状态面板读取权威档案优先_20260503.md",
        "总纲通用进化机制": MANAGER / "07文档" / "设计纲领" / "影子试验逐步组合失败隔离通用进化机制_20260503.md",
        "进化通用方法": EVOLUTION / "03数据" / "04通用方法" / "影子试验_逐步组合_失败隔离通用进化机制_20260503.md",
        "版本升级治理规则": MANAGER / "01配置" / "upgrade_rules.json",
        "软件版本台账": MANAGER / "01配置" / "version_ledger.json",
        "版本升级评估脚本": MANAGER / "02脚本" / "维护" / "version_check.py",
        "版本升级评估报告": MANAGER / "04日志" / "版本升级治理" / "upgrade_check_latest.json",
        "股票四系统融合面板": OUT_DIR / "股票四系统融合闭环状态面板_最新.json",
        "股票四系统融合验证脚本": MANAGER / "02脚本" / "验证股票四系统融合闭环状态面板.py",
        "脚本标头审计脚本": MANAGER / "02脚本" / "验证脚本标头规范.py",
    }

    stock_health = http_json("http://127.0.0.1:19300/%E5%81%A5%E5%BA%B7")
    wecom_health = http_json("http://127.0.0.1:19302/health")
    inheritance_verify = run_python(MANAGER / "02脚本" / "验证子系统全闭环继承状态.py")
    script_header_verify = run_python(files["脚本标头审计脚本"])
    version_report = {}
    if files["版本升级评估报告"].exists():
        try:
            version_report = json.loads(files["版本升级评估报告"].read_text(encoding="utf-8-sig"))
        except Exception:
            version_report = {}
    fusion_report = {}
    if files["股票四系统融合面板"].exists():
        try:
            fusion_report = json.loads(files["股票四系统融合面板"].read_text(encoding="utf-8-sig"))
        except Exception:
            fusion_report = {}
    minimum_card_verify_report = {}
    if files["191最小行动卡验证日志"].exists():
        try:
            minimum_card_verify_report = json.loads(files["191最小行动卡验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            minimum_card_verify_report = {}
    source_navigation_verify_report = {}
    if files["191资料来源导航卡验证日志"].exists():
        try:
            source_navigation_verify_report = json.loads(files["191资料来源导航卡验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            source_navigation_verify_report = {}
    source_candidate_verify_report = {}
    if files["199资料候选处理包验证日志"].exists():
        try:
            source_candidate_verify_report = json.loads(files["199资料候选处理包验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            source_candidate_verify_report = {}
    fill_suggestion_verify_report = {}
    if files["200填写建议草案验证日志"].exists():
        try:
            fill_suggestion_verify_report = json.loads(files["200填写建议草案验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            fill_suggestion_verify_report = {}
    minimal_confirmation_verify_report = {}
    if files["201最小人工确认清单验证日志"].exists():
        try:
            minimal_confirmation_verify_report = json.loads(files["201最小人工确认清单验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            minimal_confirmation_verify_report = {}
    candidate_filled_csv_verify_report = {}
    if files["202候选填写CSV副本验证日志"].exists():
        try:
            candidate_filled_csv_verify_report = json.loads(files["202候选填写CSV副本验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_filled_csv_verify_report = {}
    candidate_write_diff_verify_report = {}
    if files["203候选写入差异预览验证日志"].exists():
        try:
            candidate_write_diff_verify_report = json.loads(files["203候选写入差异预览验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_write_diff_verify_report = {}
    candidate_quality_preview_verify_report = {}
    if files["204候选采用后质量预演验证日志"].exists():
        try:
            candidate_quality_preview_verify_report = json.loads(files["204候选采用后质量预演验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_quality_preview_verify_report = {}
    candidate_confirmation_verify_report = {}
    if files["205候选采用确认回执草案验证日志"].exists():
        try:
            candidate_confirmation_verify_report = json.loads(files["205候选采用确认回执草案验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_confirmation_verify_report = {}
    receipt_status_verify_report = {}
    if files["210确认回执状态面板验证日志"].exists():
        try:
            receipt_status_verify_report = json.loads(files["210确认回执状态面板验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            receipt_status_verify_report = {}
    post_confirmation_dispatch_verify_report = {}
    if files["211回执后调度清单验证日志"].exists():
        try:
            post_confirmation_dispatch_verify_report = json.loads(files["211回执后调度清单验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            post_confirmation_dispatch_verify_report = {}
    receipt_example_verify_report = {}
    if files["212确认回执填写样例副本验证日志"].exists():
        try:
            receipt_example_verify_report = json.loads(files["212确认回执填写样例副本验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            receipt_example_verify_report = {}
    post_confirmation_rehearsal_verify_report = {}
    if files["213确认后路径演练报告验证日志"].exists():
        try:
            post_confirmation_rehearsal_verify_report = json.loads(files["213确认后路径演练报告验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            post_confirmation_rehearsal_verify_report = {}
    formal_receipt_todo_verify_report = {}
    if files["214正式回执待办卡验证日志"].exists():
        try:
            formal_receipt_todo_verify_report = json.loads(files["214正式回执待办卡验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            formal_receipt_todo_verify_report = {}
    formal_receipt_prefill_verify_report = {}
    if files["215正式回执填写前自检验证日志"].exists():
        try:
            formal_receipt_prefill_verify_report = json.loads(files["215正式回执填写前自检验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            formal_receipt_prefill_verify_report = {}
    formal_receipt_rerun_verify_report = {}
    if files["216正式回执录入后受控重跑预演验证日志"].exists():
        try:
            formal_receipt_rerun_verify_report = json.loads(files["216正式回执录入后受控重跑预演验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            formal_receipt_rerun_verify_report = {}
    candidate_pre_gate_verify_report = {}
    if files["206候选采用前闸口验证日志"].exists():
        try:
            candidate_pre_gate_verify_report = json.loads(files["206候选采用前闸口验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_pre_gate_verify_report = {}
    candidate_controlled_plan_verify_report = {}
    if files["207候选采用受控执行预案验证日志"].exists():
        try:
            candidate_controlled_plan_verify_report = json.loads(files["207候选采用受控执行预案验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_controlled_plan_verify_report = {}
    candidate_preview_verify_report = {}
    if files["208候选采用预览验证日志"].exists():
        try:
            candidate_preview_verify_report = json.loads(files["208候选采用预览验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            candidate_preview_verify_report = {}
    controlled_command_verify_report = {}
    if files["209受控写入命令草案验证日志"].exists():
        try:
            controlled_command_verify_report = json.loads(files["209受控写入命令草案验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            controlled_command_verify_report = {}
    quality_gate_verify_report = {}
    if files["198填写质量闸口验证日志"].exists():
        try:
            quality_gate_verify_report = json.loads(files["198填写质量闸口验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            quality_gate_verify_report = {}
    after_191_preflight_verify_report = {}
    if files["197完成后预演检查验证日志"].exists():
        try:
            after_191_preflight_verify_report = json.loads(files["197完成后预演检查验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            after_191_preflight_verify_report = {}
    template_sync_verify_report = {}
    if files["194模板同步执行验证日志"].exists():
        try:
            template_sync_verify_report = json.loads(files["194模板同步执行验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            template_sync_verify_report = {}
    completion_observation_verify_report = {}
    if files["股票四系统闭环完成观察记录验证日志"].exists():
        try:
            completion_observation_verify_report = json.loads(files["股票四系统闭环完成观察记录验证日志"].read_text(encoding="utf-8-sig"))
        except Exception:
            completion_observation_verify_report = {}

    checks: list[dict[str, Any]] = [
        {"名称": "股票助手19300监听", "通过": port_listening(19300), "摘要": "19300端口可连接"},
        {"名称": "企微桥接19302监听", "通过": port_listening(19302), "摘要": "19302端口可连接"},
        {"名称": "股票助手健康接口", "通过": stock_health.get("可访问") is True, "摘要": json.dumps(stock_health, ensure_ascii=False)[:300]},
        {"名称": "企微桥接健康接口", "通过": wecom_health.get("可访问") is True, "摘要": json.dumps(wecom_health, ensure_ascii=False)[:300]},
        {"名称": "股票交付边界已知且C+++可用", "通过": contains_pass(files["股票完全交付验收"], ["C+++", "真实主动消息尚未成功"]), "摘要": str(files["股票完全交付验收"])},
        {"名称": "股票C+++日常可用验收仍通过", "通过": markdown_acceptance_pass(files["股票C+++验收"], 33), "摘要": str(files["股票C+++验收"])},
        {"名称": "四系统小闭环仍8/8", "通过": contains_pass(files["四系统验收"], ["通过数量：8", "失败数量：0"]), "摘要": str(files["四系统验收"])},
        {"名称": "一键执行最近失败为0", "通过": contains_pass(files["一键执行记录"], ["失败数：0"]), "摘要": str(files["一键执行记录"])},
        {"名称": "子系统继承验证通过", "通过": inheritance_verify["成功"], "摘要": inheritance_verify.get("输出", "")[:300]},
        {"名称": "主线脚本标头审计通过", "通过": script_header_verify["成功"], "摘要": script_header_verify.get("输出", "")[:300]},
        {"名称": "施工接续边界写入当前面板", "通过": contains_pass(files["当前施工面板"], ["一键接续施工包", "准入和阶段判定只认固定"]), "摘要": str(files["当前施工面板"])},
        {"名称": "版本升级治理无铁律违反", "通过": version_report.get("违反铁律数量") == 0, "摘要": str(files["版本升级评估报告"])},
        {"名称": "股票四系统融合面板通过", "通过": fusion_report.get("融合结论") == "通过：可以按融合主线继续施工" and "不影响" in fusion_report.get("是否影响股票日常使用", ""), "摘要": str(files["股票四系统融合面板"])},
        {"名称": "191最小行动卡验证通过", "通过": minimum_card_verify_report.get("失败") == 0, "摘要": json.dumps(minimum_card_verify_report, ensure_ascii=False)[:300]},
        {"名称": "191资料来源导航卡验证通过", "通过": source_navigation_verify_report.get("失败") == 0, "摘要": json.dumps(source_navigation_verify_report, ensure_ascii=False)[:300]},
        {"名称": "199资料候选处理包验证通过", "通过": source_candidate_verify_report.get("失败") == 0, "摘要": json.dumps(source_candidate_verify_report, ensure_ascii=False)[:300]},
        {"名称": "200填写建议草案验证通过", "通过": fill_suggestion_verify_report.get("失败") == 0, "摘要": json.dumps(fill_suggestion_verify_report, ensure_ascii=False)[:300]},
        {"名称": "201最小人工确认清单验证通过", "通过": minimal_confirmation_verify_report.get("失败") == 0, "摘要": json.dumps(minimal_confirmation_verify_report, ensure_ascii=False)[:300]},
        {"名称": "202候选填写CSV副本验证通过", "通过": candidate_filled_csv_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_filled_csv_verify_report, ensure_ascii=False)[:300]},
        {"名称": "203候选写入差异预览验证通过", "通过": candidate_write_diff_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_write_diff_verify_report, ensure_ascii=False)[:300]},
        {"名称": "204候选采用后质量预演验证通过", "通过": candidate_quality_preview_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_quality_preview_verify_report, ensure_ascii=False)[:300]},
        {"名称": "205候选采用确认回执草案验证通过", "通过": candidate_confirmation_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_confirmation_verify_report, ensure_ascii=False)[:300]},
        {"名称": "210确认回执状态面板验证通过", "通过": receipt_status_verify_report.get("失败") == 0, "摘要": json.dumps(receipt_status_verify_report, ensure_ascii=False)[:300]},
        {"名称": "211回执后调度清单验证通过", "通过": post_confirmation_dispatch_verify_report.get("失败") == 0, "摘要": json.dumps(post_confirmation_dispatch_verify_report, ensure_ascii=False)[:300]},
        {"名称": "212确认回执填写样例副本验证通过", "通过": receipt_example_verify_report.get("失败") == 0, "摘要": json.dumps(receipt_example_verify_report, ensure_ascii=False)[:300]},
        {"名称": "213确认后路径演练报告验证通过", "通过": post_confirmation_rehearsal_verify_report.get("失败") == 0, "摘要": json.dumps(post_confirmation_rehearsal_verify_report, ensure_ascii=False)[:300]},
        {"名称": "214正式回执待办卡验证通过", "通过": formal_receipt_todo_verify_report.get("失败") == 0, "摘要": json.dumps(formal_receipt_todo_verify_report, ensure_ascii=False)[:300]},
        {"名称": "215正式回执填写前自检验证通过", "通过": formal_receipt_prefill_verify_report.get("失败") == 0, "摘要": json.dumps(formal_receipt_prefill_verify_report, ensure_ascii=False)[:300]},
        {"名称": "216正式回执录入后受控重跑预演验证通过", "通过": formal_receipt_rerun_verify_report.get("失败") == 0, "摘要": json.dumps(formal_receipt_rerun_verify_report, ensure_ascii=False)[:300]},
        {"名称": "206候选采用前闸口验证通过", "通过": candidate_pre_gate_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_pre_gate_verify_report, ensure_ascii=False)[:300]},
        {"名称": "207候选采用受控执行预案验证通过", "通过": candidate_controlled_plan_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_controlled_plan_verify_report, ensure_ascii=False)[:300]},
        {"名称": "208候选采用预览验证通过", "通过": candidate_preview_verify_report.get("失败") == 0, "摘要": json.dumps(candidate_preview_verify_report, ensure_ascii=False)[:300]},
        {"名称": "209受控写入命令草案验证通过", "通过": controlled_command_verify_report.get("失败") == 0, "摘要": json.dumps(controlled_command_verify_report, ensure_ascii=False)[:300]},
        {"名称": "198填写质量闸口验证通过", "通过": quality_gate_verify_report.get("失败") == 0, "摘要": json.dumps(quality_gate_verify_report, ensure_ascii=False)[:300]},
        {"名称": "197完成后预演检查验证通过", "通过": after_191_preflight_verify_report.get("失败") == 0, "摘要": json.dumps(after_191_preflight_verify_report, ensure_ascii=False)[:300]},
        {"名称": "194模板同步执行验证通过", "通过": template_sync_verify_report.get("失败") == 0, "摘要": json.dumps(template_sync_verify_report, ensure_ascii=False)[:300]},
        {"名称": "股票四系统闭环完成观察记录验证通过", "通过": completion_observation_verify_report.get("失败") == 0, "摘要": json.dumps(completion_observation_verify_report, ensure_ascii=False)[:300]},
    ]
    for name, path in files.items():
        checks.append({"名称": f"关键文件存在：{name}", "通过": path.exists(), "摘要": str(path)})

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "四系统小闭环开工快检",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行四系统小闭环开工快检.py",
        "快检结论": "通过：可以继续施工" if not failed else "待处理：存在开工断点",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查项": checks,
        "关键文件": {name: file_state(path) for name, path in files.items()},
        "下一步": "继续按四系统小闭环施工；如要完整回归，再运行执行四系统股票小闭环.py --no-open。" if not failed else "先处理失败检查项，再继续施工。",
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "重启服务": False,
            "写正式业务库": False,
            "券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }

    latest_json = OUT_DIR / "四系统小闭环开工快检_最新.json"
    latest_md = OUT_DIR / "四系统小闭环开工快检_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": report["快检结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
