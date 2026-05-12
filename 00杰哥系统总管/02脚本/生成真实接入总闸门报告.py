"""
名称：生成真实接入总闸门报告.py
作用：汇总总体验收、阶段判定、旧系统保护、日常可用版和稳定中台结果，生成真实接入前总闸门报告。
触发方式：python 生成真实接入总闸门报告.py
依赖：Python 标准库；真实接入总闸门规则.json；各验收日志。
所属系统：00杰哥系统总管
安全边界：只读检查并生成门禁报告；不抓取真实业务；不启用Webhook；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实接入前总闸门报告脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [item for item in root.rglob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def latest_json(root: Path, pattern: str) -> tuple[Path | None, dict[str, Any]]:
    path = latest_file(root, pattern)
    return (path, load_json(path)) if path else (None, {})


def pass_count(data: dict[str, Any]) -> tuple[int | None, int | None]:
    summary = data.get("summary") or data.get("汇总") or data.get("姹囨€?") or {}
    total = summary.get("total") or summary.get("项目总数") or summary.get("文件数")
    failed = summary.get("failed") or summary.get("失败") or 0
    return total, failed


def make_check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rules = load_json(manager / "01配置" / "真实接入总闸门规则.json")
    acceptance_path, acceptance = latest_json(manager / "04日志", "v3-acceptance-最新.json")
    stage_path, stage = latest_json(manager / "03数据" / "阶段判定", "基础可用版完成判定_最新.json")
    old_path, old_protection = latest_json(manager / "04日志", "old-system-protection-verify-最新.json")
    first_batch_path, first_batch = latest_json(manager / "04日志", "first-batch-n8n-controlled-verify-最新.json")
    daily_entry_path, daily_entry = latest_json(manager / "04日志", "daily-usable-entry-verify-最新.json")
    daily_queue_path, daily_queue = latest_json(manager / "04日志", "daily-task-entry-queue-verify-最新.json")
    daily_confirm_path, daily_confirm = latest_json(manager / "04日志", "daily-task-confirmation-verify-最新.json")
    stable_heartbeat_path, stable_heartbeat = latest_json(manager / "04日志", "stable-hub-heartbeat-verify-最新.json")
    stable_diagnosis_path, stable_diagnosis = latest_json(manager / "04日志", "stable-hub-diagnosis-plan-verify-最新.json")
    stable_patrol_path, stable_patrol = latest_json(manager / "04日志", "stable-hub-patrol-verify-最新.json")
    hard_switches = rules.get("硬性关闭开关", {})
    total, failed = pass_count(acceptance)
    checks = [
        make_check("v3总体验收全绿", failed == 0 and total is not None, {"路径": str(acceptance_path), "总数": total, "失败": failed}),
        make_check("基础可用版完成", stage.get("完成判定") == "基础可用版已完成，可进入真实接入前讨论", {"路径": str(stage_path), "阶段进度": stage.get("阶段性工作进度百分比"), "总体进度": stage.get("总体进度估算百分比")}),
        make_check("旧系统保护通过", pass_count(old_protection)[1] == 0 and old_path is not None, str(old_path)),
        make_check("第一批n8n受控启用闭环通过", pass_count(first_batch)[1] == 0 and first_batch_path is not None, str(first_batch_path)),
        make_check("日常入口通过", pass_count(daily_entry)[1] == 0 and daily_entry_path is not None, str(daily_entry_path)),
        make_check("日常任务队列通过", pass_count(daily_queue)[1] == 0 and daily_queue_path is not None, str(daily_queue_path)),
        make_check("人工确认链通过", pass_count(daily_confirm)[1] == 0 and daily_confirm_path is not None, str(daily_confirm_path)),
        make_check("稳定中台心跳通过", pass_count(stable_heartbeat)[1] == 0 and stable_heartbeat_path is not None, str(stable_heartbeat_path)),
        make_check("稳定中台诊断通过", pass_count(stable_diagnosis)[1] == 0 and stable_diagnosis_path is not None, str(stable_diagnosis_path)),
        make_check("稳定中台巡检通过", pass_count(stable_patrol)[1] == 0 and stable_patrol_path is not None, str(stable_patrol_path)),
        make_check("硬性关闭开关全部关闭", all(value is False for value in hard_switches.values()), hard_switches),
        make_check("税收业务保持暂停", hard_switches.get("允许税收业务接入") is False, hard_switches.get("允许税收业务接入")),
        make_check("旧系统保持只读保护", hard_switches.get("允许旧系统写入") is False and hard_switches.get("允许删除或迁移旧系统文件") is False, {"允许旧系统写入": hard_switches.get("允许旧系统写入"), "允许删除或迁移旧系统文件": hard_switches.get("允许删除或迁移旧系统文件")}),
    ]
    failed_checks = [item for item in checks if item["结果"] != "通过"]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "real-access-master-gate",
        "阶段": rules.get("阶段"),
        "总闸门结论": "真实接入保持关闭；允许继续只读评审和回滚准备" if not failed_checks else "真实接入前门禁未通过",
        "候选接入层级": rules.get("候选接入层级", []),
        "优先候选场景": rules.get("优先候选场景", []),
        "硬性关闭开关": hard_switches,
        "检查结果": checks,
        "汇总": {"通过": len(checks) - len(failed_checks), "失败": len(failed_checks)},
        "下一步": [
            "继续保持Webhook、企业微信真实发送、税收业务和旧系统写入关闭",
            "为股票研究公开数据只读探测生成小流量方案",
            "为知识库、本地办公材料、视频素材处理分别建立回滚清单",
            "真实执行前必须重新跑总体验收和本总闸门验证",
        ],
    }
    output_dir = manager / "03数据" / "真实接入闸门"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "真实接入总闸门_最新.json"
    latest = output_dir / "真实接入总闸门_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"结论": report["总闸门结论"], "通过": report["汇总"]["通过"], "失败": report["汇总"]["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
