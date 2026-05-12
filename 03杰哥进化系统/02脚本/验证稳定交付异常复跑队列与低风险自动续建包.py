# -*- coding: utf-8 -*-
"""验证稳定交付异常复跑队列与低风险自动续建包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包" / "稳定交付异常复跑队列与低风险自动续建包_最新.json"
RERUN_JSON = ROOT / "03数据" / "50稳定交付异常复跑队列与低风险自动续建包" / "稳定交付低风险只读复跑结果_最新.json"
LOG_DIR = ROOT / "04日志" / "稳定交付异常复跑队列与低风险自动续建包验收"
LATEST_LOG = LOG_DIR / "stable-delivery-rerun-rebuild-package-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    rerun = read_json(RERUN_JSON) if RERUN_JSON.exists() else {}

    if asset.get("状态") != "stable_delivery_rerun_rebuild_candidate_ready":
        errors.append("状态必须为 stable_delivery_rerun_rebuild_candidate_ready")
    queue = asset.get("异常复跑队列", [])
    if len(queue) < 8:
        errors.append("异常复跑队列不得少于 8 项")
    if len(asset.get("低风险自动续建清单", [])) < 5:
        errors.append("低风险自动续建清单不得少于 5 项")
    if len(asset.get("停止规则", [])) < 5:
        errors.append("停止规则不得少于 5 项")

    for item in queue:
        for key in ["编号", "名称", "触发条件", "执行模式", "脚本", "工作目录", "允许自动复跑", "红线"]:
            if key not in item:
                errors.append(f"复跑队列缺少字段：{item.get('编号')} {key}")
        if item.get("允许自动复跑") is True and not Path(item.get("脚本", "")).exists():
            errors.append(f"允许自动复跑脚本不存在：{item.get('编号')} {item.get('脚本')}")

    if rerun:
        if rerun.get("总体状态") != "pass":
            errors.append("低风险只读复跑结果必须通过")
        if rerun.get("汇总", {}).get("失败") != 0:
            errors.append("低风险只读复跑失败数必须为 0")
    else:
        errors.append("低风险只读复跑结果不存在")

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
        "名称": "稳定交付异常复跑队列与低风险自动续建包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "复跑队列": len(queue),
            "低风险续建项": len(asset.get("低风险自动续建清单", [])),
            "停止规则": len(asset.get("停止规则", [])),
            "复跑执行总数": rerun.get("汇总", {}).get("总数", 0),
            "复跑失败数": rerun.get("汇总", {}).get("失败", 0),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
