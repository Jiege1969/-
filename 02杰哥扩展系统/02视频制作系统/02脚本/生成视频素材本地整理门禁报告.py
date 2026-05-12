"""
名称：生成视频素材本地整理门禁报告.py
作用：运行视频素材候选、分镜素材匹配和主题化预演脚本，并生成本地整理门禁报告。
触发方式：python 生成视频素材本地整理门禁报告.py
依赖：Python 标准库；视频素材本地整理门禁.json；生成视频素材候选.py；生成视频分镜素材匹配.py；生成视频主题化预演.py。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只生成本地素材候选、分镜匹配和门禁报告；不删除原素材；不移动原素材；不覆盖原素材；不调用剪辑软件真实渲染；不自动发布；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建视频素材本地整理门禁报告脚本。
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
    gate = load_json(root / "01配置" / "视频素材本地整理门禁.json")
    runs = [
        run_script(root, "生成视频素材候选.py"),
        run_script(root, "生成视频分镜素材匹配.py"),
        run_script(root, "生成视频主题化预演.py"),
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "视频素材本地整理门禁",
        "脚本执行": runs,
        "默认开关": gate.get("默认开关", {}),
        "准入要求": gate.get("准入要求", []),
        "结论": "允许本地素材候选、分镜匹配和主题化预演；禁止删除原素材、真实渲染和自动发布。",
        "下一步": [
            "正式剪辑前人工确认素材来源和版权边界",
            "真实渲染前单独生成渲染放行单",
            "发布前必须人工确认平台、标题、封面和风险提示"
        ],
    }
    output_dir = root / "03数据" / "08本地整理门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"视频素材本地整理门禁报告_{timestamp}.json"
    latest = output_dir / "视频素材本地整理门禁报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    failed = [item for item in runs if item["退出码"] != 0]
    print(json.dumps({"执行脚本数": len(runs), "失败脚本数": len(failed), "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
