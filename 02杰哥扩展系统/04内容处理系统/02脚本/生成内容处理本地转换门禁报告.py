"""
名称：生成内容处理本地转换门禁报告.py
作用：运行内容素材索引、批处理计划和转换预演脚本，并生成本地转换门禁报告。
触发方式：python 生成内容处理本地转换门禁报告.py
依赖：Python 标准库；内容处理本地转换门禁.json；生成内容素材索引.py；生成内容批处理计划.py；生成内容转换预演.py。
所属系统：02杰哥扩展系统/04内容处理系统
安全边界：只生成索引、计划、转换预演和门禁报告；不覆盖源文件；不删除源文件；不外发转换结果；不跳过格式校验；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建内容处理本地转换门禁报告脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_script(root: Path, name: str) -> dict[str, Any]:
    path = root / "02脚本" / name
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return {"脚本": str(path), "退出码": result.returncode, "输出": result.stdout.strip() or result.stderr.strip()}


def main() -> int:
    root = module_root()
    gate = load_json(root / "01配置" / "内容处理本地转换门禁.json")
    runs = [
        run_script(root, "生成内容素材索引.py"),
        run_script(root, "生成内容批处理计划.py"),
        run_script(root, "生成内容转换预演.py"),
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "内容处理本地转换门禁",
        "脚本执行": runs,
        "默认开关": gate.get("默认开关", {}),
        "准入要求": gate.get("准入要求", []),
        "结论": "允许本地索引、批处理计划和转换预演；禁止覆盖源文件、删除源文件和外发转换结果。",
        "下一步": [
            "转换前确认源文件格式和用途",
            "转换结果先进入人工确认队列",
            "正式使用前检查格式、内容完整性和敏感信息"
        ],
    }
    output_dir = root / "03数据" / "05本地转换门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"内容处理本地转换门禁报告_{timestamp}.json"
    latest = output_dir / "内容处理本地转换门禁报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    failed = [item for item in runs if item["退出码"] != 0]
    print(json.dumps({"执行脚本数": len(runs), "失败脚本数": len(failed), "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
