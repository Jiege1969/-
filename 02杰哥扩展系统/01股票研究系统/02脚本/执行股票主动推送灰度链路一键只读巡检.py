# -*- coding: utf-8 -*-
"""
名称：执行股票主动推送灰度链路一键只读巡检.py
作用：一键只读巡检股票主动推送灰度链路247-256是否齐全，并确认真实发送、n8n、券商、交易仍关闭。
触发方式：python 执行股票主动推送灰度链路一键只读巡检.py
依赖：Python标准库；247-256主动推送灰度准备链路。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地链路并写入257巡检包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送灰度链路一键只读巡检。
标识：stock-active-push-gray-chain-one-click-readonly-patrol-run
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送灰度链路一键只读巡检",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        f"- 总体状态：{report['总体状态']}",
        f"- 通过：{report['通过']}",
        f"- 失败：{report['失败']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 巡检结果",
        "",
    ]
    for item in report["巡检结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 当前阻断项", ""])
    for item in report["当前阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data = root / "03数据"
    paths = {
        "247": data / "247主动推送灰度启用准备包" / "股票主动推送灰度启用准备包_最新.json",
        "248": data / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json",
        "249": data / "249主动推送dry-run消息样本包" / "股票主动推送dry-run消息样本包_最新.json",
        "250": data / "250主动推送真实灰度人工确认回执模板包" / "股票主动推送真实灰度人工确认回执模板包_最新.json",
        "251": data / "251主动推送交易化表达与重复发送拦截预演包" / "股票主动推送交易化表达与重复发送拦截预演包_最新.json",
        "252": data / "252主动推送真实灰度发送前最终只读总闸口" / "股票主动推送真实灰度发送前最终只读总闸口_最新.json",
        "253": data / "253主动推送灰度发送日志台账与回滚演练包" / "股票主动推送灰度发送日志台账与回滚演练包_最新.json",
        "254": data / "254主动推送人工确认回执填写校验与闸口复跑包" / "股票主动推送人工确认回执填写校验与闸口复跑包_最新.json",
        "255": data / "255主动推送单条灰度人工触发执行预案与停止开关包" / "股票主动推送单条灰度人工触发执行预案与停止开关包_最新.json",
        "256": data / "256主动推送灰度链路总索引与操作卡" / "股票主动推送灰度链路总索引与操作卡_最新.json",
    }
    docs = {key: load_json(path) for key, path in paths.items()}

    checks = [
        check("247到256文件齐全", all(path.exists() for path in paths.values()), {key: str(path) for key, path in paths.items() if not path.exists()}),
        check("247允许推进准备但不允许真实推送", docs["247"].get("可以推进准备工作") is True and docs["247"].get("可以立即真实推送") is False, docs["247"].get("当前结论")),
        check("248真实发送与n8n均未放行", docs["248"].get("是否允许真实发送") is False and docs["248"].get("是否允许n8n自动推送") is False, {"真实发送": docs["248"].get("是否允许真实发送"), "n8n": docs["248"].get("是否允许n8n自动推送")}),
        check("249保持dry-run", docs["249"].get("dry_run") is True and docs["249"].get("真实发送") is False and docs["249"].get("n8n") is False, {"dry_run": docs["249"].get("dry_run"), "真实发送": docs["249"].get("真实发送")}),
        check("250人工确认模板未生效", docs["250"].get("模板状态") == "待人工确认，未生效" and docs["250"].get("是否允许真实发送") is False, docs["250"].get("模板状态")),
        check("251扫描拦截通过", docs["251"].get("总体状态") == "pass" and int(docs["251"].get("交易化表达命中数", -1)) == 0, docs["251"].get("交易化表达命中数")),
        check("252最终总闸口保持blocked", docs["252"].get("总体状态") == "blocked" and docs["252"].get("是否允许真实发送") is False, docs["252"].get("阻断项", [])),
        check("253回滚演练通过且不发送", docs["253"].get("演练通过") is True and docs["253"].get("是否真实发送") is False, {"演练": docs["253"].get("演练通过"), "真实发送": docs["253"].get("是否真实发送")}),
        check("254回执校验保持blocked", docs["254"].get("总体状态") == "blocked" and docs["254"].get("是否允许真实发送") is False, docs["254"].get("阻断项", [])),
        check("255单条触发预案拒绝执行", docs["255"].get("预案是否允许执行") is False and docs["255"].get("是否真实发送") is False, docs["255"].get("当前阻断项", [])),
        check("256总索引完整", docs["256"].get("链路完整度") == "9/9" and docs["256"].get("链路判定") == "pass", docs["256"].get("链路完整度")),
    ]

    dangerous = []
    for key, doc in docs.items():
        actions = doc.get("实际动作", {}) or doc.get("actual_actions", {})
        for danger_key in ["调用企业微信API", "真实发送企业微信", "启用n8n", "触发n8n", "重载19310", "重载19302", "调用券商接口", "自动交易", "写正式规则库", "修改总管面板", "修改一键接续包"]:
            if actions.get(danger_key) is not False and danger_key in actions:
                dangerous.append({"包": key, "危险动作": danger_key, "值": actions.get(danger_key)})
    checks.append(check("危险动作全部关闭", not dangerous, dangerous))

    failed = [item for item in checks if not item["通过"]]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "当前结论": "股票主动推送灰度链路巡检通过；链路完整，真实发送仍保持blocked。",
        "巡检结果": checks,
        "当前阻断项": docs["256"].get("当前阻断项", []),
        "实际动作": {
            "读取247到256本地包": True,
            "写本地257巡检包": True,
            "调用企业微信API": False,
            "真实发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "重载19310": False,
            "重载19302": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式规则库": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }
    out_dir = data / "257主动推送灰度链路一键只读巡检包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送灰度链路一键只读巡检_{stamp}.json"
    latest_json = out_dir / "股票主动推送灰度链路一键只读巡检_最新.json"
    output_md = out_dir / f"股票主动推送灰度链路一键只读巡检_{stamp}.md"
    latest_md = out_dir / "股票主动推送灰度链路一键只读巡检_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["通过"], "失败": report["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
