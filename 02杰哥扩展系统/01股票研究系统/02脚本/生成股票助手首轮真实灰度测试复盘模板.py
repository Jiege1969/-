# -*- coding: utf-8 -*-
"""
名称：生成股票助手首轮真实灰度测试复盘模板.py
作用：生成股票助手首轮真实企业微信灰度测试后的复盘模板、原因归类、进化输入和样本清理标准。
触发方式：python 生成股票助手首轮真实灰度测试复盘模板.py
依赖：Python标准库；股票助手首轮真实灰度测试复盘模板规则.json；股票助手首轮真实灰度测试消息样例_最新.json；股票助手真实灰度执行手册草案_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不自动清理。
创建/修改记录：2026-04-28 创建股票助手首轮真实灰度测试复盘模板脚本。
标识：stock-assistant-first-real-gray-test-review-template-generate
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


def empty_review_rows(samples: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in samples:
        row = {field: "" for field in fields}
        row["测试编号"] = sample.get("编号", "")
        row["原始输入"] = sample.get("输入", "")
        row["实际路由"] = sample.get("预期路由", "")
        row["是否通过"] = "待测试"
        rows.append(row)
    return rows


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手首轮真实灰度测试复盘模板",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、模板结论",
        "",
        f"- 是否具备复盘模板条件：{report['是否具备复盘模板条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置判定",
        "",
    ]
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、复盘记录模板", ""])
    for row in report["复盘记录模板"]:
        lines.append(f"- {row['测试编号']}：{row['原始输入']}，状态={row['是否通过']}")
    lines.extend(["", "## 四、原因归类", ""])
    for item in report["原因归类"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、进化系统输入", ""])
    for item in report["进化输入"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、样本清理标准", ""])
    for item in report["清理标准"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 七、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手首轮真实灰度测试复盘模板规则.json"
    paths = {
        "首轮真实灰度测试消息样例": root / "03数据" / "57首轮真实灰度测试消息样例" / "股票助手首轮真实灰度测试消息样例_最新.json",
        "真实灰度执行手册草案": root / "03数据" / "55真实灰度执行手册草案" / "股票助手真实灰度执行手册草案_最新.json",
        "首轮真实灰度测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
    }
    rule = load_json(rule_path)
    samples = load_json(paths["首轮真实灰度测试消息样例"])
    manual = load_json(paths["真实灰度执行手册草案"])
    test_record = load_json(paths["首轮真实灰度测试记录包"])
    actions = rule.get("安全边界", {})
    messages = samples.get("测试消息", [])
    fields = rule.get("复盘字段", [])
    judgement = {
        "测试消息样例通过": samples.get("是否具备测试消息样例条件") is True,
        "执行手册草案通过": manual.get("是否具备执行手册草案条件") is True,
        "首轮真实灰度测试仍未执行": test_record.get("当前测试状态") == "未执行",
        "复盘字段完整": len(fields) >= 12,
        "原因归类完整": len(rule.get("原因归类", [])) >= 10,
        "进化输入完整": len(rule.get("进化输入", [])) >= 7,
        "清理标准完整": len(rule.get("清理标准", [])) >= 4,
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "复盘原则": rule.get("复盘原则", []),
        "前置判定": judgement,
        "复盘字段": fields,
        "复盘记录模板": empty_review_rows(messages, fields),
        "原因归类": rule.get("原因归类", []),
        "进化输入": rule.get("进化输入", []),
        "清理标准": rule.get("清理标准", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备复盘模板条件": passed,
        "当前结论": "首轮真实灰度测试复盘模板已具备，可用于测试后沉淀经验、归因问题和输入进化系统；当前不执行真实测试、不清理样本。" if passed else "首轮真实灰度测试复盘模板前置材料不完整，不能作为复盘依据。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "58首轮真实灰度测试复盘模板"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手首轮真实灰度测试复盘模板_{stamp}.json"
    latest_json = output_dir / "股票助手首轮真实灰度测试复盘模板_最新.json"
    output_md = output_dir / f"股票助手首轮真实灰度测试复盘模板_{stamp}.md"
    latest_md = output_dir / "股票助手首轮真实灰度测试复盘模板_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备复盘模板条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
