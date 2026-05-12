# -*- coding: utf-8 -*-
"""
验证下一轮并行派工与任务队列视图。

检查重点：
- JSON 可解析。
- 活跃窗口容量不超过 3。
- 高风险安全边界保持关闭，02扩展真实动作为 shadow/禁用。
- 固定回收报告存在。
"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
CONTEXT = MANAGER / "03数据" / "开工上下文"
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"
PANEL = MANAGER / "07文档" / "当前施工面板.md"

GENERATOR = MANAGER / "02脚本" / "生成下一轮并行派工与任务队列视图.py"
VERIFIER = MANAGER / "02脚本" / "验证下一轮并行派工与任务队列视图.py"
CONFIG_PATH = CONTEXT / "下一轮并行派工队列配置_最新.json"
VIEW_JSON = STATE / "下一轮并行派工任务队列视图_最新.json"
VIEW_MD = STATE / "下一轮并行派工任务队列视图_最新.md"
DISPATCH_MD = CONTEXT / "下一轮并行派工队列启动包_最新.md"
GEN_REPORT_JSON = STATE / "下一轮并行派工任务队列视图生成报告_最新.json"
RECOVERY_REPORT = RECOVERY / "00总管_本轮小任务A回收报告_最新.md"
VERIFY_JSON = STATE / "下一轮并行派工任务队列视图验收_最新.json"
VERIFY_MD = STATE / "下一轮并行派工任务队列视图验收_最新.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json_result(path: Path) -> tuple[bool, dict[str, Any], str]:
    if not path.exists():
        return False, {}, "文件不存在"
    try:
        return True, json.loads(path.read_text(encoding="utf-8-sig")), ""
    except Exception as exc:
        return False, {}, str(exc)


def compile_ok(path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    config_ok, config, config_error = load_json_result(CONFIG_PATH)
    view_ok, view, view_error = load_json_result(VIEW_JSON)
    report_ok, generation, report_error = load_json_result(GEN_REPORT_JSON)
    compile_generator, generator_error = compile_ok(GENERATOR)
    compile_verifier, verifier_error = compile_ok(VERIFIER)

    safety = view.get("安全边界", {})
    active_count = view.get("活跃窗口数量", -1)
    max_active = view.get("容量规则", {}).get("最大活跃窗口", -1)
    queue_names = [item.get("队列项") for item in view.get("队列", [])]
    false_keys = ["企业微信真实发送", "触发n8n", "调用券商接口", "自动交易", "写正式库"]

    checks = [
        check(compile_generator, "生成脚本可编译", generator_error),
        check(compile_verifier, "验证脚本可编译", verifier_error),
        check(config_ok, "配置 JSON 可解析", config_error),
        check(view_ok, "队列视图 JSON 可解析", view_error),
        check(report_ok, "生成报告 JSON 可解析", report_error),
        check(config.get("只读视图") is True, "配置声明只读视图", config.get("只读视图")),
        check(view.get("只读视图") is True, "视图声明只读", view.get("只读视图")),
        check(max_active == 3, "最大活跃窗口为3", max_active),
        check(active_count <= 3, "活跃窗口数量不超过3", active_count),
        check(set(["00总管", "01智能", "02扩展", "03进化", "总体系统回收"]).issubset(set(queue_names)), "下一轮优先级覆盖五类任务", queue_names),
        check(view.get("02扩展滚动", {}).get("允许多任务滚动") is True, "02扩展允许多任务滚动", view.get("02扩展滚动", {})),
        check(view.get("02扩展滚动", {}).get("高风险真实动作") == "shadow/禁用", "02扩展高风险真实动作保持 shadow/禁用", view.get("02扩展滚动", {}).get("高风险真实动作")),
        check(all(safety.get(key) is False for key in false_keys), "核心安全边界全部关闭", safety),
        check(safety.get("02扩展高风险真实动作") == "shadow/禁用", "安全边界声明02扩展 shadow/禁用", safety.get("02扩展高风险真实动作")),
        check(VIEW_MD.exists(), "队列视图 Markdown 存在", str(VIEW_MD)),
        check(DISPATCH_MD.exists(), "队列启动包存在", str(DISPATCH_MD)),
        check(RECOVERY_REPORT.exists(), "固定回收报告存在", str(RECOVERY_REPORT)),
        check("下一轮并行派工任务队列视图" in read_text(PANEL), "当前施工面板 marker 小节已同步", str(PANEL)),
        check(generation.get("结论") == "通过", "生成报告结论通过", generation.get("结论")),
        check(view.get("阻断数量") == 0, "队列视图阻断项为0", view.get("阻断数量")),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "下一轮并行派工任务队列视图验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "阻断数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "企业微信真实发送": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式库": False,
            "02扩展高风险真实动作": "shadow/禁用",
        },
    }
    write_json(VERIFY_JSON, result)
    lines = [
        "# 下一轮并行派工任务队列视图验收",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        f"- 阻断数量：{result['阻断数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend([
        "",
        "## 安全边界",
        "- 企业微信真实发送、n8n、券商接口、自动交易、正式库写入均关闭。",
        "- 02扩展高风险真实动作保持 shadow/禁用。",
        "",
    ])
    write_text(VERIFY_MD, "\n".join(lines))

    recovery_text = read_text(RECOVERY_REPORT)
    recovery_text = recovery_text.replace("【验收结果】等待验证脚本执行。", f"【验收结果】{result['结论']}；通过 {result['通过数量']}/{len(checks)}；失败 {result['失败数量']}；阻断项 {result['阻断数量']}。")
    write_text(RECOVERY_REPORT, recovery_text)

    print(json.dumps({"状态": result["结论"], "通过": result["通过数量"], "失败": result["失败数量"], "阻断": result["阻断数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
