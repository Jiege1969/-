# -*- coding: utf-8 -*-
"""
名称：验证最新锚点不回退旧流水.py
作用：核查关键准入/阶段判定脚本是否仍用旧时间戳流水作为当前依据。
触发方式：python 验证最新锚点不回退旧流水.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取脚本并写入验收报告；不执行被检查脚本；不删除文件；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建最新锚点不回退旧流水验收入口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
LOG_DIR = MANAGER / "04日志" / "制度化治理"

WATCH_FILES = [
    ROOT / "00杰哥系统总管" / "02脚本" / "生成日常可用版阶段报告.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成基础可用版完成判定报告.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "执行当前低风险自动推进队列.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "知识库检索.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "提交日常任务到人工确认队列.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "生成日常任务人工确认单.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "知识库" / "生成R02知识库单文档入库候选预检单.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库本地问答预演.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "知识库" / "验证知识库本地问答预演.py",
    ROOT / "01杰哥智能系统" / "02脚本" / "知识库" / "生成知识库系统状态摘要.py",
    ROOT / "02杰哥扩展系统" / "02视频制作系统" / "02脚本" / "生成视频制作系统状态摘要.py",
    ROOT / "02杰哥扩展系统" / "02视频制作系统" / "02脚本" / "验证视频制作系统状态摘要.py",
    ROOT / "02杰哥扩展系统" / "03本职工作系统" / "02脚本" / "生成本职工作系统状态摘要.py",
    ROOT / "02杰哥扩展系统" / "03本职工作系统" / "02脚本" / "验证本职工作系统状态摘要.py",
    ROOT / "02杰哥扩展系统" / "04内容处理系统" / "02脚本" / "生成内容处理系统状态摘要.py",
    ROOT / "02杰哥扩展系统" / "04内容处理系统" / "02脚本" / "验证内容处理系统状态摘要.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成股票四系统融合闭环状态面板.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "执行四系统小闭环开工快检.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成四系统股票小闭环状态面板.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "执行四系统股票小闭环.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成股票四系统闭环完成观察记录.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成四系统股票小闭环历史观察面板.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "验证四系统股票小闭环历史观察面板.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "维护" / "version_check.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "维护" / "generate_n8n_shadow_plan.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成旧口径冲突审计报告.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成施工前保护闸口报告.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "验证股票企业微信真实灰度回滚预案包汇总.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "验证股票企业微信真实灰度确认回执登记包汇总.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "验证股票助手n8n未激活导入人工确认回执模板汇总.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "生成股票助手首轮真实灰度测试消息样例.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "生成股票助手真实灰度高风险操作申请单模板.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "生成股票助手真实灰度执行手册草案.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "生成股票助手n8n未激活导入执行前只读核验包.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "同步L5AI报告到判断复盘账.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "生成300只候选评分因子拆解报告.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成攻坚队列门禁完成度汇总.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成小流量只读接入禁用态完成度汇总.py",
    ROOT / "00杰哥系统总管" / "02脚本" / "生成首批小流量批次预检总表.py",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "验证股票企业微信n8n适配器禁用态.py",
]

FORBIDDEN_SNIPPETS = [
    ".rglob(",
    ".glob(\"*",
    ".glob('*",
    "st_mtime",
    "任务队列演练_{",
    "任务队列_{",
    "日常任务人工确认单_{",
    "knowledge-local-qa-preview-{",
    "知识库本地问答预演_{",
    "knowledge-local-qa-preview-verify-{",
    "knowledge-system-status-summary-{",
    "知识库系统状态摘要_{",
    "video-production-system-status-summary-{",
    "视频制作系统状态摘要_{",
    "video-production-system-status-summary-verify-{",
    "office-work-system-status-summary-{",
    "本职工作系统状态摘要_{",
    "office-work-system-status-summary-verify-{",
    "content-processing-system-status-summary-{",
    "内容处理系统状态摘要_{",
    "content-processing-system-status-summary-verify-{",
    "股票四系统融合闭环状态面板_{",
    "四系统小闭环开工快检_{",
    "四系统股票小闭环状态面板_{",
    "四系统股票小闭环一键执行_{",
    "股票四系统闭环完成观察记录_{",
    "四系统股票小闭环历史观察面板_{",
    "four-system-stock-loop-history-panel-verify-{",
    "upgrade_check_{",
    "n8n_shadow_plan_{",
    "n8n_workflows_export_{",
    "old-contract-conflict-audit-{",
    "construction-protection-gate-{",
    "stock-wework-real-gray-rollback-plan-package-summary-verify-{",
    "stock-wework-real-gray-confirmation-receipt-package-summary-verify-{",
    "stock-assistant-n8n-inactive-import-human-confirmation-receipt-template-summary-verify-{",
    "股票助手首轮真实灰度测试消息样例_{",
    "股票助手真实灰度高风险操作申请单模板_{",
    "股票助手真实灰度执行手册草案_{",
    "股票助手n8n未激活导入执行前只读核验包_{",
    "L5AI报告同步判断复盘账_{",
    "300只候选评分因子拆解报告_{",
    "copy2(latest_",
    "JSONDecodeError",
    "continue\n        return {}",
    "sorted(parent.glob",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def scan_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"路径": str(path), "存在": False, "通过": False, "命中": ["文件不存在"]}
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = [snippet for snippet in FORBIDDEN_SNIPPETS if snippet in text]
    if path.name == "验证股票企业微信n8n适配器禁用态.py":
        hits = [hit for hit in hits if hit != "JSONDecodeError"]
    if path.name == "生成旧口径冲突审计报告.py":
        hits = [hit for hit in hits if hit != ".rglob("]
    return {
        "路径": str(path),
        "存在": True,
        "通过": not hits,
        "命中": hits,
    }


def build_report() -> dict[str, Any]:
    checks = [scan_file(path) for path in WATCH_FILES]
    failed = [item for item in checks if not item["通过"]]
    return {
        "名称": "最新锚点不回退旧流水验收",
        "验收时间": now_text(),
        "检查脚本数量": len(checks),
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查项": checks,
        "当前结论": "通过" if not failed else "未通过",
        "规则": [
            "准入和阶段判定只认固定最新锚点。",
            "最新锚点缺失或损坏时失败闭口，不回退旧时间戳流水。",
            "旧时间戳文件只能作为归档或审计资产，不参与当前放行依据。",
        ],
        "安全边界": {
            "未执行被检查脚本": True,
            "未删除文件": True,
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
        },
    }


def write_reports(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "最新锚点不回退旧流水验收_最新.json"
    md_path = OUT_DIR / "最新锚点不回退旧流水验收_最新.md"
    log_path = LOG_DIR / "latest-anchor-no-archive-fallback-verify-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    json_path.write_text(text, encoding="utf-8")
    log_path.write_text(text, encoding="utf-8")
    lines = [
        "# 最新锚点不回退旧流水验收",
        "",
        f"- 验收时间：{report['验收时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 检查脚本数量：{report['检查脚本数量']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查项",
    ]
    for item in report["检查项"]:
        status = "通过" if item["通过"] else "未通过"
        hits = "、".join(item["命中"]) if item["命中"] else "无"
        lines.append(f"- {status}：`{item['路径']}`；命中：{hits}")
    lines.extend(["", "## 规则"])
    lines.extend([f"- {item}" for item in report["规则"]])
    lines.extend([
        "",
        "## 安全边界",
        "- 只读检查脚本文本；未执行被检查脚本；未删除文件；未触发 n8n；未发送企业微信；未调用券商接口；未自动交易。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = build_report()
    write_reports(report)
    print(json.dumps({
        "状态": report["当前结论"],
        "检查脚本数量": report["检查脚本数量"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "输出": str(OUT_DIR / "最新锚点不回退旧流水验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if report["当前结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
