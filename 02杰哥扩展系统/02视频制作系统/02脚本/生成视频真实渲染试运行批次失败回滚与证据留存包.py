# -*- coding: utf-8 -*-
"""
生成视频真实渲染试运行批次失败回滚与证据留存包。

本脚本只读取第24包预检与白名单未生效闸口产物，并写入第25包材料。
不调用 MoneyPrinterTurbo，不执行 magick，不真实渲染，不生成真实视频，
不上传发布，不接 n8n，不改企业微信公共配置、总管面板、一键接续包或服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE24_DIR = ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包"
DATA_DIR = ROOT / "03数据" / "25真实渲染试运行批次失败回滚与证据留存包"

SOURCE24_PACKAGE = SOURCE24_DIR / "视频真实渲染试运行批次预检与白名单未生效闸口包_最新.json"
SOURCE24_PRECHECK = SOURCE24_DIR / "视频真实渲染试运行批次预检_最新.json"
SOURCE24_GATE = SOURCE24_DIR / "视频真实渲染白名单未生效闸口_最新.json"
SOURCE24_SIGNOFF = SOURCE24_DIR / "视频真实渲染试运行批次人工签收清单_最新.json"
SOURCE24_READONLY = SOURCE24_DIR / "视频真实渲染试运行批次只读预检报告_最新.json"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚与证据留存包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚与证据留存包_最新.md"
MATRIX_LATEST = DATA_DIR / "视频真实渲染试运行批次失败场景矩阵_最新.json"
MATRIX_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败场景矩阵_最新.md"
ROLLBACK_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚动作清单_最新.json"
ROLLBACK_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚动作清单_最新.md"
EVIDENCE_LATEST = DATA_DIR / "视频真实渲染试运行批次失败证据留存索引_最新.json"
EVIDENCE_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败证据留存索引_最新.md"

BATCH_ID = "TRIAL-FAILURE-ROLLBACK-20260508-001"
TASK_ID = "TRIAL-FAILURE-TASK-20260508-001"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_or_empty(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def guarded_status(generated_at: str) -> dict[str, Any]:
    flags = {
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
        "real_render": False,
        "generate_real_video": False,
        "publish": False,
        "upload_publish": False,
        "call_money_printer_turbo": False,
        "execute_magick": False,
        "execute_magick_version": False,
        "trigger_n8n": False,
        "modify_wecom_public_config": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_pack": False,
        "reload_service": False,
    }
    return {
        "生成时间": generated_at,
        "error_count": 0,
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
        "real_render": False,
        "publish": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "触发n8n": False,
        "修改企业微信公共配置": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "重载服务": False,
        "readonly_flags_ascii": flags,
    }


def source24_snapshot() -> dict[str, Any]:
    files = {
        "第24包总包": SOURCE24_PACKAGE,
        "第24包批次预检": SOURCE24_PRECHECK,
        "第24包白名单未生效闸口": SOURCE24_GATE,
        "第24包人工签收清单": SOURCE24_SIGNOFF,
        "第24包只读预检报告": SOURCE24_READONLY,
    }
    docs = {name: load_json(path) for name, path in files.items()}
    return {
        "来源说明": "承接第24视频包：真实渲染试运行批次预检与白名单未生效闸口包",
        "来源文件": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_or_empty(path),
                "error_count": docs[name].get("error_count"),
                "batch_allowed": docs[name].get("batch_allowed"),
                "whitelist_effective": docs[name].get("whitelist_effective"),
                "trial_run_allowed": docs[name].get("trial_run_allowed"),
                "can_enter_real_render": docs[name].get("can_enter_real_render"),
                "real_render": docs[name].get("real_render"),
                "publish": docs[name].get("publish"),
                "真实渲染": docs[name].get("真实渲染"),
                "上传发布": docs[name].get("上传发布"),
            }
            for name, path in files.items()
        },
    }


def build_failure_matrix(generated_at: str) -> dict[str, Any]:
    scenarios = [
        {
            "scenario_id": "FAIL-ENV-UNAVAILABLE",
            "失败场景": "环境不可用",
            "触发条件": "真实渲染候选环境、依赖或只读识别结果不可满足试运行要求。",
            "失败原因": "环境不可用，不能进入试运行批次。",
            "闸口动作": "保持批次关闭，仅登记失败证据。",
        },
        {
            "scenario_id": "FAIL-MATERIAL-MISSING",
            "失败场景": "素材缺失",
            "触发条件": "任务素材、授权凭据、分镜素材匹配或低风险测试素材任一缺失。",
            "失败原因": "素材缺失，不能形成可验收试运行输入。",
            "闸口动作": "保持只读状态，等待人工补齐素材证据。",
        },
        {
            "scenario_id": "FAIL-WHITELIST-INACTIVE",
            "失败场景": "白名单未生效",
            "触发条件": "第24包确认 whitelist_effective=false 且 trial_run_allowed=false。",
            "失败原因": "白名单未生效，试运行仍未获授权。",
            "闸口动作": "阻止进入真实渲染，保留第24包前置快照。",
        },
        {
            "scenario_id": "FAIL-OUTPUT-UNWRITABLE",
            "失败场景": "输出目录不可写",
            "触发条件": "隔离输出目录未创建、无写入权限或与生产目录边界不清。",
            "失败原因": "输出目录不可写或隔离边界不足。",
            "闸口动作": "不创建真实视频产物，不清理生产目录。",
        },
        {
            "scenario_id": "FAIL-MANUAL-REJECTED",
            "失败场景": "生成后人工否决",
            "触发条件": "人工签收状态为 rejected，或人工复核明确否决试运行样例。",
            "失败原因": "生成后人工否决，不能发布或复用为生产输入。",
            "闸口动作": "仅记录否决证据和签收状态，不重试真实渲染。",
        },
    ]
    for item in scenarios:
        item.update(
            {
                "batch_allowed": False,
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "real_render": False,
                "publish": False,
                "证据要求": ["批次ID", "任务ID", "前置快照", "失败原因", "人工签收状态", "留存期限"],
            }
        )
    result = {
        "名称": "视频真实渲染试运行批次失败场景矩阵",
        "批次ID": BATCH_ID,
        "任务ID": TASK_ID,
        "矩阵状态": "active_as_dry_run_evidence_only",
        "失败场景数量": len(scenarios),
        "失败场景矩阵": scenarios,
    }
    result.update(guarded_status(generated_at))
    return result


def build_rollback_actions(generated_at: str, matrix: dict[str, Any]) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for index, scenario in enumerate(matrix["失败场景矩阵"], start=1):
        actions.append(
            {
                "action_id": f"ROLLBACK-DRY-{index:02d}",
                "关联场景": scenario["scenario_id"],
                "动作名称": f"{scenario['失败场景']}失败回滚登记",
                "dry_run_only": True,
                "删除真实文件": False,
                "清理生产目录": False,
                "重试真实渲染": False,
                "真实渲染": False,
                "发布": False,
                "动作步骤": [
                    "冻结当前试运行批次状态为 batch_allowed=false。",
                    "记录失败原因、前置快照和人工签收状态。",
                    "登记待人工复核事项，签收状态保持 unsigned。",
                    "保留证据索引，不删除、不清理、不重试、不发布。",
                ],
                "允许写入范围": [str(DATA_DIR)],
                "禁止动作": [
                    "调用 MoneyPrinterTurbo",
                    "执行 magick 或 magick -version",
                    "真实渲染",
                    "生成真实视频",
                    "上传发布",
                    "接 n8n",
                    "修改企业微信公共配置",
                    "修改总管面板",
                    "修改一键接续包",
                    "重载服务",
                ],
            }
        )
    result = {
        "名称": "视频真实渲染试运行批次失败回滚动作清单",
        "批次ID": BATCH_ID,
        "任务ID": TASK_ID,
        "清单状态": "dry_run_only",
        "动作数量": len(actions),
        "全部动作dry_run_only": all(item["dry_run_only"] is True for item in actions),
        "全部动作不删除真实文件": all(item["删除真实文件"] is False for item in actions),
        "全部动作不清理生产目录": all(item["清理生产目录"] is False for item in actions),
        "全部动作不重试真实渲染": all(item["重试真实渲染"] is False for item in actions),
        "回滚动作清单": actions,
    }
    result.update(guarded_status(generated_at))
    return result


def build_evidence_index(generated_at: str, matrix: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    retention_days = 180
    retention_until = (datetime.now() + timedelta(days=retention_days)).strftime("%Y-%m-%d")
    result = {
        "名称": "视频真实渲染试运行批次失败证据留存索引",
        "批次ID": BATCH_ID,
        "任务ID": TASK_ID,
        "前置快照": snapshot,
        "失败原因": [
            {
                "scenario_id": item["scenario_id"],
                "失败场景": item["失败场景"],
                "失败原因": item["失败原因"],
            }
            for item in matrix["失败场景矩阵"]
        ],
        "人工签收状态": "unsigned",
        "留存期限": {
            "retention_days": retention_days,
            "retention_until": retention_until,
            "说明": "不少于180天；如人工复核要求更长留存期，以人工复核要求为准。",
        },
        "证据项": [
            {"名称": "失败场景矩阵JSON", "path": str(MATRIX_LATEST), "required": True},
            {"名称": "失败场景矩阵MD", "path": str(MATRIX_MD_LATEST), "required": True},
            {"名称": "回滚动作清单JSON", "path": str(ROLLBACK_LATEST), "required": True},
            {"名称": "回滚动作清单MD", "path": str(ROLLBACK_MD_LATEST), "required": True},
            {"名称": "证据留存索引JSON", "path": str(EVIDENCE_LATEST), "required": True},
            {"名称": "证据留存索引MD", "path": str(EVIDENCE_MD_LATEST), "required": True},
        ],
    }
    result.update(guarded_status(generated_at))
    return result


def build_package(
    generated_at: str,
    matrix: dict[str, Any],
    rollback: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行批次失败回滚与证据留存包",
        "包版本": "25",
        "批次ID": BATCH_ID,
        "任务ID": TASK_ID,
        "承接上一轮": "第24视频包：真实渲染试运行批次预检与白名单未生效闸口包",
        "包结论": "白名单仍未生效；本包仅建立失败回滚和证据留存材料，不真实渲染。",
        "产物": {
            "失败场景矩阵": str(MATRIX_LATEST),
            "回滚动作清单": str(ROLLBACK_LATEST),
            "证据留存索引": str(EVIDENCE_LATEST),
        },
        "摘要": {
            "失败场景数量": matrix["失败场景数量"],
            "回滚动作数量": rollback["动作数量"],
            "人工签收状态": evidence["人工签收状态"],
            "留存期限": evidence["留存期限"],
        },
    }
    result.update(guarded_status(generated_at))
    return result


def markdown_matrix(matrix: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次失败场景矩阵",
        "",
        f"- 批次ID：{matrix['批次ID']}",
        f"- 任务ID：{matrix['任务ID']}",
        "- batch_allowed：false",
        "- whitelist_effective：false",
        "- trial_run_allowed：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "",
        "| 场景ID | 失败场景 | 失败原因 | 闸口动作 |",
        "| --- | --- | --- | --- |",
    ]
    for item in matrix["失败场景矩阵"]:
        lines.append(f"| {item['scenario_id']} | {item['失败场景']} | {item['失败原因']} | {item['闸口动作']} |")
    return "\n".join(lines) + "\n"


def markdown_rollback(rollback: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次失败回滚动作清单",
        "",
        f"- 批次ID：{rollback['批次ID']}",
        f"- 任务ID：{rollback['任务ID']}",
        "- 全部动作 dry_run_only：true",
        "- 删除真实文件：false",
        "- 清理生产目录：false",
        "- 重试真实渲染：false",
        "",
        "| 动作ID | 关联场景 | dry_run_only | 禁止真实动作 |",
        "| --- | --- | --- | --- |",
    ]
    for item in rollback["回滚动作清单"]:
        lines.append(f"| {item['action_id']} | {item['关联场景']} | true | 删除/清理/重试/渲染/发布均为 false |")
    return "\n".join(lines) + "\n"


def markdown_evidence(evidence: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次失败证据留存索引",
        "",
        f"- 批次ID：{evidence['批次ID']}",
        f"- 任务ID：{evidence['任务ID']}",
        f"- 人工签收状态：{evidence['人工签收状态']}",
        f"- 留存期限：{evidence['留存期限']['retention_days']}天，至 {evidence['留存期限']['retention_until']}",
        "- batch_allowed：false",
        "- whitelist_effective：false",
        "- trial_run_allowed：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "",
        "## 失败原因",
        "",
    ]
    for item in evidence["失败原因"]:
        lines.append(f"- {item['scenario_id']}：{item['失败场景']}，{item['失败原因']}")
    lines.extend(["", "## 前置快照", ""])
    for name, info in evidence["前置快照"]["来源文件"].items():
        lines.append(f"- {name}：exists={str(info['exists']).lower()}，sha256={info['sha256']}")
    return "\n".join(lines) + "\n"


def markdown_package(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 视频真实渲染试运行批次失败回滚与证据留存包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 批次ID：{package['批次ID']}",
            f"- 任务ID：{package['任务ID']}",
            f"- 包结论：{package['包结论']}",
            "- error_count：0",
            "- batch_allowed：false",
            "- whitelist_effective：false",
            "- trial_run_allowed：false",
            "- can_enter_real_render：false",
            "- real_render：false",
            "- publish：false",
            "",
            "## 产物",
            "",
            f"- 失败场景矩阵：{package['产物']['失败场景矩阵']}",
            f"- 回滚动作清单：{package['产物']['回滚动作清单']}",
            f"- 证据留存索引：{package['产物']['证据留存索引']}",
        ]
    ) + "\n"


def write_with_timestamp(latest_path: Path, data: dict[str, Any], stamp: str) -> None:
    write_json(DATA_DIR / latest_path.name.replace("_最新.json", f"_{stamp}.json"), data)
    write_json(latest_path, data)


def main() -> int:
    generated_at = now_text()
    stamp = stamp_text()
    snapshot = source24_snapshot()
    matrix = build_failure_matrix(generated_at)
    rollback = build_rollback_actions(generated_at, matrix)
    evidence = build_evidence_index(generated_at, matrix, snapshot)
    package = build_package(generated_at, matrix, rollback, evidence)

    write_with_timestamp(MATRIX_LATEST, matrix, stamp)
    write_text(MATRIX_MD_LATEST, markdown_matrix(matrix))
    write_with_timestamp(ROLLBACK_LATEST, rollback, stamp)
    write_text(ROLLBACK_MD_LATEST, markdown_rollback(rollback))
    write_with_timestamp(EVIDENCE_LATEST, evidence, stamp)
    write_text(EVIDENCE_MD_LATEST, markdown_evidence(evidence))
    write_with_timestamp(PACKAGE_LATEST, package, stamp)
    write_text(PACKAGE_MD_LATEST, markdown_package(package))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "batch_allowed": False,
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "real_render": False,
                "publish": False,
                "error_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
