# -*- coding: utf-8 -*-
"""
名称：验证股票系统C加加加日常可用总验收.py
作用：按当前C+++交付形态验收股票系统日常可用性，覆盖本地闭环、质量灯号、安全边界和交付材料。
触发方式：python 验证股票系统C加加加日常可用总验收.py
依赖：交付总包、交付控制台、质量面板、报告安全检查、194受控同步dry-run验证等最新文件。
所属系统：02杰哥扩展系统/01股票研究系统
输出：03数据/153C加加加总验收/股票系统C加加加日常可用总验收_最新.json 与 .md；05入口工具打开入口。
安全边界：只读本地状态文件；只写03数据/153C加加加总验收和05入口工具；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不更新施工接续包。
标识：stock-cppp-daily-acceptance
"""

from __future__ import annotations

import json
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_check(name: str, path: Path, min_size: int = 1) -> dict[str, Any]:
    wait_for_file_stable(path)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "检查项": name,
        "路径": str(path),
        "通过": bool(exists and size >= min_size),
        "存在": exists,
        "大小": size,
        "说明": "文件存在且大小符合要求" if exists and size >= min_size else "文件缺失或为空",
    }


def report_data_check(path: Path) -> dict[str, Any]:
    wait_for_file_stable(path)
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    text = path.read_text(encoding="utf-8-sig") if exists else ""
    ok = exists and "状态：通过" in text and "严重问题数：0" in text
    return {
        "检查项": "报告数据口径检查",
        "路径": str(path),
        "通过": ok,
        "存在": exists,
        "大小": size,
        "说明": "报告数据口径检查结论通过且严重问题为0" if ok else "报告数据口径检查未通过或结论缺失",
    }


def service_port_check(name: str, port: int) -> dict[str, Any]:
    ok = False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            ok = True
        message = f"127.0.0.1:{port} 正常监听"
    except OSError as exc:
        message = f"127.0.0.1:{port} 未能连接：{exc}"
    return {
        "检查项": name,
        "路径": f"127.0.0.1:{port}",
        "通过": ok,
        "存在": ok,
        "大小": 0,
        "说明": message,
    }


def first_pending_stock(entry: dict[str, Any]) -> dict[str, Any]:
    tasks = entry.get("逐股任务", []) if isinstance(entry.get("逐股任务"), list) else []
    for item in tasks:
        if int(item.get("合计待填") or 0) > 0:
            return item
    return {}


def stock_evidence_target_follow_check(root: Path) -> dict[str, Any]:
    entry_path = root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json"
    package_path = root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.json"
    entry = load_json(entry_path, {}) or {}
    package = load_json(package_path, {}) or {}
    expected = first_pending_stock(entry)
    actual = package.get("目标股票", {}) if isinstance(package.get("目标股票"), dict) else {}
    passed = bool(expected) and actual.get("代码") == expected.get("代码")
    return {
        "检查项": "单股证据核验目标跟随189入口",
        "路径": f"{entry_path} -> {package_path}",
        "通过": passed,
        "存在": entry_path.exists() and package_path.exists(),
        "大小": package_path.stat().st_size if package_path.exists() else 0,
        "说明": (
            f"189第一只待核验={expected.get('名称')}({expected.get('代码')})；"
            f"190当前目标={actual.get('名称')}({actual.get('代码')})"
        ),
    }


def template_sync_dry_run_verify_check(root: Path) -> dict[str, Any]:
    path = root / "04日志" / "单股证据核验模板同步执行" / "single-stock-evidence-template-sync-execute-verify-最新.json"
    data = load_json(path, {}) or {}
    checks = data.get("检查项", []) if isinstance(data.get("检查项"), list) else []
    passed = (
        path.exists()
        and int(data.get("失败") or 0) == 0
        and any(item.get("名称") == "193闸口状态与191完成度一致" and item.get("通过") is True for item in checks)
        and any(item.get("名称") == "默认不写入人工模板" and item.get("通过") is True for item in checks)
    )
    return {
        "检查项": "194受控同步dry-run验证",
        "路径": str(path),
        "通过": passed,
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "说明": f"通过={data.get('通过')}；失败={data.get('失败')}；验证193闸口状态与默认不写入人工模板",
    }


def after_191_preflight_verify_check(root: Path) -> dict[str, Any]:
    path = root / "04日志" / "单股证据核验191完成后预演检查" / "single-stock-evidence-after-191-preflight-verify-最新.json"
    data = load_json(path, {}) or {}
    checks = data.get("检查项", []) if isinstance(data.get("检查项"), list) else []
    passed = (
        path.exists()
        and int(data.get("失败") or 0) == 0
        and any(item.get("名称") in {"默认模式不写191台账", "验证过程不额外改写191台账"} and item.get("通过") is True for item in checks)
        and any(item.get("名称") in {"默认模式不覆盖CSV表单", "验证过程不覆盖CSV表单"} and item.get("通过") is True for item in checks)
        and any(item.get("名称") == "执行模式符合当前阶段" and item.get("通过") is True for item in checks)
        and any(item.get("名称") == "预演动作链完整" and item.get("通过") is True for item in checks)
    )
    return {
        "检查项": "197单股证据核验191完成后预演检查",
        "路径": str(path),
        "通过": passed,
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "说明": f"通过={data.get('通过')}；失败={data.get('失败')}；验证当前阶段写入边界、CSV不覆盖、动作链完整",
    }


def current_manual_guidance_legacy_check(root: Path) -> dict[str, Any]:
    current_docs = [
        root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.json",
        root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.md",
        root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.json",
        root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.md",
        root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写工作台_最新.md",
    ]
    current_bats = list((root / "05入口工具").glob("*.bat"))
    hits: list[str] = []
    doc_forbidden = [
        "python 同步单股证据核验CSV表单到台账.py",
        "python 生成公司概况核验导入预览.py",
        "python 生成事件风险证据核验预览.py",
        "python 生成行业景气核验预览.py",
        '"预览脚本": "生成公司概况核验导入预览.py"',
        '"预览脚本": "生成事件风险证据核验预览.py"',
        '"预览脚本": "生成行业景气核验预览.py"',
        "填完模板后，运行对应预览脚本",
    ]
    bat_forbidden = [
        "python \"同步单股证据核验CSV表单到台账.py\"",
        "python 同步单股证据核验CSV表单到台账.py",
        "生成公司概况核验导入预览.py",
        "生成事件风险证据核验预览.py",
        "生成行业景气核验预览.py",
        "192单股证据核验台账同步预览\\单股证据核验台账同步预览_最新.md",
        "193单股证据核验模板同步执行闸口\\单股证据核验模板同步执行闸口_最新.md",
    ]
    for path in current_docs:
        wait_for_file_stable(path)
        if not path.exists():
            hits.append(f"缺失：{path}")
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for token in doc_forbidden:
            if token in text:
                hits.append(f"{path} -> {token}")
    for path in current_bats:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for token in bat_forbidden:
            if token in text:
                hits.append(f"{path} -> {token}")
    return {
        "检查项": "当前人工入口无旧口径直达指令",
        "路径": "189/190/191最新产物与05入口工具",
        "通过": not hits,
        "存在": all(path.exists() for path in current_docs),
        "大小": len(current_docs) + len(current_bats),
        "说明": "未发现旧直达指令" if not hits else "；".join(hits[:8]),
    }


def wait_for_file_stable(path: Path, attempts: int = 5, delay: float = 0.2) -> None:
    """Avoid transient false negatives while another local script is rewriting a file."""
    previous_size = -1
    for _ in range(attempts):
        if not path.exists():
            time.sleep(delay)
            continue
        current_size = path.stat().st_size
        if current_size > 0 and current_size == previous_size:
            return
        previous_size = current_size
        time.sleep(delay)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统C+++日常可用总验收 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过：{report['通过数量']} / {report['检查数量']}",
        f"- 失败：{report['失败数量']}",
        f"- 当前交付层级：{report['当前交付层级']}",
        f"- 剩余硬阻断：{report['剩余硬阻断']}",
        "",
        "## 二、检查明细",
        "",
    ]
    lines.append("| 检查项 | 结果 | 说明 |")
    lines.append("|---|---|---|")
    for item in report["检查结果"]:
        lines.append(f"| {item['检查项']} | {'通过' if item['通过'] else '失败'} | {item['说明']} |")
    lines.extend([
        "",
        "## 三、失败项",
        "",
    ])
    failed = [item for item in report["检查结果"] if not item["通过"]]
    if failed:
        for item in failed:
            lines.append(f"- {item['检查项']}：{item['说明']}，`{item.get('路径', '')}`")
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
        "- 不触发n8n。",
        "- 不发送企业微信真实消息。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不修改旧系统。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "股票系统C+++日常可用总验收_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    total_package_path = root / "03数据" / "144交付总包" / "股票系统交付总包_最新.json"
    quality_path = root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.json"
    safety_path = root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.json"

    total = load_json(total_package_path, {})
    quality = load_json(quality_path, {})
    safety = load_json(safety_path, {})
    quality_light = (quality.get("质量灯号") or {}).get("灯号") or "未知"
    safety_conclusion = safety.get("安全结论") or "未知"
    remaining_block = str(total.get("剩余硬阻断") or "")
    remaining_block_ok = ("可信IP" in remaining_block) or (remaining_block in {"无", "无阻断", "无硬阻断"})
    delivery_level = str(total.get("当前交付层级") or "")
    delivery_level_ok = ("C+++" in delivery_level) or delivery_level.startswith("D")

    daily_available_text = str(total.get("日常可用结论") or total.get("日常可用") or "")
    checks: list[dict[str, Any]] = [
        {"检查项": "交付总包声明日常可用", "通过": "可日常使用" in daily_available_text or total.get("日常可用") is True, "说明": daily_available_text},
        {"检查项": "交付层级达到C+++或更高", "通过": delivery_level_ok, "说明": delivery_level},
        {"检查项": "剩余硬阻断状态合理", "通过": remaining_block_ok, "说明": remaining_block},
        {"检查项": "质量灯号未红灯", "通过": quality_light in {"绿灯", "黄灯"}, "说明": f"质量灯号={quality_light}"},
        {"检查项": "报告安全边界通过", "通过": safety_conclusion == "通过" and int(safety.get("命中总数") or 0) == 0, "说明": f"安全结论={safety_conclusion}，命中={safety.get('命中总数')}"},
    ]
    checks.extend([
        service_port_check("股票助手服务19300实时监听", 19300),
        service_port_check("股票企微桥接19302实时监听", 19302),
    ])
    file_targets = [
        ("AI分析报告", root / "03数据" / "135分层日报" / "AI分析报告_最新.md", 1000),
        ("企微推送草案", root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md", 300),
        ("交付控制台", root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.md", 500),
        ("日常速查卡", root / "03数据" / "145日常速查卡" / "股票系统日常使用速查卡_最新.md", 500),
        ("质量观察面板", root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md", 500),
        ("报告安全边界检查", root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md", 500),
        ("可信IP状态监测", root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md", 500),
        ("日常一键运行记录", root / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.md", 500),
        ("企微真实推送复测控制器", root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.md", 500),
        ("企微前台交互回归验收", root / "03数据" / "182企微前台交互回归验收" / "股票企微前台交互回归验收_最新.md", 500),
        ("金融复核覆盖面板", root / "03数据" / "186金融复核覆盖面板" / "推荐观察股金融复核覆盖面板_最新.md", 500),
        ("复盘学习闭环状态面板", root / "03数据" / "187复盘学习闭环状态面板" / "股票复盘学习闭环状态面板_最新.md", 500),
        ("判断复盘到期提醒清单", root / "03数据" / "188判断复盘到期提醒与人工填写清单" / "股票判断复盘到期提醒与人工填写清单_最新.md", 500),
        ("证据链人工核验入口", root / "03数据" / "189证据链人工核验入口" / "股票证据链人工核验入口_最新.md", 500),
        ("单股证据核验工作包", root / "03数据" / "190单股证据核验工作包" / "单股证据核验工作包_最新.md", 500),
        ("单股证据核验人工填写台账", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写台账_最新.md", 500),
        ("单股证据核验人工填写CSV表单", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv", 500),
        ("单股证据核验人工填写说明卡", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写说明卡_最新.md", 500),
        ("单股证据核验人工填写最小行动卡", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写最小行动卡_最新.md", 500),
        ("单股证据核验资料来源导航卡", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验资料来源导航卡_最新.md", 500),
        ("单股证据核验资料候选处理包", root / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.md", 500),
        ("单股证据核验191填写建议草案", root / "03数据" / "200单股证据核验191填写建议草案" / "单股证据核验191填写建议草案_最新.md", 500),
        ("单股证据核验最小人工确认清单", root / "03数据" / "201单股证据核验最小人工确认清单" / "单股证据核验最小人工确认清单_最新.md", 500),
        ("单股证据核验191候选填写CSV副本", root / "03数据" / "202单股证据核验191候选填写CSV副本" / "单股证据核验191候选填写CSV副本_最新.md", 500),
        ("单股证据核验191候选写入差异预览", root / "03数据" / "203单股证据核验191候选写入差异预览" / "单股证据核验191候选写入差异预览_最新.md", 500),
        ("单股证据核验191候选采用后质量预演", root / "03数据" / "204单股证据核验191候选采用后质量预演" / "单股证据核验191候选采用后质量预演_最新.md", 500),
        ("单股证据核验191候选采用确认回执草案", root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.md", 500),
        ("单股证据核验确认回执状态面板", root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.md", 500),
        ("单股证据核验回执后调度清单", root / "03数据" / "211单股证据核验回执后调度清单" / "单股证据核验回执后调度清单_最新.md", 500),
        ("单股证据核验确认回执填写样例副本", root / "03数据" / "212单股证据核验确认回执填写样例副本" / "单股证据核验确认回执填写样例副本_最新.md", 500),
        ("单股证据核验确认后路径演练报告", root / "03数据" / "213单股证据核验确认后路径演练报告" / "单股证据核验确认后路径演练报告_最新.md", 500),
        ("单股证据核验正式回执待办卡", root / "03数据" / "214单股证据核验正式回执待办卡" / "单股证据核验正式回执待办卡_最新.md", 500),
        ("单股证据核验正式回执填写前自检", root / "03数据" / "215单股证据核验正式回执填写前自检" / "单股证据核验正式回执填写前自检_最新.md", 500),
        ("单股证据核验正式回执录入后受控重跑预演", root / "03数据" / "216单股证据核验正式回执录入后受控重跑预演" / "单股证据核验正式回执录入后受控重跑预演_最新.md", 500),
        ("单股证据核验191候选采用前闸口", root / "03数据" / "206单股证据核验191候选采用前闸口" / "单股证据核验191候选采用前闸口_最新.md", 500),
        ("单股证据核验191候选采用受控执行预案", root / "03数据" / "207单股证据核验191候选采用受控执行预案" / "单股证据核验191候选采用受控执行预案_最新.md", 500),
        ("单股证据核验191候选采用预览", root / "03数据" / "208单股证据核验191候选采用预览" / "单股证据核验191候选采用预览_最新.md", 500),
        ("单股证据核验受控写入命令草案", root / "03数据" / "209单股证据核验受控写入命令草案" / "单股证据核验受控写入命令草案_最新.md", 500),
        ("单股证据核验191填写质量闸口", root / "03数据" / "198单股证据核验191填写质量闸口" / "单股证据核验191填写质量闸口_最新.md", 500),
        ("单股证据核验人工填写工作台", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写工作台_最新.md", 500),
        ("单股证据核验人工填写进度自检面板", root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写进度自检面板_最新.md", 500),
        ("单股证据核验台账同步预览", root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.md", 500),
        ("单股证据核验模板同步执行闸口", root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.md", 500),
        ("单股证据核验模板同步执行报告", root / "03数据" / "194单股证据核验模板同步执行" / "单股证据核验模板同步执行报告_最新.md", 500),
        ("单股证据核验191完成后预演检查", root / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md", 500),
        ("证据核验正式导入执行报告", root / "03数据" / "195证据核验正式导入执行" / "股票证据核验正式导入执行报告_最新.md", 500),
        ("事件风险核验证据账", root / "03数据" / "195事件风险核验证据账" / "事件风险核验证据账_最新.json", 300),
        ("推荐点击详情与手机排版验收", root / "03数据" / "196推荐点击详情与手机排版验收" / "股票推荐点击详情与手机排版验收_最新.md", 500),
    ]
    checks.extend(file_check(name, path, min_size) for name, path, min_size in file_targets)
    checks.append(report_data_check(root / "03数据" / "183报告数据口径检查" / "股票报告数据口径检查_最新.md"))
    checks.append(stock_evidence_target_follow_check(root))
    checks.append(current_manual_guidance_legacy_check(root))
    checks.append(template_sync_dry_run_verify_check(root))
    checks.append(after_191_preflight_verify_check(root))
    minimum_card_verify = root / "04日志" / "单股证据核验人工填写最小行动卡" / "single-stock-evidence-minimum-action-card-verify-最新.json"
    minimum_card_data = load_json(minimum_card_verify, {}) or {}
    checks.append({
        "检查项": "191最小行动卡验证",
        "路径": str(minimum_card_verify),
        "通过": minimum_card_verify.exists() and int(minimum_card_data.get("失败") or 0) == 0,
        "存在": minimum_card_verify.exists(),
        "大小": minimum_card_verify.stat().st_size if minimum_card_verify.exists() else 0,
        "说明": f"通过={minimum_card_data.get('通过')}；失败={minimum_card_data.get('失败')}",
    })
    source_nav_verify = root / "04日志" / "单股证据核验资料来源导航卡" / "single-stock-evidence-source-navigation-card-verify-最新.json"
    source_nav_data = load_json(source_nav_verify, {}) or {}
    checks.append({
        "检查项": "191资料来源导航卡验证",
        "路径": str(source_nav_verify),
        "通过": source_nav_verify.exists() and int(source_nav_data.get("失败") or 0) == 0,
        "存在": source_nav_verify.exists(),
        "大小": source_nav_verify.stat().st_size if source_nav_verify.exists() else 0,
        "说明": f"通过={source_nav_data.get('通过')}；失败={source_nav_data.get('失败')}",
    })
    source_candidate_verify = root / "04日志" / "单股证据核验资料候选处理包" / "single-stock-evidence-source-candidate-package-verify-最新.json"
    source_candidate_data = load_json(source_candidate_verify, {}) or {}
    checks.append({
        "检查项": "199资料候选处理包验证",
        "路径": str(source_candidate_verify),
        "通过": source_candidate_verify.exists() and int(source_candidate_data.get("失败") or 0) == 0,
        "存在": source_candidate_verify.exists(),
        "大小": source_candidate_verify.stat().st_size if source_candidate_verify.exists() else 0,
        "说明": f"通过={source_candidate_data.get('通过')}；失败={source_candidate_data.get('失败')}",
    })
    suggestion_draft_verify = root / "04日志" / "单股证据核验191填写建议草案" / "single-stock-evidence-191-fill-suggestion-draft-verify-最新.json"
    suggestion_draft_data = load_json(suggestion_draft_verify, {}) or {}
    checks.append({
        "检查项": "200填写建议草案验证",
        "路径": str(suggestion_draft_verify),
        "通过": suggestion_draft_verify.exists() and int(suggestion_draft_data.get("失败") or 0) == 0,
        "存在": suggestion_draft_verify.exists(),
        "大小": suggestion_draft_verify.stat().st_size if suggestion_draft_verify.exists() else 0,
        "说明": f"通过={suggestion_draft_data.get('通过')}；失败={suggestion_draft_data.get('失败')}",
    })
    minimal_confirmation_verify = root / "04日志" / "单股证据核验最小人工确认清单" / "single-stock-evidence-minimal-human-confirmation-list-verify-最新.json"
    minimal_confirmation_data = load_json(minimal_confirmation_verify, {}) or {}
    checks.append({
        "检查项": "201最小人工确认清单验证",
        "路径": str(minimal_confirmation_verify),
        "通过": minimal_confirmation_verify.exists() and int(minimal_confirmation_data.get("失败") or 0) == 0,
        "存在": minimal_confirmation_verify.exists(),
        "大小": minimal_confirmation_verify.stat().st_size if minimal_confirmation_verify.exists() else 0,
        "说明": f"通过={minimal_confirmation_data.get('通过')}；失败={minimal_confirmation_data.get('失败')}",
    })
    candidate_csv_verify = root / "04日志" / "单股证据核验191候选填写CSV副本" / "single-stock-evidence-191-candidate-filled-csv-copy-verify-最新.json"
    candidate_csv_data = load_json(candidate_csv_verify, {}) or {}
    checks.append({
        "检查项": "202候选填写CSV副本验证",
        "路径": str(candidate_csv_verify),
        "通过": candidate_csv_verify.exists() and int(candidate_csv_data.get("失败") or 0) == 0,
        "存在": candidate_csv_verify.exists(),
        "大小": candidate_csv_verify.stat().st_size if candidate_csv_verify.exists() else 0,
        "说明": f"通过={candidate_csv_data.get('通过')}；失败={candidate_csv_data.get('失败')}",
    })
    candidate_diff_verify = root / "04日志" / "单股证据核验191候选写入差异预览" / "single-stock-evidence-191-candidate-write-diff-preview-verify-最新.json"
    candidate_diff_data = load_json(candidate_diff_verify, {}) or {}
    checks.append({
        "检查项": "203候选写入差异预览验证",
        "路径": str(candidate_diff_verify),
        "通过": candidate_diff_verify.exists() and int(candidate_diff_data.get("失败") or 0) == 0,
        "存在": candidate_diff_verify.exists(),
        "大小": candidate_diff_verify.stat().st_size if candidate_diff_verify.exists() else 0,
        "说明": f"通过={candidate_diff_data.get('通过')}；失败={candidate_diff_data.get('失败')}",
    })
    candidate_quality_preview_verify = root / "04日志" / "单股证据核验191候选采用后质量预演" / "single-stock-evidence-191-candidate-adoption-quality-preview-verify-最新.json"
    candidate_quality_preview_data = load_json(candidate_quality_preview_verify, {}) or {}
    checks.append({
        "检查项": "204候选采用后质量预演验证",
        "路径": str(candidate_quality_preview_verify),
        "通过": candidate_quality_preview_verify.exists() and int(candidate_quality_preview_data.get("失败") or 0) == 0,
        "存在": candidate_quality_preview_verify.exists(),
        "大小": candidate_quality_preview_verify.stat().st_size if candidate_quality_preview_verify.exists() else 0,
        "说明": f"通过={candidate_quality_preview_data.get('通过')}；失败={candidate_quality_preview_data.get('失败')}",
    })
    candidate_confirmation_verify = root / "04日志" / "单股证据核验191候选采用确认回执草案" / "single-stock-evidence-191-candidate-adoption-confirmation-draft-verify-最新.json"
    candidate_confirmation_data = load_json(candidate_confirmation_verify, {}) or {}
    checks.append({
        "检查项": "205候选采用确认回执草案验证",
        "路径": str(candidate_confirmation_verify),
        "通过": candidate_confirmation_verify.exists() and int(candidate_confirmation_data.get("失败") or 0) == 0,
        "存在": candidate_confirmation_verify.exists(),
        "大小": candidate_confirmation_verify.stat().st_size if candidate_confirmation_verify.exists() else 0,
        "说明": f"通过={candidate_confirmation_data.get('通过')}；失败={candidate_confirmation_data.get('失败')}",
    })
    receipt_status_verify = root / "04日志" / "单股证据核验确认回执状态面板" / "single-stock-evidence-confirmation-receipt-status-panel-verify-最新.json"
    receipt_status_data = load_json(receipt_status_verify, {}) or {}
    checks.append({
        "检查项": "210确认回执状态面板验证",
        "路径": str(receipt_status_verify),
        "通过": receipt_status_verify.exists() and int(receipt_status_data.get("失败") or 0) == 0,
        "存在": receipt_status_verify.exists(),
        "大小": receipt_status_verify.stat().st_size if receipt_status_verify.exists() else 0,
        "说明": f"通过={receipt_status_data.get('通过')}；失败={receipt_status_data.get('失败')}",
    })
    post_confirmation_dispatch_verify = root / "04日志" / "单股证据核验回执后调度清单" / "single-stock-evidence-post-confirmation-dispatch-list-verify-最新.json"
    post_confirmation_dispatch_data = load_json(post_confirmation_dispatch_verify, {}) or {}
    checks.append({
        "检查项": "211回执后调度清单验证",
        "路径": str(post_confirmation_dispatch_verify),
        "通过": post_confirmation_dispatch_verify.exists() and int(post_confirmation_dispatch_data.get("失败") or 0) == 0,
        "存在": post_confirmation_dispatch_verify.exists(),
        "大小": post_confirmation_dispatch_verify.stat().st_size if post_confirmation_dispatch_verify.exists() else 0,
        "说明": f"通过={post_confirmation_dispatch_data.get('通过')}；失败={post_confirmation_dispatch_data.get('失败')}",
    })
    receipt_example_verify = root / "04日志" / "单股证据核验确认回执填写样例副本" / "single-stock-evidence-confirmation-receipt-filled-example-copy-verify-最新.json"
    receipt_example_data = load_json(receipt_example_verify, {}) or {}
    checks.append({
        "检查项": "212确认回执填写样例副本验证",
        "路径": str(receipt_example_verify),
        "通过": receipt_example_verify.exists() and int(receipt_example_data.get("失败") or 0) == 0,
        "存在": receipt_example_verify.exists(),
        "大小": receipt_example_verify.stat().st_size if receipt_example_verify.exists() else 0,
        "说明": f"通过={receipt_example_data.get('通过')}；失败={receipt_example_data.get('失败')}",
    })
    post_confirmation_rehearsal_verify = root / "04日志" / "单股证据核验确认后路径演练报告" / "single-stock-evidence-post-confirmation-path-rehearsal-report-verify-最新.json"
    post_confirmation_rehearsal_data = load_json(post_confirmation_rehearsal_verify, {}) or {}
    checks.append({
        "检查项": "213确认后路径演练报告验证",
        "路径": str(post_confirmation_rehearsal_verify),
        "通过": post_confirmation_rehearsal_verify.exists() and int(post_confirmation_rehearsal_data.get("失败") or 0) == 0,
        "存在": post_confirmation_rehearsal_verify.exists(),
        "大小": post_confirmation_rehearsal_verify.stat().st_size if post_confirmation_rehearsal_verify.exists() else 0,
        "说明": f"通过={post_confirmation_rehearsal_data.get('通过')}；失败={post_confirmation_rehearsal_data.get('失败')}",
    })
    formal_receipt_todo_verify = root / "04日志" / "单股证据核验正式回执待办卡" / "single-stock-evidence-formal-confirmation-receipt-todo-card-verify-最新.json"
    formal_receipt_todo_data = load_json(formal_receipt_todo_verify, {}) or {}
    checks.append({
        "检查项": "214正式回执待办卡验证",
        "路径": str(formal_receipt_todo_verify),
        "通过": formal_receipt_todo_verify.exists() and int(formal_receipt_todo_data.get("失败") or 0) == 0,
        "存在": formal_receipt_todo_verify.exists(),
        "大小": formal_receipt_todo_verify.stat().st_size if formal_receipt_todo_verify.exists() else 0,
        "说明": f"通过={formal_receipt_todo_data.get('通过')}；失败={formal_receipt_todo_data.get('失败')}",
    })
    formal_receipt_prefill_verify = root / "04日志" / "单股证据核验正式回执填写前自检" / "single-stock-evidence-formal-confirmation-receipt-prefill-check-verify-最新.json"
    formal_receipt_prefill_data = load_json(formal_receipt_prefill_verify, {}) or {}
    checks.append({
        "检查项": "215正式回执填写前自检验证",
        "路径": str(formal_receipt_prefill_verify),
        "通过": formal_receipt_prefill_verify.exists() and int(formal_receipt_prefill_data.get("失败") or 0) == 0,
        "存在": formal_receipt_prefill_verify.exists(),
        "大小": formal_receipt_prefill_verify.stat().st_size if formal_receipt_prefill_verify.exists() else 0,
        "说明": f"通过={formal_receipt_prefill_data.get('通过')}；失败={formal_receipt_prefill_data.get('失败')}",
    })
    formal_receipt_rerun_rehearsal_verify = root / "04日志" / "单股证据核验正式回执录入后受控重跑预演" / "single-stock-evidence-formal-confirmation-post-entry-controlled-rerun-rehearsal-verify-最新.json"
    formal_receipt_rerun_rehearsal_data = load_json(formal_receipt_rerun_rehearsal_verify, {}) or {}
    checks.append({
        "检查项": "216正式回执录入后受控重跑预演验证",
        "路径": str(formal_receipt_rerun_rehearsal_verify),
        "通过": formal_receipt_rerun_rehearsal_verify.exists() and int(formal_receipt_rerun_rehearsal_data.get("失败") or 0) == 0,
        "存在": formal_receipt_rerun_rehearsal_verify.exists(),
        "大小": formal_receipt_rerun_rehearsal_verify.stat().st_size if formal_receipt_rerun_rehearsal_verify.exists() else 0,
        "说明": f"通过={formal_receipt_rerun_rehearsal_data.get('通过')}；失败={formal_receipt_rerun_rehearsal_data.get('失败')}",
    })
    candidate_pre_gate_verify = root / "04日志" / "单股证据核验191候选采用前闸口" / "single-stock-evidence-191-candidate-adoption-pre-gate-verify-最新.json"
    candidate_pre_gate_data = load_json(candidate_pre_gate_verify, {}) or {}
    checks.append({
        "检查项": "206候选采用前闸口验证",
        "路径": str(candidate_pre_gate_verify),
        "通过": candidate_pre_gate_verify.exists() and int(candidate_pre_gate_data.get("失败") or 0) == 0,
        "存在": candidate_pre_gate_verify.exists(),
        "大小": candidate_pre_gate_verify.stat().st_size if candidate_pre_gate_verify.exists() else 0,
        "说明": f"通过={candidate_pre_gate_data.get('通过')}；失败={candidate_pre_gate_data.get('失败')}",
    })
    candidate_controlled_plan_verify = root / "04日志" / "单股证据核验191候选采用受控执行预案" / "single-stock-evidence-191-candidate-adoption-controlled-plan-verify-最新.json"
    candidate_controlled_plan_data = load_json(candidate_controlled_plan_verify, {}) or {}
    checks.append({
        "检查项": "207候选采用受控执行预案验证",
        "路径": str(candidate_controlled_plan_verify),
        "通过": candidate_controlled_plan_verify.exists() and int(candidate_controlled_plan_data.get("失败") or 0) == 0,
        "存在": candidate_controlled_plan_verify.exists(),
        "大小": candidate_controlled_plan_verify.stat().st_size if candidate_controlled_plan_verify.exists() else 0,
        "说明": f"通过={candidate_controlled_plan_data.get('通过')}；失败={candidate_controlled_plan_data.get('失败')}",
    })
    candidate_preview_verify = root / "04日志" / "单股证据核验191候选采用预览" / "single-stock-evidence-191-candidate-adoption-preview-verify-最新.json"
    candidate_preview_data = load_json(candidate_preview_verify, {}) or {}
    checks.append({
        "检查项": "208候选采用预览验证",
        "路径": str(candidate_preview_verify),
        "通过": candidate_preview_verify.exists() and int(candidate_preview_data.get("失败") or 0) == 0,
        "存在": candidate_preview_verify.exists(),
        "大小": candidate_preview_verify.stat().st_size if candidate_preview_verify.exists() else 0,
        "说明": f"通过={candidate_preview_data.get('通过')}；失败={candidate_preview_data.get('失败')}",
    })
    controlled_command_verify = root / "04日志" / "单股证据核验受控写入命令草案" / "single-stock-evidence-controlled-write-command-draft-verify-最新.json"
    controlled_command_data = load_json(controlled_command_verify, {}) or {}
    checks.append({
        "检查项": "209受控写入命令草案验证",
        "路径": str(controlled_command_verify),
        "通过": controlled_command_verify.exists() and int(controlled_command_data.get("失败") or 0) == 0,
        "存在": controlled_command_verify.exists(),
        "大小": controlled_command_verify.stat().st_size if controlled_command_verify.exists() else 0,
        "说明": f"通过={controlled_command_data.get('通过')}；失败={controlled_command_data.get('失败')}",
    })
    quality_gate_verify = root / "04日志" / "单股证据核验191填写质量闸口" / "single-stock-evidence-191-quality-gate-verify-最新.json"
    quality_gate_data = load_json(quality_gate_verify, {}) or {}
    checks.append({
        "检查项": "198填写质量闸口验证",
        "路径": str(quality_gate_verify),
        "通过": quality_gate_verify.exists() and int(quality_gate_data.get("失败") or 0) == 0,
        "存在": quality_gate_verify.exists(),
        "大小": quality_gate_verify.stat().st_size if quality_gate_verify.exists() else 0,
        "说明": f"通过={quality_gate_data.get('通过')}；失败={quality_gate_data.get('失败')}",
    })

    failed = [item for item in checks if not item["通过"]]
    conclusion = "通过：股票系统C+++日常可用形态成立" if not failed else "未通过：存在需修复项"
    report = {
        "名称": "股票系统C+++日常可用总验收",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "验证股票系统C加加加日常可用总验收.py",
        "当前交付层级": total.get("当前交付层级") or "未知",
        "剩余硬阻断": total.get("剩余硬阻断") or "未知",
        "验收结论": conclusion,
        "检查数量": len(checks),
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改旧系统": False,
            "是否更新施工接续包": False,
        },
    }

    output_dir = root / "03数据" / "153C加加加总验收"
    output_json = output_dir / f"股票系统C加加加日常可用总验收_{stamp}.json"
    output_md = output_dir / f"股票系统C加加加日常可用总验收_{stamp}.md"
    latest_json = output_dir / "股票系统C加加加日常可用总验收_最新.json"
    latest_md = output_dir / "股票系统C加加加日常可用总验收_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(latest_md)

    print(json.dumps({
        "状态": "完成",
        "验收结论": conclusion,
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
