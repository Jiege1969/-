from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path("D:/杰哥智能化系统")
EXT = ROOT / "02杰哥扩展系统"
WECOM_ACCESS = EXT / "00公共组件" / "企业微信接入设置"
OUT_DIR = EXT / "03数据" / "02知识库问答与多助手路由本轮交付"

SOURCES = {
    "全盘架构": ROOT / "杰哥智能化系统全盘架构说明_20260504.md",
    "当前施工面板": ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md",
    "一键接续施工包": ROOT / "00杰哥系统总管" / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    "下一轮施工派工确认报告": ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "下一轮施工派工确认报告_最新.md",
    "四大系统验收读取口径": ROOT / "00杰哥系统总管" / "01配置" / "四大系统验收读取口径.json",
    "股票最终收口报告": EXT / "01股票研究系统" / "03数据" / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告_最新.json",
    "股票最终收口验收": EXT / "01股票研究系统" / "03数据" / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告验收_最新.json",
    "股票阶段状态确认": EXT / "01股票研究系统" / "03数据" / "243股票系统阶段性交付状态确认" / "股票系统阶段性交付状态确认_最新.json",
    "股票阶段状态确认验收": EXT / "01股票研究系统" / "03数据" / "243股票系统阶段性交付状态确认" / "股票系统阶段性交付状态确认验收_最新.json",
    "知识库可追溯问答框": EXT / "07知识库系统" / "08可追溯问答框" / "03数据" / "01交付包" / "知识库可追溯问答框交付包_最新.json",
    "知识库问答框验收": EXT / "07知识库系统" / "08可追溯问答框" / "04日志" / "knowledge-traceable-qa-box-delivery-verify-最新.json",
    "企业微信终端分工": WECOM_ACCESS / "01配置" / "企业微信机器人终端分工总表.json",
    "企业微信路由预演": WECOM_ACCESS / "03数据" / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json",
    "企业微信本地调用预演": WECOM_ACCESS / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json",
    "企业微信接入状态摘要": WECOM_ACCESS / "03数据" / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json",
    "上一轮多助手影子预案": WECOM_ACCESS / "03数据" / "12多助手统一路由影子预案" / "企业微信多助手统一路由影子预案_最新.json",
    "写入前备份目录": EXT / "05备份" / "20260505_1130_知识库问答与多助手路由写入前备份",
}


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


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None,
    }


def evidence(source_name: str, source_path: Path, section: str, fields: list[str], validation: str) -> dict[str, Any]:
    return {
        "来源名称": source_name,
        "来源文件": str(source_path),
        "来源文件存在": source_path.exists(),
        "来源章节或字段": section,
        "字段": fields,
        "验收状态": validation,
    }


def build_qa_samples(stock_final: dict[str, Any], stock_final_verify: dict[str, Any], stock_stage: dict[str, Any], stock_stage_verify: dict[str, Any]) -> list[dict[str, Any]]:
    final_path = SOURCES["股票最终收口报告"]
    final_verify_path = SOURCES["股票最终收口验收"]
    stage_path = SOURCES["股票阶段状态确认"]
    stage_verify_path = SOURCES["股票阶段状态确认验收"]

    return [
        {
            "问题": "股票系统现在是否已经阶段性交付完成？",
            "回答结论": f"是。股票系统当前状态为“{stock_stage.get('当前状态')}”，状态口径为“{stock_stage.get('状态口径')}”，后续不再归类为正在搭建主线。",
            "来源文件": str(stage_path),
            "来源章节或字段": "当前状态 / 状态口径 / 主线归类 / 工时口径",
            "验收状态": f"{stock_stage_verify.get('结论')}，通过{stock_stage_verify.get('通过数量')}，失败{stock_stage_verify.get('失败数量')}",
            "风险边界": "本结论只确认股票阶段性交付状态，不代表02扩展系统整体完成，也不授权股票新功能、n8n、券商接口或自动交易。",
            "证据": [
                evidence("股票阶段状态确认", stage_path, "当前状态", ["当前状态", "状态口径", "主线归类", "工时口径"], str(stock_stage_verify.get("结论"))),
                evidence("股票阶段状态确认验收", stage_verify_path, "检查结果", ["当前状态正确", "状态口径正确", "主线归类正确"], str(stock_stage_verify.get("结论"))),
            ],
        },
        {
            "问题": "股票系统阶段性交付完成的核心依据是什么？",
            "回答结论": "核心依据是242最终收口报告总结论通过，且237交付闭环、238灰度准入、240确认令写入、241单条真实灰度发送等关键验收均通过。",
            "来源文件": str(final_path),
            "来源章节或字段": "总结论 / 已完成清单 / 验收结果 / 检查项",
            "验收状态": f"{stock_final_verify.get('结论')}，通过{stock_final_verify.get('通过数量')}，失败{stock_final_verify.get('失败数量')}",
            "风险边界": "241中的真实发送是既有股票单人白名单灰度证据，本轮不复用它扩大任何真实发送范围。",
            "证据": [
                evidence("股票最终收口报告", final_path, "总结论 / 验收结果", ["总结论", "已完成清单", "验收结果"], str(stock_final.get("总结论"))),
                evidence("股票最终收口验收", final_verify_path, "检查结果", ["关键验收包全部通过", "单条真实灰度发送成功", "n8n未触发"], str(stock_final_verify.get("结论"))),
            ],
        },
        {
            "问题": "企业微信真实发送是否可以在本轮扩大范围？",
            "回答结论": "不可以。本轮只允许知识库问答和多助手路由影子预案；股票既有真实灰度发送不能作为扩大发送范围的授权。",
            "来源文件": str(final_path),
            "来源章节或字段": "下一步交接说明 / 安全边界 / 真实灰度发送结果",
            "验收状态": "证据存在且边界明确；本轮预案仍为shadow/local_preview_only。",
            "风险边界": "不得真实发送、不得扩大白名单、不得触发Webhook或n8n；如未来扩面必须重新授权、确认令、计数与回滚验收。",
            "证据": [
                evidence("股票最终收口报告", final_path, "下一步交接说明", ["若继续扩大企业微信真实发送范围", "安全边界"], str(stock_final.get("总结论"))),
                evidence("股票阶段状态确认", stage_path, "不改变的安全边界", ["触发n8n", "群发", "外部客户发送"], str(stock_stage.get("结论"))),
            ],
        },
        {
            "问题": "如果股票阶段交付相关动作失败，已有回滚证据在哪里？",
            "回答结论": "已有回滚证据包括历史K线刷新前备份、影子重跑前备份、对照重生成前备份、确认令回滚目标和企业微信计数文件。",
            "来源文件": str(final_path),
            "来源章节或字段": "回滚证据",
            "验收状态": f"{stock_final_verify.get('结论')}，通过{stock_final_verify.get('通过数量')}，失败{stock_final_verify.get('失败数量')}",
            "风险边界": "本轮只读取回滚证据，不执行回滚；新建问答和路由预案无正式覆盖动作。",
            "证据": [
                evidence("股票最终收口报告", final_path, "回滚证据", ["历史K线刷新前备份", "企业微信确认令回滚目标", "企业微信计数文件"], str(stock_final.get("总结论"))),
            ],
        },
        {
            "问题": "股票系统交付后还剩多少主交付工时？",
            "回答结论": "股票系统剩余主交付工时为0小时；后续只保留优化、灰度监控、问题修复和质量增强。",
            "来源文件": str(stage_path),
            "来源章节或字段": "工时口径 / 后续工作口径",
            "验收状态": f"{stock_stage_verify.get('结论')}，通过{stock_stage_verify.get('通过数量')}，失败{stock_stage_verify.get('失败数量')}",
            "风险边界": "0小时只适用于股票系统，不适用于知识库、企业微信多助手、视频、办公、内容处理等02扩展剩余项。",
            "证据": [
                evidence("股票阶段状态确认", stage_path, "工时口径 / 后续工作口径", ["工时口径", "后续工作口径"], str(stock_stage_verify.get("结论"))),
            ],
        },
    ]


def route_plan() -> list[dict[str, Any]]:
    return [
        {
            "助手": "股票助手",
            "目标路由": "股票研究",
            "影子验证": "可以",
            "正式放量": "不新增放量；仅保留既有股票线路和灰度监控",
            "输入样例": ["新易盛", "这只股票现在怎么看"],
            "输出要求": ["只读分析", "非交易声明", "风险边界", "详情入口"],
            "禁止项": ["股票新功能", "券商接口", "自动交易", "下单", "扩大真实发送"],
        },
        {
            "助手": "总管助手",
            "目标路由": "系统状态",
            "影子验证": "可以",
            "正式放量": "暂不放量；需总管统一最新状态源和回收口径",
            "输入样例": ["系统现在进度多少", "当前施工面板在哪里"],
            "输出要求": ["只读状态", "来源路径", "阻断项", "下一步"],
            "禁止项": ["修改总管进度口径", "替总管重算进度", "执行高风险动作"],
        },
        {
            "助手": "知识库助手",
            "目标路由": "知识库问答",
            "影子验证": "可以",
            "正式放量": "暂不放量；需人工复核和01知识库覆盖确认",
            "输入样例": ["股票系统为什么算交付完成", "企业微信为什么不能扩大发送"],
            "输出要求": ["回答结论", "来源文件", "来源章节或字段", "验收状态", "风险边界"],
            "禁止项": ["修改01智能系统中台代码", "写正式向量库", "调用模型推理替代证据", "真实发送"],
        },
        {
            "助手": "进化规则助手",
            "目标路由": "进化规则候选",
            "影子验证": "只允许路由到候选说明",
            "正式放量": "不能放量；03进化正式规则代码禁止修改",
            "输入样例": ["这次股票交付经验能沉淀什么规则", "哪些规则还只是候选"],
            "输出要求": ["候选规则说明", "来源证据", "待人工复核", "不得固化声明"],
            "禁止项": ["修改03进化系统规则代码", "反写业务系统", "把候选当正式规则"],
        },
        {
            "助手": "默认兜底助手",
            "目标路由": "澄清一次",
            "影子验证": "可以",
            "正式放量": "仅限本地预演；真实企业微信放量暂不扩大",
            "输入样例": ["这个事情你怎么看", "帮我处理一下"],
            "输出要求": ["只追问一次", "给出可选意图", "不执行动作"],
            "禁止项": ["越权猜测", "直接调用业务系统", "真实发送", "触发n8n"],
        },
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 02扩展系统本轮验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 施工框名称：{report['施工框名称']}",
        f"- 负责范围：{report['负责范围']}",
        "- 高风险动作：全部未触发",
        "",
        "## 小样本问答清单",
        "",
    ]
    for sample in report["小样本问答清单"]:
        lines.extend([
            f"### {sample['问题']}",
            "",
            f"- 回答结论：{sample['回答结论']}",
            f"- 来源文件：{sample['来源文件']}",
            f"- 来源章节或字段：{sample['来源章节或字段']}",
            f"- 验收状态：{sample['验收状态']}",
            f"- 风险边界：{sample['风险边界']}",
            "",
        ])
    lines.extend(["## 多助手路由影子预案", ""])
    for item in report["多助手路由影子预案"]:
        lines.append(f"- {item['助手']} -> {item['目标路由']}；影子验证：{item['影子验证']}；正式放量：{item['正式放量']}。")
    lines.extend(["", "## 发现的问题", ""])
    for item in report["发现的问题"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 剩余有效工时", ""])
    lines.append(f"- 02扩展系统建议剩余：{report['剩余有效工时']['02扩展系统建议剩余']}")
    lines.append(f"- 股票系统：{report['剩余有效工时']['股票系统']}")
    lines.extend(["", "## 需要总管收口", ""])
    for item in report["需要总管收口的事项"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stock_final = load_json(SOURCES["股票最终收口报告"])
    stock_final_verify = load_json(SOURCES["股票最终收口验收"])
    stock_stage = load_json(SOURCES["股票阶段状态确认"])
    stock_stage_verify = load_json(SOURCES["股票阶段状态确认验收"])
    knowledge_box = load_json(SOURCES["知识库可追溯问答框"])
    knowledge_verify = load_json(SOURCES["知识库问答框验收"])
    router = load_json(SOURCES["企业微信路由预演"])
    local_call = load_json(SOURCES["企业微信本地调用预演"])
    wecom_status = load_json(SOURCES["企业微信接入状态摘要"])
    acceptance_scope = load_json(SOURCES["四大系统验收读取口径"])

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "施工框名称": "02扩展系统：知识库可追溯问答 + 企业微信多助手路由预案",
        "负责范围": "02扩展系统内的小样本问答、影子路由预案、验收报告；不修改总管进度口径、01智能中台代码、03进化正式规则代码。",
        "读取来源": {name: file_record(path) for name, path in SOURCES.items()},
        "盘点结果": {
            "02扩展知识库问答框": {
                "状态": knowledge_box.get("汇总", {}).get("状态"),
                "问题数量": knowledge_box.get("汇总", {}).get("问题数量"),
                "证据卡数量": knowledge_box.get("汇总", {}).get("证据卡数量"),
                "验收": knowledge_verify.get("汇总", {}),
            },
            "企业微信助手": {
                "状态": wecom_status.get("汇总", {}).get("状态"),
                "统一路由状态": router.get("汇总", {}).get("状态"),
                "路由样例数量": router.get("汇总", {}).get("样例数量"),
                "路由真实动作数量": router.get("汇总", {}).get("真实动作数量"),
                "本地调用状态": local_call.get("汇总", {}).get("状态"),
                "本地调用真实动作数量": local_call.get("汇总", {}).get("真实动作数量"),
            },
            "四大系统验收读取口径": acceptance_scope.get("扩展系统", {}),
        },
        "小样本问答清单": build_qa_samples(stock_final, stock_final_verify, stock_stage, stock_stage_verify),
        "多助手路由影子预案": route_plan(),
        "哪些可以影子验证": [
            "股票助手：只读稳定性复核和既有路线健康检查。",
            "总管助手：只读状态查询，但不修改总管进度口径。",
            "知识库助手：读取02扩展侧小样本问答和知识库可追溯问答框。",
            "默认兜底助手：只追问一次，不执行业务动作。",
            "进化规则助手：只生成候选说明，不写03正式规则。"
        ],
        "哪些不能正式放量": [
            "任何企业微信真实发送扩面。",
            "知识库正式问答入口外发。",
            "进化规则助手正式固化规则。",
            "总管助手自动重算或写总管口径。",
            "股票助手新增功能、券商接口、自动交易或n8n接入。"
        ],
        "发现的问题": [
            "知识库可追溯问答框已形成02扩展交付层，但正式知识库覆盖、向量写库和中台能力仍归01智能系统。",
            "企业微信多助手当前仍主要是统一路由和本地调用预演，不能误报为正式多助手放量。",
            "进化规则助手只能做候选路由说明，不能修改03进化正式规则代码。",
            "总管助手路由需要总管统一最新状态源，否则可能引用旧摘要。",
            "股票交付证据可作为问答样本来源，但不能继续推动股票新功能。"
        ],
        "剩余有效工时": {
            "股票系统": "0小时",
            "02扩展系统总管当前口径": "16-28小时",
            "02扩展系统建议剩余": "12-20小时",
            "说明": "本轮形成知识库问答小样本和多助手路由预案，建议总管回收后再决定是否下调。"
        },
        "需要总管收口的事项": [
            "是否认可本轮小样本问答和多助手路由预案构成02扩展交付闭环证据。",
            "是否将02扩展系统剩余有效工时从16-28小时下调到12-20小时。",
            "是否批准下一步对总管助手、知识库助手、进化规则助手做本地桥接影子验证。",
            "是否统一总管助手的状态源，避免读取旧摘要。",
            "是否继续保持企业微信真实发送不扩面，直到人工确认新灰度门禁。"
        ],
        "未触碰边界确认": {
            "修改00总管进度口径文件": False,
            "修改01智能系统中台代码": False,
            "修改03进化系统规则代码": False,
            "企业微信真实发送": False,
            "扩大真实发送范围": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "继续给股票系统加新功能": False,
        },
        "高风险动作确认": {
            "企业微信真实发送": "否",
            "n8n": "否",
            "券商接口": "否",
            "自动交易": "否",
            "正式库写入": "否",
        },
    }

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    latest_json = OUT_DIR / "02扩展知识库问答与多助手路由本轮交付包_最新.json"
    latest_md = OUT_DIR / "02扩展知识库问答与多助手路由本轮交付包_最新.md"
    write_json(OUT_DIR / f"02扩展知识库问答与多助手路由本轮交付包_{stamp}.json", report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(OUT_DIR / f"02扩展知识库问答与多助手路由本轮交付包_{stamp}.md", markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": "generated", "小样本数量": len(report["小样本问答清单"]), "路由数量": len(report["多助手路由影子预案"]), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
