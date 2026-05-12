"""
名称：验证办公材料本地生成门禁.py
作用：生成并验证办公材料本地生成门禁报告，确认正式文档覆盖、涉密读取、自动外发、上传、n8n触发和企业微信真实发送均关闭。
触发方式：python 验证办公材料本地生成门禁.py
依赖：Python 标准库；生成办公材料本地生成门禁报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证门禁报告；不读取涉密资料；不覆盖正式文档；不自动外发；不上传；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建办公材料本地生成门禁验收脚本。
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


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "03本职工作系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成办公材料本地生成门禁报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "04本地生成门禁" / "办公材料本地生成门禁报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("默认开关", {})
    checks = [
        check("门禁报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("门禁报告存在", report_path.exists(), str(report_path)),
        check("允许本地草稿生成", switches.get("允许生成本地草稿") is True, switches.get("允许生成本地草稿")),
        check("禁止覆盖正式文档", switches.get("允许覆盖正式文档") is False, switches.get("允许覆盖正式文档")),
        check("禁止读取涉密资料", switches.get("允许读取涉密资料") is False, switches.get("允许读取涉密资料")),
        check("禁止自动外发", switches.get("允许自动外发") is False, switches.get("允许自动外发")),
        check("禁止自动上传", switches.get("允许自动上传") is False, switches.get("允许自动上传")),
        check("禁止跳过人工确认", switches.get("允许跳过人工确认") is False, switches.get("允许跳过人工确认")),
        check("禁止触发n8n", switches.get("允许触发n8n") is False, switches.get("允许触发n8n")),
        check("禁止企业微信真实发送", switches.get("允许企业微信真实发送") is False, switches.get("允许企业微信真实发送")),
        check("存在任务计划", Path(report.get("任务计划", {}).get("路径", "")).exists(), report.get("任务计划", {})),
        check("存在草稿框架", Path(report.get("草稿框架", {}).get("路径", "")).exists(), report.get("草稿框架", {})),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "office-local-draft-gate-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "办公材料门禁"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"office-local-draft-gate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
