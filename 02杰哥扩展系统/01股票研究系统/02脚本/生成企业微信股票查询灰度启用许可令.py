# -*- coding: utf-8 -*-
"""
名称：生成企业微信股票查询灰度启用许可令.py
作用：生成股票研究系统企业微信查询灰度启用前的许可条件和风险闸口。
触发方式：python 生成企业微信股票查询灰度启用许可令.py
依赖：Python标准库；企业微信股票查询灰度启用规则.json；企业微信股票查询禁用态规则.json；股票研究日常使用包_最新.md；stock-wework-query-dryrun-verify-最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成许可令草稿；不真实发送企业微信；不触发n8n；不启动或重启服务；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信股票查询灰度启用许可令生成脚本。
标识：stock-wework-query-gray-gate-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def contains_all(text: str, words: list[str]) -> bool:
    return all(word in text for word in words)


def build_markdown(report: dict[str, Any]) -> str:
    evidence_lines = "\n".join(
        f"- {item['名称']}：{'通过' if item['通过'] else '未通过'}。{item['详情']}"
        for item in report["证据检查"]
    )
    blocked_lines = "\n".join(f"- {item}" for item in report["仍然禁止"])
    confirm_lines = "\n".join(f"- {item}" for item in report["必须人工确认后才可执行"])
    scope = report["灰度范围"]
    commands = "\n".join(f"- {item}" for item in scope["首批指令"])
    return f"""# 企业微信股票查询灰度启用许可令

生成时间：{report['生成时间']}

结论：{report['结论']}

定位：本许可令只用于判断是否具备进入灰度启用讨论和人工确认的条件，不代表已经启用真实企业微信发送。

## 一、证据检查

{evidence_lines}

## 二、灰度范围

- 首批用户：{scope['首批用户']}
- 首批股票：{scope['首批股票']}
- 回复定位：{scope['回复定位']}

### 首批指令

{commands}

## 三、仍然禁止

{blocked_lines}

## 四、必须人工确认后才可执行

{confirm_lines}

## 五、执行原则

1. 企业微信真实发送、n8n正式触发、服务启动或重启都属于高风险动作。
2. OpenClaw只做消息网关，不写股票业务判断逻辑。
3. n8n负责后续统一编排，股票研究系统只提供数据、分析和回复草稿。
4. 任何交易接口和自动下单能力保持关闭。
5. 数据健康度降级时，先回退到只读查询和复盘，不强化分析结论。
"""


def main() -> int:
    root = module_root()
    manager_root = system_root() / "00杰哥系统总管"
    config = load_json(root / "01配置" / "企业微信股票查询灰度启用规则.json")
    disabled_config = load_json(root / "01配置" / "企业微信股票查询禁用态规则.json")
    dryrun_report = load_json(root / "04日志" / "企业微信股票查询禁用态" / "stock-wework-query-dryrun-verify-最新.json")
    daily_package = root / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.md"
    daily_text = daily_package.read_text(encoding="utf-8") if daily_package.exists() else ""
    assistant_entry = root / "02脚本" / "股票助手入口.py"
    assistant_text = assistant_entry.read_text(encoding="utf-8") if assistant_entry.exists() else ""
    old_bridge_report = root / "04日志" / "旧系统桥接" / "old-stock-readonly-bridge-最新.json"

    checks = [
        {
            "名称": "灰度启用规则存在",
            "通过": config.get("模式") == "gray_gate_only",
            "详情": str(root / "01配置" / "企业微信股票查询灰度启用规则.json"),
        },
        {
            "名称": "禁用态规则仍为只模拟",
            "通过": disabled_config.get("模式") == "dry_run_only",
            "详情": disabled_config.get("模式", "缺失"),
        },
        {
            "名称": "禁用态模拟验收通过",
            "通过": dryrun_report.get("失败") == 0,
            "详情": dryrun_report.get("结论", "未找到禁用态模拟验收结果"),
        },
        {
            "名称": "日常使用包存在",
            "通过": daily_package.exists(),
            "详情": str(daily_package),
        },
        {
            "名称": "数据健康度满足灰度前置条件",
            "通过": "数据健康度：优秀" in daily_text or "数据健康度：良好" in daily_text,
            "详情": "要求优秀或良好",
        },
        {
            "名称": "股票助手具备查询接口代码",
            "通过": contains_all(assistant_text, ["/daily-package", "/data-health", "/status-summary", "/report/latest"]),
            "详情": str(assistant_entry),
        },
        {
            "名称": "旧系统桥接验收记录存在",
            "通过": old_bridge_report.exists(),
            "详情": str(old_bridge_report),
        },
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    ready_for_manual_confirm = failed == 0
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "gray_gate_only",
        "通过": passed,
        "失败": failed,
        "证据检查": checks,
        "结论": "已具备提交人工确认灰度启用的条件，但尚未启用真实企业微信链路。" if ready_for_manual_confirm else "暂不具备提交灰度启用确认的条件。",
        "灰度范围": config.get("灰度启用范围", {}),
        "仍然禁止": config.get("当前阶段禁止动作", []),
        "必须人工确认后才可执行": config.get("人工确认后才允许进入的动作", []),
        "实际动作": {
            "真实发送企业微信": False,
            "触发n8n正式工作流": False,
            "启动或重启服务": False,
            "写旧系统": False,
            "写正式业务库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "19企业微信灰度启用"
    log_dir = root / "04日志" / "企业微信灰度启用"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "企业微信股票查询灰度启用许可令_最新.json"
    latest_json = output_dir / "企业微信股票查询灰度启用许可令_最新.json"
    md_path = output_dir / "企业微信股票查询灰度启用许可令_最新.md"
    latest_md = output_dir / "企业微信股票查询灰度启用许可令_最新.md"
    log_path = log_dir / f"stock-wework-query-gray-gate-generate-{timestamp}.json"
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, build_markdown(report))
    write_text(latest_md, build_markdown(report))
    write_json(log_path, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
