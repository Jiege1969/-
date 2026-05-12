# -*- coding: utf-8 -*-
"""
名称：生成企业微信真实发送灰度准入与停止开关方案.py
作用：汇总当前 v21 短回复 dry-run、历史真实灰度闸口和公共受控发送器状态，生成企业微信真实发送前的灰度准入与停止开关方案。
安全边界：只读本地草稿、验收产物、入口源码和配置摘要；只写03数据/236准入方案；不调用发送器、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
SCRIPT_DIR = ROOT / "02脚本"
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
COMMON_SCRIPT_DIR = COMMON_ROOT / "02脚本"
COMMON_CONFIG_DIR = COMMON_ROOT / "01配置"
OUT_DIR = DATA / "236企业微信真实发送灰度准入与停止开关方案"

LATEST_SHORT_JSON = DATA / "24企业微信短回复" / "企业微信单股短回复_最新.json"
LATEST_SHORT_MD = DATA / "24企业微信短回复" / "企业微信单股短回复_最新.md"

VERIFY_FILES = {
    "234模板替换准入": DATA / "234企业微信短回复v21正式模板替换准入" / "企业微信短回复v21正式模板替换准入与回滚方案验收_最新.json",
    "235v21模板dry_run": DATA / "235企业微信短回复v21模板dry_run" / "企业微信单股短回复v21模板dry_run实跑输出验收_最新.json",
    "231shadow实跑": DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json",
    "233历史K线正式刷新": DATA / "233历史K线东方财富增强受控刷新" / "重点关注池历史K线东方财富增强受控刷新验收_最新.json",
    "230正式成交额对照": DATA / "230微信短文正式生成器正式成交额口径对照包" / "微信短文正式生成器正式成交额口径对照包验收_最新.json",
}

SEND_ENTRY_FILES = {
    "公共受控发送器": COMMON_SCRIPT_DIR / "企业微信受控发送器.py",
    "主动研究企微灰度发送": SCRIPT_DIR / "执行股票主动研究企微灰度发送.py",
    "股票企业微信桥接入口": SCRIPT_DIR / "股票企业微信桥接入口.py",
    "股票助手入口": SCRIPT_DIR / "股票助手入口.py",
    "停止桥接入口脚本": SCRIPT_DIR / "停止股票企业微信桥接入口.ps1",
    "n8n适配器禁用态": SCRIPT_DIR / "执行股票企业微信n8n适配器禁用态.py",
}

LEGACY_GATE_FILES = {
    "真实灰度最终闸口包": DATA / "36真实灰度最终闸口" / "股票企业微信真实灰度最终闸口包_最新.json",
    "真实灰度人工确认单包": DATA / "42企业微信真实灰度人工确认单" / "股票企业微信真实灰度人工确认单包_最新.json",
    "真实灰度回滚预案包": DATA / "41企业微信真实灰度回滚预案" / "股票企业微信真实灰度回滚预案包_最新.json",
    "真实发送凭据隔离审计包": DATA / "45企业微信真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json",
}

SENDER_CONFIG = COMMON_CONFIG_DIR / "企业微信受控发送配置.json"
APP_PROFILE_CONFIG = COMMON_CONFIG_DIR / "企业微信应用目标档案.json"
COUNTER_DIR = COMMON_ROOT / "03数据" / "04企业微信灰度发送计数"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "sha256": sha256(path),
    }


def verify_summary() -> list[dict[str, Any]]:
    rows = []
    for name, path in VERIFY_FILES.items():
        data = load_json(path, {})
        rows.append({
            "名称": name,
            "路径": str(path),
            "存在": path.exists(),
            "结论": data.get("结论", data.get("状态", "")),
            "通过数量": int(data.get("通过数量", data.get("通过", 0)) or 0),
            "失败数量": int(data.get("失败数量", data.get("失败", 1)) or 1) if data.get("结论", data.get("状态", "")) not in {"通过", "完成"} else int(data.get("失败数量", data.get("失败", 0)) or 0),
        })
    return rows


def today_counter() -> dict[str, Any]:
    path = COUNTER_DIR / f"企业微信灰度发送计数_{datetime.now().strftime('%Y%m%d')}.json"
    data = load_json(path, {"已真实发送": 0, "记录": []})
    return {
        "路径": str(path),
        "存在": path.exists(),
        "已真实发送": int(data.get("已真实发送", 0) or 0),
        "记录数量": len(data.get("记录", [])) if isinstance(data.get("记录", []), list) else 0,
    }


def source_contains(path: Path, *needles: str) -> bool:
    text = read_text(path)
    return all(needle in text for needle in needles)


def build_gate_plan(sender_config: dict[str, Any], app_profile: dict[str, Any]) -> dict[str, Any]:
    send_cfg = sender_config.get("真实发送", {}) if isinstance(sender_config, dict) else {}
    whitelist = sender_config.get("白名单", {}).get("接收人ID列表", []) if isinstance(sender_config, dict) else []
    return {
        "灰度范围": {
            "接收人": "仅本人白名单",
            "白名单": whitelist,
            "最大消息数": send_cfg.get("首轮灰度最大消息数", 5),
            "禁止群发": send_cfg.get("允许群发") is False,
            "禁止外部客户": send_cfg.get("允许外部客户") is False,
        },
        "目标应用": {
            "当前启用应用": app_profile.get("当前启用应用", ""),
            "档案状态": app_profile.get("应用档案", {}).get(app_profile.get("当前启用应用", ""), {}).get("状态", ""),
            "只记录变量名不记录密钥": True,
        },
        "人工确认闸口": [
            "必须人工确认本轮只发送 1 条 v21 短回复草稿。",
            "必须人工确认发送对象仍为本人白名单，不允许群发、外部客户或多接收人。",
            "必须人工确认 n8n 继续禁用，不把真实发送等同于 n8n 接入。",
            "必须人工确认发送后立即检查 04日志/企业微信受控发送器 最新日志和当天计数。",
        ],
        "停止开关": [
            "一级停止：不传 --real-send，公共受控发送器保持 dry-run。",
            "二级停止：停止或不启动 127.0.0.1:19302 股票企业微信桥接入口。",
            "三级停止：执行股票企业微信 n8n 适配器禁用态脚本，继续禁止 n8n 路由。",
            "四级停止：如出现误发风险，将企业微信受控发送配置中的真实发送启用位改为 false，并保留改动前后快照。",
            "五级停止：如发送已发生，立即记录发送日志、response_url 指纹、接收人和时间，不做追加发送。",
        ],
        "回滚步骤": [
            "恢复 `03数据/24企业微信短回复` 中保留的旧统一短回复或重新运行默认旧模板生成链路。",
            "关闭 `--use-v21-template-dry-run` 和 `--shadow-v21-dry-run` 显式参数，回到默认旧模板行为。",
            "如桥接入口已启动，执行停止桥接入口脚本并确认 19302 不再监听。",
            "保留本次 236 准入包、发送前草稿、发送器日志和当天计数，作为审计证据。",
        ],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信真实发送灰度准入与停止开关方案",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、上游验收",
        "",
    ]
    for item in report["上游验收"]:
        lines.append(f"- {item['名称']}：{item['结论']}（{item['通过数量']}/{item['通过数量'] + item['失败数量']}）")
    lines.extend(["", "## 二、发送前硬闸口", ""])
    for item in report["发送前硬闸口"]:
        lines.append(f"- {item['名称']}：{'通过' if item['通过'] else '阻断'}。{item['说明']}")
    lines.extend(["", "## 三、人工确认闸口", ""])
    for item in report["灰度方案"]["人工确认闸口"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、停止开关", ""])
    for item in report["灰度方案"]["停止开关"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    short_json = load_json(LATEST_SHORT_JSON, {})
    short_text = str(short_json.get("短回复", ""))
    actions = short_json.get("实际动作", {})
    sender_config = load_json(SENDER_CONFIG, {})
    app_profile = load_json(APP_PROFILE_CONFIG, {})
    upstream = verify_summary()
    upstream_ok = all(item["存在"] and item["结论"] == "通过" and item["失败数量"] == 0 for item in upstream)
    counter = today_counter()

    hard_gates = [
        {
            "名称": "235 v21 dry-run 验收通过",
            "通过": any(item["名称"] == "235v21模板dry_run" and item["结论"] == "通过" and item["失败数量"] == 0 for item in upstream),
            "说明": "必须先证明24草稿可被显式写为 v21 正式成交额口径 dry-run。",
        },
        {
            "名称": "24草稿仍为v21_template_dry_run",
            "通过": short_json.get("模板模式") == "v21_template_dry_run" and LATEST_SHORT_MD.exists(),
            "说明": str(short_json.get("模板模式", "")),
        },
        {
            "名称": "24草稿使用正式成交额阈值",
            "通过": "250.85亿元" in short_text and "301.02亿元" in short_text and "估算口径" not in short_text,
            "说明": "要求 250.85亿元 / 301.02亿元，且不含估算降级。",
        },
        {
            "名称": "24草稿实际动作全关闭",
            "通过": bool(actions) and all(value is False for value in actions.values()),
            "说明": json.dumps(actions, ensure_ascii=False),
        },
        {
            "名称": "公共受控发送器默认不真实发送",
            "通过": source_contains(SEND_ENTRY_FILES["公共受控发送器"], "--real-send", "dry-run", "是否允许进入真实发送"),
            "说明": "源码要求显式 --real-send，且有 allowed 检查。",
        },
        {
            "名称": "主动研究灰度发送入口仍需显式--real-send",
            "通过": source_contains(SEND_ENTRY_FILES["主动研究企微灰度发送"], "--real-send", "公共受控发送器"),
            "说明": "真实发送不经默认路径触发。",
        },
        {
            "名称": "发送白名单仍为单人且禁止群发",
            "通过": len(sender_config.get("白名单", {}).get("接收人ID列表", [])) == 1 and sender_config.get("真实发送", {}).get("允许群发") is False,
            "说明": json.dumps(sender_config.get("白名单", {}), ensure_ascii=False),
        },
        {
            "名称": "n8n不在本步骤启用",
            "通过": SEND_ENTRY_FILES["n8n适配器禁用态"].exists(),
            "说明": "本方案只记录禁用态和停止开关，不导入、不激活 n8n。",
        },
        {
            "名称": "当天真实发送计数可审计",
            "通过": counter["存在"],
            "说明": json.dumps(counter, ensure_ascii=False),
        },
    ]

    hard_ok = all(item["通过"] for item in hard_gates)
    report = {
        "名称": "企业微信真实发送灰度准入与停止开关方案",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": (
            "准入材料齐全，但本包只允许进入人工确认前审阅；未取得人工确认前，真实发送、n8n启用、服务重启继续阻断。"
            if upstream_ok and hard_ok
            else "存在未通过闸口；不允许进入真实发送。"
        ),
        "允许真实发送": False,
        "允许n8n启用": False,
        "允许服务重启": False,
        "上游验收": upstream,
        "发送前硬闸口": hard_gates,
        "最新24草稿": {
            "json": str(LATEST_SHORT_JSON),
            "md": str(LATEST_SHORT_MD),
            "模板模式": short_json.get("模板模式", ""),
            "股票": short_json.get("股票", ""),
            "短回复长度": len(short_text),
            "实际动作": actions,
        },
        "发送入口快照": {name: snapshot(path) for name, path in SEND_ENTRY_FILES.items()},
        "旧灰度资产复用": {name: snapshot(path) for name, path in LEGACY_GATE_FILES.items()},
        "发送配置摘要": {
            "配置文件": str(SENDER_CONFIG),
            "真实发送启用位当前值": sender_config.get("真实发送", {}).get("是否启用"),
            "首轮灰度最大消息数": sender_config.get("真实发送", {}).get("首轮灰度最大消息数"),
            "允许群发": sender_config.get("真实发送", {}).get("允许群发"),
            "白名单": sender_config.get("白名单", {}).get("接收人ID列表", []),
            "凭据存在性": sender_config.get("凭据存在性", {}),
        },
        "当天发送计数": counter,
        "灰度方案": build_gate_plan(sender_config, app_profile),
        "实际动作": {
            "调用公共受控发送器": False,
            "调用企业微信token接口": False,
            "尝试发送企业微信": False,
            "发送企业微信成功": False,
            "触发n8n": False,
            "导入或启用n8n": False,
            "重启19300": False,
            "重启19302": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信真实发送灰度准入与停止开关方案_最新.json"
    latest_md = OUT_DIR / "企业微信真实发送灰度准入与停止开关方案_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "允许真实发送": False,
        "硬闸口通过": hard_ok,
        "上游通过": upstream_ok,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
