# -*- coding: utf-8 -*-
"""
名称：生成股票助手真实灰度前只读环境快照.py
作用：采集股票助手真实灰度前的Docker、Ollama、关键交付产物和安全边界只读快照。
触发方式：python 生成股票助手真实灰度前只读环境快照.py
依赖：Python标准库；股票助手真实灰度前只读环境快照规则.json；docker命令可选；ollama容器可选。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置、文件存在状态和只读命令输出并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不自动修复。
创建/修改记录：2026-04-28 创建股票助手真实灰度前只读环境快照脚本。
标识：stock-assistant-real-gray-readonly-environment-snapshot-generate
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_readonly_command(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "命令": " ".join(args),
            "可执行": True,
            "退出码": completed.returncode,
            "标准输出": completed.stdout.strip(),
            "标准错误": completed.stderr.strip(),
        }
    except Exception as exc:
        return {
            "命令": " ".join(args),
            "可执行": False,
            "退出码": None,
            "标准输出": "",
            "标准错误": str(exc),
        }


def parse_docker_ps(output: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"原始行": line})
    return rows


def parse_ollama_list(output: str) -> list[dict[str, str]]:
    lines = [line for line in output.splitlines() if line.strip()]
    if len(lines) <= 1:
        return []
    models: list[dict[str, str]] = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 4:
            models.append({"名称": parts[0], "ID": parts[1], "大小": parts[2], "修改时间": " ".join(parts[3:])})
        else:
            models.append({"原始行": line})
    return models


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手真实灰度前只读环境快照",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、快照结论",
        "",
        f"- 是否具备只读环境快照条件：{report['是否具备只读环境快照条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、关键产物状态",
        "",
    ]
    for item in report["关键产物状态"]:
        lines.append(f"- {item['名称']}：存在={item['存在']}，路径=`{item['路径']}`")
    lines.extend(["", "## 三、Docker容器只读快照", ""])
    for item in report["Docker容器"]:
        name = item.get("Names") or item.get("Names".lower()) or item.get("原始行", "")
        state = item.get("State") or item.get("Status") or ""
        image = item.get("Image") or ""
        lines.append(f"- {name}：{state} {image}")
    lines.extend(["", "## 四、Ollama模型只读快照", ""])
    for item in report["Ollama模型"]:
        lines.append(f"- {item.get('名称', item.get('原始行', ''))}：{item.get('大小', '')}")
    lines.extend(["", "## 五、只读命令结果", ""])
    for item in report["只读命令结果"]:
        lines.append(f"- {item['命令']}：可执行={item['可执行']}，退出码={item['退出码']}")
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手真实灰度前只读环境快照规则.json"
    rule = load_json(rule_path)
    paths = {
        "股票助手交付提交包": root / "03数据" / "54交付提交包" / "股票助手交付提交包_最新.json",
        "股票助手真实灰度执行手册草案": root / "03数据" / "55真实灰度执行手册草案" / "股票助手真实灰度执行手册草案_最新.json",
        "股票企业微信真实灰度未确认拦截包": root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json",
        "股票企业微信首轮真实灰度测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
        "股票助手独立使用说明": root / "07文档" / "股票助手独立使用说明.md",
    }
    docker_result = run_readonly_command(["docker", "ps", "--format", "{{json .}}"])
    ollama_result = run_readonly_command(["docker", "exec", "ollama", "ollama", "list"])
    product_status = [{"名称": name, "路径": str(path), "存在": path.exists()} for name, path in paths.items()]
    actions = rule.get("安全边界", {})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "快照原则": rule.get("快照原则", []),
        "关键产物状态": product_status,
        "只读命令结果": [docker_result, ollama_result],
        "Docker容器": parse_docker_ps(docker_result.get("标准输出", "")),
        "Ollama模型": parse_ollama_list(ollama_result.get("标准输出", "")),
        "是否具备只读环境快照条件": all(item["存在"] for item in product_status) and all(actions.values()),
        "当前结论": "已生成真实灰度前只读环境快照，可作为后续人工放行前的环境基线；命令失败仅记录，不自动修复。" ,
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "56真实灰度前只读环境快照"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手真实灰度前只读环境快照_{stamp}.json"
    latest_json = output_dir / "股票助手真实灰度前只读环境快照_最新.json"
    output_md = output_dir / f"股票助手真实灰度前只读环境快照_{stamp}.md"
    latest_md = output_dir / "股票助手真实灰度前只读环境快照_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备只读环境快照条件": report["是否具备只读环境快照条件"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
