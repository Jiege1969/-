"""
名称：生成企业微信沙箱回环门禁报告.py
作用：运行企业微信凭据隔离、路径模板、只读回环和沙箱回滚演练脚本，并生成沙箱回环门禁报告。
触发方式：python 生成企业微信沙箱回环门禁报告.py
依赖：Python 标准库；企业微信沙箱回环门禁.json；检查企业微信凭据隔离.py；检查企业微信凭据路径模板.py；企业微信只读回环预演.py；生成企业微信沙盒回滚演练.py。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只生成沙箱和只读回环报告；不写入真实凭据；不真实发送企业微信；不触发Webhook；不触发n8n；不在OpenClaw写业务判断；不绕过统一消息出口。
创建/修改记录：2026-04-27 创建企业微信沙箱回环门禁报告脚本。
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
    gate = load_json(root / "01配置" / "企业微信沙箱回环门禁.json")
    runs = [
        run_script(root, "检查企业微信凭据隔离.py"),
        run_script(root, "检查企业微信凭据路径模板.py"),
        run_script(root, "企业微信只读回环预演.py"),
        run_script(root, "生成企业微信沙盒回滚演练.py"),
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "企业微信沙箱回环门禁",
        "脚本执行": runs,
        "默认开关": gate.get("默认开关", {}),
        "准入要求": gate.get("准入要求", []),
        "结论": "允许凭据隔离、路径模板、只读回环和沙箱回滚演练；禁止真实凭据写入、真实发送、Webhook触发和绕过统一消息出口。",
        "下一步": [
            "真实发送前必须由统一消息出口生成放行单",
            "OpenClaw继续只作为边缘消息代理",
            "任何企业微信真实凭据不得写入当前配置模板"
        ],
    }
    output_dir = root / "03数据" / "06沙箱回环门禁"
    latest = output_dir / "企业微信沙箱回环门禁报告_最新.json"
    output = latest
    write_json(output, report)
    write_json(latest, report)
    failed = [item for item in runs if item["退出码"] != 0]
    print(json.dumps({"执行脚本数": len(runs), "失败脚本数": len(failed), "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
