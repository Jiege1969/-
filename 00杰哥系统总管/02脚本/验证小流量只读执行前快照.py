"""
名称：验证小流量只读执行前快照.py
作用：生成并验证小流量只读执行前快照，确认总闸门、执行方案、旧系统保护和禁用态完成度均通过，且真实动作关闭。
触发方式：python 验证小流量只读执行前快照.py
依赖：Python 标准库；生成小流量只读执行前快照.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证快照；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读执行前快照验收脚本。
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
    script = manager / "02脚本" / "生成小流量只读执行前快照.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    snapshot_path = manager / "03数据" / "小流量只读执行" / "小流量只读执行前快照_最新.json"
    snapshot = load_json(snapshot_path) if snapshot_path.exists() else {}
    switches = snapshot.get("真实动作关闭开关", {})
    checks = [
        check("快照生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("快照文件存在", snapshot_path.exists(), str(snapshot_path)),
        check("快照检查全部通过", snapshot.get("汇总", {}).get("失败") == 0, snapshot.get("汇总", {})),
        check("真实联网关闭", switches.get("真实联网") is False, switches),
        check("正式知识库写入关闭", switches.get("正式知识库写入") is False, switches),
        check("企业微信真实发送关闭", switches.get("企业微信真实发送") is False, switches),
        check("n8n真实触发关闭", switches.get("n8n真实触发") is False, switches),
        check("税收业务关闭", switches.get("税收业务") is False, switches),
        check("旧系统写入关闭", switches.get("旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "readonly-pre-execution-snapshot-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"readonly-pre-execution-snapshot-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "readonly-pre-execution-snapshot-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
