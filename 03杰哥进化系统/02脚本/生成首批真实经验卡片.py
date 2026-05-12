"""
名称：生成首批真实经验卡片.py
作用：把本轮 v3 搭建中已经发生的关键问题和成功做法沉淀为稳定经验卡片。
触发方式：python 生成首批真实经验卡片.py
依赖：Python 标准库。
所属系统：03杰哥进化系统
安全边界：只写入 03杰哥进化系统经验数据目录；不修改业务系统配置，不自动固化规则。
创建/修改记录：2026-04-26 创建首批真实经验卡片生成脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def card_dir() -> Path:
    target = system_root() / "03数据" / "01问题卡片"
    target.mkdir(parents=True, exist_ok=True)
    return target


def success_dir() -> Path:
    target = system_root() / "03数据" / "02成功经验"
    target.mkdir(parents=True, exist_ok=True)
    return target


def failure_dir() -> Path:
    target = system_root() / "03数据" / "03失败教训"
    target.mkdir(parents=True, exist_ok=True)
    return target


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def cards() -> list[dict[str, Any]]:
    generated_at = now_text()
    return [
        {
            "卡片ID": "EXP-20260426-001",
            "生成时间": generated_at,
            "卡片类型": "同类复用",
            "来源系统": "00杰哥系统总管",
            "来源阶段": "总体验收脚本搭建",
            "问题现象": "总体验收脚本扫描脚本时误匹配自身，导致递归执行和异常进程。",
            "根因分类": "编码问题",
            "根本原因": "脚本发现逻辑没有排除当前运行脚本，自动发现机制缺少自排除边界。",
            "解决办法": "查找候选脚本时排除 `$PSCommandPath`，并为每个子步骤增加超时控制。",
            "验证方法": "运行总体验收，确认步骤数量固定且无递归进程。",
            "可复用逻辑": "任何自动发现机制都必须排除自身，并设置超时和失败边界。",
            "可迁移场景": ["脚本扫描", "插件发现", "工作流草案生成", "日志聚合"],
            "不可迁移边界": "手工指定单一文件执行时不需要自发现排除。",
            "经验状态": "已提炼",
            "是否建议固化": True,
        },
        {
            "卡片ID": "EXP-20260426-002",
            "生成时间": generated_at,
            "卡片类型": "类似借鉴",
            "来源系统": "02杰哥扩展系统/00公共组件",
            "来源阶段": "统一消息出口与 OpenClaw 回环测试",
            "问题现象": "Windows 子进程读取中文 JSON 输出时，中文键名被乱码破坏，导致验收脚本取不到字段。",
            "根因分类": "编码问题",
            "根本原因": "机器消费的 stdout 和人类阅读的 UTF-8 中文文件混用，PowerShell 默认编码造成歧义。",
            "解决办法": "机器消费的自检 stdout 使用 ASCII JSON；落盘文件继续使用 UTF-8 中文。",
            "验证方法": "运行统一消息出口和 OpenClaw 验收，确认字段能稳定读取。",
            "可复用逻辑": "机器接口优先无歧义，用户文档保持可读性，两者分层输出。",
            "可迁移场景": ["验收脚本", "n8n草案生成", "消息队列", "跨进程调用"],
            "不可迁移边界": "面向用户的正式文档不能为了机器读取牺牲中文可读性。",
            "经验状态": "已提炼",
            "是否建议固化": True,
        },
        {
            "卡片ID": "EXP-20260426-003",
            "生成时间": generated_at,
            "卡片类型": "类似借鉴",
            "来源系统": "01杰哥智能系统/知识库",
            "来源阶段": "知识库全文索引和税收政策索引",
            "问题现象": "元数据伴随文件可能被索引脚本误当作正文资料进入全文索引。",
            "根因分类": "数据问题",
            "根本原因": "控制数据和业务正文放在同一目录时，扫描规则没有区分文件角色。",
            "解决办法": "所有扫描正文资料的脚本排除 `.元数据.json`，元数据只用于治理和复核。",
            "验证方法": "运行知识库底座和税收业务底座验收，确认索引结构正常。",
            "可复用逻辑": "数据目录可以共存，但控制文件和业务文件必须按规则分层处理。",
            "可迁移场景": ["知识库", "税收政策", "股票数据快照", "视频素材登记"],
            "不可迁移边界": "如果目录物理隔离，则可减少后缀排除规则。",
            "经验状态": "已提炼",
            "是否建议固化": True,
        },
        {
            "卡片ID": "EXP-20260426-004",
            "生成时间": generated_at,
            "卡片类型": "异类归纳",
            "来源系统": "02杰哥扩展系统/00公共组件",
            "来源阶段": "企业微信助手安全底座",
            "问题现象": "真实企业微信和 n8n 接入前，无法直接证明生产闭环可用，但直接接入又有误发和误触发风险。",
            "根因分类": "架构问题",
            "根本原因": "外部真实系统既是可用性验证对象，也是风险来源，必须先验证链路形状再做真实接入。",
            "解决办法": "先建立本地回环：模拟企微消息 -> 标准请求 -> 模拟响应 -> 统一消息出口。",
            "验证方法": "OpenClaw 边缘网关验收和统一消息出口验收通过。",
            "可复用逻辑": "先验证链路形状，再做只读联通，最后做受控真实联调。",
            "可迁移场景": ["企业微信", "n8n", "Qdrant", "数据库写入", "自动化办公"],
            "不可迁移边界": "回环通过不代表真实生产可用，仍需真实依赖联通和小范围测试。",
            "经验状态": "已提炼",
            "是否建议固化": True,
        },
        {
            "卡片ID": "EXP-20260426-005",
            "生成时间": generated_at,
            "卡片类型": "异类归纳",
            "来源系统": "02杰哥扩展系统/05税收业务系统",
            "来源阶段": "税收政策全文索引",
            "问题现象": "政策文件可以被解析和检索，但有效状态未核实前不能作为正式依据。",
            "根因分类": "理解偏差",
            "根本原因": "可检索不等于可信，可引用不等于可作为正式结论。",
            "解决办法": "索引中保留有效状态和可作为正式依据字段，待核实资料只能进入预览和辅助分析。",
            "验证方法": "税收业务底座验收确认政策全文索引结构和安全控制字段存在。",
            "可复用逻辑": "高风险领域必须区分资料可见、资料可信、结论可用三个层级。",
            "可迁移场景": ["股票研究", "税收业务", "系统运维", "企业微信主动推送"],
            "不可迁移边界": "低风险草稿类任务可降低人工确认要求，但仍需保留来源记录。",
            "经验状态": "已提炼",
            "是否建议固化": True,
        },
        {
            "卡片ID": "EXP-20260426-006",
            "生成时间": generated_at,
            "卡片类型": "同类复用",
            "来源系统": "03杰哥进化系统",
            "来源阶段": "进化系统底座验收",
            "问题现象": "Python 脚本中误把布尔值写成 JSON 风格 `true`，导致脚本运行失败。",
            "根因分类": "编码问题",
            "根本原因": "配置文件语法和代码语法混淆，JSON 的 `true` 不能直接用于 Python 代码。",
            "解决办法": "Python 代码中使用 `True`，JSON 文件中使用 `true`，并通过 py_compile 先做语法检查。",
            "验证方法": "重新运行进化系统底座验收，结果 10/10 通过。",
            "可复用逻辑": "配置和代码边界必须清晰，跨语言布尔值、空值和字符串规则不能混用。",
            "可迁移场景": ["Python脚本", "JSON配置", "PowerShell脚本", "n8n表达式"],
            "不可迁移边界": "模板文本中引用语法示例时不属于运行代码。",
            "经验状态": "已提炼",
            "是否建议固化": True,
        },
    ]


def write_card(card: dict[str, Any]) -> Path:
    file_name = f"{card['卡片ID']}_{card['卡片类型']}.json"
    output = card_dir() / file_name
    output.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    if card["卡片类型"] in {"同类复用", "类似借鉴"}:
        (success_dir() / file_name).write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        (failure_dir() / file_name).write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> int:
    outputs = [str(write_card(card)) for card in cards()]
    latest = card_dir() / "首批真实经验卡片_最新.json"
    latest.write_text(json.dumps({"生成时间": now_text(), "卡片数量": len(outputs), "文件": outputs}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"卡片数量": len(outputs), "输出清单": str(latest)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
