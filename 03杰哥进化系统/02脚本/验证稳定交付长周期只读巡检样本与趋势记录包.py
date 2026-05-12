# -*- coding: utf-8 -*-
"""验证稳定交付长周期只读巡检样本与趋势记录包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "55稳定交付长周期只读巡检样本与趋势记录包" / "稳定交付长周期只读巡检样本与趋势记录包_最新.json"
SUMMARY_JSON = ROOT / "03数据" / "55稳定交付长周期只读巡检样本与趋势记录包" / "长周期只读巡检趋势汇总_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定交付长周期只读巡检样本与趋势记录包验收"
LATEST_LOG = LOG_DIR / "stable-delivery-long-term-patrol-trend-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    summary = read_json(SUMMARY_JSON) if SUMMARY_JSON.exists() else {}

    if asset.get("状态") != "stable_delivery_long_term_patrol_trend_candidate_ready":
        errors.append("状态必须为 stable_delivery_long_term_patrol_trend_candidate_ready")
    if len(asset.get("趋势源", [])) < 6:
        errors.append("趋势源不得少于 6 项")
    if len(asset.get("长周期达标条件", [])) < 4:
        errors.append("长周期达标条件不得少于 4 项")
    if len(asset.get("样本口径", [])) < 4:
        errors.append("样本口径不得少于 4 项")

    for item in asset.get("趋势源", []):
        for key in ["编号", "名称", "路径", "趋势指标"]:
            if not item.get(key):
                errors.append(f"趋势源缺少字段：{item.get('编号')} {key}")
        if item.get("路径") and not Path(item["路径"]).exists():
            errors.append(f"趋势源路径不存在：{item.get('编号')} {item.get('路径')}")

    if not summary:
        errors.append("长周期只读巡检趋势汇总不存在")
    else:
        if summary.get("总体状态") != "pass":
            errors.append("长周期只读巡检趋势汇总必须通过")
        if summary.get("汇总", {}).get("失败") != 0:
            errors.append("趋势汇总失败数必须为 0")
        if summary.get("自然日长周期已达标") is not False:
            errors.append("当前不得伪装为自然日长周期已达标")

    for name, path_text in asset.get("输出文件", {}).items():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{name} {path_text}")

    for flag in [
        "真实发送企业微信",
        "触发n8n",
        "接n8n",
        "接券商",
        "交易",
        "登录电子税务局",
        "接财税软件",
        "生成正式税务结论",
        "真实渲染视频",
        "自动发布视频",
        "自动转正式规则",
        "修改运行配置",
        "修改总管面板",
        "修改一键接续包",
        "重载19310",
        "重载19302",
        "请求19302业务接口",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "稳定交付长周期只读巡检样本与趋势记录包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "趋势源": len(asset.get("趋势源", [])),
            "达标条件": len(asset.get("长周期达标条件", [])),
            "样本口径": len(asset.get("样本口径", [])),
            "趋势失败": summary.get("汇总", {}).get("失败", 0),
            "自然日长周期已达标": summary.get("自然日长周期已达标"),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
