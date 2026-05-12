# -*- coding: utf-8 -*-
"""
Name: 执行治理内核执行化总控.py
System: 00杰哥系统总管 / 02脚本
Purpose: 将治理内核执行化为一次只读总控检查，覆盖施工门禁、总管权责、脚本入口注册、规则血缘、单一真理来源、当前运行能力体检。
Trigger: 手动执行；后续可接入开工自检或施工前门禁。
Dependencies: 六层规则体系与治理内核规则.json；系统底层逻辑.md；搭建与施工规范_完整版.md；Windows Scheduled Tasks。
Output: 00杰哥系统总管/03数据/运行状态/治理内核执行化总控_最新.json。
Safety: 只读扫描和本机端口检查；不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不修改业务规则生效开关。
ChangeLog: 2026-05-10 created as governance execution controller.
"""

from __future__ import annotations

import json
import re
import socket
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
EVOLUTION = ROOT / "03杰哥进化系统"
CONFIG = MANAGER / "01配置" / "六层规则体系与治理内核规则.json"
STATE_DIR = MANAGER / "03数据" / "运行状态"
OUT = STATE_DIR / "治理内核执行化总控_最新.json"

SCRIPT_EXTENSIONS = {".py", ".ps1", ".vbs", ".bat", ".cmd"}
EXCLUDED_PARTS = {
    ".venv",
    "site-packages",
    "__pycache__",
    "05备份",
    "06临时",
    "06经验归档",
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def file_status(path: Path) -> dict:
    item = path if path.exists() else None
    return {
        "路径": str(path),
        "存在": bool(item),
        "大小": item.stat().st_size if item else 0,
        "最后修改时间": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if item else None,
    }


def run_powershell_json(script: str):
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if completed.returncode != 0:
        return {"ok": False, "stderr": completed.stderr.strip(), "stdout": completed.stdout.strip()}
    text = completed.stdout.strip()
    if not text:
        return []
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"ok": False, "parse_error": True, "stdout": text[:2000]}


def task_snapshot() -> list[dict]:
    ps = r"""
$rows=@()
Get-ScheduledTask | Where-Object {
    $_.TaskName -like '*杰哥*' -or $_.TaskName -like '*股票*' -or $_.TaskName -like '*Sparkle*'
} | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName -ErrorAction SilentlyContinue
    $rows += [pscustomobject]@{
        TaskName=$_.TaskName
        State=[string]$_.State
        Hidden=$_.Settings.Hidden
        Execute=($_.Actions | ForEach-Object {$_.Execute}) -join ' || '
        Arguments=($_.Actions | ForEach-Object {$_.Arguments}) -join ' || '
        LastRunTime=if($info){$info.LastRunTime.ToString('yyyy-MM-dd HH:mm:ss')}else{$null}
        LastTaskResult=if($info){$info.LastTaskResult}else{$null}
    }
}
$rows | ConvertTo-Json -Depth 5
"""
    data = run_powershell_json(ps)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    return []


def extract_paths_from_task(task: dict) -> list[str]:
    text = f"{task.get('Execute', '')} {task.get('Arguments', '')}"
    pattern = r"[A-Z]:\\[^\"'\s]+(?:\.py|\.ps1|\.vbs|\.bat|\.cmd)"
    return sorted(set(re.findall(pattern, text, flags=re.IGNORECASE)))


def is_owned_script(path: Path) -> bool:
    if path.suffix.lower() not in SCRIPT_EXTENSIONS:
        return False
    lowered = {part.lower() for part in path.parts}
    return not any(part.lower() in lowered for part in EXCLUDED_PARTS)


def scan_owned_scripts() -> list[Path]:
    return [p for p in ROOT.rglob("*") if p.is_file() and is_owned_script(p)]


def header_fields(path: Path) -> dict:
    try:
        first = "\n".join(path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[:24])
    except OSError:
        first = ""
    fields = {
        "Name": bool(re.search(r"Name[:：]|脚本名称[:：]|名称[:：]", first)),
        "System": bool(re.search(r"System[:：]|所属系统[:：]", first)),
        "Purpose": bool(re.search(r"Purpose[:：]|功能描述[:：]|作用[:：]", first)),
        "Trigger": bool(re.search(r"Trigger[:：]|调用方式[:：]|触发", first)),
        "Dependencies": bool(re.search(r"Dependencies[:：]|依赖", first)),
        "Output": bool(re.search(r"Output[:：]|输出", first)),
        "Safety": bool(re.search(r"Safety[:：]|安全边界", first)),
    }
    fields["完整"] = all(fields.values())
    return fields


def check_port(port: int) -> dict:
    ok = False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            ok = True
    except OSError:
        ok = False
    return {"端口": port, "监听": ok}


def construction_gate(rule: dict) -> dict:
    required = rule.get("治理内核能力", {}).get("施工门禁器", {}).get("必须检查", [])
    checks = {
        "施工对象": "治理内核执行化总控",
        "影响系统": ["00总管", "03进化"],
        "动作层级": "流程脚本",
        "动作性质": "只读检查与状态输出",
        "真实发送": False,
        "外网写入": False,
        "交易相关": False,
        "规则进化": False,
        "回滚方案": "删除本轮新增输出文件即可回滚状态；脚本本身另由人工管理。",
        "证据路径": str(OUT),
    }
    missing = [name for name in required if name not in checks]
    blockers = []
    if checks["真实发送"] or checks["外网写入"] or checks["交易相关"] or checks["规则进化"]:
        blockers.append("触及红线动作，需要人工确认。")
    return {
        "状态": "放行" if not missing and not blockers else "阻断",
        "门禁类型": "只读施工门禁",
        "必检项": required,
        "检查值": checks,
        "缺失项": missing,
        "阻断原因": blockers,
    }


def manager_authority(rule: dict) -> dict:
    authority = rule.get("总管核心权责", {})
    required = ["定位", "权责", "四大系统关系", "裁决顺序", "红线动作", "边界"]
    missing = [name for name in required if not authority.get(name)]
    expected_order = rule.get("核心定义", {}).get("六层链条", [])
    actual_order = authority.get("裁决顺序", [])
    order_ok = bool(expected_order) and actual_order == expected_order
    if not order_ok and "裁决顺序" not in missing:
        missing.append("裁决顺序与六层链条一致性")
    return {
        "状态": "已刻入" if not missing else "需补齐",
        "缺失项": missing,
        "定位": authority.get("定位"),
        "权责项数": len(authority.get("权责", [])) if isinstance(authority.get("权责"), list) else 0,
        "四大系统关系": authority.get("四大系统关系", {}),
        "裁决顺序": actual_order,
        "红线动作": authority.get("红线动作", []),
    }


def script_entry_registry(tasks: list[dict], owned_scripts: list[Path]) -> dict:
    task_entries = []
    for task in tasks:
        paths = extract_paths_from_task(task)
        task_entries.append({
            "任务名": task.get("TaskName"),
            "状态": task.get("State"),
            "隐藏": task.get("Hidden"),
            "执行器": task.get("Execute"),
            "参数": task.get("Arguments"),
            "脚本路径": paths,
            "脚本存在": {path: Path(path).exists() for path in paths},
            "最近结果": task.get("LastTaskResult"),
        })
    by_system: dict[str, dict] = {}
    for path in owned_scripts:
        rel = path.relative_to(ROOT)
        system = rel.parts[0]
        slot = by_system.setdefault(system, {"数量": 0, "大小": 0})
        slot["数量"] += 1
        slot["大小"] += path.stat().st_size
    for value in by_system.values():
        value["大小MB"] = round(value.pop("大小") / 1024 / 1024, 3)
    return {
        "计划任务入口数": len(task_entries),
        "计划任务入口": task_entries,
        "自有脚本总数": len(owned_scripts),
        "自有脚本按系统": by_system,
    }


def rule_lineage(tasks: list[dict], extra_paths: list[Path]) -> dict:
    active_paths: set[Path] = set()
    for task in tasks:
        for text_path in extract_paths_from_task(task):
            path = Path(text_path)
            if path.exists() and is_owned_script(path):
                active_paths.add(path)
    for path in extra_paths:
        if path.exists():
            active_paths.add(path)
    records = []
    for path in sorted(active_paths, key=lambda p: str(p)):
        fields = header_fields(path)
        records.append({
            "路径": str(path),
            "完整": fields["完整"],
            "字段": fields,
        })
    missing = [item for item in records if not item["完整"]]
    return {
        "活跃入口脚本数": len(records),
        "血缘完整数": len(records) - len(missing),
        "需补齐数": len(missing),
        "需补齐样例": missing[:30],
        "记录": records,
    }


def truth_source_audit() -> dict:
    roots = [
        MANAGER / "01配置",
        MANAGER / "03数据" / "运行状态",
        MANAGER / "07文档",
        EVOLUTION / "规则库",
    ]
    files = []
    for root in roots:
        if root.exists():
            files.extend([p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".md"}])
    groups: dict[str, list[Path]] = {}
    for path in files:
        groups.setdefault(str(path.with_suffix("")), []).append(path)
    pairs = []
    needs_review = []
    for base, paths in groups.items():
        suffixes = {p.suffix.lower() for p in paths}
        if not {".json", ".md"}.issubset(suffixes):
            continue
        path_text = base
        json_path = next((p for p in paths if p.suffix.lower() == ".json"), None)
        adjudicated = False
        adjudication_note = None
        if json_path:
            try:
                payload = read_json(json_path)
                policy = payload.get("真理来源裁定") if isinstance(payload, dict) else None
                if isinstance(policy, dict) and policy.get("裁定状态") == "已裁定":
                    adjudicated = True
                    adjudication_note = policy.get("主从关系")
            except (OSError, json.JSONDecodeError):
                adjudicated = False
        if "\\03数据\\运行状态\\" in path_text:
            truth = "JSON"
            action = "Markdown如非人工面板需要，后续可停止生成或归档。"
        elif "\\07文档\\" in path_text:
            truth = "Markdown"
            action = "JSON如存在，应只作为索引或机器映射。"
        elif "\\规则库\\" in path_text:
            if adjudicated:
                truth = "已裁定"
                action = adjudication_note or "Markdown为人读规则语义真源，JSON为机器映射和执行检查投影。"
            else:
                truth = "待裁定"
                action = "规则库双格式需逐条判断：MD为人读原则，JSON为机器映射时可保留。"
        else:
            truth = "待裁定"
            action = "需按用途确认单一真理来源。"
        item = {
            "基名": base,
            "文件": [str(p) for p in paths],
            "建议真理来源": truth,
            "建议动作": action,
        }
        pairs.append(item)
        if truth == "待裁定":
            needs_review.append(item)
    return {
        "双格式组数": len(pairs),
        "待裁定组数": len(needs_review),
        "待裁定样例": needs_review[:30],
        "样例": pairs[:80],
    }


def runtime_health(tasks: list[dict]) -> dict:
    ports = [19300, 19302, 19310, 28100, 5801, 5802]
    task_names = [
        "杰哥智能化系统_股票企业微信桥接入口服务",
        "杰哥智能化系统_意图归因API服务",
        "杰哥智能化系统_报警查询API服务",
        "杰哥智能化系统_血脉分钟级只读探针",
        "杰哥智能化系统_Sparkle开机自启",
    ]
    task_index = {task.get("TaskName"): task for task in tasks}
    selected = []
    for name in task_names:
        item = task_index.get(name)
        selected.append({
            "任务名": name,
            "存在": bool(item),
            "状态": item.get("State") if item else None,
            "隐藏": item.get("Hidden") if item else None,
            "最近结果": item.get("LastTaskResult") if item else None,
        })
    return {
        "核心端口": [check_port(port) for port in ports],
        "核心计划任务": selected,
    }


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    rule = read_json(CONFIG)
    tasks = task_snapshot()
    owned_scripts = scan_owned_scripts()
    extra_lineage = [
        MANAGER / "02脚本" / "执行治理内核执行化总控.py",
        MANAGER / "02脚本" / "执行六层规则体系治理内核只读检查.py",
        MANAGER / "02脚本" / "执行真理来源裁定待办与系统能力体检.ps1",
        MANAGER / "02脚本" / "blood_probe_minutely.ps1",
    ]
    gate = construction_gate(rule)
    registry = script_entry_registry(tasks, owned_scripts)
    authority = manager_authority(rule)
    lineage = rule_lineage(tasks, extra_lineage)
    truth = truth_source_audit()
    health = runtime_health(tasks)
    status = "通过"
    warnings = []
    if gate["状态"] != "放行":
        status = "阻断"
    if authority["状态"] != "已刻入":
        warnings.append("总管核心权责仍未完整刻入治理内核规则。")
    if lineage["需补齐数"] > 0:
        warnings.append(f"仍有{lineage['需补齐数']}个活跃入口脚本标头或血缘字段需补齐。")
    if truth["待裁定组数"] > 0:
        warnings.append(f"发现{truth['待裁定组数']}组双格式真理来源需裁定。")
    if any(not item["监听"] for item in health["核心端口"] if item["端口"] in {19302, 5801, 5802}):
        warnings.append("核心端口 19302/5801/5802 存在未监听项。")
    result = {
        "名称": "治理内核执行化总控",
        "检查时间": now_text(),
        "状态": status,
        "安全边界": {
            "触发n8n": False,
            "发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
            "修改业务规则生效开关": False,
        },
        "底层入口": {
            "底层逻辑": file_status(MANAGER / "系统底层逻辑.md"),
            "通用原则": file_status(EVOLUTION / "规则库" / "搭建与施工规范_完整版.md"),
            "治理内核规则": file_status(CONFIG),
        },
        "施工门禁": gate,
        "总管核心权责": authority,
        "脚本入口注册表": registry,
        "规则血缘台账": lineage,
        "单一真理来源审计": truth,
        "当前运行能力体检": health,
        "警告": warnings,
        "下一步队列": [
            "将本总控接入开工自检，使施工前自动生成门禁状态。",
            "对规则库双格式文件逐条裁定真理来源。",
            "把总管核心权责口径继续下沉到具体子系统质量评分和施工门禁模板。",
        ],
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
