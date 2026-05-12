# -*- coding: utf-8 -*-
"""
名称：迁移企业微信本机环境到新系统.py
作用：从旧系统本机环境文件中提取企业微信相关变量，写入新系统公共组件本机环境文件，帮助断开运行时对旧系统目录的依赖。
触发方式：python 迁移企业微信本机环境到新系统.py
依赖：Python标准库；旧系统本机环境.env；新系统00公共组件/01配置目录。
所属系统：02杰哥扩展系统/00公共组件
安全边界：只读取旧环境文件；只写入新系统企业微信本机环境.env；不打印密钥值；不发送消息；不触发n8n；不写旧系统；不交易。
创建/修改记录：2026-04-30 创建企业微信本机环境迁移脚本。
标识：wecom-local-env-migrate-to-v3
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "01配置"
LOG_DIR = ROOT / "04日志" / "企业微信本机环境迁移"
OLD_ENV = Path("D:/杰哥智能体操作系统/01_系统配置/本机环境.env")
NEW_ENV = CONFIG_DIR / "企业微信本机环境.env"

ALLOWED_PREFIXES = ("WECOM_",)
REQUIRED_KEYS = [
    "WECOM_CORP_ID",
    "WECOM_AGENT_ID",
    "WECOM_APP_SECRET",
    "WECOM_DEFAULT_USER_ID",
    "WECOM_CALLBACK_TOKEN",
    "WECOM_CALLBACK_AES_KEY",
]


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if key.startswith(ALLOWED_PREFIXES):
            values[key] = value.strip().strip('"').strip("'")
    return values


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_env_text(values: dict[str, str]) -> str:
    lines = [
        "# 名称：企业微信本机环境.env",
        "# 作用：新系统企业微信桥接和受控发送的本机环境变量；禁止进入知识库；禁止在日志中输出明文。",
        "# 触发方式：由股票企业微信桥接入口.py、企业微信受控发送器.py只读加载。",
        "# 依赖：旧系统本机环境.env一次性迁移；新系统企业微信桥接入口；企业微信受控发送器。",
        "# 所属系统：02杰哥扩展系统/00公共组件",
        f"# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for key in sorted(values):
        lines.append(f"{key}={values[key]}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    values = parse_env(OLD_ENV)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if NEW_ENV.exists():
        backup = ROOT / "06临时" / f"企业微信本机环境.env.{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak"
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_text(NEW_ENV.read_text(encoding="utf-8-sig", errors="replace"), encoding="utf-8")
    else:
        backup = None
    NEW_ENV.write_text(build_env_text(values), encoding="utf-8")
    presence = {key: bool(values.get(key, "").strip()) for key in REQUIRED_KEYS}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "旧环境文件存在": OLD_ENV.exists(),
        "新环境文件": str(NEW_ENV),
        "迁移变量数量": len(values),
        "必需变量存在性": presence,
        "已备份旧新环境文件": bool(backup),
        "备份文件": str(backup) if backup else "",
        "安全边界": {
            "打印密钥值": False,
            "写旧系统": False,
            "发送企业微信": False,
            "触发n8n": False,
            "自动交易": False,
        },
    }
    output = LOG_DIR / f"wecom-local-env-migrate-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = LOG_DIR / "wecom-local-env-migrate-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"ok": all(presence.values()), "迁移变量数量": len(values), "输出": str(output)}, ensure_ascii=False))
    return 0 if all(presence.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
