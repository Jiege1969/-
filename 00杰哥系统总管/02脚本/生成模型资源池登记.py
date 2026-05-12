# -*- coding: utf-8 -*-
"""
名称：生成模型资源池登记.py
作用：读取模型资源池登记规则和模型路由策略，生成模型资源池登记报告。
触发方式：python 生成模型资源池登记.py
依赖：Python 标准库；模型资源池登记规则.json；模型路由策略.json；可选ollama命令或Docker内ollama容器。
所属系统：00杰哥系统总管
安全边界：只读模型状态并生成登记报告；不拉取模型；不删除模型；不切换生产配置；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建模型资源池登记脚本；2026-04-27 增加Docker容器ollama只读查询和模型名称规范化。
标识：model-resource-pool-register
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_ollama_models() -> dict[str, Any]:
    api_status = read_ollama_models_from_api("http://127.0.0.1:29134/api/tags")
    if not api_status.get("需人工核实"):
        return api_status

    command = shutil.which("ollama")
    if not command:
        docker = shutil.which("docker")
        if not docker:
            return {"状态": "ollama命令和docker命令均不可用", "模型列表": [], "需人工核实": True}
        try:
            result = subprocess.run([docker, "exec", "jiege_v3_ollama", "ollama", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        except Exception as exc:
            return {"状态": "新系统docker内ollama查询失败", "错误": str(exc), "模型列表": [], "需人工核实": True}
        models = parse_ollama_list(result.stdout)
        return {
            "状态": "可访问" if result.returncode == 0 else "docker内ollama返回错误",
            "查询方式": "docker exec jiege_v3_ollama ollama list",
            "返回码": result.returncode,
            "模型列表": models,
            "模型数量": len(models),
            "需人工核实": result.returncode != 0,
            "错误输出": result.stderr.strip(),
        }
    try:
        result = subprocess.run([command, "list"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    except Exception as exc:
        return {"状态": "ollama查询失败", "错误": str(exc), "模型列表": [], "需人工核实": True}
    models = parse_ollama_list(result.stdout)
    return {
        "状态": "可访问" if result.returncode == 0 else "ollama返回错误",
        "查询方式": "ollama list",
        "返回码": result.returncode,
        "模型列表": models,
        "模型数量": len(models),
        "需人工核实": result.returncode != 0,
        "错误输出": result.stderr.strip(),
    }


def read_ollama_models_from_api(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"状态": "新系统Ollama API不可访问", "查询方式": url, "错误": str(exc), "模型列表": [], "需人工核实": True}
    models = [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
    return {
        "状态": "可访问",
        "查询方式": url,
        "模型列表": models,
        "模型数量": len(models),
        "需人工核实": False,
    }


def parse_ollama_list(output: str) -> list[str]:
    models: list[str] = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def normalize_model_name(name: str) -> str:
    return name[:-7] if name.endswith(":latest") else name


def flatten_strategy_models(strategy: dict[str, Any]) -> set[str]:
    models: set[str] = set()
    for values in strategy.get("模型分层", {}).values():
        for model in values:
            models.add(str(model))
    return models


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "模型资源池登记规则.json"
    strategy_path = manager / "01配置" / "模型路由策略.json"
    rules = load_json(rule_path)
    strategy = load_json(strategy_path) if strategy_path.exists() else {}
    ollama = read_ollama_models()
    expected = rules.get("预计模型清单", [])
    strategy_models = flatten_strategy_models(strategy)
    visible_models = set(ollama.get("模型列表", []))
    normalized_visible_models = {normalize_model_name(item) for item in visible_models}
    registered = []
    for item in expected:
        name = item.get("名称")
        registered.append({
            "名称": name,
            "角色": item.get("角色", []),
            "优先级": item.get("优先级"),
            "在路由策略中": name in strategy_models,
            "本机Ollama可见": name in visible_models or name in normalized_visible_models,
            "当前状态": "已可见" if name in visible_models or name in normalized_visible_models else "待核实",
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "路由策略文件": str(strategy_path),
        "Ollama只读状态": ollama,
        "模型资源池": registered,
        "汇总": {
            "登记模型数": len(registered),
            "路由策略模型数": len(strategy_models),
            "Ollama可见模型数": len(visible_models),
            "待核实模型数": sum(1 for item in registered if item.get("当前状态") == "待核实"),
            "默认主脑候选数": len(rules.get("默认主脑候选", [])),
        },
        "安全边界": rules.get("安全边界", {}),
        "当前结论": "模型资源池已登记；当前只做只读盘点，不下载、不删除、不切换生产配置。",
    }
    output_dir = manager / "03数据" / "模型资源池"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"模型资源池登记_{timestamp}.json"
    latest = output_dir / "模型资源池登记_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"登记模型数": report["汇总"]["登记模型数"], "Ollama可见模型数": report["汇总"]["Ollama可见模型数"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
