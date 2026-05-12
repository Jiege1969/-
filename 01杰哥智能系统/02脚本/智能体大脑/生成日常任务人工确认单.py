"""
名称：生成日常任务人工确认单.py
作用：从日常任务队列生成任务人工确认单，明确路由、风险、允许动作、禁止动作和放行条件。
触发方式：python 生成日常任务人工确认单.py；验证阶段可使用 --demo。
依赖：Python 标准库；任务队列 jsonl 文件；日常任务入口规则.json。
所属系统：01杰哥智能系统
安全边界：只读取任务队列并写入确认单；不执行任务、不触发n8n、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建日常任务人工确认单生成脚本。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def build_confirmation(task: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    route = task.get("路由结果", {})
    paused = route.get("是否暂停") is True
    risk = route.get("风险等级", "低")
    return {
        "确认单ID": f"CONF-{task.get('任务ID')}",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task.get("任务ID"),
        "任务类型": route.get("任务类型"),
        "目标系统": route.get("目标系统"),
        "风险等级": risk,
        "任务摘要": task.get("原始内容"),
        "当前状态": "暂停待人工决定" if paused else "待人工确认",
        "建议处理方式": route.get("建议处理方式"),
        "允许动作": [
            "生成只读计划",
            "生成草稿",
            "生成检查清单",
            "写入本系统日志和临时演练目录"
        ],
        "禁止动作": rules.get("禁止自动执行", []),
        "放行条件": [
            "人工确认任务目标、范围和输入材料",
            "人工确认是否允许进入对应系统的真实链路",
            "高风险动作另行生成回滚方案",
            "税收业务保持暂停，除非用户明确恢复施工"
        ],
        "安全边界": {
            "是否执行任务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否执行税收业务": False
        },
    }


def write_markdown(confirmations: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# 日常任务人工确认单",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 确认单数量：{len(confirmations)}",
        "",
    ]
    for item in confirmations:
        lines.extend([
            f"## {item['确认单ID']}",
            "",
            f"- 任务ID：{item['任务ID']}",
            f"- 任务类型：{item['任务类型']}",
            f"- 目标系统：{item['目标系统']}",
            f"- 风险等级：{item['风险等级']}",
            f"- 当前状态：{item['当前状态']}",
            f"- 建议处理方式：{item['建议处理方式']}",
            f"- 任务摘要：{item['任务摘要']}",
            "",
            "允许动作：",
        ])
        lines.extend(f"- {value}" for value in item["允许动作"])
        lines.append("")
        lines.append("禁止动作：")
        lines.extend(f"- {value}" for value in item["禁止动作"])
        lines.append("")
        lines.append("放行条件：")
        lines.extend(f"- {value}" for value in item["放行条件"])
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="read temporary rehearsal queue")
    args = parser.parse_args()
    root = system_root()
    rules = load_json(root / "01杰哥智能系统" / "01配置" / "日常任务入口规则.json")
    if args.demo:
        queue = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "任务队列_最新.jsonl"
        output_dir = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "人工确认单"
    else:
        queue = root / "01杰哥智能系统" / "03数据" / "任务队列" / "01待人工确认" / "任务队列_最新.jsonl"
        output_dir = root / "01杰哥智能系统" / "03数据" / "任务队列" / "02人工确认单"
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = read_jsonl(queue)
    confirmations = [build_confirmation(task, rules) for task in tasks]
    json_output = output_dir / "日常任务人工确认单_最新.json"
    md_output = output_dir / "日常任务人工确认单_最新.md"
    text = json.dumps(confirmations, ensure_ascii=False, indent=2)
    json_output.write_text(text, encoding="utf-8")
    write_markdown(confirmations, md_output)
    print(json.dumps({"确认单数量": len(confirmations), "输出": str(json_output)}, ensure_ascii=False))
    return 0 if confirmations else 1


if __name__ == "__main__":
    raise SystemExit(main())
