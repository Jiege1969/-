# -*- coding: utf-8 -*-
"""
名称：生成税收问题驱动取证任务包.py
作用：读取税收业务问题输入，离线生成场景识别、关键词、官方检索任务、证据台账模板、答案草案模板和人工复核单。
触发方式：python 生成税收问题驱动取证任务包.py
依赖：Python标准库；税收问题驱动取证工作流规则.json；税种分类规则.json；税收业务处理模板.json；税收政策来源.json；税收业务问题输入_最新.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只做离线任务包；不联网检索、不下载、不写正式政策库、不写向量库、不触发n8n、不推送企微、不向外部问答窗口提问、不生成正式税务结论。
创建/修改记录：2026-04-30 创建税收问题驱动取证任务包脚本。
标识：tax-question-driven-evidence-task-package
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def contains_any(text: str, words: list[str]) -> bool:
    return any(word and word in text for word in words)


def identify_taxes(question: str, tax_rules: dict[str, Any]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for item in tax_rules.get("税种", []):
        hit_words = [word for word in item.get("关键词", []) if word in question]
        if hit_words:
            matches.append(
                {
                    "税种": item.get("税种"),
                    "命中关键词": hit_words,
                    "常见业务场景": item.get("常见业务场景", [])
                }
            )
    if not matches:
        matches.append({"税种": "待人工判断", "命中关键词": [], "常见业务场景": []})
    return matches


def identify_scenes(question: str, rule: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = []
    for scene, words in rule.get("场景关键词", {}).items():
        hit_words = [word for word in words if word in question]
        if hit_words:
            scenes.append({"场景": scene, "命中关键词": hit_words})
    if not scenes:
        scenes.append({"场景": "待人工补充", "命中关键词": []})
    return scenes


def build_keywords(question: str, taxes: list[dict[str, Any]], scenes: list[dict[str, Any]]) -> list[str]:
    keywords: list[str] = []
    for item in taxes:
        if item.get("税种") != "待人工判断":
            keywords.append(str(item.get("税种")))
        keywords.extend(item.get("命中关键词", []))
    for item in scenes:
        keywords.append(str(item.get("场景")))
        keywords.extend(item.get("命中关键词", []))
    for word in ["纳税人", "税率", "征收率", "政策依据", "发票", "适用条件"]:
        if word in question and word not in keywords:
            keywords.append(word)
    deduped: list[str] = []
    for word in keywords:
        if word and word not in deduped:
            deduped.append(word)
    return deduped


def build_search_tasks(question: dict[str, Any], sources: dict[str, Any], keywords: list[str], rule: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    query = " ".join(keywords[:8])
    for index, source in enumerate(sources.get("官方来源", []), start=1):
        tasks.append(
            {
                "任务ID": f"SEARCH-{index:02d}",
                "来源名称": source.get("名称"),
                "入口地址": source.get("地址"),
                "用途": source.get("用途"),
                "建议检索词": query,
                "执行状态": "待执行",
                "是否允许自动联网": False,
                "是否允许自动下载": False,
                "输出要求": [
                    "记录候选标题、链接、发布日期、文号、来源名称。",
                    "非官方转载不得作为正式依据。",
                    "发现地方口径时必须登记地区。"
                ]
            }
        )
    tasks.append(
        {
            "任务ID": "SEARCH-LOCAL-QUESTION",
            "来源名称": "官方问答或地方税务局公开问答",
            "入口地址": "待人工选择官方入口",
            "用途": "寻找可参考问答案例或办税口径",
            "建议检索词": f"{query} 问答 案例 12366",
            "执行状态": "待人工确认入口后执行",
            "是否允许自动联网": False,
            "是否允许自动下载": False,
            "输出要求": [
                "只登记官方问答或地方税务局公开问答。",
                "不得自动向外部问答窗口提交真实问题。",
                "问答案例只能作为参考，不能替代政策文件。"
            ]
        }
    )
    return tasks


def build_evidence_template(question: dict[str, Any], tasks: list[dict[str, Any]], rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "问题编号": question.get("问题编号"),
        "业务问题": question.get("业务问题"),
        "证据状态": "待收集",
        "证据条目": [
            {
                "证据ID": f"EVD-{index:02d}",
                "对应检索任务ID": task.get("任务ID"),
                "来源名称": task.get("来源名称"),
                "标题": "待填写",
                "文号": "待填写",
                "发布日期": "待填写",
                "施行日期": "待填写",
                "有效状态": "待核实",
                "来源链接": "待填写",
                "本地保存路径": "待下载后填写",
                "是否官方来源": "待核实",
                "是否可作为正式依据候选": False,
                "人工复核状态": "待复核",
                "备注": ""
            }
            for index, task in enumerate(tasks, start=1)
        ],
        "安全边界": rule.get("安全边界", {})
    }


def build_answer_markdown(package: dict[str, Any]) -> str:
    question = package["问题输入"]
    lines = [
        "# 税收问题答案草案模板",
        "",
        f"生成时间：{package['生成时间']}",
        f"问题编号：{question.get('问题编号')}",
        "",
        "## 业务问题原文",
        "",
        str(question.get("业务问题", "")),
        "",
        "## 场景识别",
        "",
    ]
    for item in package.get("场景识别", []):
        lines.append(f"- {item.get('场景')}：命中 {', '.join(item.get('命中关键词', [])) or '待人工补充'}")
    lines.extend(["", "## 税种识别", ""])
    for item in package.get("税种识别", []):
        lines.append(f"- {item.get('税种')}：命中 {', '.join(item.get('命中关键词', [])) or '待人工判断'}")
    lines.extend(
        [
            "",
            "## 初步结论草案",
            "",
            "待官方依据收集和人工复核后填写。当前不得作为正式税务结论。",
            "",
            "## 适用条件",
            "",
            "- 待根据政策原文和业务事实填写。",
            "",
            "## 官方依据清单",
            "",
        ]
    )
    for task in package.get("官方检索任务", []):
        lines.append(f"- {task.get('任务ID')}：{task.get('来源名称')}；检索词：{task.get('建议检索词')}")
    lines.extend(
        [
            "",
            "## 本地证据路径",
            "",
            "- 待下载或登记后填写。",
            "",
            "## 风险点",
            "",
            "- 政策有效状态待核实。",
            "- 地方执行口径待核实。",
            "- 业务事实不足时不得形成确定判断。",
            "",
            "## 待人工复核事项",
            "",
            "- 事实要素是否完整。",
            "- 政策文件是否现行有效。",
            "- 问答案例是否仅作为参考。",
            "- 是否需要咨询主管税务机关或专业人员。",
            "",
            "## 声明",
            "",
            "本文件为答案草案模板，不是正式税务结论，不得直接用于对外申报、承诺或决策。",
            "",
        ]
    )
    return "\n".join(lines)


def build_review_markdown(package: dict[str, Any]) -> str:
    question = package["问题输入"]
    lines = [
        "# 税收问题人工复核单模板",
        "",
        f"生成时间：{package['生成时间']}",
        f"问题编号：{question.get('问题编号')}",
        "",
        "## 复核对象",
        "",
        f"- 业务问题：{question.get('业务问题')}",
        "- 答案草案：税收问题答案草案模板_最新.md",
        "- 证据台账：税收问题证据台账模板_最新.json",
        "",
        "## 复核清单",
        "",
        "- 事实要素是否完整：待复核",
        "- 税种识别是否正确：待复核",
        "- 官方依据是否充分：待复核",
        "- 政策有效状态是否确认：待复核",
        "- 地方执行口径是否需要补充：待复核",
        "- 问答案例是否仅作为参考：待复核",
        "- 初步结论是否超出证据范围：待复核",
        "",
        "## 复核结论",
        "",
        "- 复核人：",
        "- 复核时间：",
        "- 复核结论：待复核",
        "- 是否允许进入可复用案例库：否",
        "- 备注：",
        "",
    ]
    return "\n".join(lines)


def build_task_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 税收问题驱动取证任务包",
        "",
        f"生成时间：{package['生成时间']}",
        f"问题编号：{package['问题输入'].get('问题编号')}",
        "",
        "## 问题",
        "",
        str(package["问题输入"].get("业务问题", "")),
        "",
        "## 关键词",
        "",
        "- " + "、".join(package.get("关键词", [])),
        "",
        "## 官方检索任务",
        "",
    ]
    for task in package.get("官方检索任务", []):
        lines.append(f"- {task['任务ID']}：{task['来源名称']}；{task['建议检索词']}；状态：{task['执行状态']}")
    lines.extend(["", "## 产物", ""])
    for key, value in package.get("输出文件", {}).items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in package.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "税收问题驱动取证工作流规则.json"
    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    question_path = output_dir / rule["输出"]["问题输入模板"]
    if not question_path.exists():
        template_script = root / "02脚本" / "生成税收业务问题输入模板.py"
        raise RuntimeError(f"缺少问题输入模板，请先运行：python {template_script}")
    question = load_json(question_path)
    tax_rules = load_json(root / "01配置" / "税种分类规则.json")
    process_template = load_json(root / "01配置" / "税收业务处理模板.json")
    sources = load_json(root / "01配置" / "税收政策来源.json")
    question_text = str(question.get("业务问题", ""))
    taxes = identify_taxes(question_text, tax_rules)
    scenes = identify_scenes(question_text, rule)
    keywords = build_keywords(question_text, taxes, scenes)
    search_tasks = build_search_tasks(question, sources, keywords, rule)
    evidence = build_evidence_template(question, search_tasks, rule)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_latest = output_dir / rule["输出"]["任务包最新文件"]
    task_dated = output_dir / f"税收问题驱动取证任务包_{stamp}.json"
    task_md_latest = output_dir / rule["输出"]["任务包Markdown最新文件"]
    task_md_dated = output_dir / f"税收问题驱动取证任务包_{stamp}.md"
    evidence_latest = output_dir / rule["输出"]["证据台账模板"]
    answer_latest = output_dir / rule["输出"]["答案草案模板"]
    review_latest = output_dir / rule["输出"]["人工复核单模板"]
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "问题输入文件": str(question_path),
        "问题输入": question,
        "税种识别": taxes,
        "场景识别": scenes,
        "关键词": keywords,
        "事实采集字段": process_template.get("事实采集字段", []),
        "处理流程": process_template.get("处理流程", []),
        "官方检索任务": search_tasks,
        "资料下载计划": {
            "当前状态": "待官方检索任务产生候选链接后，再进入下载清单和下载闸口。",
            "是否允许自动下载": False,
            "关联工具": [
                "税收人工入口资料下载器.py",
                "生成税收人工入口资料下载选择模板.py",
                "税收人工入口资料下载闸口.py"
            ]
        },
        "输出文件": {
            "任务包JSON": str(task_latest),
            "任务包Markdown": str(task_md_latest),
            "证据台账模板": str(evidence_latest),
            "答案草案模板": str(answer_latest),
            "人工复核单模板": str(review_latest)
        },
        "安全边界": rule.get("安全边界", {}),
        "结论": "已离线生成问题驱动官方取证任务包；当前不联网、不下载、不生成正式税务结论。"
    }
    write_json(task_dated, package)
    write_json(task_latest, package)
    task_markdown = build_task_markdown(package)
    write_text(task_md_dated, task_markdown)
    write_text(task_md_latest, task_markdown)
    write_json(evidence_latest, evidence)
    write_text(answer_latest, build_answer_markdown(package))
    write_text(review_latest, build_review_markdown(package))
    print(json.dumps({"税种": [item.get("税种") for item in taxes], "场景数量": len(scenes), "检索任务数量": len(search_tasks), "输出": str(task_latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
