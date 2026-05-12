# -*- coding: utf-8 -*-
"""
名称：生成股票助手真实灰度执行手册草案.py
作用：汇总交付提交包、未确认拦截和首轮测试记录，生成股票助手真实企业微信灰度执行手册草案。
触发方式：python 生成股票助手真实灰度执行手册草案.py
依赖：Python标准库；股票助手真实灰度执行手册草案规则.json；股票助手交付提交包_最新.json；股票企业微信真实灰度未确认拦截包_最新.json；股票企业微信首轮真实灰度测试记录包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手真实灰度执行手册草案脚本。
标识：stock-assistant-real-gray-execution-manual-draft-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手真实灰度执行手册草案",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、草案结论",
        "",
        f"- 是否具备执行手册草案条件：{report['是否具备执行手册草案条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置判定",
        "",
    ]
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、执行阶段草案", ""])
    for item in report["执行阶段"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、回滚条件", ""])
    for item in report["回滚条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、验收口径", ""])
    for item in report["验收口径"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、仍需人工确认", ""])
    for item in report["仍需人工确认"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 七、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手真实灰度执行手册草案规则.json"
    paths = {
        "交付提交包": root / "03数据" / "54交付提交包" / "股票助手交付提交包_最新.json",
        "未确认拦截包": root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json",
        "首轮测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
    }
    rule = load_json(rule_path)
    submit_package = load_json(paths["交付提交包"])
    guard = load_json(paths["未确认拦截包"])
    test_record = load_json(paths["首轮测试记录包"])
    actions = rule.get("安全边界", {})
    judgement = {
        "交付提交包通过": submit_package.get("是否具备提交用户阅读确认条件") is True,
        "未确认拦截仍启用": guard.get("是否启用未确认拦截") is True,
        "首轮真实灰度测试仍未执行": test_record.get("当前测试状态") == "未执行",
        "执行阶段完整": len(rule.get("执行阶段", [])) >= 8,
        "回滚条件完整": len(rule.get("回滚条件", [])) >= 7,
        "验收口径完整": len(rule.get("验收口径", [])) >= 6,
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "草案原则": rule.get("草案原则", []),
        "前置判定": judgement,
        "执行阶段": rule.get("执行阶段", []),
        "回滚条件": rule.get("回滚条件", []),
        "验收口径": rule.get("验收口径", []),
        "仍需人工确认": rule.get("仍需人工确认", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备执行手册草案条件": passed,
        "当前结论": "真实灰度执行手册草案已具备，可作为人工确认后的执行依据；当前仍不执行导入、启用、发送、重启或写库动作。" if passed else "真实灰度执行手册草案前置材料不完整，不能作为执行依据。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "55真实灰度执行手册草案"
    latest_json = output_dir / "股票助手真实灰度执行手册草案_最新.json"
    latest_md = output_dir / "股票助手真实灰度执行手册草案_最新.md"
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备执行手册草案条件": passed, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
