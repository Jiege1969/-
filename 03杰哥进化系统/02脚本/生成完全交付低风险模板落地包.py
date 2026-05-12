# -*- coding: utf-8 -*-
"""生成完全交付低风险模板落地包。

仅把 68 包中的低风险拆单进一步落成模板文件；不触发外部系统，
不打开任何红线动作，不修改总管面板、一键接续包、服务配置或正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "72完全交付低风险模板落地包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付低风险模板落地包验收"
SOURCE_PACKAGE = (
    EVOLUTION_ROOT
    / "03数据"
    / "68完全交付使用版低风险可推进拆单包"
    / "完全交付使用版低风险可推进拆单包_最新.json"
)

PACKAGE_JSON = DATA_DIR / "完全交付低风险模板落地包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付低风险模板落地包_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付低风险模板落地包_最新.json"

TEMPLATE_FILES = {
    "用户反馈样本模板": DATA_DIR / "用户反馈样本模板_最新.json",
    "视频环境识别候选模板": DATA_DIR / "视频环境识别候选模板_最新.json",
    "只读核对扩展模板": DATA_DIR / "只读核对扩展模板_最新.json",
    "异常样例扩展模板": DATA_DIR / "异常样例扩展模板_最新.json",
    "文档交接增强模板": DATA_DIR / "文档交接增强模板_最新.json",
    "长周期样本记录模板": DATA_DIR / "长周期样本记录模板_最新.json",
}

TEMPLATE_MD_FILES = {
    name: DATA_DIR / f"{name}_最新.md" for name in TEMPLATE_FILES
}

REQUIRED_TEMPLATE_NAMES = list(TEMPLATE_FILES)

SAFETY_BOUNDARY = {
    "不修改总管面板": True,
    "不修改一键接续包": True,
    "不修改生成日常可用版自主巡检快照.py": True,
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
        items = data.get("拆单项", [])
        return {
            "存在": True,
            "路径": str(path),
            "名称": data.get("名称"),
            "拆单项数量": len(items) if isinstance(items, list) else 0,
            "结论": data.get("结论"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"存在": True, "路径": str(path), "解析失败": repr(exc)}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_template(
    name: str,
    source_split: str,
    purpose: str,
    inputs: list[str],
    outputs: list[str],
    acceptance: list[str],
    fields: list[dict[str, str]],
    sample_rows: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "模板名称": name,
        "生成时间": now(),
        "来源拆单": source_split,
        "用途": purpose,
        "输入": inputs,
        "输出": outputs,
        "验收": acceptance,
        "红线": False,
        "red_line": False,
        "红线说明": "false；本模板只用于本地文档、样本、字段和只读核对，不开放真实外部动作。",
        "字段": fields,
        "样例": sample_rows,
        "禁止动作": [
            "真实发送企业微信",
            "触发n8n",
            "连接券商或交易",
            "登录税局或接财税软件",
            "真实渲染或发布视频",
            "转正式规则",
            "重载19310或19302",
        ],
        "落地状态": "template_ready",
    }


def build_templates() -> list[dict[str, Any]]:
    return [
        make_template(
            "用户反馈样本模板",
            "税收/股票/视频用户反馈样本模板",
            "沉淀脱敏用户反馈字段，用于人工复核体验、结果和缺口，不要求登录或连接高风险系统。",
            ["业务类型", "用户问题", "人工复核结果", "脱敏证据路径", "是否需要人工复核"],
            ["反馈样本记录", "共用字段字典", "人工复核标记"],
            ["输入、输出、验收、红线字段齐全", "红线=false", "不包含登录税局、连接券商、真实渲染发布要求"],
            [
                {"字段": "业务类型", "说明": "税收/股票/视频/通用", "必填": "是"},
                {"字段": "反馈描述", "说明": "用户可读的脱敏反馈", "必填": "是"},
                {"字段": "脱敏证据路径", "说明": "本地只读证据路径或占位", "必填": "是"},
                {"字段": "人工复核状态", "说明": "待复核/已复核/不适用", "必填": "是"},
            ],
            [{"业务类型": "视频", "反馈描述": "素材缺口已脱敏记录", "人工复核状态": "待复核"}],
        ),
        make_template(
            "视频环境识别候选模板",
            "视频环境识别候选",
            "仅记录视频环境候选项和人工确认项，不运行渲染链路，不读取或提交发布账号凭据。",
            ["本地视频草稿需求", "素材缺口清单", "人工确认字段"],
            ["视频环境候选表", "素材与版权确认字段", "发布前人工闸口清单"],
            ["红线=false", "只登记候选依赖和确认项", "不调用渲染、发布、账号读取动作"],
            [
                {"字段": "候选环境", "说明": "本地工具名或人工填写", "必填": "是"},
                {"字段": "素材版权状态", "说明": "待确认/已确认/不适用", "必填": "是"},
                {"字段": "发布账号检查", "说明": "固定为不读取不提交", "必填": "是"},
                {"字段": "人工闸口", "说明": "发布前必须人工确认", "必填": "是"},
            ],
            [{"候选环境": "本地草稿占位", "素材版权状态": "待确认", "发布账号检查": "不读取不提交"}],
        ),
        make_template(
            "只读核对扩展模板",
            "只读核对覆盖",
            "扩展生成、执行、验证三段产物的只读覆盖矩阵，只检查本地文件存在、字段完整、红线关闭。",
            ["现有生成包", "执行只读核对报告", "验证报告"],
            ["只读覆盖矩阵", "字段完整性清单", "红线关闭核对项"],
            ["覆盖生成/执行/验证三段", "每项均可只读核对", "红线=false 且错误数为0时通过"],
            [
                {"字段": "核对对象", "说明": "文件或模板名称", "必填": "是"},
                {"字段": "存在性检查", "说明": "pass/fail", "必填": "是"},
                {"字段": "字段完整检查", "说明": "pass/fail", "必填": "是"},
                {"字段": "红线检查", "说明": "必须为false", "必填": "是"},
            ],
            [{"核对对象": "用户反馈样本模板_最新.json", "存在性检查": "pass", "红线检查": "false"}],
        ),
        make_template(
            "异常样例扩展模板",
            "异常样例扩展",
            "扩展可演练但不执行外部动作的异常样例，覆盖缺文件、缺字段、依赖缺失、权限未授权等情形。",
            ["现有异常样例库", "失败分级规则", "只读核对输出"],
            ["异常样例扩展表", "只读演练预期结果", "人工复核备注模板"],
            ["每个异常有触发条件、期望提示、恢复建议", "红线=false", "不要求真实发送、登录、交易、渲染"],
            [
                {"字段": "异常类型", "说明": "缺文件/缺字段/依赖缺失/权限未授权", "必填": "是"},
                {"字段": "触发条件", "说明": "只读演练条件", "必填": "是"},
                {"字段": "期望提示", "说明": "用户可读提示", "必填": "是"},
                {"字段": "恢复建议", "说明": "人工处理建议", "必填": "是"},
            ],
            [{"异常类型": "缺字段", "触发条件": "模板缺少验收", "期望提示": "字段不完整"}],
        ),
        make_template(
            "文档交接增强模板",
            "文档交接增强",
            "补齐交付摘要、操作边界、人工接手点和失败后查看位置，方便非技术人员接手。",
            ["现有交付摘要", "只读核对报告", "验收日志索引", "红线关闭清单"],
            ["交接增强清单", "非技术用户阅读版检查表", "人工接手点索引"],
            ["每个交接点有输入、输出、确认人占位", "红线=false", "可被只读核对脚本引用"],
            [
                {"字段": "交接点", "说明": "交付节点名称", "必填": "是"},
                {"字段": "输入材料", "说明": "接手前需要看到的材料", "必填": "是"},
                {"字段": "输出材料", "说明": "接手后产物", "必填": "是"},
                {"字段": "确认人占位", "说明": "人工确认责任位", "必填": "是"},
            ],
            [{"交接点": "只读核对完成", "输入材料": "核对报告", "输出材料": "验收结论"}],
        ),
        make_template(
            "长周期样本记录模板",
            "长周期样本",
            "设计跨自然日、跨异常、跨业务的只读样本记录模板，为后续人工验收提供连续证据。",
            ["历史只读巡检结果", "三日巡检样本模板", "异常恢复日志索引"],
            ["7日只读样本计划", "每日样本记录模板", "趋势汇总字段定义"],
            ["覆盖税收、股票、视频、规则治理等非真实动作样本", "红线=false", "每条样本只记录状态和证据路径"],
            [
                {"字段": "样本日期", "说明": "自然日", "必填": "是"},
                {"字段": "业务域", "说明": "税收/股票/视频/规则治理/通用", "必填": "是"},
                {"字段": "只读状态", "说明": "pass/fail/blocked", "必填": "是"},
                {"字段": "证据路径", "说明": "本地只读证据或日志路径", "必填": "是"},
            ],
            [{"样本日期": "YYYY-MM-DD", "业务域": "规则治理", "只读状态": "pass"}],
        ),
    ]


def build_template_markdown(template: dict[str, Any]) -> str:
    lines = [
        f"# {template['模板名称']}",
        "",
        f"- 来源拆单：{template['来源拆单']}",
        f"- 用途：{template['用途']}",
        f"- 红线：{str(template['红线']).lower()}",
        "",
        "## 输入",
        *[f"- {item}" for item in template["输入"]],
        "",
        "## 输出",
        *[f"- {item}" for item in template["输出"]],
        "",
        "## 验收",
        *[f"- {item}" for item in template["验收"]],
        "",
        "## 字段",
        "",
        "| 字段 | 说明 | 必填 |",
        "| --- | --- | --- |",
    ]
    for field in template["字段"]:
        lines.append(f"| {field['字段']} | {field['说明']} | {field['必填']} |")
    return "\n".join(lines)


def build_package(templates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "名称": "完全交付低风险模板落地包",
        "生成时间": now(),
        "性质": "68包低风险拆单的模板化落地包；仅生成本地模板与只读核对材料。",
        "来源摘要": read_json_if_exists(SOURCE_PACKAGE),
        "模板数量": len(templates),
        "模板清单": [
            {
                "模板名称": template["模板名称"],
                "模板文件": str(TEMPLATE_FILES[template["模板名称"]]),
                "说明文件": str(TEMPLATE_MD_FILES[template["模板名称"]]),
                "输入": template["输入"],
                "输出": template["输出"],
                "验收": template["验收"],
                "红线": template["红线"],
            }
            for template in templates
        ],
        "安全边界": SAFETY_BOUNDARY,
        "验收口径": {
            "必备模板": REQUIRED_TEMPLATE_NAMES,
            "模板必备字段": ["模板名称", "输入", "输出", "验收", "红线"],
            "红线": False,
            "错误数要求": 0,
        },
        "结论": "6个低风险模板均已落地为本地文件，红线=false，允许进入只读核对与验证。",
    }


def build_package_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 完全交付低风险模板落地包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 模板数量：{package['模板数量']}",
        f"- 结论：{package['结论']}",
        "",
        "| 模板 | 红线 | 文件 |",
        "| --- | --- | --- |",
    ]
    for item in package["模板清单"]:
        lines.append(f"| {item['模板名称']} | {str(item['红线']).lower()} | {item['模板文件']} |")
    lines.extend(["", "## 安全边界", ""])
    lines.extend(f"- {key}：{value}" for key, value in package["安全边界"].items())
    return "\n".join(lines)


def main() -> int:
    templates = build_templates()
    for template in templates:
        write_json(TEMPLATE_FILES[template["模板名称"]], template)
        write_text(TEMPLATE_MD_FILES[template["模板名称"]], build_template_markdown(template))

    package = build_package(templates)
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_markdown(package))

    log = {
        "名称": "生成完全交付低风险模板落地包",
        "生成时间": now(),
        "状态": "pass",
        "模板数量": len(templates),
        "红线": False,
        "输出": [str(PACKAGE_JSON), str(PACKAGE_MD), *[str(path) for path in TEMPLATE_FILES.values()]],
    }
    write_json(GEN_LOG, log)
    print(json.dumps({"状态": "pass", "模板数量": len(templates), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
