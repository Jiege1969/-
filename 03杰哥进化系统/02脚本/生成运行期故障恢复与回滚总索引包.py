# -*- coding: utf-8 -*-
"""生成运行期故障恢复与回滚总索引包。

只汇总本地故障恢复、停机闸口、回滚剧本和人工确认入口；不执行回滚，
不触发外部系统，不写正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "87运行期故障恢复与回滚总索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期故障恢复与回滚总索引包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "问题闭环总台账": EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json",
    "n8n失败演练回滚": EVOLUTION_ROOT / "03数据" / "81n8n离线闸口失败演练与回滚剧本包" / "n8n离线闸口失败演练与回滚剧本包_最新.json",
    "暂停闸口与人工接管": EVOLUTION_ROOT / "03数据" / "77自主运行暂停闸口与人工接管演练包" / "自主运行暂停闸口与人工接管演练包_最新.json",
    "每日运行日报": EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定交付版每日运行日报与次日待办包_最新.json",
    "证据归档冻结候选": EVOLUTION_ROOT / "03数据" / "86运行期证据归档与版本冻结候选包" / "运行期证据归档与版本冻结候选包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "运行期故障恢复与回滚总索引包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期故障恢复与回滚总索引包_最新.md"
RECOVERY_JSON = DATA_DIR / "故障恢复路线图_最新.json"
RECOVERY_MD = DATA_DIR / "故障恢复路线图_最新.md"
ROLLBACK_MD = DATA_DIR / "回滚与停机闸口索引_最新.md"
HANDOFF_MD = DATA_DIR / "人工接管恢复清单_最新.md"
GEN_LOG = LOG_DIR / "生成运行期故障恢复与回滚总索引包_最新.json"

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


def build_recovery_routes() -> list[dict[str, Any]]:
    return [
        {"场景": "总巡检失败", "第一动作": "暂停低风险续跑", "查证据": "总巡检快照/一键总回归", "恢复方式": "生成候选修复与只读复验", "需总管确认": False},
        {"场景": "一键总回归失败", "第一动作": "登记失败项", "查证据": "一键只读总回归报告", "恢复方式": "只读定位，修判定口径或候选资产", "需总管确认": False},
        {"场景": "触碰红线", "第一动作": "立即停机登记", "查证据": "暂停闸口与人工接管包", "恢复方式": "等待总管确认", "需总管确认": True},
        {"场景": "n8n启用/导入风险", "第一动作": "保持离线禁入", "查证据": "n8n失败演练回滚/凭据隔离包", "恢复方式": "只生成离线回滚剧本", "需总管确认": True},
        {"场景": "正式规则申请", "第一动作": "只生成申请草案", "查证据": "正式规则申请草案审查包", "恢复方式": "总管确认后再处理", "需总管确认": True},
        {"场景": "视频真实渲染风险", "第一动作": "保持试运行禁入", "查证据": "视频放行材料完整性复核包", "恢复方式": "补材料，不试运行", "需总管确认": True},
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
    routes = build_recovery_routes()
    package = {
        "名称": "运行期故障恢复与回滚总索引包",
        "生成时间": now_text(),
        "状态": "runtime_recovery_rollback_index_ready" if all(item["存在"] for item in source_summary.values()) else "runtime_recovery_rollback_index_blocked",
        "用途": "把运行期故障、红线停机、n8n离线回滚、正式规则申请和视频试运行禁入统一到恢复索引。",
        "来源摘要": source_summary,
        "故障恢复路线": routes,
        "恢复原则": [
            "先停机或暂停低风险续跑，再查证据。",
            "只读复验优先，不直接动正式规则或运行配置。",
            "涉及外部动作、服务重载、正式规则、真实渲染发布时必须总管确认。",
            "本包只提供索引和剧本，不执行真实回滚。",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "故障恢复路线图JSON": str(RECOVERY_JSON),
            "故障恢复路线图Markdown": str(RECOVERY_MD),
            "回滚与停机闸口索引": str(ROLLBACK_MD),
            "人工接管恢复清单": str(HANDOFF_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(RECOVERY_JSON, {"名称": "故障恢复路线图", "路线": routes, "安全边界": SAFETY_BOUNDARY})
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    route_rows = [f"| {item['场景']} | {item['第一动作']} | {item['恢复方式']} | {item['需总管确认']} |" for item in routes]
    package_md = "\n".join([
        "# 运行期故障恢复与回滚总索引包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        "- 结论：只做恢复索引，不执行真实回滚。",
        "",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(RECOVERY_MD, "\n".join(["# 故障恢复路线图", "", "| 场景 | 第一动作 | 恢复方式 | 需总管确认 |", "| --- | --- | --- | --- |", *route_rows]))
    write_text(ROLLBACK_MD, "\n".join(["# 回滚与停机闸口索引", "", "- n8n 只允许离线回滚剧本，不启用 webhook。", "- 正式规则只允许申请草案，不自动生效。", "- 视频真实渲染只允许材料复核，不试运行。", "- 服务重载只登记需总管确认。"]))
    write_text(HANDOFF_MD, "\n".join(["# 人工接管恢复清单", "", "- 读取本包总包状态。", "- 查看对应故障场景路线。", "- 查证据路径。", "- 触碰红线时停止执行并等待总管确认。"]))
    write_json(GEN_LOG, {"名称": "生成运行期故障恢复与回滚总索引包", "生成时间": now_text(), "通过": package["状态"] == "runtime_recovery_rollback_index_ready", "错误数": 0 if package["状态"] == "runtime_recovery_rollback_index_ready" else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "来源": len(source_summary), "路线": len(routes), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if package["状态"] == "runtime_recovery_rollback_index_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
