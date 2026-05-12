# -*- coding: utf-8 -*-
"""生成低风险只读调度器交接班摘要与未完成项继承包。

只生成本地交接班摘要、未完成项继承样例和不发送/不恢复证明；
不发送通知，不触发 n8n，不自动恢复任务，不写正式规则。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "117低风险只读调度器交接班摘要与未完成项继承包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "低风险只读调度器交接班摘要与未完成项继承包验收"

SUMMARY_JSON = DATA_DIR / "交接班摘要_最新.json"
SUMMARY_MD = DATA_DIR / "交接班摘要_最新.md"
INHERIT_JSON = DATA_DIR / "未完成项继承清单_最新.json"
INHERIT_MD = DATA_DIR / "未完成项继承清单_最新.md"
NO_ACTION_JSON = DATA_DIR / "不发送不恢复证明_最新.json"
NO_ACTION_MD = DATA_DIR / "不发送不恢复证明_最新.md"
PACKAGE_JSON = DATA_DIR / "低风险只读调度器交接班摘要与未完成项继承包_最新.json"
PACKAGE_MD = DATA_DIR / "低风险只读调度器交接班摘要与未完成项继承包_最新.md"
GENERATE_LOG = LOG_DIR / "low-risk-readonly-scheduler-handoff-inheritance-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safety_flags() -> dict[str, Any]:
    return {
        "readonly_only": True,
        "local_file_only": True,
        "handoff_summary_only": True,
        "inheritance_preview_only": True,
        "send_allowed": False,
        "real_send": False,
        "real_wecom_send": False,
        "network_request": False,
        "no_network_request": True,
        "connect_n8n": False,
        "trigger_n8n": False,
        "no_n8n_trigger": True,
        "auto_resume_task": False,
        "auto_schedule_task": False,
        "write_formal_rule": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_service": False,
        "delete_business_artifact": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_summary(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "低风险只读调度器交接班摘要",
        "生成时间": generated_at,
        "版本": "v1-local-readonly-handoff",
        "交接班窗口": {
            "当前班次": "日内值守收口",
            "接班班次": "下一轮只读接续",
            "接续方式": "本地文件继承，不注册真实计划任务",
        },
        "本班已完成": [
            "只读调度器连续干跑、漂移复核、红线失败注入、本地值守摘要等前置包已形成验收链路。",
            "第十五轮并行调度索引已登记本包为 ROUND15-AR。",
            "本包只落地 117 数据目录，不占用 113 历史目录。",
        ],
        "本班暂停项": [
            "企业微信真实发送继续暂停。",
            "n8n、webhook、系统计划任务注册继续暂停。",
            "任何自动恢复未完成任务、自动跨日执行或写正式规则动作继续暂停。",
        ],
        "接班关注": [
            "复核未完成项继承清单是否仍全部为本地预演。",
            "接班后只能继续只读汇总和人工确认队列整理。",
            "如需要真实通知、真实调度或自动恢复，必须先取得总管明确确认。",
        ],
        "验收口径": [
            "数据目录必须为 117低风险只读调度器交接班摘要与未完成项继承包。",
            "验证日志必须写入固定日志目录。",
            "所有外部动作、自动恢复和正式规则写入字段必须为 false。",
        ],
        **safety_flags(),
    }


def build_inheritance(generated_at: str) -> dict[str, Any]:
    items = [
        {
            "编号": "HI-001",
            "未完成项": "跨日值守样本后续复核",
            "来源": "第十五轮跨日值守样本并行调度索引包",
            "继承方式": "登记为下一轮只读待办",
            "当前动作": "仅生成本地继承记录",
            "允许自动恢复": False,
            "需总管确认": True,
        },
        {
            "编号": "HI-002",
            "未完成项": "异常升级草案人工确认队列复查",
            "来源": "低风险只读调度器异常升级草案与总管确认队列包",
            "继承方式": "保留人工确认队列入口",
            "当前动作": "仅记录需复查字段",
            "允许自动恢复": False,
            "需总管确认": True,
        },
        {
            "编号": "HI-003",
            "未完成项": "本地值守摘要补充人工口径",
            "来源": "低风险只读调度器本地值守摘要与不发送通知包",
            "继承方式": "生成接班备注",
            "当前动作": "只读补充摘要，不发送通知",
            "允许自动恢复": False,
            "需总管确认": False,
        },
        {
            "编号": "HI-004",
            "未完成项": "证据留存到期检查预演",
            "来源": "第十五轮 AS 待执行项",
            "继承方式": "登记后续只读检查",
            "当前动作": "不删除、不移动、不压缩业务产物",
            "允许自动恢复": False,
            "需总管确认": True,
        },
    ]
    return {
        "名称": "低风险只读调度器未完成项继承清单",
        "生成时间": generated_at,
        "继承项数量": len(items),
        "低风险只读可继续项数量": sum(1 for item in items if item["需总管确认"] is False),
        "需总管确认项数量": sum(1 for item in items if item["需总管确认"] is True),
        "继承项": items,
        **safety_flags(),
    }


def build_no_action_proof(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "低风险只读调度器不发送不恢复证明",
        "生成时间": generated_at,
        "证明范围": "本包只生成本地交接班材料和未完成项继承预演，不外发、不触发、不恢复。",
        "证据": [
            "通知类内容仅以本地 Markdown/JSON 形式保存。",
            "未完成项全部标记为允许自动恢复=false。",
            "脚本仅使用 pathlib/json/hashlib/datetime 等本地标准库。",
            "未读取任何消息通道密钥、n8n 凭据、券商、税局或财税软件凭据。",
        ],
        **safety_flags(),
    }


def summary_md(summary: dict[str, Any]) -> str:
    lines = [
        "# 低风险只读调度器交接班摘要",
        "",
        f"- 生成时间：{summary['生成时间']}",
        "- 结论：本包只用于本地交接班，不发送通知，不触发 n8n，不自动恢复任务。",
        "",
        "## 本班已完成",
        "",
        *[f"- {item}" for item in summary["本班已完成"]],
        "",
        "## 本班暂停项",
        "",
        *[f"- {item}" for item in summary["本班暂停项"]],
        "",
        "## 接班关注",
        "",
        *[f"- {item}" for item in summary["接班关注"]],
        "",
        "## 验收口径",
        "",
        *[f"- {item}" for item in summary["验收口径"]],
        "",
    ]
    return "\n".join(lines)


def inheritance_md(inheritance: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['未完成项']} | {item['来源']} | {item['继承方式']} | {item['允许自动恢复']} | {item['需总管确认']} |"
        for item in inheritance["继承项"]
    ]
    return "\n".join(
        [
            "# 未完成项继承清单",
            "",
            f"- 生成时间：{inheritance['生成时间']}",
            f"- 继承项数量：{inheritance['继承项数量']}",
            "",
            "| 编号 | 未完成项 | 来源 | 继承方式 | 允许自动恢复 | 需总管确认 |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def proof_md(proof: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 不发送不恢复证明",
            "",
            f"- 生成时间：{proof['生成时间']}",
            "- send_allowed: false",
            "- real_send: false",
            "- trigger_n8n: false",
            "- auto_resume_task: false",
            "- write_formal_rule: false",
            "",
            "## 证据",
            "",
            *[f"- {item}" for item in proof["证据"]],
            "",
        ]
    )


def package_md(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 低风险只读调度器交接班摘要与未完成项继承包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 数据目录：{package['数据目录']}",
            f"- 验收日志目录：{package['验收日志目录']}",
            "- 结论：验收以 117 数据目录为准；未使用 113 目录。",
            "",
            "## 输出文件",
            "",
            *[f"- {name}: {path}" for name, path in package["输出文件"].items()],
            "",
            "## 安全边界",
            "",
            "- 不发送企业微信，不触发 n8n，不联网。",
            "- 不自动恢复任务，不注册真实调度，不写正式规则。",
            "- 不接券商、不交易、不登录税局、不接财税软件。",
            "- 不修改总管面板，不修改一键接续包，不重载服务。",
            "",
        ]
    )


def main() -> int:
    generated_at = now()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    summary = build_summary(generated_at)
    inheritance = build_inheritance(generated_at)
    proof = build_no_action_proof(generated_at)

    write_json(SUMMARY_JSON, summary)
    write_text(SUMMARY_MD, summary_md(summary))
    write_json(INHERIT_JSON, inheritance)
    write_text(INHERIT_MD, inheritance_md(inheritance))
    write_json(NO_ACTION_JSON, proof)
    write_text(NO_ACTION_MD, proof_md(proof))

    package = {
        "名称": "低风险只读调度器交接班摘要与未完成项继承包",
        "生成时间": generated_at,
        "状态": "low_risk_readonly_scheduler_handoff_inheritance_ready",
        "数据目录": str(DATA_DIR),
        "验收日志目录": str(LOG_DIR),
        "历史目录保护": {
            "113已被历史包占用": True,
            "本次写入113目录": False,
            "最终验收目录": str(DATA_DIR),
        },
        "指标": {
            "继承项数量": inheritance["继承项数量"],
            "低风险只读可继续项数量": inheritance["低风险只读可继续项数量"],
            "需总管确认项数量": inheritance["需总管确认项数量"],
        },
        "输出文件": {
            "交接班摘要JSON": str(SUMMARY_JSON),
            "交接班摘要Markdown": str(SUMMARY_MD),
            "未完成项继承清单JSON": str(INHERIT_JSON),
            "未完成项继承清单Markdown": str(INHERIT_MD),
            "不发送不恢复证明JSON": str(NO_ACTION_JSON),
            "不发送不恢复证明Markdown": str(NO_ACTION_MD),
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
        },
        **safety_flags(),
    }
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, package_md(package))

    file_hashes = {name: sha256_file(Path(path)) for name, path in package["输出文件"].items()}
    write_json(
        GENERATE_LOG,
        {
            "名称": "生成低风险只读调度器交接班摘要与未完成项继承包",
            "生成时间": now(),
            "通过": True,
            "错误数": 0,
            "数据目录": str(DATA_DIR),
            "未写入113目录": True,
            "文件哈希": file_hashes,
        },
    )
    print(json.dumps({"通过": True, "数据目录": str(DATA_DIR), "输出文件数": len(package["输出文件"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
