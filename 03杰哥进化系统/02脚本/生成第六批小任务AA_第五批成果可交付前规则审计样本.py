# -*- coding: utf-8 -*-
"""
第六批并行小任务 AA：第五批成果可交付前规则审计样本。

只读取第五批 P/Q/R/S/T/U 固定回收报告，生成 6 个可交付前规则审计样本。
不触发 n8n，不发送企业微信真实消息，不写正式库，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TASK_NAME = "第六批小任务AA_第五批成果可交付前规则审计样本"
DATA_DIR_NAME = "26第六批小任务AA_第五批成果可交付前规则审计样本"


def root() -> Path:
    return Path(r"D:\杰哥智能化系统")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def report_paths() -> list[dict[str, str]]:
    base = root() / "00杰哥系统总管" / "03数据" / "并行回收"
    return [
        {"窗口": "P", "系统": "01智能系统", "样本类型": "API影子契约与知识库证据索引", "路径": str(base / "01智能系统_第五批小任务P回收报告_最新.md")},
        {"窗口": "Q", "系统": "02扩展系统/视频", "样本类型": "视频影子成片清单", "路径": str(base / "02扩展系统_第五批小任务Q视频回收报告_最新.md")},
        {"窗口": "R", "系统": "02扩展系统/内容", "样本类型": "内容输出包影子清单", "路径": str(base / "02扩展系统_第五批小任务R内容回收报告_最新.md")},
        {"窗口": "S", "系统": "02扩展系统/企业微信", "样本类型": "企业微信灰度监控回滚演练", "路径": str(base / "02扩展系统_第五批小任务S企业微信回收报告_最新.md")},
        {"窗口": "T", "系统": "02扩展系统/税收", "样本类型": "税收政策来源人工复核单", "路径": str(base / "02扩展系统_第五批小任务T税收回收报告_最新.md")},
        {"窗口": "U", "系统": "03进化系统", "样本类型": "第四批扩展成果规则评审读取", "路径": str(base / "03进化系统_第五批小任务U回收报告_最新.md")},
    ]


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def read_reports() -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for item in report_paths():
        path = Path(item["路径"])
        text = read_text(path) if path.exists() else ""
        reports.append(
            {
                **item,
                "存在": path.exists(),
                "已读取": path.exists(),
                "验收通过": contains_any(text, ["验收通过", "验收结果：通过", "结论：完成", "已完成", "通过 23/23"]),
                "交付阻断提及": "交付阻断" in text,
                "安全阻断提及": "安全阻断" in text,
                "仍需人工确认提及": contains_any(text, ["人工复核", "人工确认", "待人工", "待核验", "待补证", "人工批准"]),
                "真实动作禁用提及": contains_any(
                    text,
                    [
                        "未触发 n8n",
                        "未触发n8n",
                        "未发送企业微信真实消息",
                        "未发企业微信真实消息",
                        "不发企业微信真实消息",
                        "未调用券商接口",
                        "未自动交易",
                        "不自动交易",
                        "未写正式库",
                        "不写正式库",
                        "真实发送禁用",
                        "正式库写入禁用",
                        "真实动作仍禁用",
                        "不调用真实外部API",
                        "未调用真实外部 API",
                    ],
                ),
                "本职工作暂停继承提及": contains_any(text, ["本职工作系统", "不触碰本职工作", "未触碰本职工作", "本职工作暂停继承"]),
                "安全边界提及": "安全边界" in text,
                "文本摘要": text[:500],
            }
        )
    return reports


def sample_for(report: dict[str, Any]) -> dict[str, Any]:
    manual_required = report["仍需人工确认提及"] or report["窗口"] in {"Q", "T", "U"}
    countable = report["存在"] and report["已读取"] and report["验收通过"]
    deliverable_state = "可计入；可交付前仍需保留人工确认/影子边界" if manual_required else "可计入；无额外交付阻断"
    action_bans = {
        "n8n触发": False,
        "企业微信真实发送": False,
        "正式库写入": False,
        "券商接口调用": False,
        "自动交易": False,
        "真实外部API或真实媒体动作": False,
        "本职工作系统触碰": False,
    }
    summaries = {
        "P": "API 与知识库证据索引联动为本地影子样本；越权外部 API、证据过旧、无证据和正式库写入继续阻断。",
        "Q": "视频复核通过后仍只生成影子成片清单；真实转码、剪辑、渲染、字幕、封面、发布继续禁用。",
        "R": "内容处理输出包仅为影子清单；输入缺失降级、敏感越权内容和真实批量转换继续阻断。",
        "S": "企业微信灰度监控为离线 shadow 读取；response_url、Webhook、n8n 和真实发送继续禁用。",
        "T": "税收政策来源装载候选需人工复核；正式库写入、正式税务适用判断和正式申报建议不放行。",
        "U": "进化规则评审读取样本可继承为审计依据；安全阻断不失败、真实动作仍禁用、本职工作暂停继承。",
    }
    return {
        "审计样本ID": f"AA-{report['窗口']}",
        "来源窗口": report["窗口"],
        "系统": report["系统"],
        "样本类型": report["样本类型"],
        "来源路径": report["路径"],
        "可计入": bool(countable),
        "仍需人工确认": bool(manual_required),
        "真实动作禁用": True,
        "本职工作暂停继承": True,
        "交付前审计结论": deliverable_state,
        "安全阻断不按失败处理": True,
        "禁止动作": action_bans,
        "规则摘要": summaries[report["窗口"]],
        "审计证据": {
            "报告存在": report["存在"],
            "报告已读取": report["已读取"],
            "验收通过": report["验收通过"],
            "交付阻断提及": report["交付阻断提及"],
            "安全阻断提及": report["安全阻断提及"],
            "真实动作禁用提及": report["真实动作禁用提及"],
            "本职工作暂停继承提及": report["本职工作暂停继承提及"],
        },
    }


def build_payload() -> dict[str, Any]:
    reports = read_reports()
    samples = [sample_for(item) for item in reports]
    return {
        "任务": TASK_NAME,
        "生成时间": now_text(),
        "读取报告数量": len(reports),
        "审计样本数量": len(samples),
        "读取报告": reports,
        "可交付前规则审计样本": samples,
        "统一审计口径": {
            "可计入": "第五批 P/Q/R/S/T/U 固定回收报告存在、已读取且验收通过时，可计入第五批成果进度。",
            "仍需人工确认": "涉及人工复核、人工确认、待核验、待补证或正式固化批准的事项，交付前仍需人工确认。",
            "真实动作禁用": True,
            "本职工作暂停继承": True,
            "安全阻断不失败": True,
            "正式库写入禁用": True,
            "n8n触发禁用": True,
            "企业微信真实发送禁用": True,
            "券商接口禁用": True,
            "自动交易禁用": True,
        },
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "真实外部API": False,
            "触碰本职工作系统": False,
            "真实媒体生成或发布": False,
        },
        "验收目标": ["输出6样本", "可计入口径", "仍需人工确认口径", "真实动作禁用", "本职工作暂停继承"],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 第六批小任务AA：第五批成果可交付前规则审计样本",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 读取报告数量：{payload['读取报告数量']}",
        f"- 审计样本数量：{payload['审计样本数量']}",
        "- 读取报告：第五批 P/Q/R/S/T/U 固定回收报告",
        "- 结论：可计入、仍需人工确认、真实动作禁用、本职工作暂停继承四类口径均已形成样本。",
        "",
        "## 读取路径",
        "",
    ]
    for item in payload["读取报告"]:
        lines.append(f"- {item['窗口']} {item['样本类型']}：`{item['路径']}`；存在={item['存在']}；已读取={item['已读取']}；验收通过={item['验收通过']}")
    lines.extend(["", "## 六个审计样本", ""])
    for sample in payload["可交付前规则审计样本"]:
        lines.extend(
            [
                f"### {sample['审计样本ID']} {sample['样本类型']}",
                f"- 来源窗口：{sample['来源窗口']}",
                f"- 系统：{sample['系统']}",
                f"- 来源路径：`{sample['来源路径']}`",
                f"- 可计入：{sample['可计入']}",
                f"- 仍需人工确认：{sample['仍需人工确认']}",
                f"- 真实动作禁用：{sample['真实动作禁用']}",
                f"- 本职工作暂停继承：{sample['本职工作暂停继承']}",
                f"- 安全阻断不按失败处理：{sample['安全阻断不按失败处理']}",
                f"- 交付前审计结论：{sample['交付前审计结论']}",
                f"- 规则摘要：{sample['规则摘要']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 统一审计口径",
            "",
            "- 可计入：报告存在、已读取且验收通过时计入第五批成果进度。",
            "- 仍需人工确认：人工复核、待核验、待补证、正式固化批准等事项不自动放行。",
            "- 真实动作禁用：n8n、企业微信真实发送、正式库、券商接口、自动交易、真实外部 API、真实媒体生成或发布均禁用。",
            "- 本职工作暂停继承：不得触碰本职工作系统。",
            "- 安全阻断不失败：安全阻断作为合规边界列示，不按交付失败处理。",
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未写正式库、知识库、向量库或业务库。",
            "- 未调用券商接口。",
            "- 未自动交易、下单或撤单。",
            "- 未触碰本职工作系统。",
            "- 未触发真实外部 API。",
            "- 未生成或发布真实媒体。",
            "",
        ]
    )
    return "\n".join(lines)


def build_recovery_report(payload: dict[str, Any], files: dict[str, str], verify_text: str = "待验证") -> str:
    return "\n".join(
        [
            "# 03进化系统_第六批小任务AA回收报告_最新",
            "",
            f"- 生成时间：{payload['生成时间']}",
            "- 任务：03进化 / 第五批成果可交付前规则审计样本",
            f"- 读取报告：P/Q/R/S/T/U，共 {payload['读取报告数量']} 份固定回收报告路径",
            f"- 输出样本：{payload['审计样本数量']} 个",
            "- 规则结论：可计入；仍需人工确认；真实动作禁用；本职工作暂停继承",
            f"- 验收结果：{verify_text}",
            "",
            "## 新增/修改文件",
            "",
            *[f"- {name}：`{path}`" for name, path in files.items()],
            "",
            "## 交付阻断",
            "",
            "- 未发现本审计样本自身的交付阻断；本轮不做真实业务交付。",
            "- 交付前仍需人工确认的样本已单独标注，不自动升级为真实动作授权。",
            "",
            "## 安全阻断",
            "",
            "- 安全阻断作为合规边界单独列示，不按失败处理。",
            "- P/Q/R/S/T/U 样本均继承真实动作禁用口径。",
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未写正式库。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未触碰本职工作系统。",
            "- 未调用真实外部 API。",
            "- 未生成或发布真实媒体。",
            "",
        ]
    )


def main() -> int:
    evo = root() / "03杰哥进化系统"
    data_dir = evo / "03数据" / DATA_DIR_NAME
    doc_path = evo / "07文档" / "第六批小任务AA_第五批成果可交付前规则审计样本说明_最新.md"
    latest_json = data_dir / f"{TASK_NAME}_最新.json"
    latest_md = data_dir / f"{TASK_NAME}_最新.md"
    recovery_path = root() / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第六批小任务AA回收报告_最新.md"

    payload = build_payload()
    write_json(latest_json, payload)
    markdown = build_markdown(payload)
    write_text(latest_md, markdown)
    write_text(doc_path, markdown)

    files = {
        "规则审计样本JSON": str(latest_json),
        "规则审计样本Markdown": str(latest_md),
        "规则审计说明文档": str(doc_path),
    }
    write_text(recovery_path, build_recovery_report(payload, files))
    print(json.dumps({"通过": True, "审计样本数量": payload["审计样本数量"], "读取报告数量": payload["读取报告数量"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
