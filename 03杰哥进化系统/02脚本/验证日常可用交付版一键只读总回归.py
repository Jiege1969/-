# -*- coding: utf-8 -*-
"""验证日常可用交付版一键只读总回归报告。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "44日常可用交付版一键只读总回归" / "日常可用交付版一键只读总回归_最新.json"
LOG_DIR = ROOT / "04日志" / "日常可用交付版一键只读总回归验收"
LATEST_LOG = LOG_DIR / "daily-usable-readonly-regression-verify-最新.json"


def main() -> int:
    errors: list[str] = []
    asset = json.loads(ASSET_JSON.read_text(encoding="utf-8-sig")) if ASSET_JSON.exists() else {}
    summary = asset.get("汇总", {})
    if asset.get("总体状态") != "pass":
        errors.append("总回归总体状态必须为 pass")
    if summary.get("失败") != 0:
        errors.append("总回归失败数必须为0")
    if summary.get("通过") != summary.get("总数"):
        errors.append("总回归通过数必须等于总数")
    if summary.get("总数", 0) < 10:
        errors.append("总回归任务数不得少于10")
    for item in asset.get("任务结果", []):
        if item.get("passed") is not True or item.get("returncode") != 0:
            errors.append(f"任务未通过：{item.get('id')} {item.get('name')}")
    for flag in [
        "重载19310",
        "重载19302",
        "请求19302业务接口",
        "真实发送企业微信",
        "触发n8n",
        "接券商",
        "交易",
        "登录电子税务局",
        "接财税软件",
        "真实渲染视频",
        "自动发布视频",
        "写正式规则",
        "修改总管面板",
        "修改一键接续包",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "日常可用交付版一键只读总回归验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "总数": summary.get("总数", 0),
            "通过": summary.get("通过", 0),
            "失败": summary.get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
