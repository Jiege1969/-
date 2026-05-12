# -*- coding: utf-8 -*-
"""执行三业务反馈样本闭环只读核对。

只读取模板包并写入核对报告；不自动吸收、不转正式规则、不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
OUTPUT_DIR = ROOT / "03数据" / "71三业务用户反馈样本闭环模板包"
ASSET_JSON = OUTPUT_DIR / "三业务用户反馈样本闭环模板包_最新.json"
CHECK_JSON = OUTPUT_DIR / "三业务反馈样本闭环只读核对_最新.json"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_FIELDS = {
    "输入原文",
    "系统输出摘要",
    "用户判定",
    "问题类型",
    "是否触红线",
    "建议候选",
    "是否可自动吸收",
    "需总管确认",
}
FORBIDDEN_ALLOWED_FLAGS = {
    "自动转正式规则",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "真实发送企业微信",
    "触发n8n",
    "接券商或交易",
    "登录税局或接财税软件",
    "真实渲染或发布视频",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_template(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(item))
    if missing:
        errors.append(f"{item.get('模板编号', 'UNKNOWN')} 缺少字段：{', '.join(missing)}")
    if item.get("是否可自动吸收") is not False:
        errors.append(f"{item.get('模板编号', 'UNKNOWN')} 是否可自动吸收必须为 false")
    if item.get("需总管确认") is not True:
        errors.append(f"{item.get('模板编号', 'UNKNOWN')} 需总管确认必须为 true")
    if not isinstance(item.get("问题类型"), list) or not item.get("问题类型"):
        errors.append(f"{item.get('模板编号', 'UNKNOWN')} 问题类型必须为非空列表")
    return errors


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}

    if not asset:
        errors.append(f"模板包不存在或为空：{ASSET_JSON}")
    if asset.get("状态") != "three_business_feedback_loop_template_ready":
        errors.append("状态必须为 three_business_feedback_loop_template_ready")

    templates = asset.get("模板列表", [])
    businesses = {item.get("业务") for item in templates}
    missing_businesses = sorted(REQUIRED_BUSINESSES - businesses)
    if missing_businesses:
        errors.append(f"三业务覆盖不完整，缺少：{', '.join(missing_businesses)}")
    if len(templates) < 3:
        errors.append("模板列表不得少于 3 项")

    declared_fields = set(asset.get("必填字段", []))
    missing_declared_fields = sorted(REQUIRED_FIELDS - declared_fields)
    if missing_declared_fields:
        errors.append(f"总包必填字段声明缺少：{', '.join(missing_declared_fields)}")

    for item in templates:
        errors.extend(check_template(item))

    safety_boundary = asset.get("安全边界", {})
    for flag in sorted(FORBIDDEN_ALLOWED_FLAGS):
        if safety_boundary.get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "三业务反馈样本闭环只读核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "fail",
        "只读核对": True,
        "不自动吸收": all(item.get("是否可自动吸收") is False for item in templates),
        "不转正式规则": safety_boundary.get("自动转正式规则") is False,
        "覆盖业务": sorted(businesses),
        "汇总": {
            "模板数": len(templates),
            "通过": 0 if errors else len(templates),
            "失败": len(errors),
        },
        "错误": errors,
        "来源文件": str(ASSET_JSON),
    }
    write_target = CHECK_JSON
    write_target.parent.mkdir(parents=True, exist_ok=True)
    write_target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
