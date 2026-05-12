# -*- coding: utf-8 -*-
"""
名称：生成无干扰自动施工队列.py
作用：根据无干扰自动施工模式规则、总架构说明和当前股票 v2.1 进度，生成下一轮可自动推进队列。
触发方式：python 生成无干扰自动施工队列.py
所属系统：00杰哥系统总管
安全边界：只读当前规则和状态；只写 00杰哥系统总管/03数据/运行状态；不重启服务；不发送企业微信；
不触发 n8n；不写正式库；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
CONFIG = MANAGER / "01配置" / "无干扰自动施工模式规则.json"
MASTER_DOC = ROOT / "杰哥智能化系统全盘架构说明_20260504.md"
OUT_DIR = MANAGER / "03数据" / "运行状态"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def exists(path: Path) -> str:
    return "存在" if path.exists() else "缺失"


def main() -> int:
    now = datetime.now()
    rule = load_json(CONFIG)
    master = load_text(MASTER_DOC)

    shadow_dir = STOCK / "03数据" / "186报告v21影子样板"
    huahong_shadow = shadow_dir / "华虹公司v21影子样板_最新.json"
    huahong_validation = shadow_dir / "华虹公司v21影子样板验收_最新.json"
    fusion_validation = STOCK / "03数据" / "运行验收" / "股票分析报告v2融合升级标准验收_最新.json"
    non_trade_gate = MANAGER / "03数据" / "运行状态" / "股票系统只分析不交易总闸门验收_最新.json"
    v21_plan = STOCK / "03数据" / "217微信短文生成器v21接入方案" / "微信短文生成器v21正式接入方案验收_最新.json"
    v21_shadow_preview = STOCK / "03数据" / "218微信短文生成器v21影子接入预演" / "微信短文生成器v21影子接入预演验收_最新.json"
    model_audit = MANAGER / "03数据" / "运行状态" / "模型路由与审稿能力只读审计验收_最新.json"
    copy_skeleton_check = MANAGER / "03数据" / "运行状态" / "扩展系统复制骨架影子检查验收_最新.json"
    low_risk_observation = MANAGER / "03数据" / "运行状态" / "后续低风险队列补充与状态观察验收_最新.json"
    wecom_route_baseline = MANAGER / "03数据" / "运行状态" / "企业微信助手统一路由状态基线验收_最新.json"
    small_flow_gate = MANAGER / "03数据" / "运行状态" / "总管小流量执行器只读门禁复核验收_最新.json"
    evolution_baseline = MANAGER / "03数据" / "运行状态" / "进化系统复盘材料状态基线验收_最新.json"
    knowledge_trace_baseline = MANAGER / "03数据" / "运行状态" / "知识库可追溯问答只读基线脚本缺口复核验收_最新.json"
    knowledge_evidence_card = MANAGER / "03数据" / "运行状态" / "知识库证据卡格式标准影子样板验收_最新.json"
    knowledge_readonly_entry = MANAGER / "03数据" / "运行状态" / "知识库只读问答入口影子方案验收_最新.json"
    wecom_kb_disabled_bridge = MANAGER / "03数据" / "运行状态" / "企业微信助手知识库问答入口禁用态桥接检查验收_最新.json"
    knowledge_gray_gate = MANAGER / "03数据" / "运行状态" / "知识库问答入口灰度门禁草案验收_最新.json"
    knowledge_confirmation_template = MANAGER / "03数据" / "运行状态" / "知识库问答入口人工确认单模板验收_最新.json"
    knowledge_gray_sample_template = MANAGER / "03数据" / "运行状态" / "知识库问答灰度样本清单影子模板验收_最新.json"
    knowledge_gray_sample_precheck = MANAGER / "03数据" / "运行状态" / "知识库问答灰度样本填写预检验收_最新.json"
    knowledge_gray_rollback = MANAGER / "03数据" / "运行状态" / "知识库问答灰度回滚清单影子模板验收_最新.json"
    knowledge_gray_total_gate = MANAGER / "03数据" / "运行状态" / "知识库问答灰度总闸门影子验收验收_最新.json"
    knowledge_gray_closure = MANAGER / "03数据" / "运行状态" / "知识库问答灰度材料收口包验收_最新.json"
    knowledge_gray_blocker = MANAGER / "03数据" / "运行状态" / "知识库问答灰度后续阻断报告验收_最新.json"
    knowledge_gray_pause_gate = MANAGER / "03数据" / "运行状态" / "知识库问答灰度施工暂停闸口记录验收_最新.json"
    knowledge_gray_permission_template = MANAGER / "03数据" / "运行状态" / "知识库问答灰度许可接收清单影子模板验收_最新.json"
    knowledge_gray_permission_precheck = MANAGER / "03数据" / "运行状态" / "知识库问答灰度许可接收清单填写预检验收_最新.json"
    knowledge_gray_terminal_index = MANAGER / "03数据" / "运行状态" / "知识库问答灰度链路终态索引验收_最新.json"
    old_path_global_scan = MANAGER / "03数据" / "运行状态" / "旧路径口径全局巡检验收_最新.json"
    global_low_risk_refresh = MANAGER / "03数据" / "运行状态" / "全局低风险施工候选刷新验收_最新.json"

    evidence = {
        "强制总纲同步规则": "已写入" if "强制施工同步规则" in master else "缺失",
        "无干扰规则": exists(CONFIG),
        "华虹影子样板": exists(huahong_shadow),
        "华虹影子验收": exists(huahong_validation),
        "v2融合标准验收": exists(fusion_validation),
        "非交易总闸门": exists(non_trade_gate),
        "v21正式接入方案验收": exists(v21_plan),
        "v21影子接入预演验收": exists(v21_shadow_preview),
        "模型路由与审稿审计验收": exists(model_audit),
        "扩展系统复制骨架影子检查验收": exists(copy_skeleton_check),
        "后续低风险队列补充与状态观察验收": exists(low_risk_observation),
        "企业微信助手统一路由状态基线验收": exists(wecom_route_baseline),
        "总管小流量执行器只读门禁复核验收": exists(small_flow_gate),
        "进化系统复盘材料状态基线验收": exists(evolution_baseline),
        "知识库可追溯问答只读基线脚本缺口复核验收": exists(knowledge_trace_baseline),
        "知识库证据卡格式标准影子样板验收": exists(knowledge_evidence_card),
        "知识库只读问答入口影子方案验收": exists(knowledge_readonly_entry),
        "企业微信助手知识库问答入口禁用态桥接检查验收": exists(wecom_kb_disabled_bridge),
        "知识库问答入口灰度门禁草案验收": exists(knowledge_gray_gate),
        "知识库问答入口人工确认单模板验收": exists(knowledge_confirmation_template),
        "知识库问答灰度样本清单影子模板验收": exists(knowledge_gray_sample_template),
        "知识库问答灰度样本填写预检验收": exists(knowledge_gray_sample_precheck),
        "知识库问答灰度回滚清单影子模板验收": exists(knowledge_gray_rollback),
        "知识库问答灰度总闸门影子验收": exists(knowledge_gray_total_gate),
        "知识库问答灰度材料收口包验收": exists(knowledge_gray_closure),
        "知识库问答灰度后续阻断报告验收": exists(knowledge_gray_blocker),
        "知识库问答灰度施工暂停闸口记录验收": exists(knowledge_gray_pause_gate),
        "知识库问答灰度许可接收清单影子模板验收": exists(knowledge_gray_permission_template),
        "知识库问答灰度许可接收清单填写预检验收": exists(knowledge_gray_permission_precheck),
        "知识库问答灰度链路终态索引验收": exists(knowledge_gray_terminal_index),
        "旧路径口径全局巡检验收": exists(old_path_global_scan),
        "全局低风险施工候选刷新验收": exists(global_low_risk_refresh),
        "总架构已记录华虹v2.1": "已记录" if "华虹公司 v2.1 影子样板与微信短文预览" in master else "未记录",
    }

    plan_done = v21_plan.exists()
    shadow_preview_done = v21_shadow_preview.exists()
    model_audit_done = model_audit.exists()
    copy_skeleton_done = copy_skeleton_check.exists()
    low_risk_done = low_risk_observation.exists()
    wecom_route_done = wecom_route_baseline.exists()
    small_flow_done = small_flow_gate.exists()
    evolution_done = evolution_baseline.exists()
    knowledge_trace_done = knowledge_trace_baseline.exists()
    knowledge_evidence_card_done = knowledge_evidence_card.exists()
    knowledge_readonly_entry_done = knowledge_readonly_entry.exists()
    wecom_kb_disabled_bridge_done = wecom_kb_disabled_bridge.exists()
    knowledge_gray_gate_done = knowledge_gray_gate.exists()
    knowledge_confirmation_template_done = knowledge_confirmation_template.exists()
    knowledge_gray_sample_template_done = knowledge_gray_sample_template.exists()
    knowledge_gray_sample_precheck_done = knowledge_gray_sample_precheck.exists()
    knowledge_gray_rollback_done = knowledge_gray_rollback.exists()
    knowledge_gray_total_gate_done = knowledge_gray_total_gate.exists()
    knowledge_gray_closure_done = knowledge_gray_closure.exists()
    knowledge_gray_blocker_done = knowledge_gray_blocker.exists()
    knowledge_gray_pause_gate_done = knowledge_gray_pause_gate.exists()
    knowledge_gray_permission_template_done = knowledge_gray_permission_template.exists()
    knowledge_gray_permission_precheck_done = knowledge_gray_permission_precheck.exists()
    knowledge_gray_terminal_index_done = knowledge_gray_terminal_index.exists()
    old_path_global_scan_done = old_path_global_scan.exists()
    global_low_risk_refresh_done = global_low_risk_refresh.exists()

    queue = [
        {
            "序号": 1,
            "任务": "生成微信短文生成器 v2.1 正式接入方案",
            "所属系统": "02股票扩展/03进化/00总管",
            "自动级别": "允许自动",
            "执行方式": "只生成方案、字段映射、验收清单和回滚点，不替换正式入口",
            "预计影响": "不影响股票系统日常使用",
            "完成条件": "方案文件存在、JSON/Markdown 可读、总架构说明同步",
            "当前状态": "已完成" if plan_done else "待执行",
        },
        {
            "序号": 2,
            "任务": "建立微信短文生成器 v2.1 影子接入验收脚本",
            "所属系统": "02股票扩展/03进化",
            "自动级别": "允许自动",
            "执行方式": "新增影子验收，不触发企业微信真实发送，不重启 19300/19302",
            "预计影响": "不影响正式问答入口",
            "完成条件": "影子验收通过且非交易边界复跑通过",
            "当前状态": "已完成" if shadow_preview_done else ("待执行" if plan_done else "排队"),
        },
        {
            "序号": 3,
            "任务": "模型路由与审稿能力只读审计",
            "所属系统": "01智能/00总管",
            "自动级别": "允许自动",
            "执行方式": "只读检查 Ollama 模型登记、路由策略、审稿边界和降级策略",
            "预计影响": "不运行批量模型任务",
            "完成条件": "审计报告生成并同步总架构说明",
            "当前状态": "已完成" if model_audit_done else ("待执行" if shadow_preview_done else "后续"),
        },
        {
            "序号": 4,
            "任务": "扩展系统复制骨架影子检查",
            "所属系统": "02扩展/03进化/00总管",
            "自动级别": "允许自动",
            "执行方式": "只做目录、规则、影子业务模板检查，不接入正式入口",
            "预计影响": "不抢股票系统资源",
            "完成条件": "复制骨架检查报告生成并同步总架构说明",
            "当前状态": "已完成" if copy_skeleton_done else ("待执行" if model_audit_done else "后续"),
        },
        {
            "序号": 5,
            "任务": "正式微信短文生成器替换运行入口",
            "所属系统": "02股票扩展/00总管",
            "自动级别": "必须停下报告",
            "执行方式": "涉及正式入口替换，需先有影子验收和明确回滚点",
            "预计影响": "可能影响企业微信股票回复",
            "完成条件": "用户确认或已有明确受控接入许可后执行",
            "当前状态": "阻断：必须停下报告",
        },
        {
            "序号": 6,
            "任务": "后续低风险队列补充与状态观察",
            "所属系统": "00总管/01智能/02扩展/03进化",
            "自动级别": "允许自动",
            "执行方式": "只刷新状态、识别下一批低风险候选，不替换正式入口，不执行高风险动作",
            "预计影响": "不影响股票系统日常使用",
            "完成条件": "后续低风险候选清单或状态观察报告生成并同步总架构说明",
            "当前状态": "已完成" if low_risk_done else ("待执行" if copy_skeleton_done else "后续"),
        },
        {
            "序号": 7,
            "任务": "企业微信助手统一路由状态基线",
            "所属系统": "02扩展/06企业微信助手/00总管",
            "自动级别": "允许自动",
            "执行方式": "只运行本地路由、本地调用、本地服务、速查卡和状态摘要验收，不真实发送企业微信",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "总管侧状态基线和验收报告全部通过",
            "当前状态": "已完成" if wecom_route_done else ("待执行" if low_risk_done else "后续"),
        },
        {
            "序号": 8,
            "任务": "总管小流量执行器只读门禁复核",
            "所属系统": "00总管",
            "自动级别": "允许自动",
            "执行方式": "只验收小流量只读方案、前快照和后观测模板，不触发执行器",
            "预计影响": "不影响业务系统运行",
            "完成条件": "小流量只读门禁相关验收全部通过",
            "当前状态": "已完成" if small_flow_done else ("待执行" if wecom_route_done else "后续"),
        },
        {
            "序号": 9,
            "任务": "进化系统复盘材料状态基线",
            "所属系统": "03进化/00总管",
            "自动级别": "允许自动",
            "执行方式": "只刷新进化系统状态摘要、复盘报告和经验卡片候选模板，不写入总纲规则",
            "预计影响": "不影响业务系统运行",
            "完成条件": "进化复盘材料状态基线和验收报告生成",
            "当前状态": "已完成" if evolution_done else ("待执行" if small_flow_done else "后续"),
        },
        {
            "序号": 10,
            "任务": "知识库可追溯问答只读基线脚本缺口复核",
            "所属系统": "01智能/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只复核知识库状态、脚本命名和缺口，不启动批量问答，不入库",
            "预计影响": "不运行模型重任务",
            "完成条件": "知识库脚本缺口复核报告生成",
            "当前状态": "已完成" if knowledge_trace_done else ("待执行" if evolution_done else "后续"),
        },
        {
            "序号": 11,
            "任务": "知识库证据卡格式标准影子样板",
            "所属系统": "01智能/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只定义证据卡字段、示例和验收清单，不启动批量问答，不入库，不接入企业微信",
            "预计影响": "不运行模型重任务",
            "完成条件": "证据卡格式影子样板和验收报告生成",
            "当前状态": "已完成" if knowledge_evidence_card_done else ("待执行" if knowledge_trace_done else "后续"),
        },
        {
            "序号": 12,
            "任务": "知识库只读问答入口影子方案",
            "所属系统": "01智能/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成入口方案、字段映射、验收清单和回滚点，不接入正式入口，不触发企业微信",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "只读问答入口影子方案和验收报告生成",
            "当前状态": "已完成" if knowledge_readonly_entry_done else ("待执行" if knowledge_evidence_card_done else "后续"),
        },
        {
            "序号": 13,
            "任务": "企业微信助手知识库问答入口禁用态桥接检查",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只检查知识库入口与企业微信助手之间的禁用态边界，不接入正式入口，不真实发送",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "禁用态桥接检查报告和验收报告生成",
            "当前状态": "已完成" if wecom_kb_disabled_bridge_done else ("待执行" if knowledge_readonly_entry_done else "后续"),
        },
        {
            "序号": 14,
            "任务": "知识库问答入口灰度门禁草案",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成灰度门禁草案和人工确认条件，不接入正式入口，不真实发送",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度门禁草案和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_gate_done else ("待执行" if wecom_kb_disabled_bridge_done else "后续"),
        },
        {
            "序号": 15,
            "任务": "知识库问答入口人工确认单模板",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成灰度前人工确认单模板，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "人工确认单模板和验收报告生成",
            "当前状态": "已完成" if knowledge_confirmation_template_done else ("待执行" if knowledge_gray_gate_done else "后续"),
        },
        {
            "序号": 16,
            "任务": "知识库问答灰度样本清单影子模板",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成灰度样本清单影子模板，不填真实样本，不放行灰度",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度样本清单影子模板和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_sample_template_done else ("待执行" if knowledge_confirmation_template_done else "后续"),
        },
        {
            "序号": 17,
            "任务": "知识库问答灰度样本填写预检脚本",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成未来样本填写预检脚本，不填样本，不放行灰度",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度样本填写预检脚本和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_sample_precheck_done else ("待执行" if knowledge_gray_sample_template_done else "后续"),
        },
        {
            "序号": 18,
            "任务": "知识库问答灰度回滚清单影子模板",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成灰度回滚清单影子模板，不执行回滚，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度回滚清单影子模板和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_rollback_done else ("待执行" if knowledge_gray_sample_precheck_done else "后续"),
        },
        {
            "序号": 19,
            "任务": "知识库问答灰度总闸门影子验收",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只汇总灰度前全部影子产物并验收，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度总闸门影子验收报告生成",
            "当前状态": "已完成" if knowledge_gray_total_gate_done else ("待执行" if knowledge_gray_rollback_done else "后续"),
        },
        {
            "序号": 20,
            "任务": "知识库问答灰度材料收口包",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只汇总灰度材料索引和接续说明，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度材料收口包和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_closure_done else ("待执行" if knowledge_gray_total_gate_done else "后续"),
        },
        {
            "序号": 21,
            "任务": "知识库问答灰度后续阻断报告",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成后续阻断报告，列出必须人工许可事项，不执行任何放行动作",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度后续阻断报告和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_blocker_done else ("待执行" if knowledge_gray_closure_done else "后续"),
        },
        {
            "序号": 22,
            "任务": "知识库问答灰度施工暂停闸口记录",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只记录暂停闸口和后续人工许可入口，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "暂停闸口记录和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_pause_gate_done else ("待执行" if knowledge_gray_blocker_done else "后续"),
        },
        {
            "序号": 23,
            "任务": "知识库问答灰度许可接收清单影子模板",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成空许可接收清单模板，不填写许可，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "许可接收清单影子模板和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_permission_template_done else ("待执行" if knowledge_gray_pause_gate_done else "后续"),
        },
        {
            "序号": 24,
            "任务": "知识库问答灰度许可接收清单填写预检脚本",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只生成未来许可填写预检脚本，不填写许可，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "许可填写预检脚本和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_permission_precheck_done else ("待执行" if knowledge_gray_permission_template_done else "后续"),
        },
        {
            "序号": 25,
            "任务": "知识库问答灰度链路终态索引",
            "所属系统": "01智能/02扩展/06企业微信助手/00总管",
            "自动级别": "允许只读观察",
            "执行方式": "只汇总灰度影子链路、阻断链路和许可预检链路，不放行灰度，不接入正式入口",
            "预计影响": "不影响企业微信正式入口",
            "完成条件": "灰度链路终态索引和验收报告生成",
            "当前状态": "已完成" if knowledge_gray_terminal_index_done else ("待执行" if knowledge_gray_permission_precheck_done else "后续"),
        },
        {
            "序号": 26,
            "任务": "旧路径口径全局巡检",
            "所属系统": "00总管/01智能/02扩展/03进化",
            "自动级别": "允许只读观察",
            "执行方式": "只扫描文档和配置中的旧路径口径，生成报告，不删除文件，不改入口",
            "预计影响": "不影响业务系统运行",
            "完成条件": "旧路径口径巡检报告和验收报告生成",
            "当前状态": "已完成" if old_path_global_scan_done else ("待执行" if knowledge_gray_terminal_index_done else "后续"),
        },
        {
            "序号": 27,
            "任务": "全局低风险施工候选刷新",
            "所属系统": "00总管/01智能/02扩展/03进化",
            "自动级别": "允许只读观察",
            "执行方式": "只刷新下一批低风险施工候选，不执行入口替换、真实发送、n8n触发或写库",
            "预计影响": "不影响业务系统运行",
            "完成条件": "全局低风险候选报告和验收报告生成",
            "当前状态": "已完成" if global_low_risk_refresh_done else ("待执行" if old_path_global_scan_done else "后续"),
        },
        {
            "序号": 28,
            "任务": "文档索引当前路径口径复核",
            "所属系统": "00总管/01智能",
            "自动级别": "允许只读观察",
            "执行方式": "只读复核设计纲领、施工面板、文档总索引和总架构说明当前路径口径，不删除文件，不改入口",
            "预计影响": "不影响业务系统运行",
            "完成条件": "文档索引当前路径口径复核报告和验收报告生成",
            "当前状态": "待执行" if global_low_risk_refresh_done else "后续",
        },
    ]

    if not plan_done:
        next_item = queue[0]
    elif not shadow_preview_done:
        next_item = queue[1]
    elif not model_audit_done:
        next_item = queue[2]
    elif not copy_skeleton_done:
        next_item = queue[3]
    elif not low_risk_done:
        next_item = queue[5]
    elif not wecom_route_done:
        next_item = queue[6]
    elif not small_flow_done:
        next_item = queue[7]
    elif not evolution_done:
        next_item = queue[8]
    elif not knowledge_trace_done:
        next_item = queue[9]
    elif not knowledge_evidence_card_done:
        next_item = queue[10]
    elif not knowledge_readonly_entry_done:
        next_item = queue[11]
    elif not wecom_kb_disabled_bridge_done:
        next_item = queue[12]
    elif not knowledge_gray_gate_done:
        next_item = queue[13]
    elif not knowledge_confirmation_template_done:
        next_item = queue[14]
    elif not knowledge_gray_sample_template_done:
        next_item = queue[15]
    elif not knowledge_gray_sample_precheck_done:
        next_item = queue[16]
    elif not knowledge_gray_rollback_done:
        next_item = queue[17]
    elif not knowledge_gray_total_gate_done:
        next_item = queue[18]
    elif not knowledge_gray_closure_done:
        next_item = queue[19]
    elif not knowledge_gray_blocker_done:
        next_item = queue[20]
    elif not knowledge_gray_pause_gate_done:
        next_item = queue[21]
    elif not knowledge_gray_permission_template_done:
        next_item = queue[22]
    elif not knowledge_gray_permission_precheck_done:
        next_item = queue[23]
    elif not knowledge_gray_terminal_index_done:
        next_item = queue[24]
    elif not old_path_global_scan_done:
        next_item = queue[25]
    elif not global_low_risk_refresh_done:
        next_item = queue[26]
    else:
        next_item = queue[27]

    conclusion = (
        f"无干扰施工队列已刷新；下一步优先执行：{next_item['任务']}。"
        "正式入口替换仍列为必须停下报告项。"
    )

    report = {
        "名称": "无干扰自动施工队列",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "无干扰自动推进",
        "当前结论": conclusion,
        "规则摘要": {
            "允许自动执行": rule.get("允许自动执行", []),
            "必须停下报告": rule.get("必须停下报告", []),
        },
        "当前证据": evidence,
        "自动施工队列": queue,
        "本轮建议执行": next_item,
        "安全边界": {
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "清理旧容器": False,
        },
    }

    lines = [
        "# 无干扰自动施工队列",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 当前证据",
        "",
    ]
    for key, value in evidence.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 自动施工队列", ""])
    for item in queue:
        lines.append(f"{item['序号']}. {item['任务']}：{item['自动级别']}；{item['执行方式']}；当前状态：{item['当前状态']}")
    lines.extend([
        "",
        "## 本轮建议执行",
        "",
        f"- {next_item['任务']}",
        f"- {next_item['执行方式']}",
        f"- 完成条件：{next_item['完成条件']}",
        "",
        "## 安全边界",
        "",
        "- 不重启 `19300/19302`。",
        "- 不发送企业微信真实消息。",
        "- 不触发 n8n。",
        "- 不写正式库。",
        "- 不调用券商接口，不自动交易。",
        "- 每步完成后必须更新总架构说明。",
    ])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    latest_json = OUT_DIR / "无干扰自动施工队列_最新.json"
    latest_md = OUT_DIR / "无干扰自动施工队列_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": "完成",
        "当前结论": report["当前结论"],
        "本轮建议执行": next_item["任务"],
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
