"""
名称：验证真实攻坚候选任务队列.py
作用：生成并验证真实接入攻坚候选任务队列，确认候选任务排序、税收暂停和真实动作关闭边界有效。
触发方式：python 验证真实攻坚候选任务队列.py
依赖：Python 标准库；生成真实攻坚候选任务队列.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证候选队列；不创建系统计划任务；不重启服务；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实攻坚候选任务队列验收脚本。
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
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成真实攻坚候选任务队列.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    queue_path = manager / "03数据" / "真实攻坚队列" / "真实攻坚候选任务队列_最新.json"
    queue = load_json(queue_path) if queue_path.exists() else {}
    safety = queue.get("安全边界", {})
    candidates = queue.get("候选队列", [])
    paused = queue.get("暂停任务", [])
    checks = [
        check("候选队列生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("候选队列文件存在", queue_path.exists(), str(queue_path)),
        check("候选任务数量充足", len(candidates) >= 6, len(candidates)),
        check("股票公开数据为第一优先级", candidates and candidates[0].get("名称") == "股票公开数据只读探测", candidates[0].get("名称") if candidates else None),
        check("税收任务保持暂停", any(item.get("状态") == "暂停" and "税收" in item.get("名称", "") for item in paused), paused),
        check("不创建系统计划任务", safety.get("不创建系统计划任务") is True, safety),
        check("不重启服务", safety.get("不重启服务") is True, safety),
        check("不触发n8n", safety.get("不触发n8n") is True, safety),
        check("不发送企业微信", safety.get("不发送企业微信") is True, safety),
        check("不写入旧系统", safety.get("不写入旧系统") is True, safety),
        check("候选任务全部带禁止事项", all(item.get("禁止事项") for item in candidates), [item.get("名称") for item in candidates if not item.get("禁止事项")]),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "real-assault-candidate-queue-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "真实攻坚队列"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"real-assault-candidate-queue-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
