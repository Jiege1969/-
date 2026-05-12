# -*- coding: utf-8 -*-
"""生成完全交付使用版低风险可推进拆单包。

仅从完全交付缺口路线图中提炼红线外、低风险、可继续推进的材料型任务。
本脚本只写入本包数据与日志，不触发外部系统，不开放任何红线。
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "68完全交付使用版低风险可推进拆单包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险可推进拆单包验收"

SOURCE_PACKAGE = (
    EVOLUTION_ROOT
    / "03数据"
    / "64完全交付使用版缺口拆解与红线解锁路线图包"
    / "完全交付使用版缺口拆解与红线解锁路线图包_最新.json"
)

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险可推进拆单包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险可推进拆单包_最新.md"
PACKAGE_CSV = DATA_DIR / "完全交付使用版低风险可推进拆单清单_最新.csv"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险可推进拆单包_最新.json"

SAFETY_BOUNDARY = {
    "不修改总管面板": True,
    "不修改一键接续包": True,
    "不修改生成日常可用版自主巡检快照": True,
    "不修改服务配置": True,
    "不重载19310": True,
    "不重载19302": True,
    "不真实发送企业微信": True,
    "不触发n8n": True,
    "不接券商或交易": True,
    "不登录税局或接财税软件": True,
    "不真实渲染或发布视频": True,
    "不转正式规则": True,
}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False, "路径": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        modules = data.get("缺口模块", [])
        return {
            "存在": True,
            "路径": str(path),
            "名称": data.get("名称"),
            "模块数": len(modules) if isinstance(modules, list) else 0,
            "结论": data.get("结论"),
        }
    except Exception as exc:  # noqa: BLE001 - 只读来源解析失败也要形成证据
        return {"存在": True, "路径": str(path), "解析失败": repr(exc)}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_items() -> list[dict[str, Any]]:
    return [
        {
            "编号": "LR-01",
            "拆单项": "文档交接增强",
            "来源依据": "完全交付缺口路线图中的使用者交付、人工确认闸口、非技术操作说明缺口",
            "目标": "补齐交付摘要、操作边界、人工接手点、失败后该看哪里四类交接说明。",
            "输入": ["现有交付摘要", "只读核对报告", "验收日志索引", "红线关闭清单"],
            "输出": ["交接增强清单", "非技术用户阅读版检查表", "人工接手点索引"],
            "验收": ["每个交接点有输入、输出、负责人或确认人占位", "不包含真实外部动作授权", "可被只读核对脚本引用"],
            "预计工时": "2h",
            "是否触红线": False,
            "推进方式": "文档整理与只读索引增强",
        },
        {
            "编号": "LR-02",
            "拆单项": "长周期样本",
            "来源依据": "完全交付缺口路线图中的长周期稳定样本不足",
            "目标": "设计跨自然日、跨异常、跨业务的只读样本记录模板，为后续人工验收提供连续证据。",
            "输入": ["历史只读巡检结果", "三日巡检样本模板", "异常恢复日志索引"],
            "输出": ["7日只读样本计划", "每日样本记录模板", "趋势汇总字段定义"],
            "验收": ["覆盖税收、股票、视频、规则治理等非真实动作样本", "每条样本只记录状态和证据路径", "不得调度真实任务"],
            "预计工时": "3h",
            "是否触红线": False,
            "推进方式": "只读样本设计",
        },
        {
            "编号": "LR-03",
            "拆单项": "异常样例扩展",
            "来源依据": "完全交付缺口路线图中的异常、恢复、回滚证据不足",
            "目标": "扩展可演练但不执行外部动作的异常样例，覆盖缺文件、字段缺失、依赖缺失、权限未授权等情况。",
            "输入": ["现有异常样例库", "失败自动分级规则", "只读核对脚本输出"],
            "输出": ["异常样例扩展表", "只读演练预期结果", "人工复核备注模板"],
            "验收": ["每个异常有触发条件、期望提示、恢复建议", "不要求真实发送、登录、交易、渲染", "可作为后续验证用例"],
            "预计工时": "2h",
            "是否触红线": False,
            "推进方式": "样例库补全",
        },
        {
            "编号": "LR-04",
            "拆单项": "只读核对覆盖",
            "来源依据": "完全交付缺口路线图中的多业务只读回归覆盖不足",
            "目标": "梳理只读核对覆盖矩阵，明确哪些文件、字段、日志、边界需要被验证。",
            "输入": ["现有生成包", "执行只读核对报告", "验证报告"],
            "输出": ["只读覆盖矩阵", "缺口补齐建议", "验收脚本检查项清单"],
            "验收": ["覆盖生成、执行、验证三段产物", "验证红线均关闭", "错误数为0时才允许通过"],
            "预计工时": "2h",
            "是否触红线": False,
            "推进方式": "本地文件结构与字段核对",
        },
        {
            "编号": "LR-05",
            "拆单项": "视频环境识别候选",
            "来源依据": "完全交付缺口路线图中的视频真实渲染发布红线未开放",
            "目标": "仅识别候选环境字段与人工确认项，不真实渲染、不连接发布账号。",
            "输入": ["本地视频草稿需求", "素材缺口清单", "人工确认字段"],
            "输出": ["视频环境识别候选表", "素材与版权确认字段", "发布前人工闸口清单"],
            "验收": ["只记录候选依赖和人工确认项", "不调用渲染命令", "不读取或提交发布账号凭据"],
            "预计工时": "2h",
            "是否触红线": False,
            "推进方式": "候选字段整理",
        },
        {
            "编号": "LR-06",
            "拆单项": "不触发真实渲染的依赖检测计划",
            "来源依据": "完全交付缺口路线图中的视频依赖确认不足但真实渲染禁止",
            "目标": "定义只读依赖检测计划，仅检查工具名、版本记录方式、缺失时提示，不运行渲染链路。",
            "输入": ["视频草稿包", "本地依赖候选清单", "人工测试说明"],
            "输出": ["依赖检测计划", "禁止动作清单", "缺失依赖提示模板"],
            "验收": ["计划中明确禁止真实渲染与发布", "检测项均为只读或人工填写", "后续执行需另设授权"],
            "预计工时": "1.5h",
            "是否触红线": False,
            "推进方式": "检测计划设计",
        },
        {
            "编号": "LR-07",
            "拆单项": "税收/股票/视频用户反馈样本模板",
            "来源依据": "完全交付缺口路线图中的用户反馈闭环样本不足",
            "目标": "为税收、股票、视频三类高风险业务准备脱敏反馈模板，只收集体验和结果描述。",
            "输入": ["用户反馈问题", "人工复核结果", "脱敏证据路径"],
            "输出": ["税收反馈模板", "股票反馈模板", "视频反馈模板", "共用字段字典"],
            "验收": ["模板不要求登录税局、连接券商、真实渲染发布", "包含脱敏说明", "包含是否需要人工复核字段"],
            "预计工时": "2h",
            "是否触红线": False,
            "推进方式": "反馈样本模板设计",
        },
    ]


def build_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 完全交付使用版低风险可推进拆单包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 来源包：{package['来源摘要'].get('路径')}",
        f"- 总结论：{package['结论']}",
        "",
        "## 拆单清单",
        "",
        "| 编号 | 拆单项 | 预计工时 | 是否触红线 | 输出 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in package["拆单项"]:
        lines.append(
            f"| {item['编号']} | {item['拆单项']} | {item['预计工时']} | "
            f"{str(item['是否触红线']).lower()} | {'；'.join(item['输出'])} |"
        )
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "本包只生成低风险拆单材料、只读核对材料和模板，不发送、不触发、不交易、不登录、不渲染发布、不转正式规则。",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["编号", "拆单项", "目标", "预计工时", "是否触红线", "推进方式"],
        )
        writer.writeheader()
        for item in items:
            writer.writerow({key: item[key] for key in writer.fieldnames})


def main() -> int:
    source_summary = read_json_if_exists(SOURCE_PACKAGE)
    items = build_items()
    package = {
        "名称": "完全交付使用版低风险可推进拆单包",
        "生成时间": now(),
        "性质": "红线外低风险可推进拆单包，仅用于文档、样本、模板、只读核对计划推进",
        "结论": "7项均为红线外低风险可推进项，可进入后续人工拆派或只读补强；不开放任何真实外部动作。",
        "来源摘要": source_summary,
        "安全边界": SAFETY_BOUNDARY,
        "拆单项": items,
        "验收口径": {
            "每项必备字段": ["目标", "输入", "输出", "验收", "预计工时", "是否触红线"],
            "是否触红线": False,
            "允许动作": ["生成文档", "生成模板", "只读核对", "本地字段验证"],
            "禁止动作": [
                "真实发送企业微信",
                "触发n8n",
                "连接券商或交易",
                "登录税局或接财税软件",
                "真实渲染或发布视频",
                "转正式规则",
            ],
        },
    }
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_markdown(package))
    write_csv(PACKAGE_CSV, items)
    write_json(
        GEN_LOG,
        {
            "名称": "生成完全交付使用版低风险可推进拆单包",
            "生成时间": now(),
            "状态": "pass",
            "输出": [str(PACKAGE_JSON), str(PACKAGE_MD), str(PACKAGE_CSV)],
            "拆单项数量": len(items),
            "红线结论": "未触红线",
        },
    )
    print(json.dumps({"状态": "pass", "拆单项数量": len(items), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
