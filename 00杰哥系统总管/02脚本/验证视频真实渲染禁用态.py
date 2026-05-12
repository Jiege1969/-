"""
名称：验证视频真实渲染禁用态.py
作用：执行并验证视频真实渲染禁用态检查，确认剪辑软件调用、真实媒体生成、原素材改动、自动发布、n8n触发和企业微信真实发送均关闭。
触发方式：python 验证视频真实渲染禁用态.py
依赖：Python 标准库；执行视频真实渲染禁用态检查.py。
所属系统：00杰哥系统总管
安全边界：只执行禁用态检查；不调用剪辑软件；不生成真实媒体；不删除、移动或覆盖原素材；不自动发布；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建视频真实渲染禁用态验收脚本。
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
    script = root / "02脚本" / "执行视频真实渲染禁用态检查.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "08本地整理门禁" / "视频真实渲染禁用态检查_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    checks = [
        check("禁用态检查生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("禁用态检查报告存在", report_path.exists(), str(report_path)),
        check("执行器为禁用态", report.get("执行器状态") == "禁用态", report.get("执行器状态")),
        check("剪辑软件调用关闭", report.get("是否调用剪辑软件") is False, report.get("是否调用剪辑软件")),
        check("真实媒体生成关闭", report.get("是否生成真实媒体") is False, report.get("是否生成真实媒体")),
        check("删除原素材关闭", report.get("是否删除原素材") is False, report.get("是否删除原素材")),
        check("移动原素材关闭", report.get("是否移动原素材") is False, report.get("是否移动原素材")),
        check("覆盖原素材关闭", report.get("是否覆盖原素材") is False, report.get("是否覆盖原素材")),
        check("自动发布关闭", report.get("是否自动发布") is False, report.get("是否自动发布")),
        check("n8n触发关闭", report.get("是否触发n8n") is False, report.get("是否触发n8n")),
        check("企业微信真实发送关闭", report.get("是否企业微信真实发送") is False, report.get("是否企业微信真实发送")),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "video-render-disabled-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "视频素材门禁"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"video-render-disabled-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "video-render-disabled-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
