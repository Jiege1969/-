# -*- coding: utf-8 -*-
"""
名称：生成股票日常使用包.py
作用：汇总股票研究系统状态摘要、候选池、L5日报、复盘账本和使用入口，生成可单独阅读的股票日常使用包。
触发方式：python 生成股票日常使用包.py
依赖：Python标准库；股票研究系统状态摘要_最新.json；重点关注池候选池_最新.json；L5深度研究报告_最新.json；复盘闭环账本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取新股票研究系统本地数据；只写03数据/17日常使用包；不调用大模型；不写旧系统；不重启服务；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票日常使用包生成脚本。
标识：stock-daily-usage-package-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path, limit: int = 7000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8-sig")
    return text[:limit]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stock_line(item: dict[str, Any]) -> str:
    name = item.get("名称", "")
    code = item.get("代码", "")
    score = item.get("系统评分", "")
    risks = "；".join(item.get("风险", [])) or "暂无突出风险，仍需人工复核。"
    basis = "；".join(item.get("依据", [])[:3]) or "暂无足够依据。"
    return f"- {name}（{code}）：评分{score}。依据：{basis}。风险：{risks}"


def build_markdown(package: dict[str, Any]) -> str:
    status = package["状态摘要"]
    health = status.get("数据健康度", {})
    candidates = package["候选池"].get("候选池", {})
    l5_items = candidates.get("L5深度研究", [])
    l6_items = candidates.get("L6轻度关注", [])
    l7_items = candidates.get("L7系统过滤", [])
    ledgers = status.get("复盘账本状态", {})
    lines = [
        "# 股票研究日常使用包",
        "",
        f"生成时间：{package['生成时间']}",
        "",
        "声明：本使用包只用于研究辅助，不构成投资建议，不连接券商接口，不自动交易。",
        "",
        "## 一、今日可用结论",
        "",
        f"- 重点关注池：{status.get('重点关注池数量', 0)}只",
        f"- 行情快照：{status.get('行情快照数量', 0)}条",
        f"- 数据健康度：{health.get('健康等级', '未知')}，指标成功{health.get('指标成功数量', 0)}/{health.get('股票数量', 0)}，成功率{health.get('成功率', 0)}%",
        f"- 使用建议：{health.get('建议', '先查看数据健康度，再阅读候选池。')}",
        "",
        "## 二、今日重点候选",
        "",
        f"- L5深度研究：{len(l5_items)}只",
        f"- L6轻度关注：{len(l6_items)}只",
        f"- L7系统过滤：{len(l7_items)}只",
        "",
        "### L5深度研究",
        "",
    ]
    if l5_items:
        lines.extend(stock_line(item) for item in l5_items)
    else:
        lines.append("- 暂无L5候选。")
    lines.extend(["", "### L6轻度关注", ""])
    if l6_items:
        lines.extend(stock_line(item) for item in l6_items)
    else:
        lines.append("- 暂无L6候选。")
    lines.extend(["", "### L7系统过滤", ""])
    if l7_items:
        lines.extend(stock_line(item) for item in l7_items)
    else:
        lines.append("- 暂无L7过滤项。")
    lines.extend([
        "",
        "## 三、复盘账本状态",
        "",
        f"- 系统判断账：{'已生成' if ledgers.get('系统判断账', {}).get('存在') else '未生成'}",
        f"- 人工决策账：{'已生成' if ledgers.get('人工决策账', {}).get('存在') else '未生成'}",
        f"- 结果验证账：{'已生成' if ledgers.get('结果验证账', {}).get('存在') else '未生成'}",
        f"- 经验提炼账：{'已生成' if ledgers.get('经验提炼账', {}).get('存在') else '未生成'}",
        "",
        "## 四、今天怎么用",
        "",
        "1. 先看数据健康度。若为降级或暂停，只做观察和复盘，不强化结论。",
        "2. 再看L5深度研究候选，决定是否继续观察或人工确认升级。",
        "3. 对不认可的候选，写入人工反馈，作为后续进化样本。",
        "4. 等后续T+1、T+3、T+5、T+20结果验证，不凭单日信号下结论。",
        "",
        "## 五、反馈格式",
        "",
        "- 继续观察：股票名称，原因",
        "- 暂不关注：股票名称，原因",
        "- 无价值：股票名称，原因",
        "- 确认L4：股票名称，原因（必须人工确认）",
        "",
        "## 六、入口",
        "",
        "- 本地股票助手：http://127.0.0.1:19300/",
        "- 最新L5日报：`03数据\\03研究报告\\L5深度研究候选日报_最新.md`",
        "- 最新状态摘要：`03数据\\16状态摘要\\股票研究系统状态摘要_最新.md`",
        "- 最新日常使用包：`03数据\\17日常使用包\\股票研究日常使用包_最新.md`",
        "",
        "## 七、安全边界",
        "",
        "- 不连接券商接口。",
        "- 不自动下单。",
        "- 不写旧系统。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不写正式业务库。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    status_path = root / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json"
    candidate_path = root / "03数据" / "14候选池" / "重点关注池候选池_最新.json"
    l5_path = root / "03数据" / "15深度研究" / "L5深度研究报告_最新.json"
    l5_markdown_path = root / "03数据" / "03研究报告" / "L5深度研究候选日报_最新.md"
    status = load_json(status_path, {}) or {}
    candidates = load_json(candidate_path, {"候选池": {}}) or {"候选池": {}}
    l5_report = load_json(l5_path, {}) or {}
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态摘要文件": str(status_path),
        "候选池文件": str(candidate_path),
        "L5报告文件": str(l5_path),
        "状态摘要": status,
        "候选池": candidates,
        "L5深度研究": l5_report,
        "L5日报片段": read_text(l5_markdown_path, 5000),
        "安全边界": {
            "是否调用大模型": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否写旧系统": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "03数据" / "17日常使用包"
    json_output = output_dir / "股票研究日常使用包_最新.json"
    json_latest = output_dir / "股票研究日常使用包_最新.json"
    md_output = output_dir / "股票研究日常使用包_最新.md"
    md_latest = output_dir / "股票研究日常使用包_最新.md"
    write_json(json_output, package)
    write_json(json_latest, package)
    markdown = build_markdown(package)
    write_text(md_output, markdown)
    write_text(md_latest, markdown)
    pool = candidates.get("候选池", {})
    print(json.dumps({"L5": len(pool.get("L5深度研究", [])), "L6": len(pool.get("L6轻度关注", [])), "L7": len(pool.get("L7系统过滤", [])), "输出": str(md_output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
