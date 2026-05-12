# -*- coding: utf-8 -*-
"""
Name: 生成股票专项质量状态卡.py
System: 00杰哥系统总管 / 02脚本
Purpose: 汇总股票系统三阶段日报质量、【杰哥推荐】学习链路、19300/19302服务能力和安全边界，形成总管可读的股票专项状态卡。
Trigger: 手动或总管巡检；可接入后续计划任务。
Dependencies: 股票日报质量评分_最新.json；杰哥推荐方法学习链路验收_最新.json；本机19300/19302健康页。
Output: 00杰哥系统总管/03数据/股票专项质量状态卡/股票专项质量状态卡_最新.json 与 .md。
Safety: 只读本地文件和127.0.0.1健康页；不触发n8n，不发送企业微信，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
MANAGER_ROOT = SYSTEM_ROOT / "00杰哥系统总管"
STOCK_ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "01股票研究系统"
OUT_DIR = MANAGER_ROOT / "03数据" / "股票专项质量状态卡"

STOCK_QUALITY_PATH = STOCK_ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票日报质量评分_最新.json"
LEARNING_CHECK_PATH = STOCK_ROOT / "03数据" / "277杰哥推荐方法学习链路验收" / "杰哥推荐方法学习链路验收_最新.json"
WORKFLOW_CHECK_PATH = STOCK_ROOT / "03数据" / "274杰哥推荐方法工作流固化验收" / "杰哥推荐方法工作流总控巡检_最新.json"
CALIBRATION_CHECK_PATH = STOCK_ROOT / "03数据" / "278杰哥推荐方法内核校准" / "杰哥推荐方法内核校准报告_最新.json"
MATERIAL_PACKAGE_PATH = STOCK_ROOT / "03数据" / "275杰哥推荐单股分析材料包" / "单股分析材料包_最新.json"
REPORT_CREDIBILITY_PATH = STOCK_ROOT / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.json"
REPORT_CALIBER_CHECK_PATH = STOCK_ROOT / "03数据" / "183报告数据口径检查" / "股票报告数据口径检查_最新.json"
REPORT_SOURCE_MAPPING_PATH = STOCK_ROOT / "03数据" / "219股票报告证据源映射" / "股票报告证据源映射预览_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_local_json(url: str, timeout: int = 5) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        return {"状态": "不可达", "错误": str(exc), "地址": url}


def status_level(stock_quality: dict[str, Any], learning: dict[str, Any], health19300: dict[str, Any], health19302: dict[str, Any]) -> str:
    if health19300.get("状态") != "正常" or health19302.get("状态") != "正常":
        return "block"
    if learning.get("结论") != "通过":
        return "block"
    if stock_quality.get("不合格点"):
        return "warning"
    return "pass"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票专项质量状态卡",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 股票日报质量：{report['股票日报质量']['评分结论']}",
        f"- 杰哥推荐学习链路：{report['杰哥推荐学习链路']['结论']}",
        "",
        "## 一、服务能力",
        "",
        f"- 19300股票助手：{report['服务状态']['19300股票助手'].get('状态')}；候选识别数量={report['服务状态']['19300股票助手'].get('杰哥推荐候选识别数量')}",
        f"- 19302企微桥接：{report['服务状态']['19302企微桥接'].get('状态')}",
        "",
        "## 二、股票日报不合格点",
        "",
    ]
    issues = report["股票日报质量"].get("不合格点", [])
    if issues:
        for index, item in enumerate(issues, start=1):
            lines.append(f"{index}. 【{item.get('阶段')}】{item.get('检查项')}：{item.get('证据')}")
    else:
        lines.append("- 无")

    lines.extend(["", "## 三、杰哥推荐学习链路", ""])
    learning = report["杰哥推荐学习链路"]
    lines.append(f"- 学习链路验收：{learning.get('结论')}")
    lines.append(f"- 工作流总控：{report['工作流总控'].get('结论')}")
    calibration = report["方法内核校准"]
    lines.append(
        f"- 方法内核校准：存在={calibration.get('存在')}；候选数量={calibration.get('候选数量')}；"
        f"P0冲突样本={calibration.get('P0冲突样本数')}；重点关注候选={calibration.get('重点关注候选')}；"
        f"重点关注待验证={calibration.get('重点关注待验证')}"
    )
    lines.append(f"- 单股材料包：存在={report['单股材料包'].get('存在')}；生成时间={report['单股材料包'].get('生成时间')}")
    credibility = report.get("报告可信度面板", {})
    lines.append(
        f"- 报告可信度面板：存在={credibility.get('存在')}；覆盖L5={credibility.get('覆盖L5数量')}；"
        f"平均可信度={credibility.get('平均可信度分')}；前台反推待优化={credibility.get('前台反推待优化数量')}"
    )
    caliber = report.get("报告数据口径检查", {})
    lines.append(
        f"- 报告数据口径检查：存在={caliber.get('存在')}；状态={caliber.get('状态')}；"
        f"严重问题={caliber.get('严重问题数')}；提示={caliber.get('提示数')}"
    )
    mapping = report.get("报告证据源映射", {})
    lines.append(
        f"- 报告证据源映射：存在={mapping.get('存在')}；映射数量={mapping.get('映射数量')}；缺口数量={mapping.get('缺口数量')}"
    )
    if learning.get("失败检查项"):
        for item in learning.get("失败检查项", [])[:8]:
            lines.append(f"- 失败项：{item.get('名称')}；{item.get('说明', '')}")
    else:
        lines.append("- 未发现失败项")

    lines.extend(
        [
            "",
            "## 四、安全边界",
            "",
            "- 未真实发送企业微信。",
            "- 未触发n8n。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未输出买卖指令。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    stock_quality = load_json(STOCK_QUALITY_PATH, {}) or {}
    learning = load_json(LEARNING_CHECK_PATH, {}) or {}
    workflow = load_json(WORKFLOW_CHECK_PATH, {}) or {}
    calibration = load_json(CALIBRATION_CHECK_PATH, {}) or {}
    material = load_json(MATERIAL_PACKAGE_PATH, {}) or {}
    report_credibility = load_json(REPORT_CREDIBILITY_PATH, {}) or {}
    report_caliber = load_json(REPORT_CALIBER_CHECK_PATH, {}) or {}
    source_mapping = load_json(REPORT_SOURCE_MAPPING_PATH, {}) or {}
    health19300 = get_local_json("http://127.0.0.1:19300/health")
    health19302 = get_local_json("http://127.0.0.1:19302/health")
    overall = status_level(stock_quality, learning, health19300, health19302)

    report = {
        "名称": "股票专项质量状态卡",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": overall,
        "股票日报质量": {
            "路径": str(STOCK_QUALITY_PATH),
            "存在": STOCK_QUALITY_PATH.exists(),
            "评分结论": stock_quality.get("评分结论", "缺失"),
            "不合格数": len(stock_quality.get("不合格点", [])) if isinstance(stock_quality.get("不合格点"), list) else None,
            "不合格点": stock_quality.get("不合格点", []) if isinstance(stock_quality.get("不合格点"), list) else [],
        },
        "杰哥推荐学习链路": {
            "路径": str(LEARNING_CHECK_PATH),
            "存在": LEARNING_CHECK_PATH.exists(),
            "结论": learning.get("结论", "缺失"),
            "失败检查项": [
                item for item in learning.get("检查项", [])
                if isinstance(item, dict) and item.get("通过") is not True
            ] if isinstance(learning.get("检查项"), list) else [],
        },
        "工作流总控": {
            "路径": str(WORKFLOW_CHECK_PATH),
            "存在": WORKFLOW_CHECK_PATH.exists(),
            "结论": workflow.get("结论", "缺失"),
        },
        "方法内核校准": {
            "路径": str(CALIBRATION_CHECK_PATH),
            "存在": CALIBRATION_CHECK_PATH.exists(),
            "生成时间": calibration.get("生成时间", ""),
            "候选数量": (calibration.get("统计") or {}).get("候选数量", ""),
            "P0冲突样本数": (calibration.get("统计") or {}).get("P0冲突样本数", ""),
            "重点关注候选": ((calibration.get("统计") or {}).get("校准分层分布") or {}).get("重点关注候选", ""),
            "重点关注待验证": ((calibration.get("统计") or {}).get("校准分层分布") or {}).get("重点关注待验证", ""),
        },
        "单股材料包": {
            "路径": str(MATERIAL_PACKAGE_PATH),
            "存在": MATERIAL_PACKAGE_PATH.exists(),
            "生成时间": material.get("生成时间", ""),
            "方法": material.get("方法", ""),
        },
        "报告可信度面板": {
            "路径": str(REPORT_CREDIBILITY_PATH),
            "存在": REPORT_CREDIBILITY_PATH.exists(),
            "生成时间": report_credibility.get("生成时间", ""),
            "覆盖L5数量": report_credibility.get("覆盖L5数量", ""),
            "平均可信度分": report_credibility.get("平均可信度分", ""),
            "可信度分布": report_credibility.get("可信度分布", {}),
            "缺口优先级": report_credibility.get("缺口优先级", []),
            "前台反推待优化数量": len(report_credibility.get("前台报告反推待优化", [])) if isinstance(report_credibility.get("前台报告反推待优化"), list) else 0,
        },
        "报告数据口径检查": {
            "路径": str(REPORT_CALIBER_CHECK_PATH),
            "存在": REPORT_CALIBER_CHECK_PATH.exists(),
            "生成时间": report_caliber.get("生成时间", ""),
            "状态": report_caliber.get("状态", "缺失"),
            "严重问题数": report_caliber.get("严重问题数", ""),
            "提示数": report_caliber.get("提示数", ""),
        },
        "报告证据源映射": {
            "路径": str(REPORT_SOURCE_MAPPING_PATH),
            "存在": REPORT_SOURCE_MAPPING_PATH.exists(),
            "生成时间": source_mapping.get("生成时间", ""),
            "映射数量": len(source_mapping.get("字段证据映射", [])) if isinstance(source_mapping.get("字段证据映射"), list) else source_mapping.get("映射数量", ""),
            "缺口数量": len(source_mapping.get("正式依据缺口", [])) if isinstance(source_mapping.get("正式依据缺口"), list) else source_mapping.get("缺口数量", ""),
        },
        "服务状态": {
            "19300股票助手": health19300,
            "19302企微桥接": health19302,
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "输出买卖指令": False,
        },
    }

    json_path = OUT_DIR / "股票专项质量状态卡_最新.json"
    md_path = OUT_DIR / "股票专项质量状态卡_最新.md"
    write_json(json_path, report)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": overall, "JSON": str(json_path), "Markdown": str(md_path)}, ensure_ascii=False))
    return 0 if overall in {"pass", "warning"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
