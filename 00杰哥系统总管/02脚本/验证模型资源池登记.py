# -*- coding: utf-8 -*-
"""
名称：验证模型资源池登记.py
作用：生成并验证模型资源池登记报告，确认基础模型和检索增强模型角色被登记且未执行模型下载、删除或生产切换。
触发方式：python 验证模型资源池登记.py
依赖：Python 标准库；生成模型资源池登记.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证模型资源池报告；不拉取模型；不删除模型；不切换生产配置；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建模型资源池登记验证脚本；2026-04-27 纳入bge-m3、qwen3-embedding和qwen3-reranker登记验证；2026-04-27 验证Docker内Ollama可见模型。
标识：model-resource-pool-register-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成模型资源池登记.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "模型资源池" / "模型资源池登记_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    models = report.get("模型资源池", [])
    summary = report.get("汇总", {})
    safety = report.get("安全边界", {})
    checks = [
        check("模型资源池登记生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("模型资源池登记文件存在", report_path.exists(), str(report_path)),
        check("登记模型数不少于十二个", summary.get("登记模型数", 0) >= 12, summary),
        check("包含总管主脑候选", any("总管主脑" in item.get("角色", []) for item in models), models),
        check("包含股票研究模型", any("股票研究" in item.get("角色", []) for item in models), models),
        check("包含代码维护模型", any("代码维护" in item.get("角色", []) for item in models), models),
        check("包含视觉理解模型", any("视觉理解" in item.get("角色", []) for item in models), models),
        check("包含知识库向量检索模型", any("知识库向量检索" in item.get("角色", []) for item in models), models),
        check("包含检索结果重排序模型", any("检索结果重排序" in item.get("角色", []) for item in models), models),
        check("Ollama至少可见九个模型", summary.get("Ollama可见模型数", 0) >= 9, summary),
        check("bge-m3已可见", any(item.get("名称") == "bge-m3" and item.get("本机Ollama可见") is True for item in models), models),
        check("qwen3-embedding已可见", any(item.get("名称") == "qwen3-embedding:4b" and item.get("本机Ollama可见") is True for item in models), models),
        check("qwen3-reranker已可见", any(item.get("名称") == "sam860/qwen3-reranker:0.6b-Q8_0" and item.get("本机Ollama可见") is True for item in models), models),
        check("未自动拉取模型", safety.get("不自动拉取模型") is True, safety),
        check("未删除模型", safety.get("不删除模型") is True, safety),
        check("未切换生产配置", safety.get("不切换生产配置") is True, safety),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "model-resource-pool-register-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "模型资源池"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"model-resource-pool-register-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "model-resource-pool-register-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
