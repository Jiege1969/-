# -*- coding: utf-8 -*-
"""
名称：验证股票n8n长期观察闭环灰度包.py
作用：验证258股票n8n长期观察闭环灰度包是否完整，并确认红线未被触发。
触发方式：python 验证股票n8n长期观察闭环灰度包.py
依赖：Python标准库；生成股票n8n长期观察闭环灰度包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地生成与校验；不导入n8n；不启用n8n工作流；不真实发送企业微信；不调用券商接口；不自动交易。
标识：stock-n8n-long-observation-loop-gray-package-verify
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
        "# 股票n8n长期观察闭环灰度包验收",
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
    generator = root / "02脚本" / "生成股票n8n长期观察闭环灰度包.py"
    latest = root / "03数据" / "258股票n8n长期观察闭环灰度包" / "股票n8n长期观察闭环灰度包_最新.json"
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
    workflow = report.get("工作流草案", {})
    source_status = report.get("源入口状态", {})

    dangerous_keys = [
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
    required_sources = ["本地主动研究闭环", "n8n未激活编排草案", "股票AI反馈记录", "进化反馈样本候选"]
    missing_sources = [name for name in required_sources if not source_status.get(name, {}).get("存在")]
    nodes = workflow.get("nodes", [])
    node_names = {str(item.get("name")) for item in nodes if isinstance(item, dict)}

    checks = [
        check("生成脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr[-1000:]}),
        check("258灰度包存在", latest.exists(), str(latest)),
        check("n8n定位正确", "调度器" in str(report.get("n8n定位", "")), report.get("n8n定位")),
        check("允许n8n参与本地长期分析dry-run", report.get("当前放行判断", {}).get("允许n8n参与本地长期分析dry-run") is True, report.get("当前放行判断")),
        check("不允许真实外部Webhook触发", report.get("当前放行判断", {}).get("允许n8n真实触发外部Webhook") is False, report.get("当前放行判断")),
        check("闭环链路覆盖研究推送反馈进化", all(keyword in "".join(report.get("闭环链路", [])) for keyword in ["研究", "推送", "反馈", "进化"]), report.get("闭环链路")),
        check("工作流节点覆盖调度分析发送闸口反馈进化", {"Schedule Trigger", "Run Local Stock Observation", "Single User Send Gate", "Feedback Intake", "Evolution Candidate Sync"}.issubset(node_names), sorted(node_names)),
        check("单人白名单锁定本人", workflow.get("nodes", [])[3].get("parameters", {}).get("allowed_receivers") == ["ChenXiaoJie"] if len(nodes) > 3 else False, workflow.get("nodes", [])[3].get("parameters", {}) if len(nodes) > 3 else {}),
        check("既有源入口存在", not missing_sources, missing_sources),
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
        "灰度包": str(latest),
        "生成stdout": completed.stdout[-2000:],
    }
    log_dir = root / "04日志" / "股票n8n长期观察闭环灰度包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = log_dir / f"stock-n8n-long-observation-loop-gray-package-verify-{stamp}.json"
    latest_json = log_dir / "stock-n8n-long-observation-loop-gray-package-verify-最新.json"
    output_md = log_dir / f"stock-n8n-long-observation-loop-gray-package-verify-{stamp}.md"
    latest_md = log_dir / "stock-n8n-long-observation-loop-gray-package-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({
        "总体状态": result["总体状态"],
        "通过": result["通过"],
        "失败": result["失败"],
        "输出": str(latest_json),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
