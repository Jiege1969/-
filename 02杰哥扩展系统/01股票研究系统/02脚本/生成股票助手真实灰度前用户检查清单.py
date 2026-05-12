# -*- coding: utf-8 -*-
"""
名称：生成股票助手真实灰度前用户检查清单.py
作用：生成用户在股票助手进入真实企业微信灰度前的阅读检查清单、不适合放行信号和放行后仍禁止事项。
触发方式：python 生成股票助手真实灰度前用户检查清单.py
依赖：Python标准库；股票助手真实灰度前用户检查清单规则.json；股票助手真实灰度放行前最终只读总包_最新.json；股票助手真实灰度人工放行确认书模板_最新.json；股票助手首轮真实灰度测试消息样例_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手真实灰度前用户检查清单脚本。
标识：stock-assistant-real-gray-user-checklist-generate
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
        "# 股票助手真实灰度前用户检查清单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、清单结论",
        "",
        f"- 是否具备用户检查清单条件：{report['是否具备用户检查清单条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置材料判定",
        "",
    ]
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、用户检查项", ""])
    for item in report["用户检查项"]:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## 四、不适合放行信号", ""])
    for item in report["不适合放行信号"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、放行后仍禁止事项", ""])
    for item in report["放行后仍禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手真实灰度前用户检查清单规则.json"
    paths = {
        "真实灰度放行前最终只读总包": root / "03数据" / "60真实灰度放行前最终只读总包" / "股票助手真实灰度放行前最终只读总包_最新.json",
        "真实灰度人工放行确认书模板": root / "03数据" / "59真实灰度人工放行确认书模板" / "股票助手真实灰度人工放行确认书模板_最新.json",
        "首轮真实灰度测试消息样例": root / "03数据" / "57首轮真实灰度测试消息样例" / "股票助手首轮真实灰度测试消息样例_最新.json",
    }
    rule = load_json(rule_path)
    loaded = {name: load_json(path) for name, path in paths.items()}
    actions = rule.get("安全边界", {})
    judgement = {
        "最终只读总包通过": loaded["真实灰度放行前最终只读总包"].get("是否具备放行前最终只读总包条件") is True,
        "人工放行确认书模板通过": loaded["真实灰度人工放行确认书模板"].get("是否具备人工放行确认书模板条件") is True,
        "测试消息样例通过": loaded["首轮真实灰度测试消息样例"].get("是否具备测试消息样例条件") is True,
        "用户检查项完整": len(rule.get("用户检查项", [])) >= 8,
        "不适合放行信号完整": len(rule.get("不适合放行信号", [])) >= 7,
        "放行后仍禁止事项完整": len(rule.get("放行后仍禁止事项", [])) >= 7,
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "检查原则": rule.get("检查原则", []),
        "前置判定": judgement,
        "用户检查项": rule.get("用户检查项", []),
        "不适合放行信号": rule.get("不适合放行信号", []),
        "放行后仍禁止事项": rule.get("放行后仍禁止事项", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备用户检查清单条件": passed,
        "当前结论": "真实灰度前用户检查清单已具备；该清单只用于用户阅读判断，不代表已经放行任何真实动作。" if passed else "真实灰度前用户检查清单前置材料不完整，不能作为用户检查入口。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "61真实灰度前用户检查清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手真实灰度前用户检查清单_{stamp}.json"
    latest_json = output_dir / "股票助手真实灰度前用户检查清单_最新.json"
    output_md = output_dir / f"股票助手真实灰度前用户检查清单_{stamp}.md"
    latest_md = output_dir / "股票助手真实灰度前用户检查清单_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备用户检查清单条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
