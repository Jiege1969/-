# -*- coding: utf-8 -*-
"""
名称：生成股票系统模型健康检查.py
作用：检查股票系统模型路由所需的本地Ollama服务和模型是否可用。
触发方式：python 生成股票系统模型健康检查.py
依赖：L5AI分析报告规则.json；本地Ollama /api/tags。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读配置；只访问本地Ollama标签接口；只写03数据/148模型健康检查；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-system-model-health-check
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def query_ollama_models(ollama_url: str, timeout: int = 8) -> tuple[bool, list[str], int | None, str | None]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(f"{ollama_url.rstrip('/')}/api/tags", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        elapsed = int((time.perf_counter() - started) * 1000)
        names = [item.get("name") for item in payload.get("models", []) if item.get("name")]
        return True, sorted(names), elapsed, None
    except Exception as exc:  # noqa: BLE001
        elapsed = int((time.perf_counter() - started) * 1000)
        return False, [], elapsed, str(exc)


def model_row(name: str, models: set[str], role: str, required: bool) -> dict[str, Any]:
    return {
        "模型": name,
        "角色": role,
        "是否必需": required,
        "是否可用": name in models,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统模型健康检查 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- Ollama地址：`{report['ollama_url']}`",
        f"- Ollama可用：{report['ollama可用']}",
        f"- 标签接口耗时：{report['标签接口耗时_ms']} ms",
        f"- 模型总数：{report['模型总数']}",
        f"- 健康结论：{report['健康结论']}",
        "",
        "## 二、主流程模型",
        "",
        "| 模型 | 角色 | 必需 | 可用 |",
        "|---|---|---:|---:|",
    ]
    for item in report["主流程模型"]:
        lines.append(f"| {item['模型']} | {item['角色']} | {item['是否必需']} | {item['是否可用']} |")
    lines.extend([
        "",
        "## 三、专业与后续模型",
        "",
        "| 模型 | 角色 | 必需 | 可用 |",
        "|---|---|---:|---:|",
    ])
    for item in report["专业与后续模型"]:
        lines.append(f"| {item['模型']} | {item['角色']} | {item['是否必需']} | {item['是否可用']} |")
    lines.extend([
        "",
        "## 四、缺失模型",
        "",
    ])
    if report["缺失模型"]:
        for item in report["缺失模型"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 五、全部可见模型",
        "",
    ])
    for name in report["全部模型"]:
        lines.append(f"- {name}")
    lines.extend([
        "",
        "## 六、安全边界",
        "",
        "- 只访问本地Ollama标签接口。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, target: Path) -> Path:
    entry_dir = root / "05入口工具"
    bat = entry_dir / "股票系统模型健康检查_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    rule_path = root / "01配置" / "L5AI分析报告规则.json"
    rule = load_json(rule_path, {})
    routing = rule.get("模型路由") or {}
    ollama_url = routing.get("ollama_url", "http://127.0.0.1:29134")
    ok, model_names, latency_ms, error = query_ollama_models(ollama_url)
    model_set = set(model_names)

    default_model = routing.get("默认分析模型", "qwen3:14b")
    complex_model = routing.get("复杂推理模型", "deepseek-r1:32b")
    fallback_model = routing.get("快速兜底模型", "qwen2.5:7b")

    main_models = [
        model_row(default_model, model_set, "L5默认分析模型", True),
        model_row(complex_model, model_set, "复杂风险复核模型", True),
        model_row(fallback_model, model_set, "快速兜底模型", True),
    ]
    optional_specs = [
        ("mychen76/Fin-R1:Q5", "金融专项复核", False),
        ("martain7r/finance-llama-8b:q4_k_m", "金融观点交叉对照", False),
        ("qwen3-embedding:4b", "相似案例向量化", False),
        ("bge-m3:latest", "备用向量模型", False),
        ("sam860/qwen3-reranker:0.6b-Q8_0", "证据重排序", False),
        ("qwen3:30b", "高质量二次总结", False),
        ("gemma3:27b", "长文本公告/研报对照", False),
        ("glm4:latest", "中文通用对照", False),
        ("deepseek-r1:7b", "快速推理备用", False),
        ("qwen3-coder:30b", "开发维护专用", False),
        ("tinyllama:latest", "连通性轻量测试", False),
    ]
    optional_models = [model_row(name, model_set, role, required) for name, role, required in optional_specs]
    missing_required = [item["模型"] for item in main_models if not item["是否可用"]]
    missing_optional = [item["模型"] for item in optional_models if item["是否必需"] and not item["是否可用"]]
    missing = missing_required + missing_optional
    if not ok:
        conclusion = "红灯：Ollama不可用"
    elif missing_required:
        conclusion = "红灯：主流程必需模型缺失"
    else:
        conclusion = "绿灯：主流程模型可用"

    report = {
        "名称": "股票系统模型健康检查",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统模型健康检查.py",
        "规则文件": str(rule_path),
        "ollama_url": ollama_url,
        "ollama可用": ok,
        "标签接口耗时_ms": latency_ms,
        "错误信息": error,
        "模型总数": len(model_names),
        "健康结论": conclusion,
        "主流程模型": main_models,
        "专业与后续模型": optional_models,
        "缺失模型": missing,
        "全部模型": model_names,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "148模型健康检查"
    output_json = output_dir / f"股票系统模型健康检查_{stamp}.json"
    output_md = output_dir / f"股票系统模型健康检查_{stamp}.md"
    latest_json = output_dir / "股票系统模型健康检查_最新.json"
    latest_md = output_dir / "股票系统模型健康检查_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    entry_bat = write_entry_open_bat(root, latest_md)

    print(json.dumps({
        "状态": "完成",
        "健康结论": conclusion,
        "模型总数": len(model_names),
        "报告": str(latest_md),
        "入口工具": str(entry_bat),
    }, ensure_ascii=False))
    return 0 if ok and not missing_required else 1


if __name__ == "__main__":
    raise SystemExit(main())
