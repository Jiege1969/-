"""
名称：生成办公材料本地生成门禁报告.py
作用：运行办公材料计划脚本，并根据本地生成门禁生成办公材料使用前放行报告。
触发方式：python 生成办公材料本地生成门禁报告.py
依赖：Python 标准库；办公材料本地生成门禁.json；生成办公材料计划.py。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只生成本地计划、草稿框架和门禁报告；不读取涉密资料；不覆盖正式文档；不自动外发；不上传；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建办公材料本地生成门禁报告脚本。
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


def main() -> int:
    root = module_root()
    gate = load_json(root / "01配置" / "办公材料本地生成门禁.json")
    script = root / "02脚本" / "生成办公材料计划.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    plan_path = root / "03数据" / "02任务计划" / "办公材料计划_最新.json"
    draft_path = root / "03数据" / "03输出草稿" / "办公材料草稿框架_最新.json"
    plan = load_json(plan_path) if plan_path.exists() else {}
    draft = load_json(draft_path) if draft_path.exists() else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "办公材料本地生成门禁",
        "计划脚本执行": {"退出码": result.returncode, "输出": result.stdout.strip() or result.stderr.strip()},
        "默认开关": gate.get("默认开关", {}),
        "准入要求": gate.get("准入要求", []),
        "任务计划": {"路径": str(plan_path), "材料类型数量": len(plan.get("材料类型", []))},
        "草稿框架": {"路径": str(draft_path), "模板数量": len(draft.get("草稿模板", []))},
        "结论": "允许本地草稿生成；禁止覆盖正式文档、自动外发、自动上传和跳过人工确认。",
        "下一步": [
            "材料进入正式使用前补充真实事实依据",
            "生成结果先进入人工确认队列",
            "确认通过后再由用户人工决定是否转为正式文档"
        ],
    }
    output_dir = root / "03数据" / "04本地生成门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"办公材料本地生成门禁报告_{timestamp}.json"
    latest = output_dir / "办公材料本地生成门禁报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"退出码": result.returncode, "输出": str(output)}, ensure_ascii=False))
    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
