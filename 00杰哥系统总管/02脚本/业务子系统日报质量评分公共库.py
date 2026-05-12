# -*- coding: utf-8 -*-
"""
Minimal daily quality scoring helpers for extension business subsystems.
Safety: read local scheduler/file state and write local reports only.
"""

from __future__ import annotations

import json
import base64
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
EXT_ROOT = SYSTEM_ROOT / "02杰哥扩展系统"
MANAGER_ROOT = SYSTEM_ROOT / "00杰哥系统总管"
MANAGER_PANEL_DIR = MANAGER_ROOT / "03数据" / "业务子系统质量透明面板"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "size": 0,
            "modified_at": "",
            "updated_today": False,
        }
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return {
        "path": str(path),
        "exists": True,
        "size": path.stat().st_size,
        "modified_at": modified.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_today": modified.date() == datetime.now().date(),
    }


def scheduled_task_state(task_name: str) -> dict[str, Any]:
    task_b64 = base64.b64encode(task_name.encode("utf-8")).decode("ascii")
    script = r"""
$name = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("__TASK_B64__"))
$task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if (-not $task) {
  [ordered]@{ exists = $false; task_name = $name } | ConvertTo-Json -Depth 6
  exit 0
}
$info = Get-ScheduledTaskInfo -TaskName $name
[ordered]@{
  exists = $true
  task_name = $name
  state = $task.State.ToString()
  last_run_time = $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss")
  last_task_result = $info.LastTaskResult
  next_run_time = $info.NextRunTime.ToString("yyyy-MM-dd HH:mm:ss")
} | ConvertTo-Json -Depth 6
""".replace("__TASK_B64__", task_b64)
    encoded_command = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-EncodedCommand", encoded_command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
        if completed.returncode != 0:
            return {"exists": False, "task_name": task_name, "error": completed.stderr.strip()}
        return json.loads(completed.stdout)
    except Exception as exc:  # noqa: BLE001
        return {"exists": False, "task_name": task_name, "error": str(exc)}


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def latest_file(base: Path, patterns: list[str]) -> Path | None:
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend([item for item in base.rglob(pattern) if item.is_file()])
    if not matches:
        return None
    return sorted(matches, key=lambda item: item.stat().st_mtime, reverse=True)[0]


def collect_latest_output_files(system_root: Path, key_outputs: list[dict[str, Any]], limit: int = 20) -> list[Path]:
    target_files: list[Path] = []
    for spec in key_outputs:
        for rel_dir in spec.get("dirs", []):
            base = system_root / rel_dir
            if base.exists():
                latest = latest_file(base, spec.get("patterns", ["*.md", "*.txt", "*.json"]))
                if latest and latest not in target_files:
                    target_files.append(latest)
    return target_files[:limit]


def read_quality_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def has_any_phrase(text: str, phrases: list[str]) -> bool:
    return any(phrase and phrase in text for phrase in phrases)


def check_outputs(system_root: Path, key_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for spec in key_outputs:
        found: Path | None = None
        for rel_dir in spec.get("dirs", []):
            base = system_root / rel_dir
            if base.exists():
                found = latest_file(base, spec.get("patterns", ["*"]))
                if found:
                    break
        state = file_state(found) if found else {
            "path": "",
            "exists": False,
            "size": 0,
            "modified_at": "",
            "updated_today": False,
        }
        ok = bool(state["exists"] and state["size"] > 0 and state["updated_today"])
        checks.append({
            "name": spec["name"],
            "ok": ok,
            "required": bool(spec.get("required", True)),
            "latest_file": state,
        })
    required = [item for item in checks if item["required"]]
    return {
        "ok": all(item["ok"] for item in required) if required else False,
        "checks": checks,
    }


def scan_banned_phrases(system_root: Path, key_outputs: list[dict[str, Any]], phrases: list[str]) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    scanned: list[str] = []
    target_files = collect_latest_output_files(system_root, key_outputs)
    for path in target_files:
        scanned.append(str(path))
        text = read_quality_text(path)
        for phrase in phrases:
            if phrase and phrase in text:
                hits.append({"phrase": phrase, "path": str(path)})
    return {
        "ok": len(hits) == 0,
        "hits": hits,
        "scanned_files": scanned,
    }


def check_universal_laws(system_root: Path, key_outputs: list[dict[str, Any]], rules: list[dict[str, Any]]) -> dict[str, Any]:
    scanned_files: list[str] = []
    rule_results: list[dict[str, Any]] = []
    target_files = collect_latest_output_files(system_root, key_outputs)
    for path in target_files:
        scanned_files.append(str(path))
    texts = [(path, read_quality_text(path)) for path in target_files]

    for rule in rules:
        rule_id = rule.get("id", "")
        severity = rule.get("severity", "deduct")
        penalty = int(rule.get("penalty", 0))
        hits: list[dict[str, str]] = []

        if rule_id == "silence_is_gold":
            missing_phrases = rule.get("missing_data_phrases", [])
            forced_phrases = rule.get("forced_conclusion_phrases", [])
            for path, text in texts:
                if has_any_phrase(text, missing_phrases) and has_any_phrase(text, forced_phrases):
                    hits.append({"path": str(path), "reason": "missing_data_with_forced_conclusion"})

        elif rule_id == "traceable_conclusions":
            conclusion_phrases = rule.get("conclusion_phrases", [])
            source_phrases = rule.get("source_phrases", [])
            for path, text in texts:
                if has_any_phrase(text, conclusion_phrases) and not has_any_phrase(text, source_phrases):
                    hits.append({"path": str(path), "reason": "conclusion_without_traceable_source"})

        elif rule_id == "human_sovereignty":
            sovereignty_phrases = rule.get("sovereignty_phrases", [])
            for path, text in texts:
                for phrase in sovereignty_phrases:
                    if phrase and phrase in text:
                        hits.append({"path": str(path), "reason": phrase})

        else:
            phrases = rule.get("phrases", [])
            for path, text in texts:
                for phrase in phrases:
                    if phrase and phrase in text:
                        hits.append({"path": str(path), "reason": phrase})

        rule_results.append({
            "id": rule_id,
            "name": rule.get("name", rule_id),
            "severity": severity,
            "penalty": penalty if hits else 0,
            "ok": len(hits) == 0,
            "hits": hits,
        })

    total_penalty = sum(item["penalty"] for item in rule_results)
    return {
        "ok": all(item["ok"] for item in rule_results),
        "total_penalty": total_penalty,
        "rules": rule_results,
        "scanned_files": scanned_files,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['system_name']}日报质量评分",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体状态：{report['overall_status']}",
        f"- 分数：{report['score']}/100",
        "",
        "## 脚本入口",
        "",
    ]
    for item in report["entry_scripts"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 三项质检",
        "",
        f"- 准时性：{report['checks']['timeliness']['ok']}；任务={report['checks']['timeliness']['task_name']}；上次运行={report['checks']['timeliness'].get('last_run_time', '')}；返回码={report['checks']['timeliness'].get('last_task_result', '')}",
        f"- 产出完整性：{report['checks']['output_completeness']['ok']}",
        f"- 输出合规模板：{report['checks']['template_compliance']['ok']}",
        "",
        "## 关键产物",
        "",
    ])
    for item in report["checks"]["output_completeness"]["checks"]:
        state = item["latest_file"]
        lines.append(
            f"- {item['name']}：ok={item['ok']}；today={state['updated_today']}；size={state['size']}；path={state['path']}"
        )
    lines.extend(["", "## 废品表达命中", ""])
    hits = report["checks"]["template_compliance"]["hits"]
    if hits:
        for hit in hits:
            lines.append(f"- {hit['phrase']}：{hit['path']}")
    else:
        lines.append("- 无命中")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 只读读取任务计划程序状态和本地文件。",
        "- 不触发n8n，不发送企业微信，不写正式业务库，不调用交易或外部执行接口。",
    ])
    return "\n".join(lines) + "\n"


def score_system(config: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now()
    system_root = EXT_ROOT / config["system_dir"]
    task = scheduled_task_state(config["task_name"])
    last_run = parse_time(str(task.get("last_run_time", "")))
    timeliness_ok = bool(
        task.get("exists")
        and last_run
        and last_run.date() == now.date()
    )
    timeliness = {
        "ok": timeliness_ok,
        "task_name": config["task_name"],
        **task,
    }
    outputs = check_outputs(system_root, config["key_outputs"])
    compliance = scan_banned_phrases(system_root, config["key_outputs"], config.get("banned_phrases", []))
    universal_laws = check_universal_laws(
        system_root,
        config["key_outputs"],
        config.get("universal_quality_rules", []),
    )
    score = 0
    score += 35 if timeliness["ok"] else 0
    score += 40 if outputs["ok"] else 0
    score += 25 if compliance["ok"] else 0
    score = max(0, score - int(universal_laws.get("total_penalty", 0)))
    severities = {
        rule.get("severity")
        for rule in universal_laws.get("rules", [])
        if not rule.get("ok")
    }
    if "highest_alert" in severities:
        overall = "highest_alert"
        score = 0
    elif "defect" in severities:
        overall = "defect"
        score = 0
    else:
        overall = "pass" if score == 100 else ("warning" if score >= 60 else "blocked")
    report = {
        "system_name": config["system_name"],
        "system_dir": str(system_root),
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": overall,
        "score": score,
        "entry_scripts": [str(system_root / "02脚本" / item) for item in config.get("entry_scripts", [])],
        "checks": {
            "timeliness": timeliness,
            "output_completeness": outputs,
            "template_compliance": compliance,
            "universal_laws": universal_laws,
        },
        "safety": {
            "trigger_n8n": False,
            "send_wecom": False,
            "write_formal_business_db": False,
            "call_trade_or_external_execute_api": False,
        },
    }
    out_dir = system_root / "04日志" / "日报质量评分"
    stamp = now.strftime("%Y%m%d-%H%M%S")
    json_path = out_dir / f"{config['slug']}-daily-quality-score-{stamp}.json"
    latest_json = out_dir / f"{config['slug']}-daily-quality-score-最新.json"
    md_path = out_dir / f"{config['system_name']}日报质量评分_{stamp}.md"
    latest_md = out_dir / f"{config['system_name']}日报质量评分_最新.md"
    write_json(json_path, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)

    manager_copy = MANAGER_PANEL_DIR / "子系统评分" / f"{config['slug']}-daily-quality-score-最新.json"
    manager_md = MANAGER_PANEL_DIR / "子系统评分" / f"{config['system_name']}日报质量评分_最新.md"
    write_json(manager_copy, report)
    write_text(manager_md, markdown)
    print(json.dumps({
        "系统": config["system_name"],
        "状态": overall,
        "分数": score,
        "输出": str(latest_json),
        "总管副本": str(manager_copy),
    }, ensure_ascii=False))
    return report


def aggregate_quality_panel(configs: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now()
    items: list[dict[str, Any]] = []
    for config in configs:
        path = MANAGER_PANEL_DIR / "子系统评分" / f"{config['slug']}-daily-quality-score-最新.json"
        data = load_json(path, {})
        items.append({
            "system_name": config["system_name"],
            "score": data.get("score", 0),
            "overall_status": data.get("overall_status", "missing"),
            "generated_at": data.get("generated_at", ""),
            "timeliness_ok": data.get("checks", {}).get("timeliness", {}).get("ok", False),
            "output_ok": data.get("checks", {}).get("output_completeness", {}).get("ok", False),
            "template_ok": data.get("checks", {}).get("template_compliance", {}).get("ok", False),
            "universal_laws_ok": data.get("checks", {}).get("universal_laws", {}).get("ok", False),
            "source": str(path),
        })
    pass_count = sum(1 for item in items if item["overall_status"] == "pass")
    blocked = [item for item in items if item["overall_status"] == "blocked"]
    warning = [item for item in items if item["overall_status"] == "warning"]
    defect = [item for item in items if item["overall_status"] == "defect"]
    highest_alert = [item for item in items if item["overall_status"] == "highest_alert"]
    report = {
        "name": "业务子系统日报质量透明面板",
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total": len(items),
            "pass": pass_count,
            "warning": len(warning),
            "blocked": len(blocked),
            "defect": len(defect),
            "highest_alert": len(highest_alert),
            "missing_or_not_run": sum(1 for item in items if item["overall_status"] == "missing"),
        },
        "items": items,
        "interpretation": {
            "naked": [item["system_name"] for item in items if not item["timeliness_ok"]],
            "lazy_or_stale": [item["system_name"] for item in items if not item["output_ok"]],
            "talking_nonsense": [item["system_name"] for item in items if not item["template_ok"]],
            "law_breakers": [item["system_name"] for item in items if not item["universal_laws_ok"]],
            "highest_alert": [item["system_name"] for item in highest_alert],
        },
        "safety": {
            "trigger_n8n": False,
            "send_wecom": False,
            "write_formal_business_db": False,
            "call_trade_or_external_execute_api": False,
        },
    }
    latest_json = MANAGER_PANEL_DIR / "业务子系统日报质量透明面板_最新.json"
    latest_md = MANAGER_PANEL_DIR / "业务子系统日报质量透明面板_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, aggregate_markdown(report))
    print(json.dumps({"状态": "updated", "输出": str(latest_json), "Markdown": str(latest_md)}, ensure_ascii=False))
    return report


def aggregate_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 业务子系统日报质量透明面板",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 覆盖系统：{report['summary']['total']}",
        f"- 通过：{report['summary']['pass']}",
        f"- 警告：{report['summary']['warning']}",
        f"- 阻断：{report['summary']['blocked']}",
        "",
        "| 子系统 | 分数 | 状态 | 准时 | 产出 | 合规 | 最近评分 |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for item in report["items"]:
        lines.append(
            f"| {item['system_name']} | {item['score']} | {item['overall_status']} | "
            f"{item['timeliness_ok']} | {item['output_ok']} | {item['template_ok']} | {item['generated_at']} |"
        )
    lines.extend(["", "## 一眼识别", ""])
    lines.append("- 裸奔： " + ("、".join(report["interpretation"]["naked"]) or "无"))
    lines.append("- 偷懒/产出陈旧： " + ("、".join(report["interpretation"]["lazy_or_stale"]) or "无"))
    lines.append("- 胡说八道/废品表达命中： " + ("、".join(report["interpretation"]["talking_nonsense"]) or "无"))
    lines.extend(["", "## 安全边界", ""])
    lines.append("- 本面板只汇总本地评分日志，不启动业务脚本，不触发n8n，不发送企业微信。")
    return "\n".join(lines) + "\n"
