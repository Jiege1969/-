# -*- coding: utf-8 -*-
"""
名称：version_check.py
作用：只读检查当前软件版本、版本台账和升级治理规则，生成升级候选评估报告。
触发方式：python version_check.py
依赖：upgrade_rules.json；version_ledger.json；本机版本命令；可选公开版本接口。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/upgrade_check_latest.json|txt。
安全边界：不下载、不安装、不升级、不停止容器、不触发n8n、不发送企业微信、不写正式业务库、不调用券商接口、不自动交易。
创建/修改记录：2026-05-03 创建版本治理检查脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-version-check
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
RULES = MANAGER / "01配置" / "upgrade_rules.json"
LEDGER = MANAGER / "01配置" / "version_ledger.json"
LOG_DIR = MANAGER / "04日志" / "版本升级治理"


def run_command(args: list[str], timeout: int = 10) -> str:
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return ((completed.stdout or "") + (completed.stderr or "")).strip()
    except Exception as exc:
        return str(exc)


def run_command_first(commands: list[list[str]], timeout: int = 10) -> str:
    last = ""
    for command in commands:
        last = run_command(command, timeout=timeout)
        if "WinError 2" not in last and "系统找不到指定的文件" not in last:
            return last
    return last


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


def http_json(url: str, timeout: int = 5) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        return {"错误": str(exc)}


def first_version(text: str) -> str:
    text = text.replace("\x00", "")
    match = re.search(r"v?\d+(?:\.\d+){1,3}", text)
    return match.group(0) if match else text.strip()


def docker_containers() -> list[dict[str, str]]:
    output = run_command(["docker", "ps", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"], timeout=15)
    rows = []
    for line in output.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            rows.append({"名称": parts[0], "镜像": parts[1], "状态": parts[2], "端口": parts[3]})
    return rows


def current_versions() -> dict[str, Any]:
    nvidia = run_command(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"], timeout=10)
    models_data = http_json("http://127.0.0.1:29134/api/tags", timeout=5)
    models = []
    if isinstance(models_data, dict) and isinstance(models_data.get("models"), list):
        models = [
            {"名称": item.get("name", ""), "digest": item.get("digest", ""), "大小": item.get("size", 0)}
            for item in models_data["models"]
        ]
    return {
        "PowerShell": run_command(["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
        "Python": first_version(run_command(["python", "--version"])),
        "pip": first_version(run_command(["python", "-m", "pip", "--version"])),
        "Node.js": run_command(["node", "--version"]),
        "npm": run_command_first([["npm", "--version"], ["npm.cmd", "--version"]]),
        "Git": first_version(run_command(["git", "--version"])),
        "Docker": first_version(run_command(["docker", "--version"])),
        "Docker Compose": first_version(run_command(["docker", "compose", "version"])),
        "WSL": first_version(run_command(["wsl", "--version"])),
        "NVIDIA": nvidia,
        "核心容器": docker_containers(),
        "Ollama模型": models,
    }


def ledger_lookup(ledger: dict[str, Any]) -> dict[str, Any]:
    host = ledger.get("宿主环境", {}) if isinstance(ledger, dict) else {}
    containers = {item.get("名称"): item for item in ledger.get("核心容器", []) if isinstance(item, dict)}
    models = {item.get("名称"): item for item in ledger.get("模型文件", []) if isinstance(item, dict)}
    return {"宿主环境": host, "核心容器": containers, "模型文件": models}


def assess(current: dict[str, Any], rules: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    lookup = ledger_lookup(ledger)
    findings: list[dict[str, Any]] = []

    for name in ["Python", "Node.js", "npm", "Docker", "Docker Compose", "WSL"]:
        current_value = str(current.get(name, ""))
        ledger_value = str(lookup["宿主环境"].get(name, ""))
        findings.append({
            "对象": name,
            "层级": "L3语言运行时" if name in {"Python", "Node.js", "npm"} else "L4系统底座",
            "当前": current_value,
            "台账": ledger_value,
            "状态": "一致" if ledger_value and current_value.startswith(ledger_value) else ("未登记" if not ledger_value else "需复核"),
            "建议": "不改全局环境；需要升级时先建项目本地环境。" if name in {"Python", "Node.js", "npm"} else "单独窗口；不得与其他层同时升级。",
        })

    ledger_containers = lookup["核心容器"]
    for item in current.get("核心容器", []):
        name = item.get("名称", "")
        ledger_item = ledger_containers.get(name, {})
        ledger_image = ledger_item.get("镜像", "")
        image = item.get("镜像", "")
        findings.append({
            "对象": name,
            "层级": "L2核心服务",
            "当前": image,
            "台账": ledger_image,
            "状态": "一致" if image == ledger_image else ("未登记" if not ledger_image else "需复核"),
            "建议": "禁止直接升级正式容器；先影子容器或并存端口验证。",
        })
        if image.endswith(":latest"):
            findings.append({
                "对象": name,
                "层级": "L2核心服务",
                "当前": image,
                "台账": ledger_image,
                "状态": "违反铁律",
                "建议": "正式链路禁止latest标签，需改为固定版本并验收。",
            })

    ledger_models = lookup["模型文件"]
    for model in current.get("Ollama模型", []):
        name = model.get("名称", "")
        ledger_item = ledger_models.get(name, {})
        status = "一致" if ledger_item and model.get("digest") == ledger_item.get("digest") else ("未登记" if not ledger_item else "需复核")
        suggestion = "新旧并存，路由灰度，旧模型保留。"
        if name.endswith(":latest"):
            status = "需治理"
            suggestion = "模型可暂用，但正式路由应优先绑定固定digest或明确版本，避免latest漂移。"
        findings.append({
            "对象": name,
            "层级": "L1模型文件",
            "当前": model.get("digest", ""),
            "台账": ledger_item.get("digest", ""),
            "状态": status,
            "建议": suggestion,
        })

    rules_ok = bool(rules.get("升级铁律")) and rules.get("升级前置条件", {}).get("require_manual_confirmation_for_formal_switch") is True
    findings.append({
        "对象": "升级治理规则",
        "层级": "总管规则",
        "当前": "已读取" if rules else "缺失",
        "台账": str(RULES),
        "状态": "通过" if rules_ok else "需修复",
        "建议": "正式升级必须人工确认；version_check只读评估。",
    })
    return findings


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 版本升级候选评估报告 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 总结论：{report['总结论']}",
        f"- 发现数量：{len(report['发现'])}",
        f"- 需要复核：{report['需复核数量']}",
        f"- 违反铁律：{report['违反铁律数量']}",
        "",
        "## 二、发现",
        "",
        "| 层级 | 对象 | 状态 | 当前 | 台账 | 建议 |",
        "|---|---|---|---|---|---|",
    ]
    for item in report["发现"]:
        lines.append(f"| {item['层级']} | {item['对象']} | {item['状态']} | {item['当前']} | {item['台账']} | {item['建议']} |")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本报告只读检查版本和台账。",
        "- 不下载、不安装、不升级、不停止容器。",
        "- 不触发 n8n，不发送企业微信。",
        "- 不写正式业务库，不调用券商接口，不自动交易。",
        "- 正式升级必须另走影子试验、备份、回滚、验收和人工确认。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    rules = load_json(RULES, {})
    ledger = load_json(LEDGER, {})
    current = current_versions()
    findings = assess(current, rules, ledger)
    need_review = [item for item in findings if item["状态"] in {"需复核", "未登记", "需治理"}]
    violations = [item for item in findings if item["状态"] == "违反铁律"]
    report = {
        "名称": "版本升级候选评估报告",
        "版本": "V1.0",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "version_check.py",
        "总结论": "通过：仅需维护台账，无正式升级动作" if not violations else "阻断：存在违反升级铁律项",
        "当前版本": current,
        "发现": findings,
        "需复核数量": len(need_review),
        "违反铁律数量": len(violations),
        "建议动作": [
            "本轮不执行任何正式升级。",
            "对未登记模型或latest模型做台账治理，不等于立即删除或替换。",
            "Python/Node保持全局不动，后续如需治理优先建立项目本地运行时。",
            "n8n样板升级流程下一步只做影子试验方案，不挂正式数据目录。",
        ],
        "安全边界": {
            "下载": False,
            "安装": False,
            "升级正式环境": False,
            "停止容器": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式业务库": False,
            "券商接口": False,
            "自动交易": False,
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    latest_json = LOG_DIR / "upgrade_check_latest.json"
    latest_md = LOG_DIR / "upgrade_check_latest.md"
    latest_txt = LOG_DIR / "upgrade_check_latest.txt"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    write_text(latest_txt, markdown)
    print(json.dumps({
        "状态": report["总结论"],
        "需复核数量": report["需复核数量"],
        "违反铁律数量": report["违反铁律数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
