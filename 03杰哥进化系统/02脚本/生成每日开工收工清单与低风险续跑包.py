# -*- coding: utf-8 -*-
"""生成每日开工收工清单与低风险续跑包。

只生成本地交接清单、续跑条件和停机闸口，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "82每日开工收工清单与低风险续跑包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "每日开工收工清单与低风险续跑包验收"

SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
REGRESSION_JSON = EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"
DELIVERY_JSON = EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包" / "日常可用版与稳定交付版最终交付收尾包_最新.json"

PACKAGE_JSON = DATA_DIR / "每日开工收工清单与低风险续跑包_最新.json"
PACKAGE_MD = DATA_DIR / "每日开工收工清单与低风险续跑包_最新.md"
START_MD = DATA_DIR / "每日开工清单_最新.md"
END_MD = DATA_DIR / "每日收工清单_最新.md"
RERUN_MD = DATA_DIR / "低风险续跑条件_最新.md"
STOP_MD = DATA_DIR / "必须停机登记项_最新.md"
GEN_LOG = LOG_DIR / "生成每日开工收工清单与低风险续跑包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "写正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    snapshot = read_json(SNAPSHOT_JSON)
    regression = read_json(REGRESSION_JSON)
    delivery = read_json(DELIVERY_JSON)
    start_items = [
        "读取最新日常可用版自主巡检快照，确认失败数为0。",
        "读取一键只读总回归验收，确认错误数为0。",
        "确认日常可用版与稳定交付版交付收尾包仍为 delivery_closeout_ready。",
        "确认本轮只做只读巡检、候选资产、验收脚本、状态包或回归清单。",
        "确认没有 19310/19302 重载需求；如有，只登记为需总管确认。",
    ]
    end_items = [
        "写明本轮新增产物、验收日志和总快照通过数。",
        "写明红线未触发项。",
        "若发现失败项，登记为问题台账或候选补强，不直接改正式规则。",
        "若发现外部系统动作需求，登记为需总管确认。",
        "刷新总巡检快照与一键只读总回归。",
    ]
    rerun_conditions = [
        "只读读取本地 JSON/Markdown/日志。",
        "生成候选包、清单、模板、验收脚本。",
        "修正只读判定口径或自引用验收口径，但不得改变业务结论。",
        "刷新巡检快照和总回归。",
    ]
    stop_items = [
        "真实发送企业微信。",
        "真实触发 n8n 或启用 webhook。",
        "接券商、交易、下单、调仓。",
        "登录电子税务局或接财税软件。",
        "真实渲染视频或自动发布视频。",
        "写正式规则或自动转正式规则。",
        "修改总管面板或一键接续包。",
        "重载 19310 或 19302。",
    ]
    package = {
        "名称": "每日开工收工清单与低风险续跑包",
        "生成时间": now_text(),
        "状态": "daily_start_end_low_risk_rerun_ready",
        "当前总巡检": {"总体状态": snapshot.get("总体状态"), "汇总": snapshot.get("汇总", {}), "路径": str(SNAPSHOT_JSON)},
        "当前总回归": {"通过": regression.get("通过"), "指标": regression.get("指标", {}), "路径": str(REGRESSION_JSON)},
        "交付收尾状态": delivery.get("状态"),
        "每日开工清单": start_items,
        "每日收工清单": end_items,
        "低风险续跑条件": rerun_conditions,
        "必须停机登记项": stop_items,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "每日开工清单": str(START_MD),
            "每日收工清单": str(END_MD),
            "低风险续跑条件": str(RERUN_MD),
            "必须停机登记项": str(STOP_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    sections = [
        "# 每日开工收工清单与低风险续跑包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 当前总巡检：{snapshot.get('总体状态')} / {snapshot.get('汇总', {})}",
        f"- 当前总回归：{regression.get('通过')} / {regression.get('指标', {})}",
    ]
    write_text(PACKAGE_MD, "\n".join(sections))
    write_text(START_MD, "# 每日开工清单\n\n" + "\n".join(f"- {item}" for item in start_items))
    write_text(END_MD, "# 每日收工清单\n\n" + "\n".join(f"- {item}" for item in end_items))
    write_text(RERUN_MD, "# 低风险续跑条件\n\n" + "\n".join(f"- {item}" for item in rerun_conditions))
    write_text(STOP_MD, "# 必须停机登记项\n\n" + "\n".join(f"- {item}" for item in stop_items))
    write_json(GEN_LOG, {"名称": "生成每日开工收工清单与低风险续跑包", "生成时间": now_text(), "通过": True, "错误数": 0, "输出": package["输出文件"]})
    print(json.dumps({"状态": "ready", "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
