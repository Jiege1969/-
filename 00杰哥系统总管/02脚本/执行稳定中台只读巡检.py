"""
名称：执行稳定中台只读巡检.py
作用：按稳定中台巡检规则执行只读巡检脚本，生成巡检闭环报告，并区分阻断当前主线与诊断观察项。
触发方式：python 执行稳定中台只读巡检.py
依赖：Python 标准库；稳定中台巡检规则.json；巡检项目内列出的只读脚本。
所属系统：00杰哥系统总管
安全边界：只执行登记的只读脚本并写入巡检日志；不创建计划任务；不重启服务；不触发n8n；不发送企业微信；不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台只读巡检执行脚本；2026-05-04 支持“阻断当前主线”字段，避免规划项失败误阻断股票四系统观察期。
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


def run_script(script: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return {
        "脚本": str(script),
        "退出码": result.returncode,
        "通过": result.returncode == 0,
        "标准输出": result.stdout.strip()[-1000:],
        "标准错误": result.stderr.strip()[-1000:],
    }


def main() -> int:
    root = v3_root()
    rules = load_json(root / "00杰哥系统总管" / "01配置" / "稳定中台巡检规则.json")
    results = []
    for item in rules.get("巡检项目", []):
        script = Path(item.get("脚本", ""))
        result = run_script(script)
        result["名称"] = item.get("名称")
        result["类型"] = item.get("类型")
        result["必检"] = item.get("必检") is True
        result["阻断当前主线"] = item.get("阻断当前主线") is not False
        result["说明"] = item.get("说明", "")
        results.append(result)
    required = [item for item in results if item.get("必检")]
    blocking = [item for item in required if item.get("阻断当前主线")]
    non_blocking_failed = [item for item in required if not item.get("阻断当前主线") and not item.get("通过")]
    report = {
        "巡检时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-readonly-patrol",
        "巡检结果": results,
        "汇总": {
            "项目总数": len(results),
            "必检项目": len(required),
            "阻断项目": len(blocking),
            "通过": sum(1 for item in blocking if item.get("通过")),
            "失败": sum(1 for item in blocking if not item.get("通过")),
            "非阻断失败": len(non_blocking_failed),
        },
        "非阻断失败项": non_blocking_failed,
        "执行开关": {
            "是否创建计划任务": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否恢复税收业务": False
        },
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "稳定中台"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stable-hub-readonly-patrol-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stable-hub-readonly-patrol-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"通过": report["汇总"]["通过"], "失败": report["汇总"]["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
