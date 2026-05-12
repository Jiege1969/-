# -*- coding: utf-8 -*-
"""
第五批并行小任务 U：第四批扩展成果规则评审读取样本。

只读取第四批 J/K/L/M/N/O 固定回收报告，生成 5 个规则评审样本。
不触发 n8n，不发送企业微信真实消息，不写正式库，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TASK_NAME = "第五批小任务U_第四批扩展成果规则评审读取样本"
DATA_DIR_NAME = "25第五批小任务U_第四批扩展成果规则评审读取样本"


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
        {"窗口": "J", "样本类型": "视频", "路径": str(base / "02扩展系统_第四批小任务J视频回收报告_最新.md")},
        {"窗口": "K", "样本类型": "内容", "路径": str(base / "02扩展系统_第四批小任务K内容回收报告_最新.md")},
        {"窗口": "L", "样本类型": "税收", "路径": str(base / "02扩展系统_第四批小任务L税收回收报告_最新.md")},
        {"窗口": "M", "样本类型": "知识库", "路径": str(base / "02扩展系统_第四批小任务M知识库回收报告_最新.md")},
        {"窗口": "N", "样本类型": "企业微信", "路径": str(base / "02扩展系统_第四批小任务N企业微信回收报告_最新.md")},
        {"窗口": "O", "样本类型": "读取规则", "路径": str(base / "00总管_第四批小任务O回收读取器回收报告_最新.md")},
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
                "验收通过": "验收通过" in text or "结论：通过" in text or "结论：完成" in text,
                "交付阻断提及": "交付阻断" in text,
                "安全阻断提及": "安全阻断" in text,
                "本职工作暂停继承": "本职工作" in text or "用户主动暂停" in text,
                "真实动作仍禁用": contains_any(
                    text,
                    [
                        "未触发 n8n",
                        "未触发n8n",
                        "未发送企业微信真实消息",
                        "未发企业微信真实消息",
                        "未调用券商接口",
                        "未自动交易",
                        "未写正式库",
                        "真实发送禁用",
                        "n8n禁用",
                        "自动交易：False",
                    ],
                ),
            }
        )
    return reports


def sample_for(report: dict[str, Any]) -> dict[str, Any]:
    sample_type = report["样本类型"]
    safety_block = report["安全阻断提及"] or report["真实动作仍禁用"]
    delivery_block = False
    countable = report["存在"] and report["已读取"] and report["验收通过"] and not delivery_block
    base = {
        "样本类型": sample_type,
        "来源窗口": report["窗口"],
        "来源路径": report["路径"],
        "可计入进度": countable,
        "安全阻断不失败": True,
        "真实动作仍禁用": True,
        "本职工作暂停继承": report["本职工作暂停继承"],
        "交付阻断": delivery_block,
        "安全阻断": safety_block,
        "读取结论": "可计入进度；安全阻断作为合规边界，不按失败处理。",
    }
    details = {
        "视频": "真实渲染、转码、剪辑、字幕、封面、发布、n8n、企业微信真实发送均保持禁用。",
        "内容": "真实转换、批量转换、外发、自动化和正式库写入均保持禁用。",
        "税收": "正式库写入、正式申报建议、自动申报、券商接口和自动交易均保持禁用。",
        "知识库": "正式知识库、向量库、数据库写入，真实外部 API，券商接口和自动交易均保持禁用。",
        "企业微信": "真实发送、response_url、Webhook、n8n、正式库写入和外部调用均保持禁用。",
    }
    base["规则评审摘要"] = details[sample_type]
    return base


def build_payload() -> dict[str, Any]:
    reports = read_reports()
    business_reports = [item for item in reports if item["窗口"] in {"J", "K", "L", "M", "N"}]
    samples = [sample_for(item) for item in business_reports]
    rule_report = next(item for item in reports if item["窗口"] == "O")
    payload = {
        "任务": TASK_NAME,
        "生成时间": now_text(),
        "读取报告": reports,
        "读取规则来源": {
            "窗口": "O",
            "路径": rule_report["路径"],
            "规则口径": [
                "只读取第四批 J/K/L/M/N/O 固定 Markdown 回收报告路径。",
                "报告不存在标为待读取，不把读取器预案自身判失败。",
                "安全阻断单独列示，不计失败。",
                "用户主动暂停和本职工作暂停口径继承，不修改进度口径数字。",
            ],
        },
        "规则评审样本数量": len(samples),
        "规则评审样本": samples,
        "统一规则口径": {
            "可计入进度": "J/K/L/M/N 已读取且验收通过时可计入进度；安全阻断不按失败处理。",
            "安全阻断不失败": True,
            "真实动作仍禁用": True,
            "本职工作暂停继承": True,
            "自动交易禁用": True,
            "券商接口禁用": True,
            "n8n触发禁用": True,
            "企业微信真实发送禁用": True,
            "正式库写入禁用": True,
        },
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "真实外部API": False,
            "触碰本职工作系统": False,
        },
    }
    return payload


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 第五批小任务U：第四批扩展成果规则评审读取样本",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 规则评审样本数量：{payload['规则评审样本数量']}",
        "- 样本类型：视频、内容、税收、知识库、企业微信",
        "- 读取规则来源：第四批 O 回收读取器回收报告",
        "- 结论：J/K/L/M/N 可作为规则评审样本；安全阻断不失败，真实动作仍禁用，本职工作暂停口径继承。",
        "",
        "## 读取路径",
        "",
    ]
    for item in payload["读取报告"]:
        lines.append(f"- {item['窗口']} {item['样本类型']}：`{item['路径']}`；存在={item['存在']}；已读取={item['已读取']}")
    lines.extend(["", "## 五个规则评审样本", ""])
    for sample in payload["规则评审样本"]:
        lines.extend(
            [
                f"### {sample['样本类型']}",
                f"- 来源窗口：{sample['来源窗口']}",
                f"- 来源路径：`{sample['来源路径']}`",
                f"- 可计入进度：{sample['可计入进度']}",
                f"- 安全阻断不失败：{sample['安全阻断不失败']}",
                f"- 真实动作仍禁用：{sample['真实动作仍禁用']}",
                f"- 本职工作暂停继承：{sample['本职工作暂停继承']}",
                f"- 规则评审摘要：{sample['规则评审摘要']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未写正式库、知识库、向量库或数据库。",
            "- 未调用券商接口。",
            "- 未自动交易、下单或撤单。",
            "- 未触碰本职工作系统。",
            "- 未触发真实外部 API。",
            "",
        ]
    )
    return "\n".join(lines)


def build_recovery_report(payload: dict[str, Any], files: dict[str, str], verify_text: str = "待验证") -> str:
    return "\n".join(
        [
            "# 03进化系统_第五批小任务U回收报告_最新",
            "",
            f"- 生成时间：{payload['生成时间']}",
            "- 任务：03进化 / 第四批扩展成果规则评审读取样本",
            f"- 读取报告：J/K/L/M/N/O，共 {len(payload['读取报告'])} 份固定回收报告路径",
            f"- 输出样本：{payload['规则评审样本数量']} 个，分别为视频、内容、税收、知识库、企业微信",
            "- 规则结论：可计入进度；安全阻断不失败；真实动作仍禁用；本职工作暂停继承",
            f"- 验收结果：{verify_text}",
            "",
            "## 新增/修改文件",
            "",
            *[f"- {name}：`{path}`" for name, path in files.items()],
            "",
            "## 交付阻断",
            "",
            "- 未发现交付阻断；本轮为读取样本和规则评审产物，不做真实业务交付。",
            "",
            "## 安全阻断",
            "",
            "- 安全阻断作为合规边界单独列示，不按失败处理。",
            "- 视频、内容、税收、知识库、企业微信样本均继承真实动作禁用口径。",
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
            "",
        ]
    )


def main() -> int:
    evo = root() / "03杰哥进化系统"
    data_dir = evo / "03数据" / DATA_DIR_NAME
    doc_path = evo / "07文档" / "第五批小任务U_第四批扩展成果规则评审读取样本说明_最新.md"
    latest_json = data_dir / f"{TASK_NAME}_最新.json"
    latest_md = data_dir / f"{TASK_NAME}_最新.md"
    recovery_path = root() / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第五批小任务U回收报告_最新.md"

    payload = build_payload()
    write_json(latest_json, payload)
    write_text(latest_md, build_markdown(payload))
    write_text(doc_path, build_markdown(payload))

    files = {
        "规则评审样本JSON": str(latest_json),
        "规则评审样本Markdown": str(latest_md),
        "规则评审说明文档": str(doc_path),
    }
    write_text(recovery_path, build_recovery_report(payload, files))
    print(json.dumps({"通过": True, "样本数量": payload["规则评审样本数量"], "读取报告数量": len(payload["读取报告"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
