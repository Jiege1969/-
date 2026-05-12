# -*- coding: utf-8 -*-
"""验证稳定候选补强与三日巡检启动包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "稳定候选补强与三日巡检启动包_最新.json"
RECORD_JSON = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日巡检当日样本记录_最新.json"
LEDGER_JSON = ROOT / "03数据" / "59稳定候选补强与三日巡检启动包" / "三日只读巡检样本台账_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定候选补强与三日巡检启动包验收"
LATEST_LOG = LOG_DIR / "stable-candidate-hardening-three-day-patrol-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    record = read_json(RECORD_JSON) if RECORD_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {}

    if asset.get("状态") != "stable_candidate_hardening_three_day_patrol_start_ready":
        errors.append("状态必须为 stable_candidate_hardening_three_day_patrol_start_ready")
    if len(asset.get("三日巡检源", [])) < 4:
        errors.append("三日巡检源不得少于 4 项")
    if len(asset.get("三日计数规则", [])) < 4:
        errors.append("三日计数规则不得少于 4 项")
    if len(asset.get("补强说明", [])) < 4:
        errors.append("补强说明不得少于 4 项")

    if not record:
        errors.append("三日巡检当日样本记录不存在")
    else:
        if record.get("当日状态") != "pass":
            errors.append("当日样本必须通过")
        if record.get("三日达标") is not False:
            errors.append("首日不得伪装为三日达标")
        failed = sum(1 for item in record.get("巡检结果", []) if item.get("当前结果") != "pass")
        if failed:
            errors.append(f"当日巡检源存在失败：{failed}")

    samples = ledger.get("自然日样本", [])
    if len(samples) < 1:
        errors.append("三日样本台账至少应有 1 个自然日样本")
    if ledger.get("三日达标") is not False:
        errors.append("当前三日样本台账不得标记达标")

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
        "创建外部定时任务",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "稳定候选补强与三日巡检启动包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "三日巡检源": len(asset.get("三日巡检源", [])),
            "已记录自然日数": len(samples),
            "三日达标": ledger.get("三日达标"),
            "当日状态": record.get("当日状态"),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
