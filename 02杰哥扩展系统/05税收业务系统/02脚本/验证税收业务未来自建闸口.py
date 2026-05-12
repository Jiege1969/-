# -*- coding: utf-8 -*-
"""
名称：验证税收业务未来自建闸口.py
作用：生成并验证税收业务未来自建闸口报告，确认真实税收网站、正式库、n8n和旧系统写入全部关闭。
触发方式：python 验证税收业务未来自建闸口.py
依赖：Python标准库；生成税收业务未来自建闸口报告.py；税收业务未来自建闸口规则.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只生成和验证本模块闸口报告；不联网；不调用大模型；不触发n8n；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建税收业务未来自建闸口验证脚本。
标识：tax-future-self-build-gate-verify
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


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成税收业务未来自建闸口报告.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    report_path = root / "03数据" / "09未来自建闸口" / "税收业务未来自建闸口报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("默认开关", {})
    actions = report.get("本次动作", {})
    forbidden = report.get("禁止范围", [])
    steps = report.get("未来自建步骤", [])
    checks = [
        check("闸口报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("闸口报告文件存在", report_path.exists(), str(report_path)),
        check("当前状态保持关闭", report.get("当前状态") == "真实税收业务关闭", report.get("当前状态")),
        check("真实联网关闭", switches.get("允许真实联网") is False, switches),
        check("自动登录关闭", switches.get("允许自动登录") is False, switches),
        check("验证码处理关闭", switches.get("允许验证码处理") is False, switches),
        check("绕过限制关闭", switches.get("允许绕过限制") is False, switches),
        check("真实抓取关闭", switches.get("允许真实抓取") is False, switches),
        check("n8n触发关闭", switches.get("允许触发n8n") is False, switches),
        check("真实发送关闭", switches.get("允许真实发送") is False, switches),
        check("正式库写入关闭", switches.get("允许写正式库") is False, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
        check("自动提交业务关闭", switches.get("允许自动提交业务") is False, switches),
        check("本次未联网", actions.get("是否联网") is False, actions),
        check("本次未调用大模型", actions.get("是否调用大模型") is False, actions),
        check("本次未触发n8n", actions.get("是否触发n8n") is False, actions),
        check("本次未真实发送", actions.get("是否真实发送") is False, actions),
        check("本次未写正式库", actions.get("是否写正式库") is False, actions),
        check("本次未写旧系统", actions.get("是否写旧系统") is False, actions),
        check("本次未执行网站抓取", actions.get("是否执行网站抓取") is False, actions),
        check("本次未提交涉税业务", actions.get("是否提交涉税业务") is False, actions),
        check("禁止绕过验证码", "绕过验证码" in forbidden, forbidden),
        check("禁止绕过反爬限制", "绕过反爬限制" in forbidden, forbidden),
        check("包含人工复核队列", any(item.get("名称") == "人工复核队列" for item in steps), steps),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "tax-future-self-build-gate-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "未来自建闸口"
    output = output_dir / f"tax-future-self-build-gate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    write_json(output, verify)
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
