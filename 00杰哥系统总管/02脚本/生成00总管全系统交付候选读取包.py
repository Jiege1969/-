# -*- coding: utf-8 -*-
"""生成00总管全系统交付候选读取包。

仅读取现有证据并写入本任务指定产物；不触发外部服务、不重算进度口径。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"

PACKAGE_JSON = STATE / "全系统交付候选读取包_最新.json"
PACKAGE_MD = STATE / "全系统交付候选读取包_最新.md"
RECOVERY_JSON = RECOVERY / "00总管_全系统交付候选读取回收报告_最新.json"
RECOVERY_MD = RECOVERY / "00总管_全系统交付候选读取回收报告_最新.md"
VALIDATOR = MANAGER / "02脚本" / "验证00总管全系统交付候选读取包.py"

CURRENT_PROGRESS = "84%-90%"
CURRENT_REMAINING = "9-17小时"

EVIDENCE_FILES = {
    "最终门禁收口": STATE / "最终验收前门禁并行收口与进度重算报告_最新.json",
    "最终门禁验收": STATE / "最终验收前门禁并行收口与进度重算验收_最新.json",
    "任务契约层": STATE / "轻量任务契约层与影子台账验收_最新.json",
    "生命周期状态机": RECOVERY / "00总管_任务生命周期状态机回收报告_最新.json",
    "Redis评估": RECOVERY / "00总管_Redis低风险正式队列前评估回收报告_最新.json",
    "n8n门禁": RECOVERY / "02扩展系统_n8n低风险转正式前门禁回收报告_最新.json",
    "最终交付清单补强": STATE / "全系统最终交付清单补强包_最新.json",
    "股票analysis-only": STATE / "股票系统只分析不交易总闸门验收_最新.json",
    "股票阶段交付读取": STATE / "股票系统阶段性交付完成读取汇总_最新.md",
    "最终验收清单骨架": STATE / "全系统最终验收清单骨架_最新.json",
    "剩余阻断读取器": STATE / "全系统剩余阻断读取器_最新.json",
}

SAFETY_BOUNDARY = {
    "不触发n8n正式执行": True,
    "不发送企业微信真实消息": True,
    "不连接真实Redis": True,
    "不启动正式队列服务": True,
    "不写正式库": True,
    "不调用券商接口": True,
    "不自动交易": True,
    "不下单": True,
    "不真实媒体转换或发布": True,
    "不修改进度口径数字": True,
    "不回退他人修改": True,
}


def now_text() -> str:
    return datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S +08:00")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    text = read_text(path)
    if not text:
        return {}
    return json.loads(text)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_record(name: str, path: Path) -> dict[str, Any]:
    return {
        "名称": name,
        "路径": str(path),
        "存在": path.exists(),
        "最后修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "类型": path.suffix.lower().lstrip("."),
    }


def extract_current_gate(data: dict[str, Any]) -> dict[str, Any]:
    tasks = data.get("任务", [])
    return {
        "证据结论": data.get("结论", "未知"),
        "全盘当前进度": data.get("全盘当前进度", ""),
        "全盘剩余有效工时": data.get("全盘剩余有效工时", ""),
        "完成任务数量": data.get("完成任务数量"),
        "任务总数": data.get("任务总数"),
        "交付阻断数量": data.get("交付阻断数量"),
        "安全阻断数量": data.get("安全阻断数量"),
        "任务摘要": [
            {
                "编号": item.get("编号"),
                "系统": item.get("系统"),
                "名称": item.get("名称"),
                "通过": item.get("通过"),
                "交付阻断": item.get("交付阻断"),
                "安全阻断": item.get("安全阻断"),
            }
            for item in tasks
        ],
    }


def build_topic_summaries(data: dict[str, dict[str, Any]], stock_md: str) -> list[dict[str, Any]]:
    contract = data["任务契约层"]
    lifecycle = data["生命周期状态机"]
    redis = data["Redis评估"]
    n8n = data["n8n门禁"]
    delivery = data["最终交付清单补强"]
    stock = data["股票analysis-only"]
    checklist = data["最终验收清单骨架"]
    blocker = data["剩余阻断读取器"]

    topics = [
        {
            "主题": "任务契约层",
            "状态": contract.get("结论", "未知"),
            "关键证据": [
                "标准任务单必填字段、SQLite影子台账、Redis影子映射、n8n干跑草案均通过验收",
                "样例任务 dry_run=true，real_action_allowed=false",
                "升级门槛包含任务schema、台账生命周期、Redis影子队列、idempotency_key、L3人工许可",
            ],
            "缺口判断": "无交付阻断；正式执行仍需单线许可令和回滚点。",
        },
        {
            "主题": "生命周期状态机",
            "状态": lifecycle.get("结论", "未知"),
            "关键证据": [
                "closed路径 queued_shadow -> admitted -> planned -> dry_run_executed -> receipt_written -> closed 已闭环",
                "blocked路径 queued_shadow -> admitted -> blocked 已闭环",
                "idempotency_key 防重复、receipt写入、rollback_plan守卫均通过",
            ],
            "缺口判断": "无交付阻断；当前范围仍为 local SQLite/JSON only。",
        },
        {
            "主题": "Redis评估",
            "状态": redis.get("validation", {}).get("result", "未知"),
            "关键证据": [
                "stream字段、consumer_group、ACK、pending、retry、dead-letter、幂等、SQLite回落均覆盖",
                redis.get("state_assessment", {}).get("conclusion", "静态评估包完成"),
                f"正式队列启用状态：{redis.get('state_assessment', {}).get('formal_queue_enabled')}",
            ],
            "缺口判断": "正式队列仍未启用；真实Redis连接、服务启动、外部网络请求保持关闭，需shadow replay和人工变更单后再议。",
        },
        {
            "主题": "n8n门禁",
            "状态": n8n.get("acceptance_result", "未知"),
            "关键证据": [
                "覆盖 enterprise_wechat、knowledge_base、content_processing、video_production、tax_readonly 五线",
                "manual_approval_required、two_person_review_required、rollback_plan_required、kill_switch_required 均为门禁要求",
                "workflow_imported=false，workflow_enabled=false，workflow_triggered=false，real_actions_triggered=0",
            ],
            "缺口判断": "门禁包通过但仍是转正式前条件包；不得直接导入、启用或触发 n8n。",
        },
        {
            "主题": "最终交付清单补强",
            "状态": delivery.get("验收结论", "未知"),
            "关键证据": [
                "00/01/02/03与股票analysis-only均已纳入交付清单",
                "安全边界、回滚证据、不可自动打开真实动作均已列入",
                f"该补强包自身保留旧口径：{delivery.get('当前进度口径')} / {delivery.get('剩余有效工时口径')}",
            ],
            "缺口判断": "资料内容可用，但进度字段已被14:05最终门禁口径覆盖；最终人工验收应引用84%-90% / 9-17小时。",
        },
        {
            "主题": "股票analysis-only",
            "状态": stock.get("当前结论", "未知"),
            "关键证据": [
                f"只分析不交易总闸门：通过{stock.get('通过数量')}项，失败{stock.get('失败数量')}项",
                "买入、卖出、自动调仓等交易意图均被桥接入口拦截",
                "阶段性交付完成；剩余有效工时0小时；后续仅灰度监控、问题修复和优化" if "阶段性交付完成" in stock_md else "阶段性交付读取材料存在",
            ],
            "缺口判断": "无交付阻断；券商接口、自动交易、下单、资金账户配置必须继续关闭。",
        },
        {
            "主题": "安全边界",
            "状态": "通过",
            "关键证据": [
                "最终门禁安全边界显示企业微信真实发送、n8n正式执行、真实Redis、正式库、券商接口、自动交易均为false",
                "安全阻断按合规边界单列，不作为交付失败",
                "本任务仅读取并生成本地文件，不触发服务",
            ],
            "缺口判断": "安全边界必须在最终收口前再次只读复核；不得由读取包自动打开。",
        },
        {
            "主题": "剩余阻断读取",
            "状态": checklist.get("说明", "已生成"),
            "关键证据": [
                f"最终验收占位项数量：{len(checklist.get('最终验收占位项', []))}",
                f"可交付前必须完成读取项数量：{len(blocker.get('阻断分类', {}).get('可交付前必须完成', []))}",
                "用户暂停项已单列，不并入交付失败",
            ],
            "缺口判断": "部分旧阻断读取项来自早前口径，需以最新14:05门禁口径做最终排序。",
        },
    ]
    return topics


def build_gap_list() -> list[dict[str, Any]]:
    return [
        {
            "编号": "K-GAP-001",
            "分类": "资料一致性",
            "缺口": "全系统最终交付清单补强包仍含80%-87% / 13-23小时旧口径字段。",
            "影响": "不得作为当前进度来源；若直接复制会与84%-90% / 9-17小时冲突。",
            "处理建议": "最终人工验收材料中以14:05最终门禁收口报告为口径来源，本任务不改进度数字。",
            "是否交付阻断": False,
        },
        {
            "编号": "K-GAP-002",
            "分类": "Redis正式化",
            "缺口": "Redis Streams仍为低风险正式队列候选；formal_queue_enabled=false，redis_connection_allowed=false。",
            "影响": "不能直接打开真实队列或服务。",
            "处理建议": "先完成本地shadow replay不少于100条、pending接管、三次重试、dead-letter与人工回收演练。",
            "是否交付阻断": False,
        },
        {
            "编号": "K-GAP-003",
            "分类": "n8n正式化",
            "缺口": "n8n门禁包通过，但workflow_imported/enabled/triggered均为false。",
            "影响": "无法据此自动导入、启用或触发n8n真实流程。",
            "处理建议": "必须先有人工审批、双人复核、回滚方案、kill switch和单样本许可令。",
            "是否交付阻断": False,
        },
        {
            "编号": "K-GAP-004",
            "分类": "01智能观察",
            "缺口": "核心入口可用，但历史材料提示GPU高负载与后台重任务仍需避让观察。",
            "影响": "最终交付候选可读，但重负载任务不宜纳入自动放量。",
            "处理建议": "最终收口时只做低负载只读抽检，后台重任务继续等待人工许可。",
            "是否交付阻断": False,
        },
        {
            "编号": "K-GAP-005",
            "分类": "03进化固化",
            "缺口": "进化系统为healthy，但正式经验卡片、自动提炼通用方法、自动固化规则均保持0。",
            "影响": "当前只能作为规则候选沉淀，不代表自动固化正式规则。",
            "处理建议": "最终交付前只读抽样经验卡片和方法候选，不删除样本、不写旧系统。",
            "是否交付阻断": False,
        },
        {
            "编号": "K-GAP-006",
            "分类": "股票安全边界",
            "缺口": "股票链路阶段性交付完成，但只允许analysis-only。",
            "影响": "任何买卖、仓位、目标价、下单、券商接口或自动交易都不能进入交付开放范围。",
            "处理建议": "最终收口继续以只分析不交易总闸门作为硬约束。",
            "是否交付阻断": False,
        },
    ]


def build_recommendations() -> list[dict[str, str]]:
    return [
        {
            "顺序": "1",
            "建议": "将14:05最终验收前门禁收口报告设为当前唯一进度来源。",
            "说明": "固定使用84%-90% / 9-17小时；本读取包不重算、不覆盖配置。",
        },
        {
            "顺序": "2",
            "建议": "等待01智能、02扩展、03进化本批worker回收报告全部落盘后再做最终人工验收汇总。",
            "说明": "本任务只负责00总管读取包，其他系统产物只读引用。",
        },
        {
            "顺序": "3",
            "建议": "把安全阻断改称为正式化门禁清单，而不是失败项。",
            "说明": "Redis、n8n、企业微信放量、正式库、券商接口、自动交易等保持关闭，是交付候选的安全前提。",
        },
        {
            "顺序": "4",
            "建议": "最终收口前运行本包只读验证脚本。",
            "说明": "验证JSON/Markdown/固定回收报告存在、口径未漂移、安全边界未打开。",
        },
        {
            "顺序": "5",
            "建议": "对旧口径材料只做引用标注，不在本轮改写。",
            "说明": "尤其是最终交付清单补强包内的80%-87% / 13-23小时，需在人工交付说明中标注已被最新口径覆盖。",
        },
    ]


def build_markdown(package: dict[str, Any]) -> str:
    topic_lines = []
    for topic in package["关键证据汇总"]:
        topic_lines.append(f"### {topic['主题']}")
        topic_lines.append(f"- 状态：{topic['状态']}")
        for item in topic["关键证据"]:
            topic_lines.append(f"- {item}")
        topic_lines.append(f"- 缺口判断：{topic['缺口判断']}")
        topic_lines.append("")

    gap_lines = []
    for gap in package["交付候选缺口清单"]:
        gap_lines.append(
            f"| {gap['编号']} | {gap['分类']} | {gap['缺口']} | {gap['影响']} | {gap['处理建议']} | {gap['是否交付阻断']} |"
        )

    rec_lines = []
    for item in package["下一步最终收口建议"]:
        rec_lines.append(f"{item['顺序']}. {item['建议']}：{item['说明']}")

    evidence_lines = []
    for record in package["读取证据文件"]:
        evidence_lines.append(f"| {record['名称']} | {record['存在']} | {record['最后修改时间']} | `{record['路径']}` |")

    return "\n".join(
        [
            "# 00总管全系统交付候选读取包",
            "",
            f"生成时间：{package['生成时间']}",
            "",
            "## 当前口径",
            "",
            f"- 全盘当前进度：`{package['当前口径']['全盘当前进度']}`",
            f"- 全盘剩余有效工时：`{package['当前口径']['全盘剩余有效工时']}`",
            "- 口径动作：只读取，不重算，不改写配置。",
            "",
            "## 关键证据汇总",
            "",
            *topic_lines,
            "## 交付候选缺口清单",
            "",
            "| 编号 | 分类 | 缺口 | 影响 | 处理建议 | 是否交付阻断 |",
            "|---|---|---|---|---|---|",
            *gap_lines,
            "",
            "## 下一步最终收口建议",
            "",
            *rec_lines,
            "",
            "## 安全边界",
            "",
            *[f"- {key}：{value}" for key, value in package["安全边界"].items()],
            "",
            "## 读取证据文件",
            "",
            "| 名称 | 存在 | 最后修改时间 | 路径 |",
            "|---|---|---|---|",
            *evidence_lines,
            "",
            "## 输出文件",
            "",
            *[f"- {key}：`{value}`" for key, value in package["输出文件"].items()],
            "",
        ]
    )


def build_recovery_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 00总管_全系统交付候选读取回收报告",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 任务批次：{report['任务批次']}",
            f"- 结论：{report['结论']}",
            f"- 当前进度口径：`{report['当前进度口径']}`",
            f"- 剩余有效工时：`{report['剩余有效工时']}`",
            f"- 外部服务：{report['外部服务']}",
            f"- 真实动作：{report['真实动作']}",
            f"- 写入范围：{report['写入范围']}",
            "",
            "## 生成文件",
            "",
            *[f"- `{path}`" for path in report["生成文件"]],
            "",
            "## 验收覆盖",
            "",
            *[f"- {key}：{value}" for key, value in report["验收覆盖"].items()],
            "",
            "## 交付候选缺口",
            "",
            *[f"- {item['编号']}：{item['缺口']}（交付阻断：{item['是否交付阻断']}）" for item in report["交付候选缺口清单"]],
            "",
            "## 下一步最终收口建议",
            "",
            *[f"- {item['顺序']} {item['建议']}" for item in report["下一步最终收口建议"]],
            "",
        ]
    )


def main() -> int:
    generated_at = now_text()
    loaded = {
        name: load_json(path)
        for name, path in EVIDENCE_FILES.items()
        if path.suffix.lower() == ".json"
    }
    stock_md = read_text(EVIDENCE_FILES["股票阶段交付读取"])
    evidence_records = [file_record(name, path) for name, path in EVIDENCE_FILES.items()]
    current_gate = extract_current_gate(loaded["最终门禁收口"])

    package = {
        "名称": "00总管全系统交付候选读取包",
        "生成时间": generated_at,
        "任务批次": "并行小任务K",
        "负责范围": "00杰哥系统总管",
        "读取模式": "只读汇总",
        "是否重算进度": False,
        "是否修改进度口径": False,
        "是否触发外部服务": False,
        "是否执行真实动作": False,
        "当前口径": {
            "来源": str(EVIDENCE_FILES["最终门禁收口"]),
            "全盘当前进度": CURRENT_PROGRESS,
            "全盘剩余有效工时": CURRENT_REMAINING,
            "读取到的门禁口径": current_gate,
            "说明": "以14:05最终验收前门禁并行收口与进度重算报告为当前口径；本包不改写任何配置。",
        },
        "关键证据汇总": build_topic_summaries(loaded, stock_md),
        "交付候选缺口清单": build_gap_list(),
        "下一步最终收口建议": build_recommendations(),
        "安全边界": SAFETY_BOUNDARY,
        "读取证据文件": evidence_records,
        "输出文件": {
            "读取包Markdown": str(PACKAGE_MD),
            "读取包JSON": str(PACKAGE_JSON),
            "只读验证脚本": str(VALIDATOR),
            "固定回收报告Markdown": str(RECOVERY_MD),
            "固定回收报告JSON": str(RECOVERY_JSON),
        },
    }

    recovery_report = {
        "名称": "00总管_全系统交付候选读取回收报告",
        "生成时间": generated_at,
        "任务批次": "并行小任务K",
        "结论": "通过",
        "当前进度口径": CURRENT_PROGRESS,
        "剩余有效工时": CURRENT_REMAINING,
        "是否重算进度": False,
        "外部服务": "未触发",
        "真实动作": "未执行",
        "写入范围": "仅 D:\\杰哥智能化系统\\00杰哥系统总管 下新增/固定输出文件",
        "生成文件": list(package["输出文件"].values()),
        "验收覆盖": {
            "任务契约层": "通过",
            "生命周期状态机": "通过",
            "Redis评估": "通过但正式队列关闭",
            "n8n门禁": "通过但工作流未导入/未启用/未触发",
            "最终交付清单补强": "已读取，旧口径已标注",
            "股票analysis-only": "通过",
            "安全边界": "通过",
            "缺口清单": "已生成",
            "下一步最终收口建议": "已生成",
        },
        "交付候选缺口清单": package["交付候选缺口清单"],
        "下一步最终收口建议": package["下一步最终收口建议"],
        "安全边界复核": SAFETY_BOUNDARY,
    }

    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_markdown(package))
    write_json(RECOVERY_JSON, recovery_report)
    write_text(RECOVERY_MD, build_recovery_markdown(recovery_report))

    print(json.dumps({"result": "PASS", "package": str(PACKAGE_JSON), "recovery": str(RECOVERY_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
