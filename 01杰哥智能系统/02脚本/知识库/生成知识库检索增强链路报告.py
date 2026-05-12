# -*- coding: utf-8 -*-
"""
名称：生成知识库检索增强链路报告.py
作用：读取知识库检索增强链路规则，检查Docker Ollama中检索增强模型可见性，并生成dry-run链路报告。
触发方式：python 生成知识库检索增强链路报告.py
依赖：Python 标准库；v3 Ollama 容器或本地 HTTP 接口；知识库检索增强链路规则.json。
所属系统：01杰哥智能系统/知识库
安全边界：只读取模型列表和本地知识库目录状态；不调用模型推理；不生成向量；不写正式向量库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建知识库检索增强链路报告脚本；2026-05-05 适配 v3 Ollama 容器名并增加 HTTP 只读兜底。
标识：knowledge-retrieval-enhancement-chain
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_ollama_list(output: str) -> list[str]:
    models: list[str] = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def normalize_model_name(name: str) -> str:
    return name[:-7] if name.endswith(":latest") else name


def read_ollama_models() -> dict[str, Any]:
    docker = shutil.which("docker")
    attempts: list[dict[str, Any]] = []
    if docker:
        for container_name in ["jiege_v3_ollama", "ollama"]:
            result = subprocess.run(
                [docker, "exec", container_name, "ollama", "list"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            models = parse_ollama_list(result.stdout)
            attempts.append(
                {
                    "查询方式": f"docker exec {container_name} ollama list",
                    "返回码": result.returncode,
                    "模型列表": models,
                    "错误输出": result.stderr.strip(),
                }
            )
            if result.returncode == 0:
                normalized = sorted({normalize_model_name(item) for item in models})
                return {
                    "状态": "可访问",
                    "查询方式": f"docker exec {container_name} ollama list",
                    "返回码": result.returncode,
                    "模型列表": models,
                    "规范化模型列表": normalized,
                    "模型数量": len(models),
                    "错误输出": result.stderr.strip(),
                    "尝试记录": attempts,
                }
    else:
        attempts.append({"查询方式": "docker", "返回码": None, "模型列表": [], "错误输出": "docker命令不可用"})

    try:
        with urllib.request.urlopen("http://127.0.0.1:29134/api/tags", timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [item.get("name", "") for item in data.get("models", []) if item.get("name")]
        normalized = sorted({normalize_model_name(item) for item in models})
        return {
            "状态": "可访问",
            "查询方式": "http://127.0.0.1:29134/api/tags",
            "返回码": 0,
            "模型列表": models,
            "规范化模型列表": normalized,
            "模型数量": len(models),
            "错误输出": "",
            "尝试记录": attempts,
        }
    except Exception as exc:
        attempts.append({"查询方式": "http://127.0.0.1:29134/api/tags", "返回码": None, "模型列表": [], "错误输出": str(exc)})

    return {
        "状态": "ollama只读查询失败",
        "查询方式": "v3 docker/http fallback",
        "返回码": 1,
        "模型列表": [],
        "规范化模型列表": [],
        "模型数量": 0,
        "错误输出": "所有只读查询均失败",
        "尝试记录": attempts,
    }


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def main() -> int:
    root = module_root()
    v3 = system_root()
    rule_path = root / "01配置" / "知识库检索增强链路规则.json"
    rules = load_json(rule_path)
    models = read_ollama_models()
    model_roles = rules.get("模型分工", {})
    visible = set(models.get("模型列表", [])) | set(models.get("规范化模型列表", []))
    model_checks = {
        "主向量模型可见": model_roles.get("主向量模型") in visible,
        "备用向量模型可见": model_roles.get("备用向量模型") in visible,
        "重排序模型可见": model_roles.get("重排序模型") in visible,
    }
    boundary = rules.get("路径边界", {})
    path_checks = {
        "原始文档数量": count_files(Path(boundary.get("原始文档目录", ""))),
        "清洗文本数量": count_files(Path(boundary.get("清洗文本目录", ""))),
        "索引清单数量": count_files(Path(boundary.get("索引清单目录", ""))),
        "检索缓存数量": count_files(Path(boundary.get("检索缓存目录", ""))),
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行模式": rules.get("执行模式"),
        "系统根目录": str(v3),
        "规则文件": str(rule_path),
        "模型分工": model_roles,
        "Ollama只读状态": models,
        "模型就绪检查": model_checks,
        "处理链路": rules.get("处理链路", []),
        "路径边界": boundary,
        "路径统计": path_checks,
        "默认开关": rules.get("默认开关", {}),
        "是否调用模型生成向量": False,
        "是否写入正式向量库": False,
        "是否触发n8n": False,
        "当前结论": "知识库检索增强链路dry-run报告已生成；模型已进入链路设计，正式向量生成和写库仍关闭。",
    }
    output_dir = root / "03数据" / "知识库" / "04检索缓存"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"知识库检索增强链路报告_{timestamp}.json"
    latest = output_dir / "知识库检索增强链路报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"模型就绪": model_checks, "是否写入正式向量库": False, "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
