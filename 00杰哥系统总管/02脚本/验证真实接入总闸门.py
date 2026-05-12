"""
名称：验证真实接入总闸门.py
作用：执行真实接入总闸门报告生成并验证硬性关闭开关、旧系统保护、税收暂停和稳定中台准入状态。
触发方式：python 验证真实接入总闸门.py
依赖：Python 标准库；生成真实接入总闸门报告.py。
所属系统：00杰哥系统总管
安全边界：只读验证并写入验收日志；不抓取真实业务；不启用Webhook；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实接入总闸门验证脚本。
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
    script = manager / "02脚本" / "生成真实接入总闸门报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    report_path = manager / "03数据" / "真实接入闸门" / "真实接入总闸门_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("硬性关闭开关", {})
    checks = [
        check("真实接入总闸门报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("真实接入总闸门报告存在", report_path.exists(), str(report_path)),
        check("门禁检查全部通过", report.get("汇总", {}).get("失败") == 0, report.get("汇总", {})),
        check("真实抓取保持关闭", switches.get("允许真实抓取") is False, switches.get("允许真实抓取")),
        check("Webhook保持关闭", switches.get("允许Webhook自动触发") is False, switches.get("允许Webhook自动触发")),
        check("企业微信真实发送保持关闭", switches.get("允许企业微信真实发送") is False, switches.get("允许企业微信真实发送")),
        check("税收业务保持暂停", switches.get("允许税收业务接入") is False, switches.get("允许税收业务接入")),
        check("旧系统禁止写入和迁移", switches.get("允许旧系统写入") is False and switches.get("允许删除或迁移旧系统文件") is False, {"允许旧系统写入": switches.get("允许旧系统写入"), "允许删除或迁移旧系统文件": switches.get("允许删除或迁移旧系统文件")}),
        check("当前结论未放行真实接入", "保持关闭" in report.get("总闸门结论", ""), report.get("总闸门结论")),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "real-access-master-gate-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "真实接入闸门"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"real-access-master-gate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
