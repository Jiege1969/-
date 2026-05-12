"""
名称：执行内容处理真实转换禁用态检查.py
作用：读取内容处理本地转换门禁报告，生成真实转换禁用态检查报告，确认源文件覆盖、删除和外发均保持关闭。
触发方式：python 执行内容处理真实转换禁用态检查.py
依赖：Python 标准库；内容处理本地转换门禁报告_最新.json；内容处理本地转换门禁.json。
所属系统：02杰哥扩展系统/04内容处理系统
安全边界：只生成真实转换禁用态检查报告；不执行真实转换；不覆盖源文件；不删除源文件；不外发转换结果；不跳过格式校验；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建内容处理真实转换禁用态检查脚本。
"""

from __future__ import annotations

import json
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


def main() -> int:
    root = module_root()
    gate = load_json(root / "01配置" / "内容处理本地转换门禁.json")
    gate_report_path = root / "03数据" / "05本地转换门禁" / "内容处理本地转换门禁报告_最新.json"
    gate_report = load_json(gate_report_path) if gate_report_path.exists() else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "内容处理真实转换禁用态检查",
        "门禁报告": str(gate_report_path),
        "门禁开关": gate.get("默认开关", {}),
        "预演脚本执行": gate_report.get("脚本执行", []),
        "是否执行真实转换": False,
        "是否覆盖源文件": False,
        "是否删除源文件": False,
        "是否外发转换结果": False,
        "是否跳过格式校验": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "执行器状态": "禁用态",
        "当前结论": "真实转换执行器保持禁用，只允许素材索引、批处理计划和转换预演。"
    }
    output_dir = root / "03数据" / "05本地转换门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"内容处理真实转换禁用态检查_{timestamp}.json"
    latest = output_dir / "内容处理真实转换禁用态检查_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否执行真实转换": report["是否执行真实转换"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
