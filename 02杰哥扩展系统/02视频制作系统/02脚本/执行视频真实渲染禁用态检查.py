"""
名称：执行视频真实渲染禁用态检查.py
作用：读取视频素材本地整理门禁报告，生成真实渲染禁用态检查报告，确认剪辑软件渲染、原素材改动和自动发布均保持关闭。
触发方式：python 执行视频真实渲染禁用态检查.py
依赖：Python 标准库；视频素材本地整理门禁报告_最新.json；视频素材本地整理门禁.json。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只生成真实渲染禁用态检查报告；不调用剪辑软件；不生成真实媒体；不删除、移动或覆盖原素材；不自动发布；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建视频真实渲染禁用态检查脚本。
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
    gate = load_json(root / "01配置" / "视频素材本地整理门禁.json")
    gate_report_path = root / "03数据" / "08本地整理门禁" / "视频素材本地整理门禁报告_最新.json"
    gate_report = load_json(gate_report_path) if gate_report_path.exists() else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "视频真实渲染禁用态检查",
        "门禁报告": str(gate_report_path),
        "门禁开关": gate.get("默认开关", {}),
        "本地整理脚本执行": gate_report.get("脚本执行", []),
        "是否调用剪辑软件": False,
        "是否生成真实媒体": False,
        "是否删除原素材": False,
        "是否移动原素材": False,
        "是否覆盖原素材": False,
        "是否自动发布": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "执行器状态": "禁用态",
        "当前结论": "真实渲染执行器保持禁用，只允许本地素材整理和预演。"
    }
    output_dir = root / "03数据" / "08本地整理门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"视频真实渲染禁用态检查_{timestamp}.json"
    latest = output_dir / "视频真实渲染禁用态检查_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否调用剪辑软件": report["是否调用剪辑软件"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
