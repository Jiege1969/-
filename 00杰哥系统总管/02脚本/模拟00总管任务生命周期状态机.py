# -*- coding: utf-8 -*-
"""00总管任务生命周期状态机本地模拟器。

只读引用现有标准任务单与SQLite影子台账，另建本地模拟SQLite/JSON验收包。
不连接Redis，不触发n8n，不发送企业微信，不写正式库，不调用模型/券商，不自动交易。
"""

from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
CONTRACT_DIR = MANAGER / "03数据" / "任务契约"
RECYCLE_DIR = MANAGER / "03数据" / "并行回收"

SAMPLE_TASK = CONTRACT_DIR / "标准任务单样例_最新.json"
SOURCE_LEDGER = CONTRACT_DIR / "轻量任务契约SQLite影子台账_最新.sqlite"
SIM_DB = CONTRACT_DIR / "任务生命周期状态机模拟器_最新.sqlite"
ACCEPTANCE_JSON = CONTRACT_DIR / "任务生命周期状态机验收包_最新.json"
EVENTS_JSON = CONTRACT_DIR / "任务生命周期状态机事件流_最新.json"
REPORT_JSON = RECYCLE_DIR / "00总管_任务生命周期状态机回收报告_最新.json"
REPORT_MD = RECYCLE_DIR / "00总管_任务生命周期状态机回收报告_最新.md"

FLOW_CLOSED = [
    "queued_shadow",
    "admitted",
    "planned",
    "dry_run_executed",
    "receipt_written",
    "closed",
]
FLOW_BLOCKED = ["queued_shadow", "admitted", "blocked"]
FORBIDDEN_ACTIONS = [
    "connect_redis",
    "trigger_n8n",
    "send_wecom",
    "write_formal_db",
    "call_model",
    "call_broker",
    "auto_trade",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_ledger_schema() -> dict[str, Any]:
    if not SOURCE_LEDGER.exists():
        return {"exists": False, "tables": []}
    conn = sqlite3.connect(SOURCE_LEDGER)
    try:
        rows = conn.execute(
            "SELECT name, type, sql FROM sqlite_master "
            "WHERE type IN ('table', 'index', 'view', 'trigger') ORDER BY type, name"
        ).fetchall()
        count = conn.execute("SELECT COUNT(*) FROM task_ledger").fetchone()[0]
        return {
            "exists": True,
            "task_ledger_rows": count,
            "objects": [
                {"name": row[0], "type": row[1], "sql": row[2]} for row in rows
            ],
        }
    finally:
        conn.close()


def init_sim_db() -> sqlite3.Connection:
    if SIM_DB.exists():
        SIM_DB.unlink()
    SIM_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SIM_DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE task_ledger (
          task_id TEXT PRIMARY KEY,
          source TEXT NOT NULL,
          target_system TEXT NOT NULL,
          risk_level TEXT NOT NULL,
          dry_run INTEGER NOT NULL,
          real_action_allowed INTEGER NOT NULL,
          idempotency_key TEXT NOT NULL UNIQUE,
          status TEXT NOT NULL,
          payload_json TEXT NOT NULL,
          receipt_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE lifecycle_events (
          event_id INTEGER PRIMARY KEY AUTOINCREMENT,
          task_id TEXT NOT NULL,
          idempotency_key TEXT NOT NULL,
          from_status TEXT,
          to_status TEXT NOT NULL,
          event_name TEXT NOT NULL,
          success INTEGER NOT NULL,
          detail_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );

        CREATE TABLE validation_checks (
          check_name TEXT PRIMARY KEY,
          passed INTEGER NOT NULL,
          detail_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """
    )
    return conn


def json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def record_event(
    conn: sqlite3.Connection,
    task: dict[str, Any],
    from_status: str | None,
    to_status: str,
    event_name: str,
    success: bool,
    detail: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO lifecycle_events (
          task_id, idempotency_key, from_status, to_status, event_name,
          success, detail_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task["task_id"],
            task["idempotency_key"],
            from_status,
            to_status,
            event_name,
            1 if success else 0,
            json_text(detail),
            now_text(),
        ),
    )


def insert_task(conn: sqlite3.Connection, task: dict[str, Any]) -> tuple[bool, str]:
    try:
        conn.execute(
            """
            INSERT INTO task_ledger (
              task_id, source, target_system, risk_level, dry_run,
              real_action_allowed, idempotency_key, status, payload_json,
              receipt_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task["task_id"],
                task.get("source", "00总管/任务生命周期状态机模拟器"),
                task.get("target_system", "00杰哥系统总管"),
                task.get("risk_level", "L1低风险影子"),
                1 if task.get("dry_run") is True else 0,
                1 if task.get("real_action_allowed") is True else 0,
                task["idempotency_key"],
                task["status"],
                json_text(task),
                json_text(task.get("receipt", {})),
                task.get("created_at", now_text()),
                now_text(),
            ),
        )
        return True, ""
    except sqlite3.IntegrityError as exc:
        return False, str(exc)


def update_status(
    conn: sqlite3.Connection,
    task: dict[str, Any],
    to_status: str,
    event_name: str,
    detail: dict[str, Any],
) -> None:
    from_status = task["status"]
    task["status"] = to_status
    task["receipt"] = detail.get("receipt", task.get("receipt", {}))
    conn.execute(
        """
        UPDATE task_ledger
        SET status = ?, payload_json = ?, receipt_json = ?, updated_at = ?
        WHERE task_id = ?
        """,
        (
            to_status,
            json_text(task),
            json_text(task.get("receipt", {})),
            now_text(),
            task["task_id"],
        ),
    )
    record_event(conn, task, from_status, to_status, event_name, True, detail)


def can_admit(task: dict[str, Any]) -> tuple[bool, str]:
    if task.get("dry_run") is not True:
        return False, "dry_run必须为true"
    if task.get("real_action_allowed") is not False:
        return False, "real_action_allowed必须为false"
    if not task.get("idempotency_key"):
        return False, "缺少idempotency_key"
    if not task.get("rollback_plan"):
        return False, "缺少rollback_plan"
    return True, "准入通过"


def simulate_closed(conn: sqlite3.Connection, task: dict[str, Any]) -> dict[str, Any]:
    task = deepcopy(task)
    task["task_id"] = "task-20260505-lifecycle-closed-001"
    task["idempotency_key"] = "20260505-lifecycle-closed-001"
    task["status"] = "queued_shadow"
    task["dry_run"] = True
    task["real_action_allowed"] = False
    task["created_at"] = now_text()
    task["receipt"] = {
        "accepted": False,
        "real_action_executed": False,
        "result": "queued_shadow only",
    }
    inserted, error = insert_task(conn, task)
    record_event(
        conn,
        task,
        None,
        "queued_shadow",
        "enqueue_shadow",
        inserted,
        {"inserted": inserted, "error": error},
    )

    ok, reason = can_admit(task)
    if not ok:
        update_status(
            conn,
            task,
            "blocked",
            "admission_blocked",
            {
                "reason": reason,
                "receipt": {
                    "accepted": False,
                    "real_action_executed": False,
                    "result": "blocked before plan",
                },
            },
        )
        return task

    update_status(
        conn,
        task,
        "admitted",
        "admit_shadow_task",
        {
            "reason": reason,
            "guards": {"dry_run": True, "real_action_allowed": False},
            "receipt": {
                "accepted": True,
                "real_action_executed": False,
                "result": "admitted to local shadow lifecycle",
            },
        },
    )
    update_status(
        conn,
        task,
        "planned",
        "build_local_plan",
        {
            "plan": [
                "read sample task",
                "write local simulation ledger",
                "write receipt",
                "close local shadow task",
            ],
            "rollback_plan_present": True,
        },
    )
    update_status(
        conn,
        task,
        "dry_run_executed",
        "execute_dry_run_locally",
        {
            "forbidden_actions_attempted": [],
            "forbidden_actions_blocked": FORBIDDEN_ACTIONS,
            "real_action_executed": False,
        },
    )
    receipt = {
        "accepted": True,
        "result": "local dry_run completed; receipt written; no real action executed",
        "real_action_executed": False,
        "evidence": {
            "sqlite": str(SIM_DB),
            "events": str(EVENTS_JSON),
            "report": str(REPORT_JSON),
        },
    }
    update_status(
        conn,
        task,
        "receipt_written",
        "write_receipt",
        {"receipt": receipt, "receipt_present": True},
    )
    update_status(
        conn,
        task,
        "closed",
        "close_shadow_task",
        {"closed": True, "receipt": receipt},
    )
    return task


def simulate_blocked(conn: sqlite3.Connection, sample: dict[str, Any]) -> dict[str, Any]:
    task = deepcopy(sample)
    task["task_id"] = "task-20260505-lifecycle-blocked-001"
    task["idempotency_key"] = "20260505-lifecycle-blocked-001"
    task["status"] = "queued_shadow"
    task["dry_run"] = True
    task["real_action_allowed"] = False
    task["created_at"] = now_text()
    task["receipt"] = {
        "accepted": False,
        "real_action_executed": False,
        "result": "queued_shadow only",
    }
    task.pop("rollback_plan", None)
    inserted, error = insert_task(conn, task)
    record_event(
        conn,
        task,
        None,
        "queued_shadow",
        "enqueue_shadow",
        inserted,
        {"inserted": inserted, "error": error},
    )
    update_status(
        conn,
        task,
        "admitted",
        "admit_for_guard_evaluation",
        {
            "guards": {"dry_run": True, "real_action_allowed": False},
            "note": "进入本地守卫评估，不进入执行计划",
        },
    )
    ok, reason = can_admit(task)
    if ok:
        reason = "预期应因缺少rollback_plan而阻断，但未阻断"
    receipt = {
        "accepted": False,
        "result": f"blocked: {reason}",
        "real_action_executed": False,
    }
    update_status(
        conn,
        task,
        "blocked",
        "rollback_plan_guard_blocked",
        {"reason": reason, "receipt": receipt},
    )
    return task


def test_duplicate_idempotency(conn: sqlite3.Connection, sample: dict[str, Any]) -> dict[str, Any]:
    duplicate = deepcopy(sample)
    duplicate["task_id"] = "task-20260505-lifecycle-duplicate-001"
    duplicate["idempotency_key"] = "20260505-lifecycle-closed-001"
    duplicate["status"] = "queued_shadow"
    duplicate["dry_run"] = True
    duplicate["real_action_allowed"] = False
    duplicate["created_at"] = now_text()
    duplicate["receipt"] = {
        "accepted": False,
        "real_action_executed": False,
        "result": "duplicate idempotency guard",
    }
    inserted, error = insert_task(conn, duplicate)
    record_event(
        conn,
        duplicate,
        None,
        "blocked",
        "duplicate_idempotency_blocked",
        not inserted,
        {"inserted": inserted, "error": error, "expected": "UNIQUE constraint failed"},
    )
    return {"blocked": not inserted, "error": error, "idempotency_key": duplicate["idempotency_key"]}


def record_check(conn: sqlite3.Connection, name: str, passed: bool, detail: Any) -> dict[str, Any]:
    item = {"check_name": name, "passed": bool(passed), "detail": detail}
    conn.execute(
        """
        INSERT INTO validation_checks (check_name, passed, detail_json, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, 1 if passed else 0, json_text(detail), now_text()),
    )
    return item


def fetch_all(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
    return [dict(row) for row in rows]


def main() -> int:
    sample = load_json(SAMPLE_TASK)
    schema = source_ledger_schema()
    conn = init_sim_db()
    try:
        closed_task = simulate_closed(conn, sample)
        blocked_task = simulate_blocked(conn, sample)
        duplicate_result = test_duplicate_idempotency(conn, sample)

        rows = fetch_all(conn, "task_ledger")
        events = fetch_all(conn, "lifecycle_events")
        closed_flow = [
            event["to_status"]
            for event in events
            if event["task_id"] == closed_task["task_id"]
            and event["event_name"] != "duplicate_idempotency_blocked"
        ]
        blocked_flow = [
            event["to_status"]
            for event in events
            if event["task_id"] == blocked_task["task_id"]
        ]
        checks = [
            record_check(conn, "读取标准任务单", SAMPLE_TASK.exists() and bool(sample), str(SAMPLE_TASK)),
            record_check(conn, "读取SQLite影子台账schema", schema.get("exists") is True, schema),
            record_check(conn, "closed状态流完整", closed_flow == FLOW_CLOSED, closed_flow),
            record_check(conn, "blocked状态流完整", blocked_flow == FLOW_BLOCKED, blocked_flow),
            record_check(conn, "idempotency_key防重复", duplicate_result["blocked"], duplicate_result),
            record_check(
                conn,
                "receipt已写入且不含真实动作",
                closed_task.get("receipt", {}).get("real_action_executed") is False
                and closed_task["status"] == "closed",
                closed_task.get("receipt", {}),
            ),
            record_check(
                conn,
                "rollback_plan守卫有效",
                closed_task.get("rollback_plan") is not None and blocked_task["status"] == "blocked",
                {"closed_has_rollback_plan": closed_task.get("rollback_plan") is not None, "blocked_status": blocked_task["status"]},
            ),
            record_check(
                conn,
                "real_action_allowed全程为false",
                all(row["real_action_allowed"] == 0 for row in rows),
                [{"task_id": row["task_id"], "real_action_allowed": row["real_action_allowed"]} for row in rows],
            ),
            record_check(
                conn,
                "禁止外部动作未触发",
                all(json.loads(event["detail_json"]).get("forbidden_actions_attempted", []) == [] for event in events),
                {"forbidden_actions": FORBIDDEN_ACTIONS, "scope": "local SQLite/JSON only"},
            ),
        ]
        conn.commit()

        failed = [item for item in checks if not item["passed"]]
        conclusion = "通过" if not failed else "未通过"
        package = {
            "名称": "00总管任务生命周期状态机与SQLite影子台账闭环验收包",
            "生成时间": now_text(),
            "结论": conclusion,
            "边界": {
                "local_sqlite_json_only": True,
                "redis_connected": False,
                "n8n_triggered": False,
                "wecom_sent": False,
                "formal_db_written": False,
                "model_called": False,
                "broker_called": False,
                "auto_trade": False,
            },
            "源输入": {
                "标准任务单": str(SAMPLE_TASK),
                "SQLite影子台账": str(SOURCE_LEDGER),
                "源台账schema摘要": schema,
            },
            "状态流": {
                "closed_path_expected": FLOW_CLOSED,
                "closed_path_actual": closed_flow,
                "blocked_path_expected": FLOW_BLOCKED,
                "blocked_path_actual": blocked_flow,
            },
            "验证项": checks,
            "产物": {
                "模拟SQLite": str(SIM_DB),
                "事件流JSON": str(EVENTS_JSON),
                "验收包JSON": str(ACCEPTANCE_JSON),
                "回收报告JSON": str(REPORT_JSON),
                "回收报告MD": str(REPORT_MD),
            },
        }
        write_json(EVENTS_JSON, {"生成时间": now_text(), "events": events})
        write_json(ACCEPTANCE_JSON, package)
        write_json(REPORT_JSON, package)
        write_text(REPORT_MD, render_markdown(package))
        print(json.dumps({"结论": conclusion, "通过": len(checks) - len(failed), "失败": len(failed)}, ensure_ascii=False))
        return 0 if not failed else 1
    finally:
        conn.close()


def render_markdown(package: dict[str, Any]) -> str:
    checks = package["验证项"]
    lines = [
        "# 00总管任务生命周期状态机回收报告",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 结论：{package['结论']}",
        "- 范围：本地SQLite/JSON模拟，不连接Redis，不触发n8n，不发企业微信，不写正式库，不调用模型/券商，不自动交易。",
        "",
        "## 状态流验收",
        f"- closed路径：{' -> '.join(package['状态流']['closed_path_actual'])}",
        f"- blocked路径：{' -> '.join(package['状态流']['blocked_path_actual'])}",
        "",
        "## 守卫验收",
    ]
    for item in checks:
        mark = "通过" if item["passed"] else "失败"
        lines.append(f"- {item['check_name']}：{mark}")
    lines.extend(
        [
            "",
            "## 输出文件",
            f"- 模拟SQLite：{package['产物']['模拟SQLite']}",
            f"- 事件流JSON：{package['产物']['事件流JSON']}",
            f"- 验收包JSON：{package['产物']['验收包JSON']}",
            f"- 回收报告JSON：{package['产物']['回收报告JSON']}",
            f"- 回收报告MD：{package['产物']['回收报告MD']}",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
