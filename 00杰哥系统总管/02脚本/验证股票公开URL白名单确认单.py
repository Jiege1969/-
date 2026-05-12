"""
名称：验证股票公开URL白名单确认单.py
作用：生成并验证股票公开URL白名单确认单，确认未人工确认前联网请求、券商接口、交易、旧系统写入、n8n触发和企业微信发送均关闭。
触发方式：python 验证股票公开URL白名单确认单.py
依赖：Python 标准库；生成股票公开URL白名单确认单.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证确认单；不联网；不抓取行情；不调用券商接口；不交易；不写入旧系统；不触发n8n；不发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建股票公开URL白名单确认单验收脚本。
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


def stock_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "01股票研究系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = stock_root()
    script = root / "02脚本" / "生成股票公开URL白名单确认单.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    form_path = root / "03数据" / "06公开数据探测" / "股票公开URL白名单确认单_最新.json"
    form = load_json(form_path) if form_path.exists() else {}
    switches = form.get("默认开关", {})
    checks = [
        check("确认单生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("确认单存在", form_path.exists(), str(form_path)),
        check("联网请求关闭", switches.get("允许联网请求") is False, switches.get("允许联网请求")),
        check("自动启用白名单关闭", switches.get("允许自动启用白名单") is False, switches.get("允许自动启用白名单")),
        check("Cookie关闭", switches.get("允许Cookie") is False, switches.get("允许Cookie")),
        check("登录态关闭", switches.get("允许登录态") is False, switches.get("允许登录态")),
        check("API密钥关闭", switches.get("允许API密钥") is False, switches.get("允许API密钥")),
        check("券商接口关闭", switches.get("允许券商接口") is False, switches.get("允许券商接口")),
        check("自动交易关闭", switches.get("允许自动交易") is False, switches.get("允许自动交易")),
        check("旧系统写入关闭", switches.get("允许写入旧系统") is False, switches.get("允许写入旧系统")),
        check("未确认URL不允许联网", form.get("统计", {}).get("是否允许联网请求") is False, form.get("统计", {})),
        check("确认要求包含税收阻断", any("税收" in item for item in form.get("人工确认要求", [])), form.get("人工确认要求", [])),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-url-whitelist-confirmation-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "股票公开数据探测"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stock-url-whitelist-confirmation-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-url-whitelist-confirmation-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
