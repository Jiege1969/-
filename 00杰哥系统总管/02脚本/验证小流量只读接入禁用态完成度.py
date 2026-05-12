"""
名称：验证小流量只读接入禁用态完成度.py
作用：生成并验证小流量只读接入禁用态完成度汇总，确认六条禁用态链路全部通过。
触发方式：python 验证小流量只读接入禁用态完成度.py
依赖：Python 标准库；生成小流量只读接入禁用态完成度汇总.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证汇总；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读接入禁用态完成度验收脚本。
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
    script = manager / "02脚本" / "生成小流量只读接入禁用态完成度汇总.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    summary_path = manager / "03数据" / "真实攻坚队列" / "小流量只读接入禁用态完成度汇总_最新.json"
    summary = load_json(summary_path) if summary_path.exists() else {}
    closed = summary.get("仍然关闭", [])
    checks = [
        check("汇总生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("汇总文件存在", summary_path.exists(), str(summary_path)),
        check("禁用态链路数量完整", summary.get("汇总", {}).get("链路总数") == 6, summary.get("汇总", {})),
        check("禁用态链路全部通过", summary.get("汇总", {}).get("失败") == 0, summary.get("汇总", {})),
        check("完成度为100", summary.get("完成度百分比") == 100, summary.get("完成度百分比")),
        check("联网抓取仍关闭", any("联网抓取" in item for item in closed), closed),
        check("企业微信真实发送仍关闭", any("企业微信真实发送" in item for item in closed), closed),
        check("税收业务仍关闭", any("税收" in item for item in closed), closed),
        check("旧系统写入仍关闭", any("旧系统" in item for item in closed), closed),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "readonly-disabled-completion-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "真实攻坚队列"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"readonly-disabled-completion-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
