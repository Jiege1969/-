# -*- coding: utf-8 -*-
"""
名称：验证股票n8n长期观察模型与时段调度策略包.py
作用：验证259策略包是否吸收模型路由、收市后分析、夜间长期观察和红线边界。
触发方式：python 验证股票n8n长期观察模型与时段调度策略包.py
依赖：Python标准库；生成股票n8n长期观察模型与时段调度策略包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地生成与校验；不修改正式模型路由；不导入n8n；不启用n8n；不真实发送企业微信；不交易。
标识：stock-n8n-long-observation-model-schedule-package-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n长期观察模型与时段调度策略包验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 总体状态：{result['总体状态']}",
        f"- 通过：{result['通过']}",
        f"- 失败：{result['失败']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}；{item['说明']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票n8n长期观察模型与时段调度策略包.py"
    latest = root / "03数据" / "259股票n8n长期观察模型与时段调度策略包" / "股票n8n长期观察模型与时段调度策略包_最新.json"
    completed = subprocess.run(
        [sys.executable, str(generator)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    report = load_json(latest, {})
    safety = report.get("安全边界", {})
    actions = report.get("实际动作", {})
    strategy = report.get("模型与时段策略", [])
    strategy_text = json.dumps(strategy, ensure_ascii=False)

    dangerous_keys = [
        "修改正式模型路由",
        "导入n8n",
        "启用n8n工作流",
        "触发n8n",
        "真实发送企业微信",
        "群发",
        "调用券商接口",
        "自动交易",
        "自动转正式规则",
        "重载19310",
        "重载19302",
        "修改总管面板",
        "修改一键接续包",
    ]
    safety_danger = [key for key in dangerous_keys if safety.get(key) is not False]
    action_danger = [key for key in dangerous_keys if key in actions and actions.get(key) is not False]
    source_status = report.get("来源文件状态", {})
    required_sources = ["股票三线模型路由", "L5AI分析报告规则", "盘后批处理资源预算规则", "个人智能母系统日常调度规则"]
    missing_sources = [name for name in required_sources if not source_status.get(name, {}).get("存在")]

    checks = [
        check("生成脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr[-1000:]}),
        check("259策略包存在", latest.exists(), str(latest)),
        check("吸收收市后分析要求", "15:40-17:30" in strategy_text and "18:00-21:30" in strategy_text, strategy_text[:1000]),
        check("吸收夜间长期观察要求", "00:30-05:30" in strategy_text and "夜间长期观察" in strategy_text, strategy_text[:1000]),
        check("保留三线模型路由", all(model in strategy_text for model in ["qwen3:14b", "deepseek-r1:32b", "mychen76/Fin-R1:Q5"]), strategy_text[:1500]),
        check("金融专业模型只做复核解释", "金融专业模型" in json.dumps(report, ensure_ascii=False) and "不直接给交易指令" in json.dumps(report, ensure_ascii=False), report.get("模型与时段策略")),
        check("n8n定位为调度而非判断核心", "n8n是调度器" in json.dumps(report, ensure_ascii=False), report.get("当前结论")),
        check("来源配置齐全", not missing_sources, missing_sources),
        check("安全边界未触发危险动作", not safety_danger, safety_danger),
        check("实际动作未触发危险动作", not action_danger, action_danger),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查结果": checks,
        "策略包": str(latest),
        "生成stdout": completed.stdout[-2000:],
    }
    log_dir = root / "04日志" / "股票n8n长期观察模型与时段调度策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = log_dir / f"stock-n8n-long-observation-model-schedule-package-verify-{stamp}.json"
    latest_json = log_dir / "stock-n8n-long-observation-model-schedule-package-verify-最新.json"
    output_md = log_dir / f"stock-n8n-long-observation-model-schedule-package-verify-{stamp}.md"
    latest_md = log_dir / "stock-n8n-long-observation-model-schedule-package-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": result["总体状态"], "通过": result["通过"], "失败": result["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
