# -*- coding: utf-8 -*-
"""
名称：生成股票n8n日内报告闭环与晨报推送策略包.py
作用：固化股票系统随问随答、收市观察、半夜规律分析、开市前晨报推送和学习沉淀闭环。
触发方式：python 生成股票n8n日内报告闭环与晨报推送策略包.py
依赖：Python标准库；258长期观察闭环灰度包；259模型与时段调度策略包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地260策略包；不导入n8n；不启用n8n；不真实发送企业微信；不群发；不接券商；不交易；不重载服务；不自动转正式规则。
标识：stock-n8n-intraday-report-loop-morning-push-package-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return module_root().parents[1]


def evolution_root() -> Path:
    return project_root() / "03杰哥进化系统"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_daily_loop(root: Path, evo: Path) -> list[dict[str, Any]]:
    return [
        {
            "环节": "轻量随问随答",
            "建议时间": "全天",
            "触发方式": "用户在企业微信或本地入口主动提问。",
            "产物": "单股短回复、图文报告入口、当前研究口径。",
            "模型": ["qwen3:14b", "qwen2.5:7b兜底"],
            "n8n角色": "不参与即时主链路，避免增加延迟。",
            "学习沉淀": "用户追问、否定、补充要求写入反馈日志，作为口径优化样本。",
        },
        {
            "环节": "收市后每日观察",
            "建议时间": "15:40-18:30",
            "触发方式": "n8n定时或人工触发本地股票主动研究闭环。",
            "产物": "分层日报、候选池、重点观察股票、第二天候选推荐草案。",
            "模型": ["规则评分优先", "qwen3:14b少量候选摘要", "deepseek-r1:32b复杂风险复核"],
            "n8n角色": "负责调度本地分析，不承载判断核心。",
            "学习沉淀": "所有候选、未入选原因、证据缺口进入日内观察账。",
        },
        {
            "环节": "半夜宏观规律分析",
            "建议时间": "00:30-05:30",
            "触发方式": "n8n低峰窗口触发长期观察和复盘归纳。",
            "产物": "市场风格、行业轮动、前日推送质量复核、替代候选、次日重点关注更新。",
            "模型": ["deepseek-r1:32b", "qwen3:30b", "mychen76/Fin-R1:Q5", "martain7r/finance-llama-8b:q4_k_m", "qwen3:14b归纳"],
            "n8n角色": "适合编排重模型和长期复盘，写本地结果，不夜间打扰用户。",
            "学习沉淀": "把推送后表现、判断偏差、更优候选和用户反馈整理为进化候选。",
        },
        {
            "环节": "开市前晨报推送",
            "建议时间": "08:20-08:40",
            "触发方式": "n8n读取半夜复盘和收市候选，生成一条本人晨报摘要。",
            "产物": "开市前重点关注晨报：保留关注、降级观察、替换候选、风险提醒、今日观察条件。",
            "模型": ["qwen3:14b归纳", "deepseek-r1:32b仅用于重大矛盾复核"],
            "n8n角色": "只负责组装和受控投递；真实发送仍走本人单条灰度闸口。",
            "学习沉淀": "晨报本身作为学习样本，晚间复盘其有效性。",
        },
    ]


def build_learning_ledger_schema() -> dict[str, Any]:
    return {
        "账本名称": "股票主动推送学习沉淀账",
        "记录粒度": "每一次候选、推送、纠偏、用户反馈、复盘都保留一条可追溯记录。",
        "核心字段": [
            "记录ID",
            "生成时间",
            "所属环节",
            "股票代码",
            "股票名称",
            "入选原因",
            "证据链摘要",
            "风险提醒",
            "观察条件",
            "是否进入晨报",
            "是否被替换",
            "替换原因",
            "用户反馈",
            "晚间复盘结论",
            "进化候选状态",
            "原始产物路径",
        ],
        "纠偏规则": [
            "如果头天推送股票晚间复盘发现证据不充分，第二天晨报必须提示降级或风险复核。",
            "如果半夜发现更有价值候选，第二天晨报必须说明替换原因，而不是悄悄换名单。",
            "如果用户反馈某类报告太空泛，后续报告必须提高财务、风险或行业依据的显示权重。",
            "纠偏只改变下一次报告和候选，不产生交易执行动作。",
        ],
    }


def build_morning_briefing_sample(root: Path, now: datetime) -> dict[str, Any]:
    source_push = root / "03数据" / "136推送草案" / "股票企微推送草案_最新.json"
    source_feedback = root / "04日志" / "用户反馈" / "反馈日志.json"
    return {
        "名称": "开市前晨报样例",
        "样例日期": "2026-05-11",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "定位": "本地晨报内容样例，只用于验收字段和口径，不发送。",
        "上游参考": {
            "推送草案": str(source_push),
            "用户反馈日志": str(source_feedback),
            "260策略包": str(root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"),
        },
        "今日重点关注": [
            {
                "代码": "sh688047",
                "名称": "龙芯中科",
                "关注口径": "半导体方向观察样本，结合用户反馈保留在晨报。",
                "观察条件": "观察162.91附近承接质量、行业强度延续性和公开证据完整度。",
                "风险提醒": "趋势持续性和证据完整度仍需复核，未完成正文核验前不升级口径。",
            },
            {
                "代码": "sh688012",
                "名称": "中微公司",
                "关注口径": "设备链方向观察样本，用于跟踪行业强度和资金活跃度是否延续。",
                "观察条件": "观察368.77附近承接质量，若弱于353.72附近则转入风险复核。",
                "风险提醒": "行业强度分和资金活跃度需要连续数据确认。",
            },
            {
                "代码": "sz002466",
                "名称": "天齐锂业",
                "关注口径": "有色金属方向观察样本，用于观察行业风格切换。",
                "观察条件": "观察78.43附近承接质量、成交活跃度和锂行业公开信息变化。",
                "风险提醒": "行业波动较大，证据链需补充公开财务与行业材料。",
            },
        ],
        "昨日推送复盘": {
            "来源": str(source_push),
            "昨日状态": "草案未发送，只保留为本地研究摘要。",
            "复盘结论": "上一版草案提示当前暂无完全符合重点研究条件的对象，因此今日晨报继续采用观察和风险复核口径。",
            "需要纠偏": "把证据缺口写明，避免只给名单不说明原因。",
        },
        "新增或替换候选": [
            {
                "代码": "sh688347",
                "名称": "华虹公司",
                "类型": "新增观察",
                "原因": "同属半导体链，行业强度与技术结构稳定，适合作为同主题补充观察。",
                "原始产物路径": str(source_push),
            },
            {
                "代码": "sh688795",
                "名称": "摩尔线程",
                "类型": "暂不进入晨报主列表",
                "原因": "活跃度较高但证据缺口偏大，先留作风险复核样本。",
                "原始产物路径": str(source_push),
            },
        ],
        "降级或风险复核": [
            {
                "对象": "所有未完成人工正文核验的候选",
                "处理": "维持观察或风险复核，不升级为更高优先级。",
                "原因": "公告、财务、行业事件正文仍需人工核验。",
            }
        ],
        "今日观察条件": [
            "行业强度、资金活跃度、技术结构三类信号至少两类延续，再保留晨报关注。",
            "若公开证据无法补齐，晚间复盘必须记录证据缺口并考虑降级。",
            "若用户反馈某只标的需要继续跟踪，次日晨报必须说明保留原因。",
        ],
        "证据缺口": [
            "公告正文未核验。",
            "最新财务正文未核验。",
            "行业事件来源仍需补充正式或权威材料。",
            "半夜宏观规律分析尚未形成可验证结论。",
        ],
        "非投资建议声明": "本晨报为研究观察摘要，仅供人工复核，不构成投资建议，不触发任何交易执行。",
        "安全边界": {
            "是否接券商": False,
            "是否交易": False,
            "是否真实发送企业微信": False,
            "是否群发": False,
            "是否导入n8n": False,
            "是否启用n8n": False,
            "是否触发n8n": False,
        },
    }


def build_learning_ledger_sample(root: Path, now: datetime) -> dict[str, Any]:
    source_push = root / "03数据" / "136推送草案" / "股票企微推送草案_最新.json"
    source_feedback = root / "04日志" / "用户反馈" / "反馈日志.json"
    source_review = root / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.json"
    records = [
        {
            "记录ID": "stock-push-learn-20260511-001",
            "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "推送对象": "sh688047 龙芯中科",
            "入选原因": "半导体方向观察样本，用户反馈记录显示继续跟踪。",
            "风险提醒": "趋势持续性和证据完整度仍需补充验证。",
            "观察条件": "观察162.91附近承接质量、行业强度延续性和公开证据完整度。",
            "是否进入晨报": True,
            "是否被替换": False,
            "替换原因": "未替换，因用户反馈与主题观察价值仍成立。",
            "用户反馈": "继续跟踪 sh688047 闭环验收测试反馈。",
            "晚间复盘结论": "保留观察，晚间重点补证据缺口，不升级口径。",
            "进化候选状态": "候选：晨报保留原因表达样本。",
            "原始产物路径": str(source_feedback),
        },
        {
            "记录ID": "stock-push-learn-20260511-002",
            "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "推送对象": "sh688012 中微公司",
            "入选原因": "设备链方向观察样本，行业强度与资金活跃度需要连续验证。",
            "风险提醒": "公开证据和事件正文未补齐前，只能维持观察。",
            "观察条件": "观察368.77附近承接质量，弱于353.72附近则进入风险复核。",
            "是否进入晨报": True,
            "是否被替换": False,
            "替换原因": "未替换，作为半导体设备链代表保留。",
            "用户反馈": "暂无新增反馈。",
            "晚间复盘结论": "等待晚间复盘补充行业与财务正文依据。",
            "进化候选状态": "候选：设备链观察条件表达样本。",
            "原始产物路径": str(source_push),
        },
        {
            "记录ID": "stock-push-learn-20260511-003",
            "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "推送对象": "sh688795 摩尔线程",
            "入选原因": "行业主题活跃，但证据缺口偏大。",
            "风险提醒": "波动和证据不足风险较高，需要风险复核。",
            "观察条件": "先核验公告、财务和行业事件正文，再判断是否恢复晨报主列表。",
            "是否进入晨报": False,
            "是否被替换": True,
            "替换原因": "由华虹公司补位，原因是同主题证据表达更清晰。",
            "用户反馈": "暂无新增反馈。",
            "晚间复盘结论": "暂缓进入晨报主列表，列入风险复核样本。",
            "进化候选状态": "候选：高活跃但证据不足的降级样本。",
            "原始产物路径": str(source_push),
        },
        {
            "记录ID": "stock-push-learn-20260511-004",
            "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
            "推送对象": "sh688347 华虹公司",
            "入选原因": "同属半导体链，行业强度和技术结构稳定，作为新增观察补位。",
            "风险提醒": "仍需补齐公开证据和正文核验。",
            "观察条件": "观察138.18附近承接质量、行业强度延续性和晚间复盘证据补齐情况。",
            "是否进入晨报": True,
            "是否被替换": False,
            "替换原因": "新增补位对象。",
            "用户反馈": "暂无新增反馈。",
            "晚间复盘结论": "作为补位观察样本进入晨报，晚间复盘验证补位质量。",
            "进化候选状态": "候选：替换说明表达样本。",
            "原始产物路径": str(source_push),
        },
    ]
    return {
        "名称": "股票主动推送学习沉淀账样例",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "定位": "本地样例账，只用于字段验收和后续学习口径沉淀，不发送、不写正式规则。",
        "来源": {
            "推送草案": str(source_push),
            "反馈日志": str(source_feedback),
            "复盘状态面板": str(source_review),
        },
        "字段": [
            "推送对象",
            "入选原因",
            "风险提醒",
            "观察条件",
            "是否进入晨报",
            "是否被替换",
            "替换原因",
            "用户反馈",
            "晚间复盘结论",
            "进化候选状态",
            "原始产物路径",
        ],
        "记录": records,
        "安全边界": {
            "是否接券商": False,
            "是否交易": False,
            "是否真实发送企业微信": False,
            "是否群发": False,
            "是否导入n8n": False,
            "是否启用n8n": False,
            "是否触发n8n": False,
        },
    }


def build_morning_briefing_markdown(sample: dict[str, Any]) -> str:
    lines = [
        "# 开市前晨报样例",
        "",
        f"- 样例日期：{sample['样例日期']}",
        f"- 生成时间：{sample['生成时间']}",
        f"- 定位：{sample['定位']}",
        "",
        "## 今日重点关注",
        "",
    ]
    for item in sample["今日重点关注"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：{item['关注口径']}观察条件：{item['观察条件']}风险提醒：{item['风险提醒']}")
    lines.extend([
        "",
        "## 昨日推送复盘",
        "",
        f"- 昨日状态：{sample['昨日推送复盘']['昨日状态']}",
        f"- 复盘结论：{sample['昨日推送复盘']['复盘结论']}",
        f"- 需要纠偏：{sample['昨日推送复盘']['需要纠偏']}",
        "",
        "## 新增或替换候选",
        "",
    ])
    for item in sample["新增或替换候选"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：{item['类型']}；原因：{item['原因']}")
    lines.extend(["", "## 降级或风险复核", ""])
    for item in sample["降级或风险复核"]:
        lines.append(f"- {item['对象']}：{item['处理']}；原因：{item['原因']}")
    lines.extend(["", "## 今日观察条件", ""])
    for item in sample["今日观察条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 证据缺口", ""])
    for item in sample["证据缺口"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 非投资建议声明", "", sample["非投资建议声明"], ""])
    return "\n".join(lines)


def build_learning_ledger_markdown(ledger: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送学习沉淀账样例",
        "",
        f"- 生成时间：{ledger['生成时间']}",
        f"- 定位：{ledger['定位']}",
        "",
        "| 推送对象 | 入选原因 | 风险提醒 | 观察条件 | 是否进入晨报 | 是否被替换 | 替换原因 | 用户反馈 | 晚间复盘结论 | 进化候选状态 | 原始产物路径 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in ledger["记录"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["推送对象"],
                    item["入选原因"],
                    item["风险提醒"],
                    item["观察条件"],
                    "是" if item["是否进入晨报"] else "否",
                    "是" if item["是否被替换"] else "否",
                    item["替换原因"],
                    item["用户反馈"],
                    item["晚间复盘结论"],
                    item["进化候选状态"],
                    item["原始产物路径"],
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def build_three_stage_reports(now: datetime) -> dict[str, Any]:
    report_date = now.strftime("%Y-%m-%d")
    stocks = [
        {
            "名称": "龙芯中科",
            "代码": "688047.SH",
            "现价": "173.82元",
            "承接位": "183.04元",
            "转强位": "201.72元",
            "风控位": "172.89元",
            "成交活跃度": "0.84倍",
            "行业": "半导体 / 国产CPU",
            "短线动作": "价格跌到183.04元承接位下方，成交活跃度只有0.84倍，短线资金没有形成回流。",
            "短线条件": "明天若不能重新站回183.04元上方，短线不进入优先盯盘；若放量站回183.04元并守住172.89元，再看止跌修复。",
            "止损线": "172.89元",
            "中线逻辑": "国产CPU方向有长期产业逻辑，但当前价格和量能不配合，只有营收改善、亏损收窄或订单催化增强，才从短线样本升级为持续跟踪对象。",
        },
        {
            "名称": "中微公司",
            "代码": "688012.SH",
            "现价": "370.00元",
            "承接位": "389.51元",
            "转强位": "429.26元",
            "风控位": "373.61元",
            "成交活跃度": "0.92倍",
            "行业": "半导体设备",
            "短线动作": "价格低于389.51元承接位，成交活跃度约0.92倍，属于弱修复状态。",
            "短线条件": "明天若放量站回389.51元上方，再看能否冲击429.26元；若开盘后无法收回389.51元，当日降级。",
            "止损线": "373.61元",
            "中线逻辑": "半导体设备链条地位更清楚，后续重点看设备订单、毛利率、国产替代进度和机构关注是否增强。",
        },
        {
            "名称": "摩尔线程",
            "代码": "688795.SH",
            "现价": "703.00元",
            "承接位": "709.13元",
            "转强位": "781.49元",
            "风控位": "680.18元",
            "成交活跃度": "0.78倍",
            "行业": "国产算力 / 半导体",
            "短线动作": "价格贴近709.13元承接位，成交活跃度约0.78倍，弹性在但资金确认不足。",
            "短线条件": "明天若站稳709.13元并明显放量，再看781.49元压力；若跌破680.18元，当日降级。",
            "止损线": "680.18元",
            "中线逻辑": "题材弹性强，但波动大，只在技术位置和行业催化同时配合时提高优先级。",
        },
    ]
    after_close_lines = [
        f"【收盘短线观察｜{report_date}】",
        "",
        "杰哥，您好。今天收盘后，通过纯量价扫描，以下个股在技术面上出现了短线可观察的信号。",
        "",
    ]
    for index, item in enumerate(stocks, start=1):
        after_close_lines.extend([
            f"{index}. {item['名称']}（{item['代码']}）",
            f"- 技术动作：{item['短线动作']}",
            f"- 明天条件：{item['短线条件']}",
            f"- 短线止损参考价：跌破{item['止损线']}则日内不再看。",
            "",
        ])
    after_close_lines.append("以上仅基于今日收盘价量结构筛选，不构成买卖建议，盈亏自负。")

    deep_lines = [
        f"【深度三维研究｜{report_date}】",
        "",
        "杰哥，您好。今晚我对观察池和主线方向做了三维过滤，以下是分层推荐。",
        "",
        "【长线·行业维度】",
        "半导体、国产算力、国产CPU和半导体设备仍是本轮观察池的主方向。长线判断不急于找买点，重点看行业指数周线结构、政策催化、国产替代进度和龙头是否持续强于板块。",
        "龙头样本：中微公司代表设备链，龙芯中科代表国产CPU，摩尔线程代表国产算力弹性方向。",
        "",
        "【中线·成长维度】",
    ]
    for item in stocks:
        deep_lines.append(f"- {item['名称']}（{item['代码']}）：{item['中线逻辑']}")
    deep_lines.extend([
        "",
        "【短线·技术维度】",
    ])
    for item in stocks:
        deep_lines.append(f"- {item['名称']}（{item['代码']}）：触发条件是放量站稳{item['承接位']}上方，强度确认看{item['转强位']}；跌破{item['风控位']}则短线逻辑失效。")
    deep_lines.extend([
        "",
        "操作优先级提示：长线不追高，等回踩支撑；中线关注逻辑是否破坏；短线以触发为唯一依据。",
        "",
        "风险提示：以上仅基于公开数据和历史走势分析，不构成投资建议，盈亏自负。",
    ])

    pre_open_lines = [
        f"【盘前出击排序｜{report_date}】",
        "",
        "杰哥，早上好。今日盘前根据触发条件共振度排序，按优先级别如下，开盘按此观察。",
        "",
        "| 优先级 | 股票 | 今日最关键触发条件 | 今日最关键止损/放弃线 | 说明 |",
        "| --- | --- | --- | --- | --- |",
        "| 高 | 中微公司（688012.SH） | 放量站回389.51元上方 | 跌破373.61元 | 行业位置和公司质量相对清楚，技术位修复后优先盯 |",
        "| 中 | 摩尔线程（688795.SH） | 站稳709.13元并明显放量 | 跌破680.18元 | 弹性强但波动大，只看条件触发 |",
        "| 低 | 龙芯中科（688047.SH） | 先收回183.04元上方 | 跌破172.89元 | 长期题材在，但当前价格和量能不配合 |",
        "",
        "所有标的仅作开盘观察参考，盘中须以走势验证，不符合条件直接放弃，不勉强交易。",
    ]

    return {
        "名称": "股票三阶段报告流程样例",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "报告日期": report_date,
        "定位": "基于现有260日内闭环包生成的三阶段报告样例；不发送、不触发n8n、不接券商、不交易。",
        "股票池基础": {
            "当前使用样本": [f"{item['名称']}（{item['代码']}）" for item in stocks],
            "实际系统已有基础": [
                "01股票池",
                "12技术指标",
                "131用户增强观察池",
                "133行业主题观察池",
                "L6行业主题观察池规则",
                "L5深度研究池规则",
                "258股票n8n长期观察闭环灰度包",
                "259股票n8n长期观察模型与时段调度策略包",
                "260股票n8n日内报告闭环与晨报推送策略包",
            ],
            "真实缺口": [
                "三阶段报告此前未固化为固定产物。",
                "300只/2000只股票池已有规则和脚本，但当前企微演示仍主要使用少量样本。",
                "行业、成长、技术三维指标存在雏形，但还没有统一映射到三份报告的验收字段。",
            ],
        },
        "三阶段报告": {
            "盘后短线复盘": "\n".join(after_close_lines),
            "晚间三维深度分析": "\n".join(deep_lines),
            "盘前出击排序": "\n".join(pre_open_lines),
        },
        "对标对表": [
            {"事项": "三阶段标题固定", "当前状态": "已在260包样例固化", "下一步": "接入股票助手入口和n8n阶段字段"},
            {"事项": "固定称呼和开头", "当前状态": "已在三份样例中固化", "下一步": "加入企业微信输出验收"},
            {"事项": "触发条件和价位", "当前状态": "样例已包含承接位、转强位、风控位", "下一步": "扩大到300只试运行池字段映射"},
            {"事项": "禁止空泛话术", "当前状态": "三阶段样例避开继续观察和需人工复核", "下一步": "加入全量报告禁词扫描"},
            {"事项": "股票池丰富度", "当前状态": "规则和脚本已有，企微报告仍未充分使用", "下一步": "复用300只试运行池并按三阶段出候选"},
            {"事项": "指标完善", "当前状态": "技术、行业、资金、部分财务已有分散产物", "下一步": "形成三阶段字段映射表"},
        ],
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否接券商": False,
            "是否交易": False,
            "是否群发": False,
        },
    }


def build_three_stage_reports_markdown(sample: dict[str, Any]) -> str:
    lines = [
        "# 股票三阶段报告流程样例",
        "",
        f"- 生成时间：{sample['生成时间']}",
        f"- 报告日期：{sample['报告日期']}",
        f"- 定位：{sample['定位']}",
        "",
        "## 真实基础与缺口",
        "",
    ]
    for item in sample["股票池基础"]["实际系统已有基础"]:
        lines.append(f"- 已有：{item}")
    for item in sample["股票池基础"]["真实缺口"]:
        lines.append(f"- 缺口：{item}")
    lines.append("")
    for name, text in sample["三阶段报告"].items():
        lines.extend([f"## {name}", "", text, ""])
    lines.extend(["## 对标对表", "", "| 事项 | 当前状态 | 下一步 |", "| --- | --- | --- |"])
    for item in sample["对标对表"]:
        lines.append(f"| {item['事项']} | {item['当前状态']} | {item['下一步']} |")
    lines.append("")
    return "\n".join(lines)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n日内报告闭环与晨报推送策略包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 日内四段闭环",
        "",
    ]
    for item in report["日内闭环"]:
        lines.append(f"### {item['环节']}")
        lines.append(f"- 建议时间：{item['建议时间']}")
        lines.append(f"- 触发方式：{item['触发方式']}")
        lines.append(f"- 产物：{item['产物']}")
        lines.append(f"- n8n角色：{item['n8n角色']}")
        lines.append(f"- 学习沉淀：{item['学习沉淀']}")
        lines.append("")
    lines.extend([
        "## 晨报口径",
        "",
        "- 晨报是一条发给本人看的摘要，可包含多只股票，但不是群发。",
        "- 晨报要说明为什么继续关注、为什么降级、为什么替换。",
        "- 头天推送如果晚间发现问题，第二天开市前必须告诉使用者。",
        "- 晨报和用户反馈都进入学习沉淀账，供进化系统形成候选。",
        "",
        "## 内容落地产物",
        "",
        f"- 开市前晨报样例：{report['内容落地产物']['开市前晨报样例']['Markdown最新文件']}",
        f"- 股票主动推送学习沉淀账样例：{report['内容落地产物']['股票主动推送学习沉淀账样例']['JSON最新文件']}",
        f"- 三阶段报告流程样例：{report['内容落地产物']['三阶段报告流程样例']['Markdown最新文件']}",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    evo = evolution_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    source_paths = {
        "258长期观察闭环灰度包": root / "03数据" / "258股票n8n长期观察闭环灰度包" / "股票n8n长期观察闭环灰度包_最新.json",
        "259模型与时段调度策略包": root / "03数据" / "259股票n8n长期观察模型与时段调度策略包" / "股票n8n长期观察模型与时段调度策略包_最新.json",
        "股票AI反馈脚本": root / "02脚本" / "记录股票AI反馈.py",
        "进化反馈样本候选脚本": evo / "02脚本" / "生成股票复盘反馈样本接入候选包.py",
        "本地主动研究闭环脚本": root / "02脚本" / "运行股票主动研究闭环_本地.py",
        "推送草案最新文件": root / "03数据" / "136推送草案" / "股票企微推送草案_最新.json",
        "反馈日志": root / "04日志" / "用户反馈" / "反馈日志.json",
        "复盘学习闭环状态面板": root / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.json",
    }
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    log_dir = root / "04日志" / "股票n8n日内报告闭环与晨报推送策略包"
    morning_sample = build_morning_briefing_sample(root, now)
    learning_ledger_sample = build_learning_ledger_sample(root, now)
    three_stage_sample = build_three_stage_reports(now)
    morning_json = out_dir / f"开市前晨报样例_{stamp}.json"
    morning_latest_json = out_dir / "开市前晨报样例_最新.json"
    morning_md = out_dir / f"开市前晨报样例_{stamp}.md"
    morning_latest_md = out_dir / "开市前晨报样例_最新.md"
    ledger_json = out_dir / f"股票主动推送学习沉淀账样例_{stamp}.json"
    ledger_latest_json = out_dir / "股票主动推送学习沉淀账样例_最新.json"
    ledger_md = out_dir / f"股票主动推送学习沉淀账样例_{stamp}.md"
    ledger_latest_md = out_dir / "股票主动推送学习沉淀账样例_最新.md"
    three_stage_json = out_dir / f"股票三阶段报告流程样例_{stamp}.json"
    three_stage_latest_json = out_dir / "股票三阶段报告流程样例_最新.json"
    three_stage_md = out_dir / f"股票三阶段报告流程样例_{stamp}.md"
    three_stage_latest_md = out_dir / "股票三阶段报告流程样例_最新.md"
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "包名": "股票n8n日内报告闭环与晨报推送策略包",
        "当前结论": "股票系统应形成随问随答、收市每日观察、半夜宏观规律分析、开市前晨报推送、晚间复盘纠偏的完整日内闭环。",
        "使用者要求吸收": [
            "轻量性问题要随时问随时回答。",
            "收市后生成每日观察，分析推荐第二天股票。",
            "半夜分析宏观规律和长期观察，得出有价值信息。",
            "开市前1小时左右推送更有价值股票给本人。",
            "推送不仅给使用者看，也是学习沉淀资料。",
            "前一天推送若晚间发现问题或有更好候选，第二天开盘前要提示重点关注变化。",
        ],
        "来源文件状态": {name: file_state(path) for name, path in source_paths.items()},
        "日内闭环": build_daily_loop(root, evo),
        "晨报推送策略": {
            "建议时间": "08:20-08:40",
            "形式": "一条本人晨报摘要，可包含多只重点关注股票；不是群发。",
            "目标接收人": "ChenXiaoJie",
            "默认数量": "3-5只候选写入晨报，一条消息摘要呈现。",
            "必须包含": [
                "今日重点关注",
                "昨日推送复盘",
                "新增或替换候选",
                "降级或风险复核",
                "今日观察条件",
                "证据缺口",
                "非投资建议声明",
            ],
            "真实发送边界": "仍需本人单条灰度发送闸口，策略包不放行真实发送。",
        },
        "学习沉淀账设计": build_learning_ledger_schema(),
        "内容落地产物": {
            "开市前晨报样例": {
                "JSON时间戳文件": str(morning_json),
                "JSON最新文件": str(morning_latest_json),
                "Markdown时间戳文件": str(morning_md),
                "Markdown最新文件": str(morning_latest_md),
            },
            "股票主动推送学习沉淀账样例": {
                "JSON时间戳文件": str(ledger_json),
                "JSON最新文件": str(ledger_latest_json),
                "Markdown时间戳文件": str(ledger_md),
                "Markdown最新文件": str(ledger_latest_md),
            },
            "三阶段报告流程样例": {
                "JSON时间戳文件": str(three_stage_json),
                "JSON最新文件": str(three_stage_latest_json),
                "Markdown时间戳文件": str(three_stage_md),
                "Markdown最新文件": str(three_stage_latest_md),
            },
        },
        "n8n编排草案": {
            "active": False,
            "流程": [
                "15:40 收市轻扫描",
                "18:30 生成每日观察与第二天候选草案",
                "00:30 半夜宏观规律和推送质量复核",
                "06:30 生成晨报候选",
                "08:20 进入本人单条晨报灰度闸口",
                "晚间复盘推送有效性并写学习账",
            ],
            "说明": "本包只生成策略，不导入或启用n8n。",
        },
        "安全边界": {
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n": False,
            "真实发送企业微信": False,
            "群发": False,
            "调用券商接口": False,
            "自动交易": False,
            "自动转正式规则": False,
            "重载19310": False,
            "重载19302": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
        "实际动作": {
            "写本地260策略包": True,
            "读取258和259策略": True,
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n": False,
            "真实发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    log_dir = root / "04日志" / "股票n8n日内报告闭环与晨报推送策略包"
    output_json = out_dir / f"股票n8n日内报告闭环与晨报推送策略包_{stamp}.json"
    latest_json = out_dir / "股票n8n日内报告闭环与晨报推送策略包_最新.json"
    output_md = out_dir / f"股票n8n日内报告闭环与晨报推送策略包_{stamp}.md"
    latest_md = out_dir / "股票n8n日内报告闭环与晨报推送策略包_最新.md"
    log_json = log_dir / f"stock-n8n-intraday-report-loop-morning-push-package-{stamp}.json"
    log_latest = log_dir / "stock-n8n-intraday-report-loop-morning-push-package-最新.json"
    write_json(output_json, report)
    write_json(latest_json, report)
    write_json(morning_json, morning_sample)
    write_json(morning_latest_json, morning_sample)
    write_text(morning_md, build_morning_briefing_markdown(morning_sample))
    write_text(morning_latest_md, build_morning_briefing_markdown(morning_sample))
    write_json(ledger_json, learning_ledger_sample)
    write_json(ledger_latest_json, learning_ledger_sample)
    write_text(ledger_md, build_learning_ledger_markdown(learning_ledger_sample))
    write_text(ledger_latest_md, build_learning_ledger_markdown(learning_ledger_sample))
    write_json(three_stage_json, three_stage_sample)
    write_json(three_stage_latest_json, three_stage_sample)
    write_text(three_stage_md, build_three_stage_reports_markdown(three_stage_sample))
    write_text(three_stage_latest_md, build_three_stage_reports_markdown(three_stage_sample))
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_json, {"生成时间": report["生成时间"], "输出": str(latest_json), "安全边界": report["安全边界"]})
    write_json(log_latest, load_json(log_json, {}))
    print(json.dumps({"状态": "完成", "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
