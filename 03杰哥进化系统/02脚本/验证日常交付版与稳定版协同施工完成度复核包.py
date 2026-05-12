# -*- coding: utf-8 -*-
"""验证日常交付版与稳定版协同施工完成度复核包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "111日常交付版与稳定版协同施工完成度复核包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常交付版与稳定版协同施工完成度复核包验收"

PACKAGE_JSON = DATA_DIR / "日常交付版与稳定版协同施工完成度复核包_最新.json"
PACKAGE_MD = DATA_DIR / "日常交付版与稳定版协同施工完成度复核包_最新.md"
BOUNDARY_JSON = DATA_DIR / "协同施工接力边界清单_最新.json"
BOUNDARY_MD = DATA_DIR / "协同施工接力边界清单_最新.md"
LATEST_LOG = LOG_DIR / "daily-stable-coop-completion-review-verify-最新.json"

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

    boundary = read_json(BOUNDARY_JSON) if BOUNDARY_JSON.exists() else []
    sources = package.get("来源摘要", [])
    matrix = package.get("完成度矩阵", [])

    if package.get("状态") != "daily_stable_coop_completion_review_ready":
        errors.append("总包状态不是协同施工完成度复核就绪")
    for path in [PACKAGE_MD, BOUNDARY_JSON, BOUNDARY_MD]:
        if not path.exists():
            errors.append(f"输出文件不存在：{path}")

    if len(sources) < 10:
        errors.append("来源摘要少于10项")
    if [item for item in sources if item.get("存在") is not True]:
        errors.append("存在缺失来源")
    if [item for item in sources if item.get("通过") is not True]:
        errors.append("存在未通过来源")

    if len(matrix) < 3:
        errors.append("完成度矩阵少于3项")
    if [item for item in matrix if item.get("通过") is not True]:
        errors.append("存在未通过完成度项")

    if len(boundary) < 5:
        errors.append("协同施工接力边界少于5项")
    if not any("多对话框" in item.get("边界", "") for item in boundary):
        errors.append("缺少多对话框协同边界")

    conclusion = package.get("结论", {})
    if conclusion.get("pass") is not True:
        errors.append("结论pass不是True")
    if conclusion.get("日常交付版可作为完成基线") is not True:
        errors.append("日常交付版未确认完成基线")
    if conclusion.get("稳定版可作为完成基线") is not True:
        errors.append("稳定版未确认完成基线")
    if conclusion.get("允许覆盖已封存证据") is not False:
        errors.append("覆盖已封存证据未保持False")
    if conclusion.get("允许红线自动生效") is not False:
        errors.append("允许红线自动生效未保持False")

    safety = package.get("安全边界", {})
    bad_safety = [key for key in HARD_FALSE_KEYS if safety.get(key) not in (False, None)]
    if bad_safety:
        errors.append("安全边界存在非False项：" + "，".join(bad_safety))

    result = {
        "名称": "日常交付版与稳定版协同施工完成度复核包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not errors,
        "错误": errors,
        "指标": {
            "错误数": len(errors),
            "来源数量": len(sources),
            "完成度项数量": len(matrix),
            "协同边界数量": len(boundary),
            "安全边界异常数量": len(bad_safety),
        },
        "验证范围": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "边界清单JSON": str(BOUNDARY_JSON),
            "边界清单Markdown": str(BOUNDARY_MD),
            "日志": str(LATEST_LOG),
        },
    }
    write_json(LATEST_LOG, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
