# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路持续巡检规则"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路持续巡检规则.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路持续巡检规则.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则_最新.md"

STAGE_INDEX_JSON = ENTRY_DIR / "税收企业微信人工复核链路阶段收口索引_最新.json"
PRECHECK_JSON = ENTRY_DIR / "税收企业微信人工复核链路一键本地预检_最新.json"
TRANSFER_JSON = ENTRY_DIR / "税收企业微信人工复核链路阶段总回传记录_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def by_keywords(data: dict[str, Any], keywords: list[str], default: Any = None) -> Any:
    for key, value in data.items():
        if any(keyword in str(key) for keyword in keywords):
            return value
    return default


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stage = load_json(STAGE_INDEX_JSON)
    precheck = load_json(PRECHECK_JSON)
    transfer = load_json(TRANSFER_JSON)

    stage_modules = by_keywords(stage, ["模块索引"], [])
    precheck_results = by_keywords(precheck, ["预检结果"], [])

    rules = {
        "名称": "税收企业微信人工复核链路持续巡检规则",
        "生成时间": now,
        "资产身份": "税务线本地持续巡检规则，不是自动化任务，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "巡检来源": {
            "阶段收口索引": str(STAGE_INDEX_JSON),
            "一键本地预检": str(PRECHECK_JSON),
            "阶段总回传记录": str(TRANSFER_JSON),
        },
        "巡检范围": [
            "人工复核阅读包、回执模板、回执填报校验、状态机、整改清单、出入口索引、敏感信息复扫、阶段收口索引、一键预检和阶段总回传记录。",
            "仅检查本地文件存在性、验收通过状态、边界声明、下一步队列和红线关闭状态。",
        ],
        "规则组": [
            {
                "规则组": "资产身份一致性",
                "必须满足": [
                    "所有人工复核链路资产必须标注dry-run、待复核分析草案或政策证据底座支撑材料。",
                    "不得出现正式税务意见、正式结论、真实发送已放行等口径。",
                ],
                "失败处理": "进入异常待核验区，不参与当前适用依据候选或对外消息。",
            },
            {
                "规则组": "验收完整性",
                "必须满足": [
                    "阶段收口索引模块数量不少于11且失败数量为0。",
                    "一键本地预检脚本数量不少于12且失败数量为0。",
                    "阶段总回传记录验收通过。",
                ],
                "失败处理": "生成整改清单，只允许人工复核后继续。",
            },
            {
                "规则组": "红线边界",
                "必须满足": [
                    "不接电子税务局。",
                    "不接财税软件。",
                    "不触发n8n。",
                    "不读取或保存企业微信凭据。",
                    "不真实发送企业微信。",
                    "不启动或重启服务。",
                    "不新增或修改端口。",
                    "不写正式库。",
                    "不生成正式税务结论。",
                ],
                "失败处理": "登记为红线阻断，不实施。",
            },
            {
                "规则组": "总管对齐",
                "必须满足": [
                    "本线只生成对齐回传记录。",
                    "总管文件、公共企业微信配置、n8n、服务脚本和正式入口由总管线判断。",
                ],
                "失败处理": "停止本线越权动作，仅回传阻断事项。",
            },
        ],
        "当前基线": {
            "阶段模块数量": by_keywords(stage, ["模块数量"], len(stage_modules)),
            "阶段失败数量": by_keywords(stage, ["失败数量"], 0),
            "一键预检脚本数量": by_keywords(precheck, ["验证脚本数量"], len(precheck_results)),
            "一键预检失败数量": by_keywords(precheck, ["失败数量"], 0),
            "阶段总回传记录存在": bool(transfer),
        },
        "漂移判定": [
            "任一必备验收报告缺失或失败，判定为链路漂移。",
            "任一安全边界从False变为True，判定为红线漂移。",
            "出现正式税务结论、正式意见、真实发送放行、凭据明文等口径，判定为高风险漂移。",
            "下一步队列重新出现已完成项且未说明原因，判定为施工队列漂移。",
        ],
        "下一步建议": [
            "生成人工复核链路持续巡检样例演练，用样例验证规则能发现缺失、失败和红线漂移。",
        ],
        "安全边界": {
            "是否创建自动化任务": False,
            "是否启动或重启服务": False,
            "是否新增或修改端口": False,
            "是否触发n8n": False,
            "是否读取或保存企业微信凭据": False,
            "是否企业微信真实发送": False,
            "是否修改公共企业微信配置": False,
            "是否修改总管文件": False,
            "是否写正式库": False,
            "是否生成正式税务结论": False,
            "是否删除或移动旧资产": False,
        },
    }

    OUT_JSON.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核链路持续巡检规则",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：税务线本地持续巡检规则，不是自动化任务，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "",
        "## 当前基线",
        "",
    ]
    for key, value in rules["当前基线"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 规则组", ""])
    for group in rules["规则组"]:
        lines.append(f"### {group['规则组']}")
        for item in group["必须满足"]:
            lines.append(f"- {item}")
        lines.append(f"- 失败处理：{group['失败处理']}")
        lines.append("")
    lines.extend(["## 漂移判定", ""])
    for item in rules["漂移判定"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in rules["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步建议", ""])
    for item in rules["下一步建议"]:
        lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    copy_latest(OUT_JSON, LATEST_JSON)
    copy_latest(OUT_MD, LATEST_MD)
    print(json.dumps({"状态": "完成", "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
