# -*- coding: utf-8 -*-
"""
名称：生成股票草案吸收报告.py
作用：根据旧草案吸收规则生成当前股票研究系统的吸收报告和施工清单。
触发方式：python 生成股票草案吸收报告.py
依赖：Python标准库；旧草案吸收规则.json；动态样本池规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读旧草案吸收规则和当前配置；只写入新系统股票模块03数据与07文档；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口。
创建/修改记录：2026-04-28 创建旧草案吸收报告生成脚本。
标识：stock-draft-absorption-report-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 旧股票草案吸收报告")
    lines.append("")
    lines.append(f"生成时间：{report['生成时间']}")
    lines.append("")
    lines.append("## 一、结论")
    lines.append("")
    lines.append(report["结论"])
    lines.append("")
    lines.append("## 二、已吸收内容")
    lines.append("")
    for item in report["已吸收内容"]:
        lines.append(f"- {item['草案内容']}：{item['吸收方式']}（{item['状态']}）")
    lines.append("")
    lines.append("## 三、8级分层")
    lines.append("")
    lines.append("| 层级 | 名称 | 数量上限 | 权限边界 | 系统动作 |")
    lines.append("|---|---|---:|---|---|")
    for item in report["8级分层"]:
        lines.append(f"| {item['层级']} | {item['名称']} | {item['数量上限']} | {item['权限边界']} | {item['系统动作']} |")
    lines.append("")
    lines.append("## 四、分层过滤漏斗")
    lines.append("")
    for item in report["分层过滤漏斗"]:
        lines.append(f"{item['步骤']}. {item['名称']}：{item['规则']}，输出：{item['输出']}。")
    lines.append("")
    lines.append("## 五、暂不吸收内容")
    lines.append("")
    for item in report["暂不吸收内容"]:
        lines.append(f"- {item['内容']}：{item['原因']}")
    lines.append("")
    lines.append("## 六、下一步施工顺序")
    lines.append("")
    for index, item in enumerate(report["下一步施工顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    absorption = load_json(root / "01配置" / "旧草案吸收规则.json")
    dynamic_pool = load_json(root / "01配置" / "动态样本池规则.json")
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "吸收规则": str(root / "01配置" / "旧草案吸收规则.json"),
        "动态样本池规则": str(root / "01配置" / "动态样本池规则.json"),
        "结论": "旧草案的核心价值可以吸收：800只核心样本池、8级分层、四层过滤漏斗、多数据源容错、盘后日报、反馈和回测闭环。当前不吸收旧目录、不提前放开真实推送、模型微调和交易接口。",
        "目标规模": dynamic_pool.get("目标规模", {}),
        "已吸收内容": absorption.get("已吸收内容", []),
        "8级分层": absorption.get("8级分层", []),
        "分层过滤漏斗": absorption.get("分层过滤漏斗", []),
        "指标参数": absorption.get("指标参数", {}),
        "多数据源容错": absorption.get("多数据源容错", []),
        "日报结构": absorption.get("日报结构", []),
        "暂不吸收内容": absorption.get("暂不吸收内容", []),
        "下一步施工顺序": absorption.get("下一步施工顺序", []),
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据" / "08草案吸收"
    doc_dir = root / "07文档"
    json_output = data_dir / f"旧股票草案吸收报告_{timestamp}.json"
    json_latest = data_dir / "旧股票草案吸收报告_最新.json"
    md_output = doc_dir / "旧股票草案吸收报告.md"
    write_json(json_output, report)
    write_json(json_latest, report)
    write_text(md_output, build_markdown(report))
    print(json.dumps({"输出": str(json_output), "文档": str(md_output), "吸收项": len(report["已吸收内容"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
