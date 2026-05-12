"""
名称：验证稳定中台心跳快照.py
作用：验证稳定中台心跳快照生成、必检容器运行、关键日志通过和安全边界关闭。
触发方式：python 验证稳定中台心跳快照.py
依赖：Python 标准库；生成稳定中台心跳快照.py。
所属系统：00杰哥系统总管
安全边界：只读检查并写入验收日志；不重启服务、不触发n8n、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台心跳快照验收脚本。
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    script = root / "00杰哥系统总管" / "02脚本" / "生成稳定中台心跳快照.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest = root / "00杰哥系统总管" / "04日志" / "稳定中台" / "stable-hub-heartbeat-最新.json"
    data = load_json(latest) if latest.exists() else {}
    checks = [
        check("心跳脚本执行成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("心跳快照存在", latest.exists(), str(latest)),
        check("心跳整体通过", data.get("心跳通过") is True, data.get("异常列表", [])),
        check("必检容器全部运行", all(item.get("存在且运行") is True for item in data.get("容器状态", [])), data.get("容器状态", [])),
        check("关键日志全部通过", all(item.get("通过") is True for item in data.get("关键日志", {}).values()), data.get("关键日志", {})),
        check("安全边界全部关闭", all(value is False for value in data.get("安全边界", {}).values()), data.get("安全边界", {})),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-heartbeat-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "稳定中台"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stable-hub-heartbeat-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
