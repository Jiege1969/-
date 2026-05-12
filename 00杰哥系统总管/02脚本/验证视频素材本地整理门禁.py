"""
名称：验证视频素材本地整理门禁.py
作用：生成并验证视频素材本地整理门禁报告，确认删除、移动、覆盖原素材、真实渲染、自动发布、n8n触发和企业微信真实发送均关闭。
触发方式：python 验证视频素材本地整理门禁.py
依赖：Python 标准库；生成视频素材本地整理门禁报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证门禁报告；不删除原素材；不移动原素材；不覆盖原素材；不调用剪辑软件真实渲染；不自动发布；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建视频素材本地整理门禁验收脚本。
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
    return v3_root() / "02杰哥扩展系统" / "02视频制作系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成视频素材本地整理门禁报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    report_path = root / "03数据" / "08本地整理门禁" / "视频素材本地整理门禁报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("默认开关", {})
    checks = [
        check("门禁报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("门禁报告存在", report_path.exists(), str(report_path)),
        check("允许生成素材候选", switches.get("允许生成素材候选") is True, switches.get("允许生成素材候选")),
        check("允许生成分镜匹配", switches.get("允许生成分镜匹配") is True, switches.get("允许生成分镜匹配")),
        check("禁止删除原素材", switches.get("允许删除原素材") is False, switches.get("允许删除原素材")),
        check("禁止移动原素材", switches.get("允许移动原素材") is False, switches.get("允许移动原素材")),
        check("禁止覆盖原素材", switches.get("允许覆盖原素材") is False, switches.get("允许覆盖原素材")),
        check("禁止真实渲染", switches.get("允许调用剪辑软件真实渲染") is False, switches.get("允许调用剪辑软件真实渲染")),
        check("禁止自动发布", switches.get("允许自动发布") is False, switches.get("允许自动发布")),
        check("禁止触发n8n", switches.get("允许触发n8n") is False, switches.get("允许触发n8n")),
        check("禁止企业微信真实发送", switches.get("允许企业微信真实发送") is False, switches.get("允许企业微信真实发送")),
        check("脚本执行均成功", all(item.get("退出码") == 0 for item in report.get("脚本执行", [])), report.get("脚本执行", [])),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "video-local-material-gate-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "视频素材门禁"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"video-local-material-gate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "video-local-material-gate-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
