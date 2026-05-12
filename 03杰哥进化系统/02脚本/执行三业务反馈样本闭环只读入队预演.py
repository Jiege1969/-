# -*- coding: utf-8 -*-
"""执行三业务反馈样本闭环只读入队预演。

只读取本包示例样本并生成候选入队预演结果；不写正式规则、不改运行配置、
不触发企业微信、n8n、券商、税局、财税软件或视频发布链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"

PACKAGE_JSON = DATA_DIR / "三业务反馈样本闭环只读入队与候选生成包_最新.json"
SAMPLE_JSON = DATA_DIR / "三业务反馈示例样本_最新.json"
PREVIEW_JSON = DATA_DIR / "候选入队预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "候选入队预演结果_最新.md"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_SAMPLE_FIELDS = {
    "样本ID",
    "来源",
    "业务线",
    "输入原文",
    "系统输出摘要",
    "用户判定",
    "问题类型",
    "建议动作",
    "是否触红线",
    "是否可自动吸收",
    "需人工确认",
}
FORBIDDEN_TRUE_FLAGS = {
    "真实发送企业微信",
    "接n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载服务",
    "触发业务接口",
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check_sample(sample: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_SAMPLE_FIELDS - set(sample))
    if missing:
        errors.append(f"{sample.get('样本ID', 'UNKNOWN')} 缺少字段：{', '.join(missing)}")
    if sample.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{sample.get('样本ID', 'UNKNOWN')} 业务线不在三业务范围内")
    if sample.get("是否可自动吸收") is not False:
        errors.append(f"{sample.get('样本ID', 'UNKNOWN')} 是否可自动吸收必须为 false")
    if sample.get("需人工确认") is not True:
        errors.append(f"{sample.get('样本ID', 'UNKNOWN')} 需人工确认必须为 true")
    return errors


def build_candidate(sample: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "候选ID": f"QUEUE-CANDIDATE-{index:03d}",
        "来源": sample["来源"],
        "来源样本ID": sample["样本ID"],
        "业务线": sample["业务线"],
        "问题类型": sample["问题类型"],
        "建议动作": sample["建议动作"],
        "需人工确认": True,
        "是否可自动吸收": False,
        "转正式规则": False,
        "候选状态": "只读入队预演",
        "允许动作": ["写入本包候选预演结果", "等待人工确认"],
        "禁止动作": ["真实发送企业微信", "接n8n", "接券商", "交易", "登录税局", "接财税软件", "自动转正式规则", "修改运行配置", "触发业务接口"],
    }


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# 候选入队预演结果",
        "",
        f"- 预演时间：{report['预演时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 错误数：{report['错误数']}",
        f"- 候选数：{report['汇总']['候选数']}",
        "",
        "| 候选ID | 来源样本ID | 业务线 | 问题类型 | 需人工确认 | 转正式规则 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["候选条目"]:
        lines.append(
            f"| {item['候选ID']} | {item['来源样本ID']} | {item['业务线']} | {item['问题类型']} | "
            f"{str(item['需人工确认']).lower()} | {str(item['转正式规则']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    sample_bundle = read_json(SAMPLE_JSON) if SAMPLE_JSON.exists() else {}

    if package.get("状态") != "three_business_feedback_readonly_queue_candidate_ready":
        errors.append("生成包状态必须为 three_business_feedback_readonly_queue_candidate_ready")
    if package.get("默认不自动吸收") is not True:
        errors.append("生成包必须声明默认不自动吸收")
    if package.get("不转正式规则") is not True:
        errors.append("生成包必须声明不转正式规则")

    safety_boundary = package.get("安全边界", {})
    for flag in sorted(FORBIDDEN_TRUE_FLAGS):
        if safety_boundary.get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    samples = sample_bundle.get("样本列表", [])
    businesses = {item.get("业务线") for item in samples}
    if businesses != REQUIRED_BUSINESSES:
        errors.append("示例样本必须且只覆盖税收、股票、视频")
    if len(samples) < 3:
        errors.append("示例样本不得少于 3 条")

    for sample in samples:
        errors.extend(check_sample(sample))

    candidates = [build_candidate(sample, index) for index, sample in enumerate(samples, 1)] if not errors else []
    report = {
        "名称": "三业务反馈样本闭环只读入队预演",
        "预演时间": now_text(),
        "总体状态": "pass" if not errors else "fail",
        "错误数": len(errors),
        "错误": errors,
        "只读预演": True,
        "读取范围": [str(PACKAGE_JSON), str(SAMPLE_JSON)],
        "未触发动作": sorted(FORBIDDEN_TRUE_FLAGS),
        "覆盖业务": sorted(businesses),
        "默认不自动吸收": all(item.get("是否可自动吸收") is False for item in samples),
        "不转正式规则": all(item.get("转正式规则") is False for item in candidates),
        "候选条目": candidates,
        "汇总": {
            "样本数": len(samples),
            "候选数": len(candidates),
            "需人工确认数": sum(1 for item in candidates if item.get("需人工确认") is True),
            "失败": len(errors),
        },
        "输出文件": {
            "候选入队预演结果JSON": str(PREVIEW_JSON),
            "候选入队预演结果Markdown": str(PREVIEW_MD),
        },
    }
    write_json(PREVIEW_JSON, report)
    write_text(PREVIEW_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "错误数": report["错误数"], "候选数": len(candidates), "输出": str(PREVIEW_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
