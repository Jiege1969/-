# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-target-isolation-package.py
Purpose: Build a readonly n8n target selection and isolation report before stock assistant inactive import.
Trigger: python 生成股票助手n8n目标实例选择与隔离核验包.py
Dependencies: Python standard library, Docker CLI readonly queries, stock n8n target isolation rule JSON.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Readonly Docker inspection and local config reads only; writes reports only under the new stock module data directory; does not import, enable, trigger, restart, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created the first readonly n8n target isolation package generator.
Marker: stock-assistant-n8n-target-isolation-package-generate
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_readonly_docker(args: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["docker", *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception as exc:
        return False, str(exc)
    return completed.returncode == 0, completed.stdout if completed.returncode == 0 else completed.stderr


def inspect_n8n_candidates() -> tuple[bool, str, list[dict[str, Any]]]:
    ok, output = run_readonly_docker(["ps", "--format", "{{.ID}}"])
    if not ok:
        return False, output, []
    ids = [line.strip() for line in output.splitlines() if line.strip()]
    if not ids:
        return True, "", []

    ok, inspect_output = run_readonly_docker(["inspect", *ids])
    if not ok:
        return False, inspect_output, []

    containers = json.loads(inspect_output)
    candidates: list[dict[str, Any]] = []
    for item in containers:
        name = str(item.get("Name", "")).lstrip("/")
        config = item.get("Config", {}) or {}
        image = str(config.get("Image", ""))
        labels = config.get("Labels", {}) or {}
        network = item.get("NetworkSettings", {}) or {}
        ports = network.get("Ports", {}) or {}
        mounts = item.get("Mounts", []) or []
        text_blob = json.dumps(
            {"name": name, "image": image, "labels": labels, "ports": ports, "mounts": mounts},
            ensure_ascii=False,
        ).lower()
        if "n8n" not in text_blob and "5678" not in text_blob:
            continue
        candidates.append(
            {
                "容器名": name,
                "镜像": image,
                "状态": item.get("State", {}).get("Status", ""),
                "端口": ports,
                "标签": labels,
                "挂载": [
                    {
                        "源": mount.get("Source", ""),
                        "目标": mount.get("Destination", ""),
                        "类型": mount.get("Type", ""),
                    }
                    for mount in mounts
                ],
            }
        )
    return True, "", candidates


def normalize_blob(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("\\", "/").lower()


def classify_candidate(candidate: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    blob = normalize_blob(candidate)
    old_paths = [path.replace("\\", "/").lower() for path in rule.get("旧系统保护路径", [])]
    old_identity = rule.get("旧系统n8n识别", {})
    old_names = [str(item).lower() for item in old_identity.get("容器名", [])]
    old_ports = [str(item) for item in old_identity.get("本地端口", [])]
    expected = rule.get("预期新系统n8n", {})
    new_root = str(rule.get("新系统根路径", "")).replace("\\", "/").lower()
    expected_name = str(expected.get("容器名", "jiege_v3_n8n")).lower()
    expected_port = str(expected.get("本地端口", "28679"))
    expected_keywords = [str(item).replace("\\", "/").lower() for item in expected.get("数据目录关键词", [])]
    name = str(candidate.get("容器名", "")).lower()

    old_hit = [path for path in old_paths if path and path in blob]
    old_name_hit = name in old_names
    old_port_hit = any(port and port in blob for port in old_ports)
    has_expected_name = name == expected_name
    has_expected_port = expected_port in blob
    has_new_root = new_root in blob or "杰哥智能化系统".lower() in blob
    has_data_keywords = all(keyword in blob for keyword in expected_keywords if keyword)

    if old_hit or old_name_hit or old_port_hit:
        result = "旧系统保护实例"
        can_import = False
        reason = "容器标签、挂载路径、容器名或端口命中旧系统保护规则，必须保持旧系统正常使用，禁止作为股票系统导入目标。"
    elif has_expected_name and has_expected_port and has_new_root and has_data_keywords:
        result = "新系统隔离候选实例"
        can_import = True
        reason = "容器名、端口和数据路径均匹配新系统隔离n8n目标，可进入未激活导入前最后核验。"
    else:
        result = "非新系统或目标不明确实例"
        can_import = False
        reason = "该n8n候选未同时满足新系统容器名、端口和数据路径要求，禁止自动导入。"

    return {
        "容器名": candidate.get("容器名", ""),
        "镜像": candidate.get("镜像", ""),
        "判定": result,
        "可作为导入目标": can_import,
        "原因": reason,
        "端口": candidate.get("端口", {}),
        "挂载": candidate.get("挂载", []),
    }


def summarize_compose(compose_text: str) -> dict[str, Any]:
    return {
        "存在docker-compose.v3草案": bool(compose_text.strip()),
        "包含jiege_v3_n8n": "jiege_v3_n8n" in compose_text,
        "包含28679端口": "28679" in compose_text,
        "包含n8n数据目录": "03数据/n8n" in compose_text or "03数据\\n8n" in compose_text,
        "草案提示": "该文件仅作为隔离目标设计依据；未运行的新系统n8n不能被跳过，不能转向旧系统导入。"
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手n8n目标实例选择与隔离核验包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备安全导入目标：{report['是否具备安全导入目标']}",
        f"- 选定目标：{report['选定目标'] or '无'}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、候选实例判定",
        "",
    ]
    for item in report["候选实例判定"]:
        lines.extend(
            [
                f"### {item['容器名'] or '未命名容器'}",
                f"- 镜像：{item['镜像']}",
                f"- 判定：{item['判定']}",
                f"- 可作为导入目标：{item['可作为导入目标']}",
                f"- 原因：{item['原因']}",
                "",
            ]
        )
    lines.extend(["## 三、预期新系统目标", ""])
    for key, value in report["预期新系统目标"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、仍禁止事项", ""])
    for key, value in report["禁止动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    rule_path = root / "01配置" / "股票助手n8n目标实例选择与隔离规则.json"
    rule = load_json(rule_path)
    compose_path = v3_root / "01杰哥智能系统" / "01配置" / "docker-compose.v3草案.yml"
    contract_path = v3_root / "01杰哥智能系统" / "01配置" / "n8n接口契约.json"
    compose_text = read_text(compose_path)
    contract = load_json(contract_path)

    docker_ok, docker_error, candidates = inspect_n8n_candidates()
    classified = [classify_candidate(candidate, rule) for candidate in candidates]
    safe_targets = [item for item in classified if item["可作为导入目标"]]
    selected = safe_targets[0]["容器名"] if len(safe_targets) == 1 else ""
    safe = len(safe_targets) == 1
    if safe:
        conclusion = "已发现唯一新系统隔离n8n候选目标；仍只允许进入未激活导入前最后核验，不允许启用或触发工作流。"
    else:
        conclusion = "暂不具备安全导入目标；旧系统n8n和非新系统n8n均不得作为导入目标，下一步应先处理新系统隔离n8n目标。"

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "Docker只读查询成功": docker_ok,
        "Docker只读查询错误": docker_error,
        "候选实例数量": len(classified),
        "候选实例判定": classified,
        "预期新系统目标": {
            "容器名": rule.get("预期新系统n8n", {}).get("容器名", "jiege_v3_n8n"),
            "本地端口": rule.get("预期新系统n8n", {}).get("本地端口", "28679"),
            "compose草案": str(compose_path),
            "compose草案摘要": summarize_compose(compose_text),
            "n8n接口契约": str(contract_path),
            "n8n接口契约接管状态": contract.get("接管状态", "未读取到"),
            "n8n接口契约允许真实执行": contract.get("允许真实执行", "未读取到"),
        },
        "是否具备安全导入目标": safe,
        "选定目标": selected,
        "当前结论": conclusion,
        "后续动作建议": [
            "未发现安全新系统目标时，不执行n8n导入；先生成新系统隔离n8n实施申请或明确目标复用规则。",
            "发现唯一安全目标时，只允许导入active=false的工作流，仍禁止启用、触发、发送、写正式库和交易接口。",
            "旧系统D:\\杰哥智能体操作系统保持正常使用，股票新系统不得写入旧系统目录。"
        ],
        "禁止动作": rule.get("禁止动作", {}),
        "实际动作": {
            "读取Docker容器状态": docker_ok,
            "读取新系统配置草案": True,
            "写入新系统股票核验报告": True,
            "导入n8n": False,
            "启用n8n": False,
            "触发n8n": False,
            "重启服务": False,
            "写旧系统": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }

    output_dir = root / "03数据" / "66n8n目标实例选择与隔离核验"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n目标实例选择与隔离核验包_{stamp}.json"
    latest_json = output_dir / "股票助手n8n目标实例选择与隔离核验包_最新.json"
    output_md = output_dir / f"股票助手n8n目标实例选择与隔离核验包_{stamp}.md"
    latest_md = output_dir / "股票助手n8n目标实例选择与隔离核验包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备安全导入目标": safe, "选定目标": selected, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
