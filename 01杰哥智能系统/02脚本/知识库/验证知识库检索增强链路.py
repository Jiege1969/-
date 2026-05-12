# -*- coding: utf-8 -*-
"""
名称：验证知识库检索增强链路.py
作用：生成并验证知识库检索增强链路报告，确认检索增强模型可见且正式向量生成、写库、n8n触发均关闭。
触发方式：python 验证知识库检索增强链路.py
依赖：Python 标准库；生成知识库检索增强链路报告.py。
所属系统：01杰哥智能系统/知识库
安全边界：只生成和验证dry-run链路报告；不调用模型推理；不生成向量；不写正式向量库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建知识库检索增强链路验证脚本。
标识：knowledge-retrieval-enhancement-chain-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
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


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    v3 = system_root()
    script = root / "02脚本" / "知识库" / "生成知识库检索增强链路报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "知识库" / "04检索缓存" / "知识库检索增强链路报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    model_checks = report.get("模型就绪检查", {})
    switches = report.get("默认开关", {})
    checks = [
        check("检索增强链路报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("检索增强链路报告文件存在", report_path.exists(), str(report_path)),
        check("主向量模型bge-m3可见", model_checks.get("主向量模型可见") is True, model_checks),
        check("备用向量模型qwen3-embedding可见", model_checks.get("备用向量模型可见") is True, model_checks),
        check("重排序模型qwen3-reranker可见", model_checks.get("重排序模型可见") is True, model_checks),
        check("未调用模型生成向量", report.get("是否调用模型生成向量") is False, report.get("是否调用模型生成向量")),
        check("未写入正式向量库", report.get("是否写入正式向量库") is False, report.get("是否写入正式向量库")),
        check("未触发n8n", report.get("是否触发n8n") is False, report.get("是否触发n8n")),
        check("正式向量库写入关闭", switches.get("允许写入正式向量库") is False, switches),
        check("税收业务关闭", switches.get("允许税收业务") is False, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "knowledge-retrieval-enhancement-chain-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "知识库"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "knowledge-retrieval-enhancement-chain-verify-最新.json"
    latest = output
    write_json(latest, verify)
    manager_output_dir = v3 / "00杰哥系统总管" / "04日志" / "知识库验收"
    manager_output_dir.mkdir(parents=True, exist_ok=True)
    manager_output = manager_output_dir / "knowledge-retrieval-enhancement-chain-verify-最新.json"
    manager_latest = manager_output
    write_json(manager_latest, verify)
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
