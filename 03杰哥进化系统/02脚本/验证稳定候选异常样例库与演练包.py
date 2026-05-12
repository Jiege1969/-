# -*- coding: utf-8 -*-
"""验证稳定候选异常样例库与演练包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "60稳定候选异常样例库与演练包" / "稳定候选异常样例库与演练包_最新.json"
DRILL_JSON = ROOT / "03数据" / "60稳定候选异常样例库与演练包" / "稳定候选异常样例只读演练_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定候选异常样例库与演练包验收"
LATEST_LOG = LOG_DIR / "stable-candidate-exception-samples-drill-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    drill = read_json(DRILL_JSON) if DRILL_JSON.exists() else {}

    if asset.get("状态") != "stable_candidate_exception_samples_drill_ready":
        errors.append("状态必须为 stable_candidate_exception_samples_drill_ready")
    samples = asset.get("异常样例", [])
    if len(samples) < 10:
        errors.append("异常样例不得少于 10 项")
    levels = {item.get("预期分级") for item in samples}
    for level in ["L1", "L2", "L3", "L4", "L5"]:
        if level not in levels:
            errors.append(f"异常样例必须覆盖 {level}")
    if len(asset.get("演练规则", [])) < 5:
        errors.append("演练规则不得少于 5 项")

    for sample in samples:
        for key in ["编号", "业务线", "异常现象", "预期分级", "自动动作", "停止条件"]:
            if not sample.get(key):
                errors.append(f"异常样例缺少字段：{sample.get('编号')} {key}")

    if not drill:
        errors.append("异常样例只读演练不存在")
    else:
        if drill.get("总体状态") != "pass":
            errors.append("异常样例只读演练必须通过")
        if drill.get("汇总", {}).get("失败") != 0:
            errors.append("异常样例只读演练失败数必须为 0")

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
        "制造真实异常",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "稳定候选异常样例库与演练包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "异常样例": len(samples),
            "覆盖分级": sorted(level for level in levels if level),
            "演练失败": drill.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
