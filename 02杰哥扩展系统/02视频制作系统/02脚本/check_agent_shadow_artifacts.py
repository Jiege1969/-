# -*- coding: utf-8 -*-
"""只读检查智能体影子层产物完整性。

检查器只读取本地文件并生成本地自检报告，不触发外部系统。
"""

from __future__ import annotations

from pathlib import Path

from agent_shadow_common import ARCHIVE_ROOT, SHADOW_ROOT, write_artifact


REQUIRED_NAMES = [
    "会话记忆最小字段清单",
    "局部修正锁定字段样例",
    "发布前最终门禁摘要模板",
    "任务回溯索引影子样例",
    "企业微信命令缺口卡",
    "影子工厂最小闭环演练报告模板",
    "成品预览回执影子样例",
    "AI标识人工确认回执样例",
    "平台规则字段待补清单",
    "发布后链接回写影子样例",
    "素材授权证明占位样例",
    "智能体影子层下一轮候选队列",
    "视频创作智能体能力映射",
    "对话意图分类表",
    "局部修正指令卡",
    "多版本预览策略",
    "大模型接入前置条件清单",
    "企业微信命令影子解析样例",
    "会话状态契约",
    "意图路由影子器",
    "局部修正闭环影子器",
    "外部引擎适配契约",
    "人工门禁升级清单",
    "企业微信视频助理影子收发格式",
    "渲染前问题卡",
    "发布前问题卡",
    "视频助理影子命令回执样例",
    "任务状态推进影子样例",
    "智能体影子层索引",
    "影子命令解析最小样例输入包",
    "人工复核页摘要模板",
    "连续施工边界检查清单",
    "视频影子工厂每日自检摘要模板",
    "智能体影子层成熟度快照",
    "企业微信视频助理安全命令白名单",
]


def forbidden_terms() -> list[str]:
    return [
        "requests",
        "url" + "lib",
        "http" + ".client",
        "sub" + "process",
        "socket",
        "selenium",
        "play" + "wright",
    ]


def file_exists(name: str, suffix: str) -> bool:
    return (SHADOW_ROOT / f"{name}_最新.{suffix}").exists()


def archive_exists(name: str, suffix: str) -> bool:
    return any(ARCHIVE_ROOT.glob(f"{name}_*.{suffix}"))


def scan_script_terms(script_dir: Path) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    terms = forbidden_terms()
    for path in script_dir.glob("generate_*shadow*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        found = [term for term in terms if term in text]
        if found:
            hits[path.name] = found
    for path in [
        script_dir / "generate_wecom_video_assistant_io_contract.py",
        script_dir / "generate_execution_precheck_cards.py",
        script_dir / "generate_engine_adapter_contract.py",
        script_dir / "generate_manual_gate_upgrade_checklist.py",
    ]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        found = [term for term in terms if term in text]
        if found:
            hits[path.name] = found
    return hits


def build() -> dict:
    missing_latest: list[str] = []
    missing_archive: list[str] = []
    for name in REQUIRED_NAMES:
        if not file_exists(name, "md") or not file_exists(name, "json"):
            missing_latest.append(name)
        if not archive_exists(name, "md") or not archive_exists(name, "json"):
            missing_archive.append(name)

    script_hits = scan_script_terms(Path(__file__).resolve().parent)
    passed = not missing_latest and not missing_archive and not script_hits
    return {
        "报告名称": "智能体影子层连续施工只读检查报告",
        "检查范围": REQUIRED_NAMES,
        "latest缺失": missing_latest,
        "archive缺失": missing_archive,
        "脚本禁止项命中": script_hits,
        "检查结论": "通过" if passed else "需复核",
        "真实系统触发": False,
        "边界确认": [
            "只读扫描本地文件。",
            "未读取企业微信公共接入配置。",
            "未发送企业微信。",
            "未触发真实模型、素材、渲染或发布。",
        ],
    }


def main() -> int:
    report = build()
    write_artifact("智能体影子层连续施工只读检查报告", "智能体影子层连续施工只读检查报告", report)
    print(report["检查结论"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
