from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
QUEUE_JSON = DATA_DIR / "五样本行业价格连续观测补数队列_最新.json"
RESULT_JSON = DATA_DIR / "五样本行业价格连续观测补数队列验收_最新.json"
RESULT_MD = DATA_DIR / "五样本行业价格连续观测补数队列验收_最新.md"


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
        "product_code",
        "product_name",
        "indicator_type",
        "current_observation_count",
        "target_min_observation_count",
        "missing_observation_count",
        "current_status",
        "priority",
        "preferred_sources",
        "minimum_fields",
        "entry_boundary",
        "front_usage"
    ]
    for key in required:
        if key not in task:
            errors.append(f"{name}: 缺少字段 {key}")
    if task.get("target_min_observation_count") != 5:
        errors.append(f"{name}: 目标观测点必须为5")
    current = task.get("current_observation_count", 0)
    missing = task.get("missing_observation_count", 0)
    if current < 5 and task.get("current_status") == "trend_ready":
        errors.append(f"{name}: 不足5点不得trend_ready")
    if current + missing != 5 and current < 5:
        errors.append(f"{name}: 待补点数计算不正确")
    if not task.get("preferred_sources"):
        errors.append(f"{name}: preferred_sources不能为空")
    if not task.get("minimum_fields"):
        errors.append(f"{name}: minimum_fields不能为空")
    boundary_text = " ".join(task.get("entry_boundary", []))
    if "不足5个连续观测点前不得生成trend_ready结论" not in boundary_text:
        errors.append(f"{name}: 缺少trend_ready闸口")
    if "本队列不写入观测账本" not in boundary_text:
        errors.append(f"{name}: 缺少不写账本边界")
    return errors


def render_md(result: dict) -> str:
    lines = [
        "# 五样本行业价格连续观测补数队列验收",
        "",
        f"- 验收时间：{result['validated_at']}",
        f"- 验收结果：{result['status']}",
        f"- 覆盖任务：{result['task_count']}",
        f"- 错误数量：{len(result['errors'])}",
        "",
        "## 任务明细",
        "",
        "| 股票 | 观测对象 | 当前点数 | 待补点数 | 状态 |",
        "|---|---|---:|---:|---|"
    ]
    for item in result["tasks"]:
        lines.append(
            f"| {item['stock']} | {item['product_name']} | {item['current_observation_count']} | "
            f"{item['missing_observation_count']} | {item['current_status']} |"
        )
    if result["errors"]:
        lines.extend(["", "## 错误", ""])
        lines.extend([f"- {err}" for err in result["errors"]])
    lines.extend([
        "",
        "## 边界",
        "",
        "- 未触发外部抓取",
        "- 未写入观测账本",
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
    for key in ["not_formal_config", "not_entrypoint", "not_external_send", "not_external_fetch", "not_formal_database_write"]:
        if queue.get(key) is not True:
            errors.append(f"queue.{key} 必须为 true")
    for key in ["not_n8n", "not_external_send", "not_external_fetch", "not_service_restart", "not_19310", "not_real_account", "not_formal_database_write", "not_broker_interface", "not_auto_trade"]:
        if queue.get("safety_boundary", {}).get(key) is not True:
            errors.append(f"safety_boundary.{key} 必须为 true")
    for task in tasks:
        errors.extend(validate_task(task))

    result = {
        "名称": "五样本行业价格连续观测补数队列验收",
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed" if not errors else "failed",
        "task_count": len(tasks),
        "errors": errors,
        "tasks": [
            {
                "stock": task.get("stock", {}).get("name", ""),
                "code": task.get("stock", {}).get("code", ""),
                "product_name": task.get("product_name", ""),
                "current_observation_count": task.get("current_observation_count", 0),
                "missing_observation_count": task.get("missing_observation_count", 0),
                "current_status": task.get("current_status", "")
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
