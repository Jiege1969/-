# -*- coding: utf-8 -*-
"""验证第三轮并行施工调度索引与合并验收准备包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
ASSET_JSON = ROOT / "03数据" / "74第三轮并行施工调度索引与合并验收准备包" / "第三轮并行施工调度索引与合并验收准备包_最新.json"
LOG_DIR = ROOT / "04日志" / "第三轮并行施工调度索引与合并验收准备包验收"
LATEST_LOG = LOG_DIR / "parallel-round3-dispatch-merge-prepare-verify-最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_log_passed(path: Path) -> bool:
    if not path.exists():
        return False
    data = read_json(path)
    if data.get("通过") is True and data.get("指标", {}).get("错误数", data.get("错误数", 0)) == 0:
        return True
    if data.get("总体状态") == "pass" and data.get("汇总", {}).get("失败", 0) == 0:
        return True
    return False


def main() -> int:
    errors: list[str] = []
    asset = read_json(ASSET_JSON) if ASSET_JSON.exists() else {}
    if asset.get("状态") != "parallel_round3_dispatch_merge_prepare_ready":
        errors.append("状态必须为 parallel_round3_dispatch_merge_prepare_ready")
    if len(asset.get("并行任务", [])) < 3:
        errors.append("并行任务不得少于 3 项")
    if len(asset.get("合并验收项", [])) < 6:
        errors.append("合并验收项不得少于 6 项")
    for item in asset.get("并行任务", []):
        for key in ["编号", "名称", "负责人", "数据目录", "验收日志", "合并条件"]:
            if not item.get(key):
                errors.append(f"并行任务缺少字段：{item.get('编号')} {key}")
        log_path = Path(item.get("验收日志", ""))
        if log_path.exists() and not verify_log_passed(log_path):
            errors.append(f"并行任务验收日志存在但未通过：{item.get('编号')} {log_path}")
    for name, path_text in asset.get("输出文件", {}).items():
        if not Path(path_text).exists():
            errors.append(f"输出文件不存在：{name} {path_text}")
    for flag, value in asset.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界 {flag} 必须为 false")
    report = {
        "名称": "第三轮并行施工调度索引与合并验收准备包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {"并行任务": len(asset.get("并行任务", [])), "合并验收项": len(asset.get("合并验收项", [])), "错误数": len(errors)},
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
