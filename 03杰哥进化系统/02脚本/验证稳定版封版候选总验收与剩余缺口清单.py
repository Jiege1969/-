# -*- coding: utf-8 -*-
"""验证稳定版封版候选总验收与剩余缺口清单。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单" / "稳定版封版候选总验收与剩余缺口清单_最新.json"
SUMMARY_JSON = ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单" / "稳定版封版候选总验收只读汇总_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定版封版候选总验收与剩余缺口清单验收"
LATEST_LOG = LOG_DIR / "stable-release-freeze-candidate-acceptance-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    summary = read_json(SUMMARY_JSON) if SUMMARY_JSON.exists() else {}

    if asset.get("状态") != "stable_release_freeze_candidate_acceptance_ready":
        errors.append("状态必须为 stable_release_freeze_candidate_acceptance_ready")
    if len(asset.get("总验收证据", [])) < 9:
        errors.append("总验收证据不得少于 9 项")
    if len(asset.get("剩余缺口", [])) < 7:
        errors.append("剩余缺口不得少于 7 项")
    if len(asset.get("后续施工建议", [])) < 4:
        errors.append("后续施工建议不得少于 4 项")

    for item in asset.get("总验收证据", []):
        for key in ["编号", "名称", "路径", "通过口径"]:
            if not item.get(key):
                errors.append(f"总验收证据缺少字段：{item.get('编号')} {key}")
        if item.get("路径") and not Path(item["路径"]).exists():
            errors.append(f"总验收证据路径不存在：{item.get('编号')} {item.get('路径')}")

    if not summary:
        errors.append("稳定版封版候选总验收只读汇总不存在")
    else:
        if summary.get("总体状态") != "pass":
            errors.append("稳定版封版候选总验收只读汇总必须通过")
        if summary.get("稳定版封版候选成立") is not True:
            errors.append("稳定版封版候选必须成立")
        if summary.get("汇总", {}).get("失败") != 0:
            errors.append("总验收证据失败数必须为 0")
        if summary.get("阻断缺口"):
            errors.append("不得存在阻断稳定版候选的缺口")

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
        "名称": "稳定版封版候选总验收与剩余缺口清单验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "总验收证据": len(asset.get("总验收证据", [])),
            "剩余缺口": len(asset.get("剩余缺口", [])),
            "后续施工建议": len(asset.get("后续施工建议", [])),
            "证据失败": summary.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
