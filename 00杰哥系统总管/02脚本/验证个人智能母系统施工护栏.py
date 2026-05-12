# -*- coding: utf-8 -*-
"""
名称：验证个人智能母系统施工护栏.py
作用：验证个人智能母系统新增施工护栏是否可用，包括交易保护窗口、施工前闸口、日常调度状态、旧口径冲突审计和新业务复制搭建清单。
触发方式：python 验证个人智能母系统施工护栏.py
依赖：Python标准库；交易保护与施工窗口规则.json；个人智能母系统日常调度规则.json；旧口径冲突审计规则.json；新业务系统复制搭建规则.json；相关生成脚本。
所属系统：00杰哥系统总管。
输出：04日志/个人智能母系统施工护栏/personal-ai-system-guardrail-verify-*.json。
安全边界：只读验证和写总管验收日志；不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易、不创建新业务正式目录。
标识：personal-ai-system-guardrail-verify；交易保护；日常调度；旧口径审计；复制搭建。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_py(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=180,
    )


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(ok), "说明": detail}


def main() -> int:
    manager = manager_root()
    checks: list[dict[str, Any]] = []
    scripts = {
        "窗口判断": manager / "02脚本" / "判断交易保护施工窗口.py",
        "施工闸口": manager / "02脚本" / "生成施工前保护闸口报告.py",
        "日常调度": manager / "02脚本" / "生成个人智能母系统日常调度状态.py",
        "日常调度验收": manager / "02脚本" / "验证个人智能母系统日常调度状态.py",
        "暂停模式控制": manager / "02脚本" / "设置个人智能母系统暂停模式.py",
        "暂停模式验收": manager / "02脚本" / "验证个人智能母系统暂停模式.py",
        "任务准入": manager / "02脚本" / "生成个人智能母系统任务准入报告.py",
        "任务准入验收": manager / "02脚本" / "验证个人智能母系统任务准入.py",
        "任务队列调度": manager / "02脚本" / "生成个人智能母系统任务队列调度面板.py",
        "任务队列调度验收": manager / "02脚本" / "验证个人智能母系统任务队列调度.py",
        "旧口径审计": manager / "02脚本" / "生成旧口径冲突审计报告.py",
        "复制搭建": manager / "02脚本" / "生成新业务系统复制搭建清单.py",
    }
    configs = {
        "交易保护与施工窗口规则": manager / "01配置" / "交易保护与施工窗口规则.json",
        "个人智能母系统日常调度规则": manager / "01配置" / "个人智能母系统日常调度规则.json",
        "个人智能母系统任务准入规则": manager / "01配置" / "个人智能母系统任务准入规则.json",
        "个人智能母系统任务队列调度规则": manager / "01配置" / "个人智能母系统任务队列调度规则.json",
        "旧口径冲突审计规则": manager / "01配置" / "旧口径冲突审计规则.json",
        "新业务系统复制搭建规则": manager / "01配置" / "新业务系统复制搭建规则.json",
    }

    for name, path in configs.items():
        data = load_json(path)
        checks.append(check(f"{name}存在且可解析", isinstance(data, dict), str(path)))
    for name, path in scripts.items():
        text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        checks.append(check(f"{name}脚本存在", path.exists(), str(path)))
        checks.append(check(f"{name}脚本含标准标头", all(word in text for word in ["名称：", "作用：", "触发方式：", "依赖：", "所属系统", "输出：", "安全边界", "标识"]), str(path)))

    trading_run = run_py(scripts["窗口判断"], "--now", "2026-05-06 10:00:00")
    trading_status = load_json(manager / "03数据" / "运行状态" / "交易保护施工窗口_最新.json", {})
    checks.append(check("交易日最高保护窗口可识别", trading_run.returncode == 0 and trading_status.get("当前运行状态") == "交易保护", trading_status))

    holiday_run = run_py(scripts["窗口判断"], "--now", "2026-05-04 10:00:00")
    holiday_status = load_json(manager / "03数据" / "运行状态" / "交易保护施工窗口_最新.json", {})
    checks.append(check("已知节假日不误判交易保护", holiday_run.returncode == 0 and holiday_status.get("是否已知非交易日") is True and holiday_status.get("当前运行状态") != "交易保护", holiday_status))

    gate_allowed_run = run_py(scripts["施工闸口"], "--action", "只读检查", "--now", "2026-05-06 10:00:00")
    gate_allowed = load_json(manager / "03数据" / "运行状态" / "施工前保护闸口_最新.json", {})
    checks.append(check("保护窗口内只读检查允许", gate_allowed_run.returncode == 0 and gate_allowed.get("闸口结论") == "允许", gate_allowed))

    gate_forbidden_run = run_py(scripts["施工闸口"], "--action", "重启19300", "--now", "2026-05-06 10:00:00")
    gate_forbidden = load_json(manager / "03数据" / "运行状态" / "施工前保护闸口_最新.json", {})
    checks.append(check("保护窗口内重启19300禁止", gate_forbidden_run.returncode == 2 and gate_forbidden.get("闸口结论") == "禁止", gate_forbidden))

    scheduler_verify_run = run_py(scripts["日常调度验收"])
    scheduler_verify = load_json(manager / "04日志" / "个人智能母系统日常调度" / "daily-scheduler-verify-最新.json", {})
    checks.append(check("日常调度状态验收通过", scheduler_verify_run.returncode == 0 and scheduler_verify.get("失败") == 0, scheduler_verify))

    scheduler_run = run_py(scripts["日常调度"], "--now", "2026-05-06 16:00:00", "--ignore-resource-pressure")
    scheduler_status = load_json(manager / "03数据" / "运行状态" / "个人智能母系统日常调度状态_最新.json", {})
    checks.append(check("收市股票分析窗口可识别", scheduler_run.returncode == 0 and scheduler_status.get("当前状态") == "收市股票分析", scheduler_status))

    pause_verify_run = run_py(scripts["暂停模式验收"])
    pause_verify = load_json(manager / "04日志" / "个人智能母系统日常调度" / "pause-mode-verify-最新.json", {})
    checks.append(check("暂停恢复模式验收通过", pause_verify_run.returncode == 0 and pause_verify.get("失败") == 0, pause_verify))

    admission_verify_run = run_py(scripts["任务准入验收"])
    admission_verify = load_json(manager / "04日志" / "个人智能母系统任务准入" / "task-admission-verify-最新.json", {})
    checks.append(check("任务准入验收通过", admission_verify_run.returncode == 0 and admission_verify.get("失败") == 0, admission_verify))

    admission_run = run_py(
        scripts["任务准入"],
        "--task", "交易保护窗口重启拦截",
        "--level", "L2",
        "--type", "L2服务级操作",
        "--action", "重启19300",
        "--now", "2026-05-06 10:00:00",
        "--ignore-resource-pressure",
    )
    admission_status = load_json(manager / "03数据" / "运行状态" / "个人智能母系统任务准入_最新.json", {})
    checks.append(check("任务准入可拦截交易保护窗口重启", admission_run.returncode == 0 and admission_status.get("准入结论") == "禁止执行", admission_status))

    queue_verify_run = run_py(scripts["任务队列调度验收"])
    queue_verify = load_json(manager / "04日志" / "个人智能母系统任务队列" / "task-queue-scheduler-verify-最新.json", {})
    checks.append(check("任务队列调度验收通过", queue_verify_run.returncode == 0 and queue_verify.get("失败") == 0, queue_verify))

    queue_panel = load_json(manager / "03数据" / "运行状态" / "个人智能母系统任务队列调度_最新.json", {})
    checks.append(check("任务队列调度不触发执行器和n8n", queue_panel.get("汇总", {}).get("触发执行器数量") == 0 and queue_panel.get("汇总", {}).get("触发n8n数量") == 0, queue_panel.get("汇总", {})))

    audit_run = run_py(scripts["旧口径审计"])
    audit_report = load_json(manager / "03数据" / "运行状态" / "旧口径冲突审计_最新.json", {})
    checks.append(check("旧口径冲突审计可生成", audit_run.returncode == 0 and isinstance(audit_report.get("发现项"), list), {"stdout": audit_run.stdout.strip(), "发现总数": audit_report.get("发现总数")}))
    checks.append(check("旧口径冲突审计不自动修改", audit_report.get("是否自动修改") is False and audit_report.get("安全边界", {}).get("是否修改文件") is False, audit_report.get("安全边界", {})))

    blueprint_run = run_py(scripts["复制搭建"], "--name", "税务资料分析系统", "--domain", "税务")
    blueprint = load_json(manager / "03数据" / "新业务复制搭建" / "新业务系统复制搭建清单_最新.json", {})
    checks.append(check("新业务复制搭建清单可生成", blueprint_run.returncode == 0 and blueprint.get("当前阶段") == "影子蓝图", blueprint))
    checks.append(check("新业务复制搭建不创建正式目录", blueprint.get("是否创建正式目录") is False and blueprint.get("安全边界", {}).get("是否影响股票系统") is False, blueprint.get("安全边界", {})))
    checks.append(check("复制搭建清单包含四系统职责", all(key in blueprint.get("四系统职责继承", {}) for key in ["00总管", "01智能", "02扩展", "03进化"]), blueprint.get("四系统职责继承", {})))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "个人智能母系统施工护栏验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "安全边界": {
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否创建新业务正式目录": False,
        },
    }
    log_dir = manager / "04日志" / "个人智能母系统施工护栏"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"personal-ai-system-guardrail-verify-{stamp}.json"
    latest = log_dir / "personal-ai-system-guardrail-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
