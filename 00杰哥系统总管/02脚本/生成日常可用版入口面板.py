"""
名称：生成日常可用版入口面板.py
作用：读取最新日常可用版入口检查报告和入口注册表，生成本机可读的日常可用入口操作索引。
触发方式：python 生成日常可用版入口面板.py
依赖：Python 标准库；daily-usable-entry-check-最新.json；日常可用版入口注册表.json。
所属系统：00杰哥系统总管
安全边界：只读取新系统日志并写入新系统文档；不触发服务、不发送企业微信、不写旧系统。
创建/修改记录：2026-04-27 创建日常可用版入口面板生成脚本；2026-04-29 升级为读取当前入口注册表并输出用户操作索引。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def command_for_entry(entry: dict[str, Any]) -> str:
    entry_type = entry.get("类型")
    if entry_type in {"http", "ollama", "http_openapi"}:
        return entry.get("检查URL", "")
    if entry_type == "script_json":
        script = str(entry.get("脚本", ""))
        if script.lower().endswith(".ps1"):
            return f"powershell -NoProfile -ExecutionPolicy Bypass -File \"{script}\""
        return f"python \"{script}\""
    if entry_type == "docker_redis":
        return f"docker exec {entry.get('容器', '')} redis-cli ping"
    if entry_type == "docker_postgres":
        return f"docker exec {entry.get('容器', '')} pg_isready"
    return ""


def escape_table(value: Any) -> str:
    return str(value or "").replace("|", "｜").replace("\r", " ").replace("\n", " ")


def read_evolution_pending(root: Path) -> dict[str, Any]:
    pending_items: list[str] = []
    stock_eval = root / "03杰哥进化系统" / "03数据" / "86股票共振规则周度进化评估" / "股票共振规则周度进化评估_最新.json"
    tax_eval = root / "03杰哥进化系统" / "03数据" / "87税收政策引用周度进化评估" / "税收政策引用周度进化评估_最新.json"
    if stock_eval.exists():
        data = load_json(stock_eval)
        suggestion = str(data.get("参数调整建议") or "")
        if suggestion and "建议将" in suggestion and "暂不建议" not in suggestion and "不足" not in suggestion:
            pending_items.append(f"股票共振规则：{suggestion}")
    if tax_eval.exists():
        data = load_json(tax_eval)
        suggestions = data.get("规则更新建议", []) if isinstance(data, dict) else []
        for item in suggestions[:3]:
            pending_items.append(f"税收政策引用：{item}")
    return {
        "待阅数量": len(pending_items),
        "提醒": "；".join(pending_items) if pending_items else "暂无需要人工处理的进化建议。",
        "来源": f"{stock_eval}；{tax_eval}",
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    report_path = manager / "04日志" / "日常可用版" / "daily-usable-entry-check-最新.json"
    registry_path = manager / "01配置" / "日常可用版入口注册表.json"
    if not report_path.exists():
        raise FileNotFoundError(f"缺少入口检查报告：{report_path}")
    report = load_json(report_path)
    registry = load_json(registry_path)
    evolution_pending = read_evolution_pending(root)
    registry_by_name = {item.get("名称"): item for item in registry.get("入口", [])}
    lines = [
        "# 日常可用版入口操作索引",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 入口总数：{report['汇总']['入口总数']}",
        f"- 必检入口：{report['汇总']['必检入口数']}",
        f"- 可用入口：{report['汇总']['可用']}",
        f"- 不可用入口：{report['汇总']['不可用']}",
        "",
        "## 可用入口",
        "",
        "| 名称 | 归属 | 类型 | 状态 | 用途 | 访问或检查方式 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report.get("入口状态", []):
        registry_entry = registry_by_name.get(item.get("名称"), {})
        status = "可用" if item.get("可用") else "不可用"
        command = command_for_entry(registry_entry)
        lines.append(
            f"| {escape_table(item.get('名称'))} | {escape_table(item.get('归属'))} | {escape_table(item.get('类型'))} | {status} | {escape_table(item.get('用途'))} | `{escape_table(command)}` |"
        )
    lines.extend([
        "",
        "## 进化信号待阅",
        "",
        f"- 待阅数量：{evolution_pending['待阅数量']}",
        f"- 最新提醒：{escape_table(evolution_pending['提醒'])}",
        f"- 来源：`{escape_table(evolution_pending['来源'])}`",
        "",
        "## 用户常用入口",
        "",
        "- 企业微信股票查询：在企业微信智能机器人对话框输入股票名称或代码，例如 `新易盛`、`300502`。",
        "- 股票图形报告公网入口：`http://43.167.210.211/wecom-bot/message?card=latest`。",
        "- 本机股票助手健康检查：`http://127.0.0.1:19300/health`。",
        "- 本机企业微信桥接健康检查：`http://127.0.0.1:19302/health`。",
        "- 总体进度面板：`D:\\杰哥智能化系统\\00杰哥系统总管\\03数据\\日常可用版总览\\日常可用版总览面板_最新.md`。",
        "",
        "## 安全边界",
        "",
        "- 本面板只展示本机入口状态和操作索引。",
        "- 不触发 n8n 工作流。",
        "- 不发送企业微信。",
        "- 不写入旧系统。",
        "- 税收业务继续暂停。",
    ])
    output = manager / "07文档" / "日常可用版入口面板.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"输出": str(output), "不可用": report["汇总"]["不可用"]}, ensure_ascii=False))
    return 0 if report["汇总"]["不可用"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
