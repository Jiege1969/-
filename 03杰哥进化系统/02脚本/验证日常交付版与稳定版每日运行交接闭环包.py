# -*- coding: utf-8 -*-
"""验证日常交付版与稳定版每日运行交接闭环包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "112日常交付版与稳定版每日运行交接闭环包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常交付版与稳定版每日运行交接闭环包验收"

PACKAGE_JSON = DATA_DIR / "日常交付版与稳定版每日运行交接闭环包_最新.json"
PACKAGE_MD = DATA_DIR / "日常交付版与稳定版每日运行交接闭环包_最新.md"
HANDOFF_JSON = DATA_DIR / "每日运行交接清单_最新.json"
HANDOFF_MD = DATA_DIR / "每日运行交接清单_最新.md"
COMMANDS_JSON = DATA_DIR / "每日只读入口命令清单_最新.json"
COMMANDS_MD = DATA_DIR / "每日只读入口命令清单_最新.md"
LATEST_LOG = LOG_DIR / "daily-stable-daily-handoff-loop-verify-最新.json"

HARD_FALSE_KEYS = [
    "真实发送企业微信",
    "真实触发n8n",
    "接券商",
    "交易",
    "登录电子税务局",
    "接财税软件",
    "真实渲染视频",
    "自动发布视频",
    "写正式规则",
    "自动转正式规则",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "红线解锁生效",
    "重载19310",
    "重载19302",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    if not PACKAGE_JSON.exists():
        errors.append(f"总包不存在：{PACKAGE_JSON}")
        package: dict[str, Any] = {}
    else:
        package = read_json(PACKAGE_JSON)

    handoff = read_json(HANDOFF_JSON) if HANDOFF_JSON.exists() else []
    commands = read_json(COMMANDS_JSON) if COMMANDS_JSON.exists() else []
    sources = package.get("来源摘要", [])

    if package.get("状态") != "daily_stable_daily_handoff_loop_ready":
        errors.append("总包状态不是每日运行交接闭环就绪")
    for path in [PACKAGE_MD, HANDOFF_JSON, HANDOFF_MD, COMMANDS_JSON, COMMANDS_MD]:
        if not path.exists():
            errors.append(f"输出文件不存在：{path}")

    if len(sources) < 9:
        errors.append("来源摘要少于9项")
    if [item for item in sources if item.get("存在") is not True]:
        errors.append("存在缺失来源")
    if [item for item in sources if item.get("通过") is not True]:
        errors.append("存在未通过来源")

    if len(handoff) < 8:
        errors.append("每日运行交接项少于8项")
    if [item for item in handoff if item.get("是否执行真实动作") is not False]:
        errors.append("存在会执行真实动作的交接项")

    if len(commands) < 5:
        errors.append("每日只读入口命令少于5项")
    if [item for item in commands if item.get("本包是否执行") is not False]:
        errors.append("存在本包内执行的命令")

    conclusion = package.get("结论", {})
    if conclusion.get("pass") is not True:
        errors.append("结论pass不是True")
    if conclusion.get("本包执行真实命令") is not False:
        errors.append("本包执行真实命令未保持False")
    if conclusion.get("允许红线自动生效") is not False:
        errors.append("允许红线自动生效未保持False")

    safety = package.get("安全边界", {})
    bad_safety = [key for key in HARD_FALSE_KEYS if safety.get(key) not in (False, None)]
    if bad_safety:
        errors.append("安全边界存在非False项：" + "，".join(bad_safety))

    result = {
        "名称": "日常交付版与稳定版每日运行交接闭环包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "来源数量": len(sources),
            "每日运行交接项数量": len(handoff),
            "每日只读入口命令数量": len(commands),
            "安全边界异常数量": len(bad_safety),
        },
        "验证范围": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "交接清单JSON": str(HANDOFF_JSON),
            "交接清单Markdown": str(HANDOFF_MD),
            "命令清单JSON": str(COMMANDS_JSON),
            "命令清单Markdown": str(COMMANDS_MD),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
