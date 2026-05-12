# -*- coding: utf-8 -*-
"""
名称：生成股票日报质量评分.py
作用：扫描当天三阶段股票报告、企微草案与盘后观察线刷新状态，生成《日报质量评分》。
审计说明：本脚本实现“仅标记不剔除”原则；质检只标记废品/事故和进化建议，不自动删除样本、不自动修改正式规则。
安全边界：只读本地报告与日志，只写260包质量评分；不真实发送企业微信；不触发n8n；不接券商；不交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any


FORBIDDEN_PHRASES = [
    "值得继续观察",
    "需人工复核",
    "暂无风险标记",
    "处在183.04元承接区附近",
    "承接区附近",
]

DOWNGRADE_PATTERNS = [
    "风险复核",
    "回避",
    "降级",
    "剔除",
    "已跌破",
    "跌破风控",
    "跌破风险",
    "逻辑兑现失败",
    "观察线刷新未通过",
    "观察线未刷新",
    "数据维护复核",
]

SAFETY_WARNINGS = [
    "系统原则：进化系统不得自动修改正式规则，仅可提出建议。",
]

LONG_TERM_FRAMEWORK_TERMS = [
    "长期成长框架",
    "长期成长质量",
    "成长框架",
    "成长质量",
]

TRADE_REASON_TERMS = [
    "买入",
    "增持",
    "推荐",
    "加仓",
    "建仓",
]

SHORT_RISK_TERMS = [
    "技术破位",
    "破位",
    "跌破",
    "风险",
    "止损",
    "风控",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def schedule_dt(hhmm: str) -> datetime:
    hour, minute = [int(part) for part in hhmm.split(":", 1)]
    return datetime.combine(datetime.now().date(), time(hour, minute))


def add_issue(issues: list[dict[str, Any]], stage: str, item: str, evidence: str, suggestion: str) -> None:
    issues.append({
        "阶段": stage,
        "检查项": item,
        "证据": evidence,
        "修改建议": suggestion,
    })


def check_report(
    stage: str,
    expected_time: str,
    json_path: Path,
    md_path: Path,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    data = load_json(json_path, {})
    text = read_text(md_path)
    generated_at = parse_dt(data.get("生成时间"))
    status = {
        "阶段": stage,
        "应到时间": expected_time,
        "JSON": str(json_path),
        "Markdown": str(md_path),
        "JSON存在": json_path.exists(),
        "Markdown存在": md_path.exists(),
        "生成时间": data.get("生成时间", ""),
        "准时": False,
        "未到生成窗口": False,
    }
    target = schedule_dt(expected_time)
    latest_allowed = target + timedelta(minutes=5)
    if datetime.now() < latest_allowed and (
        not json_path.exists()
        or not md_path.exists()
        or generated_at is None
        or generated_at.strftime("%Y-%m-%d") != today()
    ):
        status["未到生成窗口"] = True
        return status
    if not json_path.exists() or not md_path.exists():
        add_issue(issues, stage, "报告缺勤", "缺少JSON或Markdown最新文件", "补齐该阶段报告生成脚本，并纳入调度链。")
        return status
    if generated_at is None:
        add_issue(issues, stage, "生成时间缺失", "无法解析生成时间", "报告JSON必须写入可解析的生成时间。")
    elif generated_at.strftime("%Y-%m-%d") != today():
        add_issue(issues, stage, "报告缺勤", f"最新生成时间为{generated_at.strftime('%Y-%m-%d %H:%M:%S')}，不是今天", "调度器应在当天固定时点生成该阶段报告。")
    else:
        if target <= generated_at <= latest_allowed:
            status["准时"] = True
        else:
            add_issue(issues, stage, "报告迟到或时间异常", f"应到{expected_time}，实到{generated_at.strftime('%H:%M:%S')}", "检查n8n/本地调度触发时间与上游脚本耗时，迟到必须写入生产事故账。")
    if not text.strip():
        add_issue(issues, stage, "报告为空", "Markdown正文为空", "报告生成器必须在无候选时给出明确空结果正文。")
    return status


def check_forbidden_outputs(stage: str, text: str, issues: list[dict[str, Any]]) -> list[str]:
    hits = [phrase for phrase in FORBIDDEN_PHRASES if phrase in text]
    for phrase in hits:
        add_issue(
            issues,
            stage,
            "废品表达命中",
            f"命中：{phrase}",
            "删除空泛或误导性描述，改为明确价位、风险状态或数据刷新失败原因。",
        )
    return hits


def check_principle_outputs(stage: str, text: str, issues: list[dict[str, Any]]) -> list[str]:
    hits: list[str] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if (
            any(header in clean for header in ("结论", "操作策略", "策略", "操作"))
            and any(term in clean for term in LONG_TERM_FRAMEWORK_TERMS)
            and any(term in clean for term in TRADE_REASON_TERMS)
        ):
            hits.append(clean[:180])
            add_issue(
                issues,
                stage,
                "原则性废品表达",
                f"长期成长框架被用作交易理由：{clean[:120]}",
                "长期成长框架只能作为研究背景或样本分层依据，不得写成买入/增持/推荐理由。",
            )
        if (
            any(term in clean for term in LONG_TERM_FRAMEWORK_TERMS)
            and any(term in clean for term in SHORT_RISK_TERMS)
        ):
            hits.append(clean[:180])
            add_issue(
                issues,
                stage,
                "短线逻辑谬误",
                f"用长期成长质量回应短期破位或风险：{clean[:120]}",
                "三阶段短线判断必须以技术指标、价格动量和观察线状态为准；长期成长质量不得抵消技术破位。",
            )
    return hits


def extract_downgrade_lines(stage: str, text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if any(pattern in clean for pattern in DOWNGRADE_PATTERNS):
            rows.append({"阶段": stage, "提示": clean[:180]})
    return rows[:20]


def collect_stock_downgrades(stage: str, data: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in data.get("股票", []) if isinstance(data.get("股票"), list) else []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("观察线刷新状态") or item.get("当前状态") or "")
        if status and status != "有效":
            rows.append({
                "阶段": stage,
                "股票": f"{item.get('名称', '')}({item.get('代码', '')})",
                "提示": f"观察线刷新状态={status}",
            })
    return rows


def count_files_limited(path: Path, limit: int = 10000) -> int:
    count = 0
    for item in path.rglob("*"):
        if item.is_file():
            count += 1
            if count >= limit:
                return count
    return count


def latest_mtime(path: Path) -> str:
    newest = path.stat().st_mtime
    for item in path.rglob("*"):
        try:
            newest = max(newest, item.stat().st_mtime)
        except OSError:
            continue
    return datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M:%S")


def collect_redundancy_reminders(root: Path) -> list[dict[str, Any]]:
    system_root = root.parents[1]
    candidates = [
        (
            system_root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "视频生成桥梁预检" / "archive",
            "视频生成桥梁预检历史归档较多，适合周日人工确认保留策略",
        ),
        (
            system_root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "发布桥梁预检" / "archive",
            "视频发布预检历史归档较多，适合周日人工确认保留策略",
        ),
        (
            system_root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "最终真实渲染启用门禁" / "archive",
            "真实渲染门禁历史归档较多，适合周日人工确认保留策略",
        ),
        (
            system_root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "企业微信发布指令" / "archive",
            "视频企业微信发布指令历史归档较多，适合周日人工确认保留策略",
        ),
        (
            system_root / "03杰哥进化系统" / "04日志" / "阶段性多业务联调通过封版候选验收",
            "进化候选验收日志可周度压缩沉淀，避免日报面板噪声上升",
        ),
        (
            system_root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "07主题化预演",
            "视频主题化预演文件数量较多，可确认是否只保留最新与代表样本",
        ),
        (
            system_root / "02杰哥扩展系统" / "04内容处理系统" / "03数据" / "04转换预演",
            "内容处理转换预演文件数量较多，可确认是否只保留最新与代表样本",
        ),
        (
            system_root / "02杰哥扩展系统" / "02视频制作系统" / "03数据" / "18轮次012视频工厂总控层" / "智能体影子层" / "archive",
            "视频智能体影子层归档较多，可确认是否转入月度归档",
        ),
    ]
    reminders: list[dict[str, Any]] = []
    for path, reason in candidates:
        if not path.exists():
            continue
        file_count = count_files_limited(path)
        if file_count < 20:
            continue
        reminders.append({
            "目录": str(path),
            "文件数": file_count,
            "最后活动时间": latest_mtime(path),
            "提醒原因": reason,
            "建议动作": "只提醒，不删除；本周日由杰哥确认后再决定清理或压缩归档",
        })
    reminders.sort(key=lambda item: item["文件数"], reverse=True)
    return reminders[:12]


def check_jiege_recommend_learning_loop(root: Path, issues: list[dict[str, Any]]) -> dict[str, Any]:
    """检查【杰哥推荐】方法是否仍被股票系统本体掌握，防止退回旧助手逻辑。"""
    learning_path = root / "03数据" / "277杰哥推荐方法学习链路验收" / "杰哥推荐方法学习链路验收_最新.json"
    workflow_path = root / "03数据" / "274杰哥推荐方法工作流固化验收" / "杰哥推荐方法工作流总控巡检_最新.json"
    calibration_path = root / "03数据" / "278杰哥推荐方法内核校准" / "杰哥推荐方法内核校准报告_最新.json"
    material_path = root / "03数据" / "275杰哥推荐单股分析材料包" / "单股分析材料包_最新.json"
    learning = load_json(learning_path, {}) or {}
    workflow = load_json(workflow_path, {}) or {}
    calibration = load_json(calibration_path, {}) or {}
    material = load_json(material_path, {}) or {}
    calibration_stats = calibration.get("统计", {}) if isinstance(calibration.get("统计"), dict) else {}
    calibration_layers = calibration_stats.get("校准分层分布", {}) if isinstance(calibration_stats.get("校准分层分布"), dict) else {}
    checks = learning.get("检查项", []) if isinstance(learning.get("检查项"), list) else []
    failed_checks = [item for item in checks if isinstance(item, dict) and item.get("通过") is not True]
    status = {
        "学习链路验收": str(learning_path),
        "学习链路验收存在": learning_path.exists(),
        "学习链路结论": learning.get("结论", ""),
        "失败检查项": failed_checks,
        "工作流总控": str(workflow_path),
        "工作流总控存在": workflow_path.exists(),
        "工作流总控结论": workflow.get("结论", ""),
        "方法内核校准": str(calibration_path),
        "方法内核校准存在": calibration_path.exists(),
        "方法内核校准时间": calibration.get("生成时间", ""),
        "方法内核校准候选数量": calibration_stats.get("候选数量", ""),
        "方法内核校准P0冲突样本数": calibration_stats.get("P0冲突样本数", ""),
        "方法内核校准重点关注候选": calibration_layers.get("重点关注候选", ""),
        "方法内核校准重点关注待验证": calibration_layers.get("重点关注待验证", ""),
        "单股材料包": str(material_path),
        "单股材料包存在": material_path.exists(),
        "单股材料包生成时间": material.get("生成时间", ""),
        "单股材料包方法": material.get("方法", ""),
    }
    if not learning_path.exists():
        add_issue(
            issues,
            "杰哥推荐学习链路",
            "学习链路验收缺失",
            str(learning_path),
            "运行验证杰哥推荐方法学习链路.py，确认19300本体识别、材料包、报告证据段和19302桥接真源。",
        )
    elif learning.get("结论") != "通过" or failed_checks:
        add_issue(
            issues,
            "杰哥推荐学习链路",
            "学习链路验收未通过",
            json.dumps(failed_checks or learning, ensure_ascii=False)[:300],
            "先修复19300本体识别与材料包生成，再允许调整前台表达。",
        )
    if not workflow_path.exists() or workflow.get("结论") != "通过":
        add_issue(
            issues,
            "杰哥推荐工作流",
            "工作流总控未通过",
            f"总控存在={workflow_path.exists()}，结论={workflow.get('结论', '')}",
            "运行执行杰哥推荐方法工作流总控.py，确认数据地基、量价、行业、评分、材料包和学习验收均正常。",
        )
    if not calibration_path.exists() or not calibration:
        add_issue(
            issues,
            "杰哥推荐方法内核",
            "方法内核校准报告缺失",
            str(calibration_path),
            "运行校准杰哥推荐方法内核.py，确认高分冲突、失败对照距离和行业刹车已经进入质量视野。",
        )
    elif calibration_stats.get("候选数量") != 2000:
        add_issue(
            issues,
            "杰哥推荐方法内核",
            "方法内核校准候选数量异常",
            json.dumps(calibration_stats, ensure_ascii=False)[:300],
            "校准器必须覆盖2000只候选，缺口会导致前台推荐漏过冲突样本。",
        )
    if not material_path.exists() or not material:
        add_issue(
            issues,
            "杰哥推荐学习链路",
            "单股材料包缺失",
            str(material_path),
            "至少保留最新单股材料包作为链路验收证据；缺失时先运行单股分析样例生成材料包。",
        )
    return status


def check_promotion_loop(root: Path, issues: list[dict[str, Any]]) -> dict[str, Any]:
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    account_path = out_dir / "重点观察池晋级候选账_最新.json"
    auto_log_path = root / "04日志" / "重点观察池自动入池" / "重点观察池自动入池变更日志_最新.json"
    account = load_json(account_path, {})
    auto_log = load_json(auto_log_path, {})
    account_rows = account.get("候选", []) if isinstance(account.get("候选"), list) else []
    status = {
        "晋级候选账": str(account_path),
        "晋级候选账存在": account_path.exists(),
        "候选数量": len(account_rows),
        "候选账生成时间": account.get("更新时间") or account.get("生成时间", ""),
        "自动入池变更日志": str(auto_log_path),
        "自动入池变更日志存在": auto_log_path.exists(),
        "自动入池日志生成时间": auto_log.get("生成时间", ""),
        "自动入池写入数量": auto_log.get("写入数量", 0),
        "未到今日自动入池窗口": datetime.now() < schedule_dt("21:05"),
    }
    if not account_path.exists() or not account_rows:
        add_issue(issues, "重点观察池晋级闭环", "晋级候选账缺失或为空", str(account_path), "确认L5和共振报告已调用晋级候选公共库写入候选账。")
    if not auto_log_path.exists():
        add_issue(issues, "重点观察池晋级闭环", "自动入池变更日志缺失", str(auto_log_path), "晚间轻量学习闭环末尾应运行执行重点观察池自动入池.py，并写入变更日志。")
    elif str(auto_log.get("生成时间") or "")[:10] != today() and not status["未到今日自动入池窗口"]:
        add_issue(issues, "重点观察池晋级闭环", "自动入池变更日志非当天", str(auto_log.get("生成时间", "")), "确认晚间复盘学习后自动入池执行器已运行。")
    return status


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票日报质量评分 - {report['生成时间']}",
        "",
        f"结论：{report['评分结论']}",
        "",
        "## 安全警告",
        "",
    ]
    for warning in report.get("安全警告", []):
        lines.append(f"- {warning}")
    lines.extend([
        "",
        "## 一、三阶段准时性",
        "",
    ])
    for item in report["三阶段报告"]:
        lines.append(f"- {item['阶段']}：应到{item['应到时间']}；生成时间={item.get('生成时间') or '缺失'}；准时={item['准时']}")
    lines.extend(["", "## 二、不合格点", ""])
    if report["不合格点"]:
        for index, item in enumerate(report["不合格点"], start=1):
            lines.append(f"{index}. 【{item['阶段']}】{item['检查项']}：{item['证据']}；建议：{item['修改建议']}")
    else:
        lines.append("- 全部合格")
    lines.extend(["", "## 三、降级提示", ""])
    if report["降级提示"]:
        for item in report["降级提示"]:
            label = item.get("股票") or item.get("阶段", "")
            lines.append(f"- {label}：{item['提示']}")
    else:
        lines.append("- 今日未识别到降级提示")
    lines.extend(["", "## 四、晋级闭环", ""])
    promotion = report.get("晋级闭环", {})
    lines.append(f"- 晋级候选账存在：{promotion.get('晋级候选账存在')}；候选数量：{promotion.get('候选数量')}")
    lines.append(f"- 自动入池变更日志存在：{promotion.get('自动入池变更日志存在')}；写入数量：{promotion.get('自动入池写入数量')}")
    lines.extend(["", "## 五、杰哥推荐学习链路", ""])
    learning = report.get("杰哥推荐学习链路", {})
    lines.append(f"- 学习链路验收存在：{learning.get('学习链路验收存在')}；结论：{learning.get('学习链路结论') or '缺失'}")
    lines.append(f"- 工作流总控存在：{learning.get('工作流总控存在')}；结论：{learning.get('工作流总控结论') or '缺失'}")
    lines.append(
        f"- 方法内核校准存在：{learning.get('方法内核校准存在')}；候选数量：{learning.get('方法内核校准候选数量') or '缺失'}；"
        f"P0冲突样本：{learning.get('方法内核校准P0冲突样本数') if learning.get('方法内核校准P0冲突样本数') != '' else '缺失'}；"
        f"重点关注候选：{learning.get('方法内核校准重点关注候选') or '缺失'}；"
        f"重点关注待验证：{learning.get('方法内核校准重点关注待验证') or '缺失'}"
    )
    lines.append(f"- 单股材料包存在：{learning.get('单股材料包存在')}；生成时间：{learning.get('单股材料包生成时间') or '缺失'}")
    if learning.get("失败检查项"):
        for item in learning.get("失败检查项", [])[:8]:
            lines.append(f"- 失败项：{item.get('名称')}；说明：{item.get('说明', '')}")
    else:
        lines.append("- 学习链路未发现失败项")
    lines.extend(["", "## 六、冗余提醒（不删除）", ""])
    if report.get("冗余提醒"):
        for item in report["冗余提醒"]:
            lines.append(f"- {item['目录']}：{item['文件数']}个文件；{item['提醒原因']}；建议：{item['建议动作']}")
    else:
        lines.append("- 今日没有达到提醒阈值的冗余目录")
    lines.extend(["", "## 七、安全边界", "", "- 未真实发送企业微信。", "- 未触发n8n。", "- 未调用券商接口。", "- 未自动交易。"])
    return "\n".join(lines)


def build_incident_markdown(incident: dict[str, Any]) -> str:
    lines = [
        f"# 股票报告生产事故账 - {incident['生成时间']}",
        "",
        f"- 事故数量：{incident['事故数量']}",
        "",
    ]
    if incident["事故"]:
        for index, item in enumerate(incident["事故"], start=1):
            lines.append(f"{index}. 【{item['阶段']}】{item['检查项']}：{item['证据']}；纠正动作：{item['修改建议']}")
    else:
        lines.append("- 今日暂无生产事故")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    issues: list[dict[str, Any]] = []
    stages = [
        {
            "阶段": "收盘短线观察",
            "应到时间": "15:30",
            "JSON": out_dir / "收盘短线观察_基于300只轻扫描_最新.json",
            "Markdown": out_dir / "收盘短线观察_基于300只轻扫描_最新.md",
        },
        {
            "阶段": "深度三维研究",
            "应到时间": "21:00",
            "JSON": root / "03数据" / "135分层日报" / "AI分析报告_最新.json",
            "Markdown": root / "03数据" / "135分层日报" / "AI分析报告_最新.md",
        },
        {
            "阶段": "盘前出击排序",
            "应到时间": "08:50",
            "JSON": out_dir / "盘前出击排序_最新.json",
            "Markdown": out_dir / "盘前出击排序_最新.md",
        },
    ]
    stage_status = []
    forbidden_hits: dict[str, list[str]] = {}
    principle_hits: dict[str, list[str]] = {}
    downgrade_rows: list[dict[str, str]] = []
    for stage in stages:
        status = check_report(stage["阶段"], stage["应到时间"], stage["JSON"], stage["Markdown"], issues)
        stage_status.append(status)
        if status.get("未到生成窗口"):
            continue
        text = read_text(stage["Markdown"])
        data = load_json(stage["JSON"], {})
        forbidden_hits[stage["阶段"]] = check_forbidden_outputs(stage["阶段"], text, issues)
        principle_hits[stage["阶段"]] = check_principle_outputs(stage["阶段"], text, issues)
        downgrade_rows.extend(extract_downgrade_lines(stage["阶段"], text))
        downgrade_rows.extend(collect_stock_downgrades(stage["阶段"], data if isinstance(data, dict) else {}))

    risk_status_path = out_dir / "收盘短线观察前置数据刷新状态_最新.json"
    risk_status = load_json(risk_status_path, {})
    if risk_status.get("结论") != "pass" or str(risk_status.get("生成时间") or "")[:10] != today():
        add_issue(
            issues,
            "收盘短线观察",
            "观察线前置刷新未通过",
            f"状态文件={risk_status_path}，结论={risk_status.get('结论')}，生成时间={risk_status.get('生成时间', '')}",
            "盘后调度必须先强制运行刷新收盘短线观察前置数据.py，成功后再进入报告生成。",
        )

    promotion_status = check_promotion_loop(root, issues)
    jiege_learning_status = check_jiege_recommend_learning_loop(root, issues)
    redundancy_reminders = collect_redundancy_reminders(root)

    report = {
        "名称": "股票日报质量评分",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票日报质量评分.py",
        "评分结论": "全部合格" if not issues else f"{len(issues)}处不合格",
        "三阶段报告": stage_status,
        "禁用表达命中": forbidden_hits,
        "原则检查命中": principle_hits,
        "安全警告": SAFETY_WARNINGS,
        "降级提示": downgrade_rows[:50],
        "晋级闭环": promotion_status,
        "杰哥推荐学习链路": jiege_learning_status,
        "冗余提醒": redundancy_reminders,
        "不合格点": issues,
        "明日总管面板标红": bool(issues),
        "生产事故记录": issues,
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否启用n8n自动触发": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_json = out_dir / f"股票日报质量评分_{stamp}.json"
    output_md = out_dir / f"股票日报质量评分_{stamp}.md"
    latest_json = out_dir / "股票日报质量评分_最新.json"
    latest_md = out_dir / "股票日报质量评分_最新.md"
    incident = {
        "名称": "股票报告生产事故账",
        "生成时间": report["生成时间"],
        "事故数量": len(issues),
        "事故": issues,
        "安全边界": report["安全边界"],
    }
    incident_json = out_dir / f"股票报告生产事故账_{stamp}.json"
    incident_md = out_dir / f"股票报告生产事故账_{stamp}.md"
    incident_latest_json = out_dir / "股票报告生产事故账_最新.json"
    incident_latest_md = out_dir / "股票报告生产事故账_最新.md"
    markdown = build_markdown(report)
    incident_markdown = build_incident_markdown(incident)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(incident_json, incident)
    write_json(incident_latest_json, incident)
    write_text(incident_md, incident_markdown)
    write_text(incident_latest_md, incident_markdown)
    print(json.dumps({"评分结论": report["评分结论"], "不合格数": len(issues), "Markdown": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
