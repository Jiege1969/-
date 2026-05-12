# -*- coding: utf-8 -*-
"""
生成下一轮并行派工与任务队列视图。

安全边界：
- 只写 00 总管脚本、开工上下文、运行状态、并行回收和当前施工面板指定 marker 小节。
- 只生成只读/配置驱动的队列视图，不启动子系统，不触发 n8n，不发企业微信真实消息。
- 不调用券商接口，不自动交易，不写正式库，不修改股票核心脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
CONTEXT = MANAGER / "03数据" / "开工上下文"
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"
PANEL = MANAGER / "07文档" / "当前施工面板.md"

CONFIG_PATH = CONTEXT / "下一轮并行派工队列配置_最新.json"
VIEW_JSON = STATE / "下一轮并行派工任务队列视图_最新.json"
VIEW_MD = STATE / "下一轮并行派工任务队列视图_最新.md"
DISPATCH_MD = CONTEXT / "下一轮并行派工队列启动包_最新.md"
GEN_REPORT_JSON = STATE / "下一轮并行派工任务队列视图生成报告_最新.json"
GEN_REPORT_MD = STATE / "下一轮并行派工任务队列视图生成报告_最新.md"
RECOVERY_REPORT = RECOVERY / "00总管_本轮小任务A回收报告_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def replace_section(text: str, marker: str, section: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    block = f"{start}\n{section.strip()}\n{end}"
    if start in text and end in text:
        before = text.split(start, 1)[0].rstrip()
        after = text.split(end, 1)[1].lstrip()
        return f"{before}\n\n{block}\n\n{after}".strip() + "\n"
    return f"{block}\n\n{text}".strip() + "\n"


def default_config() -> dict[str, Any]:
    return {
        "名称": "下一轮并行派工队列配置",
        "配置版本": "2026-05-05-A",
        "只读视图": True,
        "容量规则": {
            "最大活跃窗口": 3,
            "活跃窗口": ["01智能系统", "02扩展系统", "03进化系统"],
            "00总管任务": "串行派工、验收、回收和进度重算，不作为子系统活跃窗口计数",
            "总体系统回收": "串行收口任务，等待活跃窗口回收报告齐备后执行",
        },
        "安全边界": {
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式库": False,
            "真实媒体转码发布": False,
            "批量转换真实业务文档": False,
            "02扩展高风险真实动作": "shadow/禁用",
        },
        "下一轮任务优先级": [
            {
                "优先级": 1,
                "队列项": "00总管",
                "窗口状态": "串行前置",
                "目标": "生成下一轮派工包、容量校验、任务队列视图和固定回收入口。",
                "回收路径": str(RECOVERY_REPORT),
            },
            {
                "优先级": 2,
                "队列项": "01智能",
                "窗口状态": "活跃",
                "目标": "推进知识检索、中台能力、异常处理和只读验收小样本。",
                "回收路径": str(RECOVERY / "01智能系统_本轮回收报告_最新.md"),
            },
            {
                "优先级": 3,
                "队列项": "02扩展",
                "窗口状态": "活跃滚动",
                "目标": "按小任务滚动推进多助手路由、知识库、税收、本职工作、内容处理、视频制作。",
                "回收路径": str(RECOVERY / "02扩展系统_本轮回收报告_最新.md"),
                "滚动小任务": [
                    "企业微信多助手统一路由影子预案",
                    "知识库可追溯问答小样本",
                    "税收政策证据链只读样本",
                    "本职工作骨架验收样本",
                    "内容处理安全队列影子样本",
                    "视频制作素材只读盘点样本",
                ],
            },
            {
                "优先级": 4,
                "队列项": "03进化",
                "窗口状态": "活跃",
                "目标": "沉淀并行施工、股票交付闭环和自动交易硬闸门为可复用评审规则。",
                "回收路径": str(RECOVERY / "03进化系统_本轮回收报告_最新.md"),
            },
            {
                "优先级": 5,
                "队列项": "总体系统回收",
                "窗口状态": "串行收口",
                "目标": "读取固定回收报告，执行冲突检测、进度重算、接续包刷新和施工面板同步。",
                "回收路径": str(RECOVERY / "00总管_本轮三线回收报告_最新.md"),
            },
        ],
        "读取依据": [
            str(STATE / "本轮并行施工进度重算报告_最新.json"),
            str(STATE / "并行施工容量控制与小队列调度验收_最新.json"),
            str(CONTEXT / "本轮并行施工派工包_最新.json"),
        ],
    }


def ensure_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        config = default_config()
        write_json(CONFIG_PATH, config)
        return config
    return load_json(CONFIG_PATH)


def build_view(config: dict[str, Any]) -> dict[str, Any]:
    active_items = [item for item in config["下一轮任务优先级"] if "活跃" in item["窗口状态"]]
    ext_items = next((item.get("滚动小任务", []) for item in active_items if item["队列项"] == "02扩展"), [])
    return {
        "名称": "下一轮并行派工任务队列视图",
        "生成时间": now_text(),
        "来源配置": str(CONFIG_PATH),
        "只读视图": config["只读视图"],
        "容量规则": config["容量规则"],
        "活跃窗口数量": len(active_items),
        "队列": config["下一轮任务优先级"],
        "02扩展滚动": {
            "允许多任务滚动": True,
            "同一时刻活跃窗口数": 1,
            "小任务数量": len(ext_items),
            "小任务": ext_items,
            "高风险真实动作": "shadow/禁用",
        },
        "安全边界": config["安全边界"],
        "读取依据": config["读取依据"],
        "结论": "通过" if len(active_items) <= config["容量规则"]["最大活跃窗口"] else "容量超限",
        "阻断数量": 0 if len(active_items) <= config["容量规则"]["最大活跃窗口"] else 1,
    }


def build_view_md(view: dict[str, Any]) -> str:
    lines = [
        "# 下一轮并行派工任务队列视图",
        f"生成时间：{view['生成时间']}",
        "",
        f"- 结论：{view['结论']}",
        f"- 只读视图：{view['只读视图']}",
        f"- 最大活跃窗口：`{view['容量规则']['最大活跃窗口']}`",
        f"- 当前活跃窗口数量：`{view['活跃窗口数量']}`",
        "- 00总管与总体系统回收均为串行任务，不挤占 01/02/03 子系统活跃窗口。",
        "",
        "## 队列优先级",
    ]
    for item in view["队列"]:
        lines.append(
            f"{item['优先级']}. {item['队列项']}：{item['窗口状态']}；{item['目标']} 回收：`{item['回收路径']}`"
        )
    lines.extend(["", "## 02扩展滚动小任务"])
    for item in view["02扩展滚动"]["小任务"]:
        lines.append(f"- {item}：只读/影子推进，高风险真实动作保持 shadow/禁用。")
    lines.extend(["", "## 安全边界"])
    for key, value in view["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def build_dispatch_md(view: dict[str, Any]) -> str:
    return "\n".join([
        "# 下一轮并行派工队列启动包",
        f"生成时间：{view['生成时间']}",
        "",
        "## 启动原则",
        "- 先读任务队列视图，再开 01/02/03 三个活跃窗口。",
        "- 02扩展可以在同一窗口内按小任务滚动，不额外突破最大 3 个活跃窗口。",
        "- 任何真实发送、n8n、券商接口、自动交易、正式库写入都保持关闭。",
        "",
        "## 读取入口",
        f"- 队列视图：`{VIEW_MD}`",
        f"- 队列配置：`{CONFIG_PATH}`",
        f"- 小任务A回收：`{RECOVERY_REPORT}`",
        "",
    ])


def build_recovery_md(view: dict[str, Any]) -> str:
    return "\n".join([
        "# 00总管 本轮小任务A回收报告",
        f"生成时间：{view['生成时间']}",
        "",
        "【施工框名称】00杰哥系统总管 / 小任务A",
        "【负责范围】下一轮并行派工自动化与任务队列视图补齐。",
        f"【新增/修改文件】{CONFIG_PATH}；{VIEW_JSON}；{VIEW_MD}；{DISPATCH_MD}；{GEN_REPORT_JSON}；{GEN_REPORT_MD}；{RECOVERY_REPORT}",
        "【验收结果】等待验证脚本执行。",
        f"【容量规则】最大活跃窗口 {view['容量规则']['最大活跃窗口']}；当前活跃窗口 {view['活跃窗口数量']}；02扩展单窗口多任务滚动。",
        "【高风险动作确认】企业微信真实发送/n8n/券商接口/自动交易/正式库写入：否。",
        "【安全边界】02扩展高风险真实动作保持 shadow/禁用；本轮未修改股票核心脚本。",
        f"【阻断项】{view['阻断数量']}",
        "【下一步建议】运行验证脚本后由总体系统回收读取本报告和队列视图。",
        "",
    ])


def build_section(view: dict[str, Any]) -> str:
    return "\n".join([
        "## 2026-05-05 下一轮并行派工任务队列视图",
        "",
        f"- 队列视图：`{VIEW_MD}`",
        f"- 队列配置：`{CONFIG_PATH}`",
        f"- 结论：{view['结论']}；阻断 `{view['阻断数量']}`。",
        f"- 容量规则：最多 `{view['容量规则']['最大活跃窗口']}` 个活跃窗口；当前活跃窗口 `{view['活跃窗口数量']}`。",
        "- 优先级：00总管 -> 01智能 -> 02扩展多个小任务滚动 -> 03进化 -> 总体系统回收。",
        "- 02扩展：允许单窗口内多任务滚动；企业微信真实发送、n8n、券商接口、自动交易、正式库写入保持 shadow/禁用。",
        "- 安全边界：未发企业微信真实消息，未触发 n8n，未调用券商接口，未自动交易，未写正式库，未修改股票核心脚本。",
    ])


def main() -> int:
    config = ensure_config()
    view = build_view(config)
    write_json(VIEW_JSON, view)
    write_text(VIEW_MD, build_view_md(view))
    write_text(DISPATCH_MD, build_dispatch_md(view))
    write_text(RECOVERY_REPORT, build_recovery_md(view))
    write_text(PANEL, replace_section(read_text(PANEL), "下一轮并行派工任务队列视图", build_section(view)))

    report = {
        "名称": "下一轮并行派工任务队列视图生成报告",
        "生成时间": view["生成时间"],
        "结论": view["结论"],
        "阻断数量": view["阻断数量"],
        "写入文件": [
            str(CONFIG_PATH),
            str(VIEW_JSON),
            str(VIEW_MD),
            str(DISPATCH_MD),
            str(GEN_REPORT_JSON),
            str(GEN_REPORT_MD),
            str(RECOVERY_REPORT),
            str(PANEL),
        ],
        "安全边界": view["安全边界"],
    }
    write_json(GEN_REPORT_JSON, report)
    write_text(
        GEN_REPORT_MD,
        "\n".join([
            "# 下一轮并行派工任务队列视图生成报告",
            f"生成时间：{report['生成时间']}",
            "",
            f"- 结论：{report['结论']}",
            f"- 阻断数量：{report['阻断数量']}",
            "- 高风险动作：全部关闭或 shadow/禁用。",
            "",
        ]),
    )
    print(json.dumps({"状态": view["结论"], "活跃窗口": view["活跃窗口数量"], "阻断": view["阻断数量"]}, ensure_ascii=False))
    return 0 if view["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
