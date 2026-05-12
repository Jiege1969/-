"""
名称：验证首批小流量批次预检总表.py
作用：生成并验证首批小流量批次预检总表，确认R01/R02/R03全部通过且真实动作未放行。
触发方式：python 验证首批小流量批次预检总表.py
依赖：Python 标准库；生成首批小流量批次预检总表.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证总表；不联网；不写库；不生成正式文档；不触发n8n；不真实发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批小流量批次预检总表验收脚本。
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
    script = manager / "02脚本" / "生成首批小流量批次预检总表.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "小流量只读执行" / "首批小流量批次预检总表_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    closed = report.get("仍然关闭", [])
    checks = [
        check("总表生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("总表存在", report_path.exists(), str(report_path)),
        check("批次数量为3", report.get("汇总", {}).get("批次总数") == 3, report.get("汇总", {})),
        check("全部批次通过", report.get("汇总", {}).get("失败") == 0, report.get("汇总", {})),
        check("真实动作未放行", report.get("是否允许真实动作") is False, report.get("是否允许真实动作")),
        check("税收仍关闭", any("税收" in item for item in closed), closed),
        check("旧系统写入仍关闭", any("旧系统" in item for item in closed), closed),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "first-readonly-batch-preflight-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"first-readonly-batch-preflight-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "first-readonly-batch-preflight-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
