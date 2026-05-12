"""
名称：检查企业微信凭据路径模板.py
作用：检查企业微信凭据路径模板是否只包含占位变量和路径规则，不包含真实凭据值。
触发方式：python 检查企业微信凭据路径模板.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只读取模板配置；不创建真实凭据文件、不读取真实凭据、不连接企业微信。
创建/修改记录：2026-04-27 创建企业微信凭据路径模板检查脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def output_dir() -> Path:
    target = module_root() / "03数据" / "01接入检查"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    config_path = module_root() / "01配置" / "企业微信凭据路径模板.json"
    config = load_json(config_path)
    placeholders = config.get("环境变量占位", {})
    switches = config.get("当前开关", {})
    template_file = config.get("建议凭据文件", {}).get("模板文件", "")
    real_file = config.get("建议凭据文件", {}).get("真实文件", "")
    risk_keywords = [
        "corpsecret",
        "secret" + "=",
        "token" + "=",
        "encodingaeskey" + "=",
        "password" + "=",
        "真实Secret",
    ]
    raw_text = config_path.read_text(encoding="utf-8").lower()
    risks = [keyword for keyword in risk_keywords if keyword.lower() in raw_text]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "配置来源": str(config_path),
        "占位变量数量": len(placeholders),
        "占位变量": list(placeholders.keys()),
        "模板文件": template_file,
        "真实文件策略": real_file,
        "风险关键词命中": risks,
        "是否创建真实凭据文件": switches.get("是否创建真实凭据文件") is True,
        "是否读取真实凭据": switches.get("是否读取真实凭据") is True,
        "是否连接企业微信": switches.get("是否连接企业微信") is True,
        "是否通过": len(placeholders) >= 5 and not risks and all(value is False for value in switches.values()),
    }
    latest = output_dir() / "企业微信凭据路径检查_最新.json"
    output = latest
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"是否通过": report["是否通过"], "占位变量数量": report["占位变量数量"], "输出": str(output)}, ensure_ascii=True))
    return 0 if report["是否通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
