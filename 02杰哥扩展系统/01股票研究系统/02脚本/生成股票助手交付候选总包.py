# -*- coding: utf-8 -*-
"""
名称：生成股票助手交付候选总包.py
作用：汇总股票助手交付前用户阅读摘要、交付材料索引、剩余动作清单、只读状态面板和进度口径，生成材料侧交付候选总包。
触发方式：python 生成股票助手交付候选总包.py
依赖：Python标准库；股票助手交付候选总包规则.json；股票助手交付前用户阅读摘要包_最新.json；股票助手交付材料索引包_最新.json；股票助手交付前剩余动作清单包_最新.json；股票助手交付前只读总状态面板_最新.json；股票企业微信真实灰度未确认拦截包_最新.json；股票企业微信首轮真实灰度测试记录包_最新.json；进度回答标准.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付候选总包脚本。
标识：stock-assistant-delivery-candidate-package-generate
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


def stock_progress(answer_standard: dict[str, Any]) -> dict[str, Any]:
    for item in answer_standard.get("重点子系统", []):
        if item.get("子系统") == "股票分析系统":
            return item
    return {}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手交付候选总包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、候选结论",
        "",
        f"- 是否具备材料侧交付候选条件：{report['是否具备材料侧交付候选条件']}",
        f"- 当前股票系统进度：{report['股票系统进度'].get('当前进度', '')}",
        f"- 可交付使用还需有效工作时间：{report['股票系统进度'].get('可交付使用还需有效工作时间', '')}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、候选交付条件",
        "",
    ]
    for key, value in report["候选交付判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、核心材料入口", ""])
    for item in report["核心材料入口"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 四、仍需人工确认", ""])
    for item in report["仍需人工确认"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    manager = sys_root / "00杰哥系统总管"
    rule_path = root / "01配置" / "股票助手交付候选总包规则.json"
    paths = {
        "用户阅读摘要包": root / "03数据" / "51交付前用户阅读摘要" / "股票助手交付前用户阅读摘要包_最新.json",
        "交付材料索引包": root / "03数据" / "49交付材料索引" / "股票助手交付材料索引包_最新.json",
        "剩余动作清单包": root / "03数据" / "50交付前剩余动作清单" / "股票助手交付前剩余动作清单包_最新.json",
        "只读总状态面板": root / "03数据" / "48交付前只读总状态面板" / "股票助手交付前只读总状态面板_最新.json",
        "未确认拦截包": root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json",
        "首轮测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
        "股票助手独立使用说明": root / "07文档" / "股票助手独立使用说明.md",
        "进度回答标准": manager / "01配置" / "进度回答标准.json",
    }
    rule = load_json(rule_path)
    user_summary = load_json(paths["用户阅读摘要包"])
    material_index = load_json(paths["交付材料索引包"])
    remaining = load_json(paths["剩余动作清单包"])
    dashboard = load_json(paths["只读总状态面板"])
    guard = load_json(paths["未确认拦截包"])
    test_record = load_json(paths["首轮测试记录包"])
    progress_standard = load_json(paths["进度回答标准"])

    judgement = {
        "用户阅读摘要已通过": user_summary.get("是否具备用户阅读摘要条件") is True,
        "交付材料索引已通过": material_index.get("是否具备交付材料索引条件") is True,
        "剩余动作清单已通过": remaining.get("是否具备剩余动作清单条件") is True,
        "只读总状态面板已通过": dashboard.get("是否适合继续低风险施工") is True,
        "未确认拦截仍启用": guard.get("是否启用未确认拦截") is True,
        "首轮真实灰度测试仍未执行": test_record.get("当前测试状态") == "未执行",
        "核心入口文件存在": paths["股票助手独立使用说明"].exists(),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "候选交付原则": rule.get("候选交付原则", []),
        "候选交付判定": judgement,
        "股票系统进度": stock_progress(progress_standard),
        "核心材料入口": [
            {"名称": "股票助手独立使用说明", "路径": str(paths["股票助手独立使用说明"])},
            {"名称": "用户阅读摘要包", "路径": str(paths["用户阅读摘要包"])},
            {"名称": "交付材料索引包", "路径": str(paths["交付材料索引包"])},
            {"名称": "交付前剩余动作清单包", "路径": str(paths["剩余动作清单包"])},
            {"名称": "交付前只读总状态面板", "路径": str(paths["只读总状态面板"])},
        ],
        "仍需人工确认": rule.get("仍需人工确认", []),
        "是否具备材料侧交付候选条件": passed,
        "当前结论": "股票助手材料侧已具备交付候选条件，可提交用户阅读和确认；真实企业微信发送、n8n启用、OpenClaw真实桥接、服务刷新和交易接口仍未放行。" if passed else "股票助手交付候选总包前置材料不完整，不能提交交付候选。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "52交付候选总包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付候选总包_{stamp}.json"
    latest_json = output_dir / "股票助手交付候选总包_最新.json"
    output_md = output_dir / f"股票助手交付候选总包_{stamp}.md"
    latest_md = output_dir / "股票助手交付候选总包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备材料侧交付候选条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
