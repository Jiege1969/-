# -*- coding: utf-8 -*-
"""
名称：验证股票n8n日内报告闭环与晨报推送策略包.py
作用：验证260策略包是否覆盖随问随答、收市观察、半夜规律、开市前晨报、纠偏和学习沉淀。
触发方式：python 验证股票n8n日内报告闭环与晨报推送策略包.py
依赖：Python标准库；生成股票n8n日内报告闭环与晨报推送策略包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地生成与校验；不导入n8n；不启用n8n；不真实发送企业微信；不接券商；不交易。
标识：stock-n8n-intraday-report-loop-morning-push-package-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def contains_all_keys(data: dict[str, Any], keys: list[str]) -> tuple[bool, list[str]]:
    missing = [key for key in keys if key not in data]
    return not missing, missing


def scan_for_blocked_terms(paths: list[Path]) -> dict[str, Any]:
    blocked_terms = ["买入", "卖出", "下单", "仓位", "满仓", "清仓"]
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for term in blocked_terms:
            if term in text:
                hits.append({"文件": str(path), "命中": term})
    return {"通过": not hits, "命中数量": len(hits), "命中": hits}


def scan_for_empty_report_terms(text: str) -> dict[str, Any]:
    blocked_terms = ["继续观察", "需人工复核", "需复核", "人工确认", "暂无额外风险标记"]
    hits = [term for term in blocked_terms if term in text]
    return {"通过": not hits, "命中": hits}


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n日内报告闭环与晨报推送策略包验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 总体状态：{result['总体状态']}",
        f"- 通过：{result['通过']}",
        f"- 失败：{result['失败']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}；{item['说明']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票n8n日内报告闭环与晨报推送策略包.py"
    latest = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"
    completed = subprocess.run(
        [sys.executable, str(generator)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    report = load_json(latest, {})
    morning_latest = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "开市前晨报样例_最新.json"
    morning_latest_md = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "开市前晨报样例_最新.md"
    ledger_latest = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票主动推送学习沉淀账样例_最新.json"
    ledger_latest_md = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票主动推送学习沉淀账样例_最新.md"
    three_stage_latest = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票三阶段报告流程样例_最新.json"
    three_stage_latest_md = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票三阶段报告流程样例_最新.md"
    morning = load_json(morning_latest, {})
    ledger = load_json(ledger_latest, {})
    three_stage = load_json(three_stage_latest, {})
    text = json.dumps(report, ensure_ascii=False)
    morning_text = json.dumps(morning, ensure_ascii=False)
    ledger_text = json.dumps(ledger, ensure_ascii=False)
    three_stage_text = json.dumps(three_stage, ensure_ascii=False)
    safety = report.get("安全边界", {})
    actions = report.get("实际动作", {})
    source_status = report.get("来源文件状态", {})
    required_sources = [
        "258长期观察闭环灰度包",
        "259模型与时段调度策略包",
        "股票AI反馈脚本",
        "进化反馈样本候选脚本",
        "本地主动研究闭环脚本",
        "推送草案最新文件",
        "反馈日志",
        "复盘学习闭环状态面板",
    ]
    missing_sources = [name for name in required_sources if not source_status.get(name, {}).get("存在")]
    dangerous_keys = [
        "导入n8n",
        "启用n8n工作流",
        "触发n8n",
        "真实发送企业微信",
        "群发",
        "调用券商接口",
        "自动交易",
        "自动转正式规则",
        "重载19310",
        "重载19302",
        "修改总管面板",
        "修改一键接续包",
    ]
    safety_danger = [key for key in dangerous_keys if safety.get(key) is not False]
    action_danger = [key for key in dangerous_keys if key in actions and actions.get(key) is not False]
    morning_required = ["今日重点关注", "昨日推送复盘", "新增或替换候选", "降级或风险复核", "今日观察条件", "证据缺口", "非投资建议声明"]
    ledger_required = ["推送对象", "入选原因", "风险提醒", "观察条件", "是否进入晨报", "是否被替换", "替换原因", "用户反馈", "晚间复盘结论", "进化候选状态", "原始产物路径"]
    morning_ok, morning_missing = contains_all_keys(morning, morning_required)
    ledger_fields = ledger.get("字段", [])
    ledger_missing = [key for key in ledger_required if key not in ledger_fields]
    ledger_records = ledger.get("记录", [])
    record_missing = []
    for index, item in enumerate(ledger_records):
        missing = [key for key in ledger_required if key not in item]
        if missing:
            record_missing.append({"序号": index, "缺字段": missing})
    blocked_scan = scan_for_blocked_terms([morning_latest, morning_latest_md, ledger_latest, ledger_latest_md])
    sample_safety = [morning.get("安全边界", {}), ledger.get("安全边界", {})]
    sample_safety_failed = []
    for index, item in enumerate(sample_safety):
        for key in ["是否接券商", "是否交易", "是否真实发送企业微信", "是否群发", "是否导入n8n", "是否启用n8n", "是否触发n8n"]:
            if item.get(key) is not False:
                sample_safety_failed.append({"样例序号": index, "字段": key, "值": item.get(key)})
    three_reports = three_stage.get("三阶段报告", {})
    after_close = three_reports.get("盘后短线复盘", "")
    deep_report = three_reports.get("晚间三维深度分析", "")
    pre_open = three_reports.get("盘前出击排序", "")
    empty_report_scan = scan_for_empty_report_terms("\n".join([after_close, deep_report, pre_open]))
    three_safety_failed = []
    for key in ["是否真实发送企业微信", "是否触发n8n", "是否接券商", "是否交易", "是否群发"]:
        if three_stage.get("安全边界", {}).get(key) is not False:
            three_safety_failed.append({"字段": key, "值": three_stage.get("安全边界", {}).get(key)})

    checks = [
        check("生成脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr[-1000:]}),
        check("260策略包存在", latest.exists(), str(latest)),
        check("覆盖轻量随问随答", "轻量随问随答" in text and "全天" in text, report.get("日内闭环")),
        check("覆盖收市后每日观察", "收市后每日观察" in text and "15:40-18:30" in text and "第二天候选推荐草案" in text, report.get("日内闭环")),
        check("覆盖半夜宏观规律分析", "半夜宏观规律分析" in text and "00:30-05:30" in text and "市场风格" in text, report.get("日内闭环")),
        check("覆盖开市前晨报推送", "开市前晨报推送" in text and "08:20-08:40" in text and "今日重点关注" in text, report.get("晨报推送策略")),
        check("晨报允许一条摘要包含多只但不群发", "一条本人晨报摘要" in text and "不是群发" in text and safety.get("群发") is False, report.get("晨报推送策略")),
        check("覆盖晚间问题纠偏和替换候选", all(keyword in text for keyword in ["晚间复盘", "降级", "替换候选", "第二天晨报"]), report.get("学习沉淀账设计")),
        check("覆盖学习沉淀和进化候选", "学习沉淀账" in text and "进化候选" in text and safety.get("自动转正式规则") is False, report.get("学习沉淀账设计")),
        check("开市前晨报样例存在", morning_latest.exists() and morning_latest_md.exists(), [str(morning_latest), str(morning_latest_md)]),
        check("开市前晨报样例字段齐全", morning_ok, morning_missing),
        check("开市前晨报样例内容覆盖要求", all(keyword in morning_text for keyword in morning_required), morning_required),
        check("股票主动推送学习沉淀账样例存在", ledger_latest.exists() and ledger_latest_md.exists(), [str(ledger_latest), str(ledger_latest_md)]),
        check("股票主动推送学习沉淀账字段齐全", not ledger_missing and not record_missing and len(ledger_records) >= 1, {"账本缺字段": ledger_missing, "记录缺字段": record_missing, "记录数": len(ledger_records)}),
        check("学习沉淀账内容覆盖要求", all(keyword in ledger_text for keyword in ledger_required), ledger_required),
        check("三阶段报告流程样例存在", three_stage_latest.exists() and three_stage_latest_md.exists(), [str(three_stage_latest), str(three_stage_latest_md)]),
        check("三阶段报告标题固定", all(keyword in three_stage_text for keyword in ["【收盘短线观察｜", "【深度三维研究｜", "【盘前出击排序｜"]), list(three_reports.keys())),
        check("三阶段报告开头固定", all(keyword in three_stage_text for keyword in [
            "杰哥，您好。今天收盘后，通过纯量价扫描",
            "杰哥，您好。今晚我对观察池和主线方向做了三维过滤",
            "杰哥，早上好。今日盘前根据触发条件共振度排序",
        ]), "固定开头检查"),
        check("三阶段报告落到触发条件和价位", all(keyword in three_stage_text for keyword in ["183.04元", "389.51元", "709.13元", "172.89元", "373.61元", "680.18元"]), "关键价位检查"),
        check("三阶段报告禁止空泛话术", empty_report_scan["通过"], empty_report_scan),
        check("三阶段对标现有股票池与指标基础", all(keyword in three_stage_text for keyword in ["01股票池", "12技术指标", "L6行业主题观察池规则", "L5深度研究池规则"]), "现有基础检查"),
        check("三阶段报告安全边界关闭", not three_safety_failed, three_safety_failed),
        check("本地样例无交易化指令词命中", blocked_scan["通过"], {"命中数量": blocked_scan["命中数量"]}),
        check("本地样例安全边界关闭", not sample_safety_failed, sample_safety_failed),
        check("来源入口齐全", not missing_sources, missing_sources),
        check("安全边界未触发危险动作", not safety_danger, safety_danger),
        check("实际动作未触发危险动作", not action_danger, action_danger),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查结果": checks,
        "策略包": str(latest),
        "生成stdout": completed.stdout[-2000:],
    }
    log_dir = root / "04日志" / "股票n8n日内报告闭环与晨报推送策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = log_dir / f"stock-n8n-intraday-report-loop-morning-push-package-verify-{stamp}.json"
    latest_json = log_dir / "stock-n8n-intraday-report-loop-morning-push-package-verify-最新.json"
    output_md = log_dir / f"stock-n8n-intraday-report-loop-morning-push-package-verify-{stamp}.md"
    latest_md = log_dir / "stock-n8n-intraday-report-loop-morning-push-package-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": result["总体状态"], "通过": result["通过"], "失败": result["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
