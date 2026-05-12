from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "五样本政策事件缺口队列_最新.json"
RESULT_JSON = DATA_DIR / "五样本政策事件缺口队列验收_最新.json"
RESULT_MD = DATA_DIR / "五样本政策事件缺口队列验收_最新.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_task(task: dict) -> list[str]:
    errors = []
    name = task.get("stock", {}).get("name", "<unknown>")
    required = [
        "stock",
        "classification",
        "priority",
        "matched_policy_events",
        "matched_event_count",
        "policy_score_allowed",
        "policy_score_action",
        "review_focus",
        "missing",
        "front_wording",
        "redline_blocking"
    ]
    for key in required:
        if key not in task:
            errors.append(f"{name}: 缺少字段 {key}")
    if task.get("matched_event_count", 0) == 0 and task.get("policy_score_allowed") is True:
        errors.append(f"{name}: 无匹配事件不得允许政策分")
    if task.get("matched_event_count", 0) > 0 and not task.get("matched_policy_events"):
        errors.append(f"{name}: matched_event_count与明细不一致")
    redline = " ".join(task.get("redline_blocking", []))
    for phrase in ["未入库政策不得参与L3政策分", "无股票暴露度映射不得给单股政策分", "不得凭空补政策强度"]:
        if phrase not in redline:
            errors.append(f"{name}: 红线缺少 {phrase}")
    front = task.get("front_wording", "")
    if task.get("policy_score_allowed") is False and "未" not in front and "待补" not in front:
        errors.append(f"{name}: 无政策分时前台口径必须说明缺口")
    return errors


def render_md(result: dict) -> str:
    lines = [
        "# 五样本政策事件缺口队列验收",
        "",
        f"- 验收时间：{result['validated_at']}",
        f"- 验收结果：{result['status']}",
        f"- 覆盖任务：{result['task_count']}",
        f"- 错误数量：{len(result['errors'])}",
        "",
        "## 任务明细",
        "",
        "| 股票 | 分类 | 匹配事件数 | 允许政策分 |",
        "|---|---|---:|---|"
    ]
    for item in result["tasks"]:
        allowed = "是" if item["policy_score_allowed"] else "否"
        lines.append(f"| {item['stock']} | {item['classification']} | {item['matched_event_count']} | {allowed} |")
    if result["errors"]:
        lines.extend(["", "## 错误", ""])
        lines.extend([f"- {err}" for err in result["errors"]])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 未触发外部抓取",
        "- 未写入政策事件库",
        "- 未改L3评分",
        "- 未发送企业微信",
        "- 未重启服务",
        "- 未调用券商接口",
        "- 未自动交易"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    queue = read_json(QUEUE_JSON)
    tasks = queue.get("tasks", [])
    errors = []
    if len(tasks) != 5:
        errors.append("tasks 数量必须为5")
    for key in ["not_formal_config", "not_entrypoint", "not_external_send", "not_external_fetch", "not_policy_event_write", "not_score_write"]:
        if queue.get(key) is not True:
            errors.append(f"queue.{key} 必须为 true")
    for key in ["not_n8n", "not_external_send", "not_external_fetch", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_policy_event_write", "not_score_write", "not_broker_interface", "not_auto_trade"]:
        if queue.get("safety_boundary", {}).get(key) is not True:
            errors.append(f"safety_boundary.{key} 必须为 true")
    for task in tasks:
        errors.extend(validate_task(task))

    result = {
        "名称": "五样本政策事件缺口队列验收",
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if not errors else "failed",
        "task_count": len(tasks),
        "errors": errors,
        "tasks": [
            {
                "stock": task.get("stock", {}).get("name", ""),
                "code": task.get("stock", {}).get("code", ""),
                "classification": task.get("classification", ""),
                "matched_event_count": task.get("matched_event_count", 0),
                "policy_score_allowed": task.get("policy_score_allowed", False)
            }
            for task in tasks
        ],
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_external_fetch": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_delete_or_move_old_assets": True,
            "not_formal_database_write": True,
            "not_policy_event_write": True,
            "not_score_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(RESULT_JSON, result)
    RESULT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "task_count": len(tasks),
        "errors": len(errors),
        "result_json": str(RESULT_JSON),
        "result_md": str(RESULT_MD)
    }, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
