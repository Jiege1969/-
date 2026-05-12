# -*- coding: utf-8 -*-
"""
名称：生成股票助手交付前最终自检包.py
作用：汇总股票助手材料侧交付前关键包状态，生成最终自检报告和仍未放行边界说明。
触发方式：python 生成股票助手交付前最终自检包.py
依赖：Python标准库；股票助手交付前最终自检规则.json；股票助手交付候选总包_最新.json；股票助手交付前用户阅读摘要包_最新.json；股票助手交付材料索引包_最新.json；股票助手交付前剩余动作清单包_最新.json；股票企业微信真实灰度未确认拦截包_最新.json；股票企业微信首轮真实灰度测试记录包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付前最终自检包脚本。
标识：stock-assistant-delivery-final-selfcheck-package-generate
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
        "# 股票助手交付前最终自检包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、自检结论",
        "",
        f"- 是否通过材料侧最终自检：{report['是否通过材料侧最终自检']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、自检明细",
        "",
    ]
    for key, value in report["自检判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、仍未放行边界", ""])
    for item in report["仍未放行边界"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、核心入口", ""])
    for item in report["核心入口"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手交付前最终自检规则.json"
    paths = {
        "交付候选总包": root / "03数据" / "52交付候选总包" / "股票助手交付候选总包_最新.json",
        "用户阅读摘要包": root / "03数据" / "51交付前用户阅读摘要" / "股票助手交付前用户阅读摘要包_最新.json",
        "交付材料索引包": root / "03数据" / "49交付材料索引" / "股票助手交付材料索引包_最新.json",
        "剩余动作清单包": root / "03数据" / "50交付前剩余动作清单" / "股票助手交付前剩余动作清单包_最新.json",
        "未确认拦截包": root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json",
        "首轮真实灰度测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
        "股票助手独立使用说明": root / "07文档" / "股票助手独立使用说明.md",
    }
    rule = load_json(rule_path)
    candidate = load_json(paths["交付候选总包"])
    user_summary = load_json(paths["用户阅读摘要包"])
    material_index = load_json(paths["交付材料索引包"])
    remaining = load_json(paths["剩余动作清单包"])
    guard = load_json(paths["未确认拦截包"])
    test_record = load_json(paths["首轮真实灰度测试记录包"])

    judgement = {
        "交付候选总包通过": candidate.get("是否具备材料侧交付候选条件") is True,
        "用户阅读摘要通过": user_summary.get("是否具备用户阅读摘要条件") is True,
        "交付材料索引通过": material_index.get("是否具备交付材料索引条件") is True,
        "剩余动作清单通过": remaining.get("是否具备剩余动作清单条件") is True,
        "未确认拦截启用": guard.get("是否启用未确认拦截") is True,
        "首轮真实灰度测试未执行": test_record.get("当前测试状态") == "未执行",
        "核心入口文件存在": paths["股票助手独立使用说明"].exists(),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "最终自检原则": rule.get("最终自检原则", []),
        "自检判定": judgement,
        "核心入口": [
            {"名称": name, "路径": str(path)}
            for name, path in paths.items()
        ],
        "仍未放行边界": rule.get("仍未放行边界", []),
        "是否通过材料侧最终自检": passed,
        "当前结论": "股票助手材料侧最终自检通过，可进入提交用户阅读确认阶段；真实企业微信发送、n8n启用、OpenClaw真实桥接、服务刷新和交易接口仍未放行。" if passed else "股票助手材料侧最终自检未通过，不能进入提交用户确认阶段。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "53交付前最终自检"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付前最终自检包_{stamp}.json"
    latest_json = output_dir / "股票助手交付前最终自检包_最新.json"
    output_md = output_dir / f"股票助手交付前最终自检包_{stamp}.md"
    latest_md = output_dir / "股票助手交付前最终自检包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否通过材料侧最终自检": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
