# -*- coding: utf-8 -*-
"""验证稳定版候选最终总索引与收口验收包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "61稳定版候选最终总索引与收口验收包" / "稳定版候选最终总索引与收口验收包_最新.json"
CHECK_JSON = ROOT / "03数据" / "61稳定版候选最终总索引与收口验收包" / "稳定版候选最终总索引只读核对_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定版候选最终总索引与收口验收包验收"
LATEST_LOG = LOG_DIR / "stable-candidate-final-master-index-closeout-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    check = read_json(CHECK_JSON) if CHECK_JSON.exists() else {}

    if asset.get("状态") != "stable_candidate_final_master_index_closeout_ready":
        errors.append("状态必须为 stable_candidate_final_master_index_closeout_ready")
    if len(asset.get("最终总索引", [])) < 13:
        errors.append("最终总索引不得少于 13 项")
    if len(asset.get("收口验收项", [])) < 7:
        errors.append("收口验收项不得少于 7 项")
    if len(asset.get("阅读入口", [])) < 5:
        errors.append("阅读入口不得少于 5 项")

    for item in asset.get("最终总索引", []):
        for key in ["编号", "阶段", "名称", "路径", "验收"]:
            if not item.get(key):
                errors.append(f"最终总索引缺少字段：{item.get('编号')} {key}")
        if item.get("路径") and not Path(item["路径"]).exists():
            errors.append(f"资料路径不存在：{item.get('编号')} {item.get('路径')}")
        if item.get("验收") and not Path(item["验收"]).exists():
            errors.append(f"验收路径不存在：{item.get('编号')} {item.get('验收')}")

    if not check:
        errors.append("最终总索引只读核对不存在")
    else:
        if check.get("总体状态") != "pass":
            errors.append("最终总索引只读核对必须通过")
        if check.get("汇总", {}).get("失败") != 0:
            errors.append("最终总索引核对失败数必须为 0")

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
        "正式封版",
    ]:
        if asset.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    report = {
        "名称": "稳定版候选最终总索引与收口验收包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "最终总索引": len(asset.get("最终总索引", [])),
            "收口验收项": len(asset.get("收口验收项", [])),
            "阅读入口": len(asset.get("阅读入口", [])),
            "索引失败": check.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
