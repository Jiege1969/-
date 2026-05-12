# -*- coding: utf-8 -*-
"""生成使用者验收签收与后续迭代队列包。

只生成签收候选、验收清单和后续迭代队列；不写正式规则，
不修改运行配置，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "89使用者验收签收与后续迭代队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "使用者验收签收与后续迭代队列包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "最终交付收尾": EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包" / "日常可用版与稳定交付版最终交付收尾包_最新.json",
    "使用者入口导航": EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包" / "使用者入口导航与常用指令包_最新.json",
    "运行指挥台": EVOLUTION_ROOT / "03数据" / "87稳定交付版运行指挥台索引包" / "稳定交付版运行指挥台索引包_最新.json",
    "证据冻结候选": EVOLUTION_ROOT / "03数据" / "86运行期证据归档与版本冻结候选包" / "运行期证据归档与版本冻结候选包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "使用者验收签收与后续迭代队列包_最新.json"
PACKAGE_MD = DATA_DIR / "使用者验收签收与后续迭代队列包_最新.md"
SIGNOFF_MD = DATA_DIR / "使用者签收检查清单_最新.md"
ITERATION_JSON = DATA_DIR / "后续迭代队列_最新.json"
ITERATION_MD = DATA_DIR / "后续迭代队列_最新.md"
HANDOFF_MD = DATA_DIR / "签收后使用说明_最新.md"
GEN_LOG = LOG_DIR / "生成使用者验收签收与后续迭代队列包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "执行真实回滚": False,
    "写正式规则": False,
    "自动转正式规则": False,
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


def build_signoff_items() -> list[dict[str, Any]]:
    return [
        {"项目": "日常可用版", "签收状态": "可签收使用", "依据": "总巡检与一键总回归通过，交付收尾包 ready"},
        {"项目": "稳定交付版", "签收状态": "可签收使用", "依据": "运行指挥台、日报、问题闭环、证据冻结候选均已落地"},
        {"项目": "完全交付使用版", "签收状态": "不在本次签收范围", "依据": "仍受外部红线能力与长期样本限制"},
        {"项目": "真正自主运行版", "签收状态": "不在本次签收范围", "依据": "正式规则、外部动作、长期自愈仍需总管确认和长周期验证"},
    ]


def build_iteration_queue() -> list[dict[str, Any]]:
    return [
        {"编号": "NEXT-001", "事项": "连续自然日运行样本累计", "类型": "低风险持续观察", "默认动作": "只读采样与日报汇总", "需总管确认": False},
        {"编号": "NEXT-002", "事项": "视频真实渲染材料补齐", "类型": "红线前置材料", "默认动作": "只读清单和人工放行草案", "需总管确认": True},
        {"编号": "NEXT-003", "事项": "n8n 离线蓝图导入前审查", "类型": "外部自动化前置", "默认动作": "凭据隔离与启用禁入检查", "需总管确认": True},
        {"编号": "NEXT-004", "事项": "三业务反馈候选转正式规则申请", "类型": "正式规则候选", "默认动作": "只生成申请草案", "需总管确认": True},
        {"编号": "NEXT-005", "事项": "使用者体验问题回收", "类型": "低风险候选补强", "默认动作": "登记台账、生成候选、只读复验", "需总管确认": False},
        {"编号": "NEXT-006", "事项": "长期稳定交付周报", "类型": "运行管理", "默认动作": "生成周报和看板数据", "需总管确认": False},
    ]


def main() -> int:
    source_summary = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed"),
            "汇总": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }
    snapshot = read_json(SOURCES["总巡检快照"])
    regression = read_json(SOURCES["一键只读总回归"])
    delivery = read_json(SOURCES["最终交付收尾"])
    signoff_items = build_signoff_items()
    iteration_queue = build_iteration_queue()
    ready = (
        snapshot.get("总体状态") == "pass"
        and snapshot.get("汇总", {}).get("失败", 0) == 0
        and regression.get("通过") is True
        and regression.get("指标", {}).get("错误数", 0) == 0
        and delivery.get("状态") == "delivery_closeout_ready"
        and all(item["存在"] for item in source_summary.values())
    )
    package = {
        "名称": "使用者验收签收与后续迭代队列包",
        "生成时间": now_text(),
        "状态": "user_signoff_iteration_queue_ready" if ready else "user_signoff_iteration_queue_blocked",
        "用途": "明确日常可用版与稳定交付版可签收使用，并把后续完全交付/自主运行事项排入队列。",
        "来源摘要": source_summary,
        "签收检查清单": signoff_items,
        "后续迭代队列": iteration_queue,
        "签收结论": "日常可用版与稳定交付版可签收使用；完全交付使用版和真正自主运行版继续作为后续迭代。",
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "使用者签收检查清单": str(SIGNOFF_MD),
            "后续迭代队列JSON": str(ITERATION_JSON),
            "后续迭代队列Markdown": str(ITERATION_MD),
            "签收后使用说明": str(HANDOFF_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(ITERATION_JSON, {"名称": "后续迭代队列", "队列": iteration_queue, "安全边界": SAFETY_BOUNDARY})
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    signoff_rows = [f"| {item['项目']} | {item['签收状态']} | {item['依据']} |" for item in signoff_items]
    iteration_rows = [f"| {item['编号']} | {item['事项']} | {item['类型']} | {item['默认动作']} | {item['需总管确认']} |" for item in iteration_queue]
    package_md = "\n".join([
        "# 使用者验收签收与后续迭代队列包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 签收结论：{package['签收结论']}",
        "",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(SIGNOFF_MD, "\n".join(["# 使用者签收检查清单", "", "| 项目 | 签收状态 | 依据 |", "| --- | --- | --- |", *signoff_rows]))
    write_text(ITERATION_MD, "\n".join(["# 后续迭代队列", "", "| 编号 | 事项 | 类型 | 默认动作 | 需总管确认 |", "| --- | --- | --- | --- | --- |", *iteration_rows]))
    write_text(HANDOFF_MD, "\n".join([
        "# 签收后使用说明",
        "",
        "- 日常可用版和稳定交付版可以进入日常使用。",
        "- 继续使用“继续”可推进低风险候选、只读巡检、状态包和回归清单。",
        "- 真实外部动作、正式规则、服务重载、总管面板或一键接续包修改仍必须总管确认。",
    ]))
    write_json(GEN_LOG, {"名称": "生成使用者验收签收与后续迭代队列包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "签收项": len(signoff_items), "迭代项": len(iteration_queue), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
