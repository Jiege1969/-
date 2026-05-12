# -*- coding: utf-8 -*-
"""
验证股票双前台终端分工与投影规则。

只做本地配置核验和只读回环；不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件" / "企业微信接入设置"
FRONT_CONFIG = ROOT / "01配置" / "股票双前台入口配置.json"
FRONT_STANDARD = ROOT / "01配置" / "股票前台输出标准_v2.json"
LAYER_RULE = ROOT / "01配置" / "股票前后台表达分层与杰哥推荐前台规则_v1.0.json"
REPORT_TEMPLATE = ROOT / "01配置" / "股票报告模板.json"
WECOM_TERMINALS = COMMON_ROOT / "01配置" / "企业微信机器人终端分工总表.json"
OUT_DIR = ROOT / "03数据" / "283股票双前台终端分工"

SHORTLINE_NAME = "杰哥股票短线分析助手"
EXPERT_NAME = "杰哥股票分析专家"
FORBIDDEN_TERMS = [
    "方法组合切换",
    "主导指标适配分",
    "复盘验证机制",
    "环境识别层",
    "失败样本校准过程",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "详情": detail}


def post_json(url: str, payload: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def stream_content(result: dict[str, Any]) -> str:
    reply = result.get("智能机器人回复", {})
    if isinstance(reply, dict):
        stream = reply.get("stream", {})
        if isinstance(stream, dict):
            return str(stream.get("content") or "")
    return str(result.get("企业微信内容") or result.get("回复") or "")


def main() -> int:
    front_config = load_json(FRONT_CONFIG)
    front_standard = load_json(FRONT_STANDARD)
    layer_rule = load_json(LAYER_RULE)
    wecom_terminals = load_json(WECOM_TERMINALS)

    checks: list[dict[str, Any]] = []

    dual = front_config.get("双前台终端", {})
    shortline = dual.get("短线助手", {}) if isinstance(dual, dict) else {}
    expert = dual.get("股票专家", {}) if isinstance(dual, dict) else {}
    current_terminal = front_config.get("企业微信终端", {})

    terminal_names = [str(item.get("名称") or "") for item in wecom_terminals.get("终端列表", [])]
    checks.append(check("股票双前台入口配置存在", FRONT_CONFIG.exists(), str(FRONT_CONFIG)))
    checks.append(check("短线助手已登记", shortline.get("名称") == SHORTLINE_NAME, shortline.get("名称")))
    checks.append(check("股票专家已登记", expert.get("名称") == EXPERT_NAME, expert.get("名称")))
    checks.append(check("默认股票前台终端为短线助手", current_terminal.get("名称") == SHORTLINE_NAME, current_terminal.get("名称")))
    checks.append(
        check(
            "短线助手关注周期完整",
            shortline.get("关注周期") == ["1-3个交易日", "3-5个交易日", "5-10个交易日"],
            shortline.get("关注周期"),
        )
    )
    checks.append(
        check(
            "股票专家关注周期完整",
            expert.get("关注周期") == ["10-20个交易日", "20-60个交易日", "60个交易日以上"],
            expert.get("关注周期"),
        )
    )
    checks.append(
        check(
            "企业微信终端总表已纳入双前台名称",
            SHORTLINE_NAME in terminal_names and EXPERT_NAME in terminal_names,
            terminal_names,
        )
    )

    front_text = FRONT_STANDARD.read_text(encoding="utf-8")
    report_template = load_json(REPORT_TEMPLATE)
    checks.append(check("前台输出标准已登记双前台分工", "双前台终端分工" in front_text, str(FRONT_STANDARD)))
    checks.append(
        check(
            "前台输出标准已融入用户股票分析模板",
            "用户股票分析模板融入规则" in front_text
            and all(keyword in front_text for keyword in ["先说结论", "重新关注时机", "关键价位对照表", "强烈关注"]),
            str(FRONT_STANDARD),
        )
    )
    checks.append(
        check(
            "前后台分层规则已覆盖双前台",
            SHORTLINE_NAME in json.dumps(layer_rule, ensure_ascii=False) and EXPERT_NAME in json.dumps(layer_rule, ensure_ascii=False),
            str(LAYER_RULE),
        )
    )
    checks.append(
        check(
            "前后台分层规则已禁止后台术语前台化",
            all(term in json.dumps(layer_rule, ensure_ascii=False) for term in FORBIDDEN_TERMS),
            FORBIDDEN_TERMS,
        )
    )
    checks.append(
        check(
            "报告模板已登记v3用户模板融入",
            "v3用户模板融入" in report_template
            and all(key in json.dumps(report_template["v3用户模板融入"], ensure_ascii=False) for key in ["短线助手单股问答", "短线主动推送", "专家中期推送"]),
            str(REPORT_TEMPLATE),
        )
    )

    try:
        shortline_result = post_json(
            "http://127.0.0.1:19302/wecom-bot/message",
            {"text": "分析 中际旭创", "stream": {"id": "stock-shortline-terminal-check"}},
        )
        shortline_text = stream_content(shortline_result)
        checks.append(
            check(
                "短线入口回环可读",
                all(term in shortline_text for term in ["分析对象", "结论", "观察条件", "风险线", "说明"]),
                shortline_text[:600],
            )
        )
        checks.append(
            check(
                "短线入口未暴露后台术语",
                not any(term in shortline_text for term in FORBIDDEN_TERMS),
                shortline_text[:600],
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(check("短线入口回环可读", False, str(exc)))
        checks.append(check("短线入口未暴露后台术语", False, str(exc)))

    try:
        expert_result = post_json(
            "http://127.0.0.1:19302/wecom-bot/message",
            {"text": "这周哪些行业最值得盯", "stream": {"id": "stock-expert-terminal-check"}},
        )
        expert_text = stream_content(expert_result)
        checks.append(
            check(
                "专家入口回环可读",
                bool(expert_text.strip()),
                expert_text[:600],
            )
        )
        checks.append(
            check(
                "专家入口未暴露后台术语",
                not any(term in expert_text for term in FORBIDDEN_TERMS),
                expert_text[:600],
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(check("专家入口回环可读", False, str(exc)))
        checks.append(check("专家入口未暴露后台术语", False, str(exc)))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "股票双前台终端分工验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not failed,
        "通过数量": len(checks) - len(failed),
        "总数量": len(checks),
        "检查项": checks,
        "当前结论": "股票双前台终端分工与前台投影规则已对齐。" if not failed else "股票双前台终端分工仍有未通过项。",
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    write_json(OUT_DIR / "股票双前台终端分工验收_最新.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
