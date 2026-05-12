# -*- coding: utf-8 -*-
"""
名称：验证一键接续施工包.py
作用：验证一键接续施工包可生成、权威输出存在、无旧时间戳流水输出。
安全边界：只读接续包并写入最新验收日志，不触发n8n、不发送企业微信、不写正式库、不调用券商接口。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path("D:/杰哥智能化系统/00杰哥系统总管")
RULE_PATH = ROOT / "01配置" / "一键接续施工包规则.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"名称": name, "通过": passed, "说明": detail}


def main() -> int:
    rule = load_json(RULE_PATH)
    outputs = rule["当前权威输出"]
    script = ROOT / "02脚本" / "生成一键接续施工包.py"
    checks: list[dict[str, Any]] = [check("生成脚本存在", script.exists(), str(script))]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("生成脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))

    latest_md = Path(outputs["Markdown"])
    latest_json = Path(outputs["JSON"])
    checks.append(check("最新Markdown存在", latest_md.exists(), str(latest_md)))
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))

    text = latest_md.read_text(encoding="utf-8-sig", errors="replace") if latest_md.exists() else ""
    package = load_json(latest_json) if latest_json.exists() else {}
    required = ["当前规则", "输入依据", "安全边界", "下一步动作"]
    missing_text = [item for item in required if item not in text]
    checks.append(check("Markdown关键章节完整", not missing_text, "缺失：" + "、".join(missing_text) if missing_text else "完整"))
    checks.append(check("输入依据无缺失", package.get("缺失文件数量") == 0, str(package.get("缺失文件数量"))))
    forbidden = package.get("实际动作", {})
    checks.append(check("高风险动作未触发", all(value is False for value in forbidden.values()), json.dumps(forbidden, ensure_ascii=False)))
    checks.append(check("输出不带时间戳文件名", "_最新" in latest_md.name and "_最新" in latest_json.name, f"{latest_md.name} / {latest_json.name}"))
    checks.append(check("无替换字符", "\ufffd" not in text, "Markdown未发现替换字符"))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_md),
    }
    output = ROOT / "04日志" / "开工上下文" / "one-click-resume-package-verify-最新.json"
    write_json(output, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
