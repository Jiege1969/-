# -*- coding: utf-8 -*-
"""
名称：生成微信短文小样本对照包.py
作用：汇总旧正式短回复、v21影子短文和成交额源门禁，生成微信短文小样本对照包。
安全边界：只读本地草稿、影子预演和223成交额源报告；只写 03数据/224微信短文小样本对照包；不改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "224微信短文小样本对照包"
CURRENT_REPLY_MD = DATA / "24企业微信短回复" / "企业微信单股短回复_最新.md"
SHADOW_221_JSON = DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览_最新.json"
SHADOW_221_VERIFY = DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览验收_最新.json"
SHADOW_222_JSON = DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演_最新.json"
SHADOW_222_VERIFY = DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演验收_最新.json"
TURNOVER_223_JSON = DATA / "223正式成交额源补齐预演" / "股票正式成交额源补齐预演_最新.json"
TURNOVER_223_VERIFY = DATA / "223正式成交额源补齐预演" / "股票正式成交额源补齐预演验收_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
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


def word_hits(text: str, words: list[str]) -> dict[str, bool]:
    return {word: word in text for word in words}


def harmful_hits(text: str) -> dict[str, bool]:
    words = ["买入", "卖出", "下单", "调仓", "目标价", "收益承诺", "自动交易"]
    raw = word_hits(text, words)
    if raw.get("自动交易") and ("不自动交易" in text or "不会自动交易" in text):
        raw["自动交易"] = False
    return raw


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 微信短文小样本对照包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 样本数量：{report['样本数量']}",
        "",
        "## 一、准入门禁",
        "",
    ]
    for key, value in report["准入门禁"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、样本对照", ""])
    for item in report["样本对照"]:
        lines.append(f"### {item['名称']}（{item['市场代码']}）")
        lines.append("")
        lines.append(f"- 旧草稿长度：{item['旧草稿长度']}")
        lines.append(f"- v21影子短文长度：{item['v21影子短文长度']}")
        lines.append(f"- 旧话术命中：{json.dumps(item['旧话术命中'], ensure_ascii=False)}")
        lines.append(f"- v21关键字段命中：{json.dumps(item['v21关键字段命中'], ensure_ascii=False)}")
        lines.append(f"- v21禁用交易词命中：{json.dumps(item['v21禁用交易词命中'], ensure_ascii=False)}")
        lines.append(f"- 对照结论：{item['对照结论']}")
        lines.append("")
    lines.extend(["## 三、v21影子短文", "", report["v21影子短文"], "", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    current_reply = load_text(CURRENT_REPLY_MD)
    shadow_221 = load_json(SHADOW_221_JSON)
    shadow_221_verify = load_json(SHADOW_221_VERIFY)
    shadow_222 = load_json(SHADOW_222_JSON)
    shadow_222_verify = load_json(SHADOW_222_VERIFY)
    turnover_223 = load_json(TURNOVER_223_JSON)
    turnover_223_verify = load_json(TURNOVER_223_VERIFY)
    sample = shadow_221.get("样本股票") or turnover_223.get("样本股票") or {"名称": "新易盛", "市场代码": "sz300502"}
    shadow_text = str(shadow_221.get("微信短文") or shadow_222.get("影子短文输出") or "").strip()
    old_words = ["操作策略", "稳住", "继续观察", "成交活跃度", "常规推荐", "图文详情"]
    required = ["观察条件", "转强条件", "失败条件", "风险", "详情", "声明"]
    turnover_status = turnover_223.get("正式成交额源状态", {})
    turnover_ready = turnover_status.get("是否解除估算降级") is True
    upstream_ok = (
        shadow_221_verify.get("结论") == "通过"
        and shadow_222_verify.get("结论") == "通过"
        and turnover_223_verify.get("结论") == "通过"
    )
    shadow_required_hits = word_hits(shadow_text, required)
    shadow_harmful_hits = harmful_hits(shadow_text)
    old_hits = word_hits(current_reply, old_words)
    candidate_safe = all(shadow_required_hits.values()) and not any(shadow_harmful_hits.values())
    formal_switch_allowed = upstream_ok and turnover_ready and candidate_safe

    sample_compare = {
        "名称": sample.get("名称", ""),
        "市场代码": sample.get("市场代码") or sample.get("代码") or "",
        "旧草稿长度": len(current_reply),
        "v21影子短文长度": len(shadow_text),
        "旧话术命中": old_hits,
        "v21关键字段命中": shadow_required_hits,
        "v21禁用交易词命中": shadow_harmful_hits,
        "成交额源状态": turnover_status,
        "对照结论": (
            "v21短文结构和安全词通过，可继续影子对照；但历史成交额未正式化，暂不允许替换正式发送模板。"
            if candidate_safe and not formal_switch_allowed
            else "v21短文与成交额源门禁均通过，可进入可控开关设计。"
        ),
    }
    report = {
        "名称": "微信短文小样本对照包",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本数量": 1,
        "当前结论": (
            "小样本对照包已生成；v21影子短文通过结构与安全检查，但历史成交额仍未正式化，正式替换开关继续阻断。"
            if not formal_switch_allowed
            else "小样本对照包已生成；上游与成交额源门禁通过，可进入正式开关影子验收。"
        ),
        "读取文件": {
            "当前正式短回复草稿": str(CURRENT_REPLY_MD),
            "221微信短文影子预览": str(SHADOW_221_JSON),
            "221验收": str(SHADOW_221_VERIFY),
            "222正式生成器影子分支": str(SHADOW_222_JSON),
            "222验收": str(SHADOW_222_VERIFY),
            "223正式成交额源预演": str(TURNOVER_223_JSON),
            "223验收": str(TURNOVER_223_VERIFY),
        },
        "准入门禁": {
            "221验收通过": shadow_221_verify.get("结论") == "通过",
            "222验收通过": shadow_222_verify.get("结论") == "通过",
            "223验收通过": turnover_223_verify.get("结论") == "通过",
            "v21短文结构通过": all(shadow_required_hits.values()),
            "v21禁用交易动作词通过": not any(shadow_harmful_hits.values()),
            "历史成交额可解除估算降级": turnover_ready,
            "允许设计正式可控开关": formal_switch_allowed,
        },
        "样本对照": [sample_compare],
        "旧正式短回复": current_reply,
        "v21影子短文": shadow_text,
        "差异摘要": [
            "旧草稿含“操作策略、稳住、继续观察、成交活跃度、常规推荐”等旧话术。",
            "v21影子短文改为观察条件、转强条件、失败条件、风险、详情、声明的 6+1 结构。",
            "v21仍保留当前历史成交额为估算口径、待正式成交额源回补的降级说明。",
        ],
        "安全边界": {
            "修改正式短回复生成器": False,
            "修改股票企业微信桥接入口": False,
            "修改股票助手入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "下一步计划": (
            "先设计低风险统一入口影子验收，只允许 dry_run 同步写出旧草稿与 v21 对照包；"
            "正式替换模板和真实发送继续等待历史成交额正式回补。"
        ),
    }

    latest_json = OUT_DIR / "微信短文小样本对照包_最新.json"
    latest_md = OUT_DIR / "微信短文小样本对照包_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "样本数量": report["样本数量"],
        "允许设计正式可控开关": formal_switch_allowed,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
