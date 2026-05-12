# -*- coding: utf-8 -*-
"""验证每日开工收工清单与低风险续跑包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = EVOLUTION_ROOT / "03数据" / "82每日开工收工清单与低风险续跑包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "每日开工收工清单与低风险续跑包验收"

PACKAGE_JSON = DATA_DIR / "每日开工收工清单与低风险续跑包_最新.json"
PACKAGE_MD = DATA_DIR / "每日开工收工清单与低风险续跑包_最新.md"
START_MD = DATA_DIR / "每日开工清单_最新.md"
END_MD = DATA_DIR / "每日收工清单_最新.md"
RERUN_MD = DATA_DIR / "低风险续跑条件_最新.md"
STOP_MD = DATA_DIR / "必须停机登记项_最新.md"
GEN_LOG = LOG_DIR / "生成每日开工收工清单与低风险续跑包_最新.json"
VERIFY_JSON = LOG_DIR / "daily-start-end-low-risk-rerun-verify-最新.json"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, START_MD, END_MD, RERUN_MD, STOP_MD, GEN_LOG]
FORBIDDEN_MARKERS = [
    "允许真实发送",
    "允许真实触发",
    "允许交易",
    "允许登录电子税务局",
    "允许接财税软件",
    "允许真实渲染",
    "允许自动发布",
    "允许写正式规则",
    "允许重载19310",
    "允许重载19302",
]


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"缺少文件：{path}")
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8-sig")) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "daily_start_end_low_risk_rerun_ready":
        errors.append("状态不正确")
    if package.get("当前总巡检", {}).get("总体状态") != "pass":
        errors.append("当前总巡检不是pass")
    if package.get("当前总回归", {}).get("指标", {}).get("错误数", 0) != 0:
        errors.append("当前总回归错误数不为0")
    if package.get("交付收尾状态") != "delivery_closeout_ready":
        errors.append("交付收尾状态不是delivery_closeout_ready")
    for key, minimum in [("每日开工清单", 5), ("每日收工清单", 5), ("低风险续跑条件", 4), ("必须停机登记项", 8)]:
        if len(package.get(key, [])) < minimum:
            errors.append(f"{key}数量不足")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为false：{flag}")
    all_text = json.dumps(package, ensure_ascii=False)
    for path in REQUIRED_FILES:
        if path.exists() and path.suffix.lower() == ".md":
            all_text += "\n" + path.read_text(encoding="utf-8-sig")
    hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")
    report = {
        "名称": "每日开工收工清单与低风险续跑包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "开工项": len(package.get("每日开工清单", [])),
            "收工项": len(package.get("每日收工清单", [])),
            "低风险续跑条件": len(package.get("低风险续跑条件", [])),
            "停机登记项": len(package.get("必须停机登记项", [])),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
