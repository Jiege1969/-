# -*- coding: utf-8 -*-
"""
名称：执行内生能力分层只读检查.py
作用：只读检查四大系统和重点子系统是否具备内生能力证据。
触发方式：python 执行内生能力分层只读检查.py
安全边界：只读扫描目录名和文件名，仅在03进化系统03数据输出检查报告；不触发n8n，不发送企业微信，不写正式库，不重启服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUTPUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "50内生能力分层只读检查"
LATEST_JSON = OUTPUT_DIR / "内生能力分层只读检查_最新.json"
LATEST_MD = OUTPUT_DIR / "内生能力分层只读检查_最新.md"


TARGETS = [
    {"层级": "四大系统", "名称": "00杰哥系统总管", "路径": ROOT / "00杰哥系统总管"},
    {"层级": "四大系统", "名称": "01杰哥智能系统", "路径": ROOT / "01杰哥智能系统"},
    {"层级": "四大系统", "名称": "02杰哥扩展系统", "路径": ROOT / "02杰哥扩展系统"},
    {"层级": "四大系统", "名称": "03杰哥进化系统", "路径": ROOT / "03杰哥进化系统"},
    {"层级": "扩展子系统", "名称": "股票研究系统", "路径": ROOT / "02杰哥扩展系统" / "01股票研究系统"},
    {"层级": "扩展子系统", "名称": "孵化区", "路径": ROOT / "02杰哥扩展系统" / "02-00孵化区"},
    {"层级": "扩展子系统", "名称": "视频制作系统", "路径": ROOT / "02杰哥扩展系统" / "02视频制作系统"},
    {"层级": "扩展子系统", "名称": "本职工作系统", "路径": ROOT / "02杰哥扩展系统" / "03本职工作系统"},
    {"层级": "扩展子系统", "名称": "内容处理系统", "路径": ROOT / "02杰哥扩展系统" / "04内容处理系统"},
    {"层级": "扩展子系统", "名称": "税收业务系统", "路径": ROOT / "02杰哥扩展系统" / "05税收业务系统"},
    {"层级": "公共通讯适配层", "名称": "企业微信接入设置", "路径": ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置"},
    {"层级": "扩展子系统", "名称": "知识库系统", "路径": ROOT / "02杰哥扩展系统" / "07知识库系统"},
]


CAPABILITIES = {
    "目标定位": ["规划", "总纲", "目标", "定位", "说明", "契约", "README"],
    "层级服从": ["层级", "上位", "依据", "规则", "母本", "契约"],
    "输入输出契约": ["输入", "输出", "接口", "入口", "路由", "schema", "模板"],
    "感知反馈": ["自检", "巡检", "health", "状态", "日志", "回执", "报告"],
    "调度协同": ["调度", "队列", "依赖", "拓扑", "接续", "分流", "路由"],
    "边界免疫": ["边界", "红线", "只读", "禁用", "暂停", "blocked", "门禁", "免疫"],
    "问题修复": ["问题", "根因", "修复", "复验", "失败", "回收", "阻断"],
    "记忆进化": ["进化", "复盘", "沉淀", "规则", "样本", "归档", "接续"],
    "用户可感知闭环": ["交付", "验收", "可用", "用户", "总览", "展示", "回复"],
}


def iter_file_names(root: Path, limit: int = 5000) -> list[str]:
    if not root.exists():
        return []
    names: list[str] = []
    for idx, path in enumerate(root.rglob("*")):
        if idx >= limit:
            break
        if path.is_file():
            names.append(path.name)
        elif path.is_dir():
            names.append(path.name)
    return names


def basic_dirs(root: Path) -> dict[str, bool]:
    return {
        "01配置": (root / "01配置").exists(),
        "02脚本": (root / "02脚本").exists(),
        "03数据": (root / "03数据").exists(),
        "04日志": (root / "04日志").exists(),
        "07文档": (root / "07文档").exists(),
    }


def capability_result(names: list[str], keywords: list[str]) -> dict[str, Any]:
    hits = []
    for name in names:
        lowered = name.lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            hits.append(name)
        if len(hits) >= 8:
            break
    return {
        "状态": "present" if hits else "missing",
        "证据数量": len(hits),
        "证据样例": hits,
    }


def inspect_target(target: dict[str, Any]) -> dict[str, Any]:
    root = Path(target["路径"])
    names = iter_file_names(root)
    dirs = basic_dirs(root)
    capabilities = {key: capability_result(names, words) for key, words in CAPABILITIES.items()}
    present = sum(1 for item in capabilities.values() if item["状态"] == "present")
    missing = [key for key, item in capabilities.items() if item["状态"] != "present"]
    structure_missing = [name for name, exists in dirs.items() if not exists]
    status = "pass" if root.exists() and present >= 7 and not structure_missing else "needs_attention"
    return {
        "层级": target["层级"],
        "名称": target["名称"],
        "路径": str(root),
        "存在": root.exists(),
        "基础目录": dirs,
        "能力": capabilities,
        "汇总": {
            "状态": status,
            "已见证据能力数": present,
            "总能力数": len(CAPABILITIES),
            "缺少证据能力": missing,
            "结构关注项": structure_missing,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 内生能力分层只读检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 目标数量：{report['汇总']['目标数量']}",
        f"- 通过数量：{report['汇总']['通过数量']}",
        f"- 需关注数量：{report['汇总']['需关注数量']}",
        "",
        "| 层级 | 系统 | 状态 | 已见证据能力数 | 缺少证据能力 | 结构关注项 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["检查结果"]:
        missing = "、".join(item["汇总"]["缺少证据能力"]) or "无"
        structure = "、".join(item["汇总"]["结构关注项"]) or "无"
        lines.append(
            f"| {item['层级']} | {item['名称']} | {item['汇总']['状态']} | "
            f"{item['汇总']['已见证据能力数']}/{item['汇总']['总能力数']} | {missing} | {structure} |"
        )
    lines.extend([
        "",
        "## 说明",
        "",
        "- 本检查只依据目录和文件名做低风险能力证据扫描，不读取业务秘密、不触发服务。",
        "- `present` 代表已有可追踪证据，不代表正式上线或能力完全成熟。",
        "- `missing` 代表当前未从文件名证据中识别到该能力，需要后续补文档、回执、检查项或脚本证据。",
        "",
        "## 安全边界",
        "",
        "- 不触发 n8n，不发送企业微信。",
        "- 不写正式库，不调用券商接口或交易。",
        "- 不办理税务，不发布视频，不重启正式服务。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    results = [inspect_target(target) for target in TARGETS]
    passed = [item for item in results if item["汇总"]["状态"] == "pass"]
    needs = [item for item in results if item["汇总"]["状态"] != "pass"]
    report = {
        "类型": "internalized-capability-layered-readonly-check",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not needs else "needs_attention",
        "汇总": {
            "目标数量": len(results),
            "通过数量": len(passed),
            "需关注数量": len(needs),
        },
        "检查结果": results,
        "安全边界": {
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口或交易": False,
            "办理税务": False,
            "发布视频": False,
            "重启正式服务": False,
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "总体状态": report["总体状态"],
        "通过": len(passed),
        "需关注": len(needs),
        "输出": str(LATEST_JSON),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
