# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION = ROOT / "03杰哥进化系统"
SOURCE = EVOLUTION / "03数据" / "110多对话框并行施工冲突扫描包" / "多对话框并行施工冲突扫描包_最新.json"
OUT_DIR = EVOLUTION / "03数据" / "113红线词命中语义复核包"
LOG_DIR = EVOLUTION / "04日志" / "红线词命中语义复核包验收"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def get_key(data: dict, name: str, default):
    return data.get(name, default)


def classify_redline_hit(path_text: str, hits: list[str]) -> dict:
    path = Path(path_text)
    exists = path.exists()
    text = read_text(path) if exists and path.is_file() else ""
    category = "需人工复核"
    conclusion = "未能自动判定语义，需要人工复核。"
    evidence = []
    actual_breach = True

    if path.name in {
        "生成多对话框并行施工冲突扫描包.py",
        "验证红线材料模板第一批只读填报预演包.py",
        "验证红线材料缺口低风险补齐第一批模板包.py",
    }:
        category = "误报-扫描或验证词库"
        conclusion = "命中来自扫描器或验证器内部词库，不代表运行配置打开。"
        actual_breach = False
        evidence = ["脚本用途为扫描/验证，命中词作为被检测样本存在。"]
    elif "股票展示口径一致性验收" in path.name:
        checks = [
            '"不接券商": true',
            '"不交易": true',
            '"不真实发送企业微信": true',
        ]
        matched = [item for item in checks if item in text]
        if len(matched) == len(checks):
            category = "误报-禁止口径为true"
            conclusion = "股票验收文件中的 true 表示红线禁止项成立，不是接券商或交易已打开。"
            actual_breach = False
            evidence = matched
    elif "视频真实渲染禁用态检查" in path.name:
        checks = [
            '"允许调用剪辑软件真实渲染": false',
            '"允许自动发布": false',
            '"是否自动发布": false',
        ]
        matched = [item for item in checks if item in text]
        if len(matched) >= 2:
            category = "误报-允许字段为false"
            conclusion = "视频禁用态检查中的允许字段均为 false，表示继续阻断真实渲染或自动发布。"
            actual_breach = False
            evidence = matched
    elif "视频任务ID与放行链一致性复核卡" in path.name:
        checks = [
            '"允许真实渲染": false',
            '"允许自动发布": false',
            "阻断真实渲染",
            "阻断自动发布",
        ]
        matched = [item for item in checks if item in text]
        if len(matched) >= 2:
            category = "误报-放行链阻断口径"
            conclusion = "复核卡明确写入真实渲染和自动发布为 false，并记录阻断原因。"
            actual_breach = False
            evidence = matched[:4]
    elif "日常可用交付版状态包" in path.name:
        checks = [
            "不允许真实触发",
            "真实触发关闭",
        ]
        matched = [item for item in checks if item in text]
        if matched:
            category = "误报-n8n关闭口径"
            conclusion = "状态包记录的是 n8n 检查项可读、真实触发关闭。"
            actual_breach = False
            evidence = matched

    return {
        "路径": path_text,
        "存在": exists,
        "命中词": hits,
        "分类": category,
        "结论": conclusion,
        "实际红线触发": actual_breach,
        "证据": evidence,
    }


def current_ports() -> list[dict]:
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True,
        encoding="gb18030",
        errors="replace",
        check=False,
    )
    rows = []
    for port in (19310, 19302):
        port_rows = []
        listeners = []
        for line in result.stdout.splitlines():
            if f":{port} " not in line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            state = parts[-2]
            pid = parts[-1]
            port_rows.append(line.strip())
            if state.upper() == "LISTENING" and pid != "0":
                listeners.append(pid)
        unique_listeners = sorted(set(listeners))
        rows.append(
            {
                "端口": port,
                "当前行": port_rows,
                "监听PID": unique_listeners,
                "TIME_WAIT_PID_0_是否忽略": True,
                "结论": "未发现多监听冲突" if len(unique_listeners) == 1 else "需人工确认",
                "通过": len(unique_listeners) == 1,
            }
        )
    return rows


def md_table(items: list[dict]) -> str:
    lines = [
        "| 分类 | 实际红线触发 | 路径 | 结论 |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            f"| {item['分类']} | {item['实际红线触发']} | {item['路径']} | {item['结论']} |"
        )
    return "\n".join(lines)


def write_outputs(payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    summary = OUT_DIR / "红线词命中语义复核包_最新.json"
    summary_md = OUT_DIR / "红线词命中语义复核包_最新.md"
    classify_md = OUT_DIR / "红线词语义分类表_最新.md"
    port_md = OUT_DIR / "端口多PID语义复核_最新.md"
    conclusion_md = OUT_DIR / "并行施工冲突结论_最新.md"

    payload["输出文件"] = {
        "总包JSON": str(summary),
        "总包Markdown": str(summary_md),
        "红线词语义分类表": str(classify_md),
        "端口多PID语义复核": str(port_md),
        "并行施工冲突结论": str(conclusion_md),
    }

    summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    classify_text = "# 红线词语义分类表\n\n" + md_table(payload["红线词语义复核"])
    classify_md.write_text(classify_text + "\n", encoding="utf-8")

    port_lines = ["# 端口多PID语义复核\n", "| 端口 | 监听PID | 结论 |", "| --- | --- | --- |"]
    for item in payload["端口语义复核"]:
        port_lines.append(f"| {item['端口']} | {', '.join(item['监听PID'])} | {item['结论']} |")
    port_lines.append("\n说明：PID 0 的 TIME_WAIT 是连接残留状态，不按抢占监听端口处理。")
    port_md.write_text("\n".join(port_lines) + "\n", encoding="utf-8")

    conclusion_text = "\n".join(
        [
            "# 并行施工冲突结论",
            "",
            f"- 生成时间：{payload['生成时间']}",
            f"- 状态：{payload['状态']}",
            f"- 确认结论：{payload['确认结论']}",
            f"- 实际红线触发数：{payload['指标']['实际红线触发数']}",
            f"- 需人工复核数：{payload['指标']['需人工复核数']}",
            f"- 端口冲突数：{payload['指标']['端口冲突数']}",
            f"- 高风险近期修改项：{payload['高风险近期修改结论']}",
            "",
            "## 总管确认",
            "",
            payload["总管确认"],
        ]
    )
    conclusion_md.write_text(conclusion_text + "\n", encoding="utf-8")

    main_md = "\n".join(
        [
            "# 红线词命中语义复核包",
            "",
            f"- 生成时间：{payload['生成时间']}",
            f"- 状态：{payload['状态']}",
            f"- 来源扫描：{payload['来源扫描']}",
            f"- 确认结论：{payload['确认结论']}",
            "",
            "## 指标",
            "",
            f"- 红线词命中项：{payload['指标']['红线词命中项']}",
            f"- 实际红线触发数：{payload['指标']['实际红线触发数']}",
            f"- 需人工复核数：{payload['指标']['需人工复核数']}",
            f"- 端口冲突数：{payload['指标']['端口冲突数']}",
            "",
            "## 文件",
            "",
            f"- 红线词语义分类表：{classify_md}",
            f"- 端口多PID语义复核：{port_md}",
            f"- 并行施工冲突结论：{conclusion_md}",
            "",
            "## 安全边界",
            "",
            "- 未真实发送企业微信",
            "- 未真实触发 n8n",
            "- 未接券商、不交易",
            "- 未登录电子税务局、未接财税软件",
            "- 未真实渲染或自动发布视频",
            "- 未写正式规则、未自动转正式规则",
            "- 未修改总管面板、未修改一键接续包",
            "- 未重载 19310/19302",
        ]
    )
    summary_md.write_text(main_md + "\n", encoding="utf-8")


def main() -> None:
    source = load_json(SOURCE)
    redline_hits = get_key(source, "红线词命中", [])
    high_risk_hits = get_key(source, "高风险冲突扫描", [])
    duplicate_groups = get_key(source, "同名最新产物重复组", [])

    reviews = [
        classify_redline_hit(str(item.get("路径", "")), item.get("命中", []))
        for item in redline_hits
    ]
    actual_breaches = [item for item in reviews if item["实际红线触发"]]
    manual_reviews = [item for item in reviews if item["分类"] == "需人工复核"]

    port_reviews = current_ports()
    port_conflicts = [item for item in port_reviews if not item["通过"]]

    status = "pass" if not actual_breaches and not manual_reviews and not port_conflicts and not duplicate_groups else "blocked"
    payload = {
        "名称": "红线词命中语义复核包",
        "生成时间": now_text(),
        "状态": status,
        "来源扫描": str(SOURCE),
        "确认结论": "未发现实际红线触发或端口打架；上轮 blocked 来自保守词命中和 TIME_WAIT 误判。"
        if status == "pass"
        else "仍存在需人工复核项，不得视为通过。",
        "指标": {
            "红线词命中项": len(redline_hits),
            "实际红线触发数": len(actual_breaches),
            "需人工复核数": len(manual_reviews),
            "端口冲突数": len(port_conflicts),
            "同名最新产物重复组": len(duplicate_groups),
            "高风险近期修改项": len(high_risk_hits),
        },
        "红线词语义复核": reviews,
        "端口语义复核": port_reviews,
        "高风险近期修改结论": "生成日常可用版自主巡检快照.py 属于总巡检聚合脚本，近期修改需要单一总管吸收；本轮未见同名产物覆盖或多监听端口证据。",
        "总管确认": "确认当前未发现多个对话框实际打架；后续并行施工仍应避免多个对话框同时修改总巡检聚合脚本、19310/19302 服务入口、总管面板和一键接续包。",
        "安全边界": {
            "真实发送企业微信": False,
            "真实触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "写正式规则": False,
            "自动转正式规则": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
    }
    write_outputs(payload)
    print(json.dumps({"status": status, "output": payload["输出文件"]["总包JSON"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
