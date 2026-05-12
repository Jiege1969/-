# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = OUT_DIR / "税收企业微信正式入口消息预演_最新.json"
PREVIEW_MD = OUT_DIR / "税收企业微信正式入口消息预演_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信正式入口消息预演验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信正式入口消息预演验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains_any(text: str, words: list[str]) -> list[str]:
    return [word for word in words if word in text]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    config = load_json(CONFIG)
    preview = load_json(PREVIEW_JSON)
    message = preview.get("消息预演", {}).get("企业微信拟发送消息", "")
    safety = preview.get("安全边界", {})
    checks: list[dict[str, Any]] = []

    checks.append(check("入口配置存在", CONFIG.exists(), str(CONFIG)))
    checks.append(check("消息预演JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("消息预演Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("入口默认dry_run_only", config.get("入口状态") == "dry_run_only", config.get("入口状态")))
    checks.append(check("真实发送未放行", config.get("真实发送放行") is False, config.get("真实发送放行")))
    checks.append(check("消息预演未真实发送", preview.get("消息预演", {}).get("是否真实发送") is False, preview.get("消息预演", {})))
    checks.append(check("发送模式为dry_run", preview.get("消息预演", {}).get("发送模式") == "dry_run", preview.get("消息预演", {}).get("发送模式")))

    required_parts = [
        "【税收分析助手-待复核草案摘要】",
        "事项：",
        "状态：",
        "置信度：",
        "政策依据候选：",
        "依据层级明细：",
        "待复核资料清单：",
        "资料缺口：",
        "风险点：",
        "人工复核：",
        "边界：待复核草案摘要预演",
    ]
    checks.append(check("消息包含企业微信必填段落", all(part in message for part in required_parts), required_parts))
    checks.append(check("消息长度不超过配置上限", len(message) <= int(config.get("消息格式", {}).get("最大字符数", 1800)), len(message)))
    checks.append(check("入口适配不再使用研发费用旧影子样例作为主来源", preview.get("旧链路是否仍作为主来源") is False, preview.get("分析草案来源")))

    prohibited = [
        "可以享受研发费用加计扣除",
        "不能享受研发费用加计扣除",
        "可以享受",
        "不能享受",
        "可扣除金额",
        "税额影响",
        "退税金额",
        "请立即申报",
        "请办理退税",
        "请开票",
        "正式税务意见",
        "正式税务结论",
        "结论确认",
    ]
    found_prohibited = contains_any(message, prohibited)
    checks.append(check("消息不含确定性税务结论或执行指令", not found_prohibited, found_prohibited))

    secret_patterns = {
        "企业微信Webhook": r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+",
        "手机号": r"\b1[3-9]\d{9}\b",
        "身份证号": r"\b\d{17}[\dXx]\b",
        "长账号或纳税人编号": r"\b[0-9A-Z]{15,20}\b",
    }
    secret_hits = {name: bool(re.search(pattern, message)) for name, pattern in secret_patterns.items()}
    checks.append(check("消息不含凭据或未脱敏敏感身份信息", not any(secret_hits.values()), secret_hits))

    required_false = [
        "是否联网",
        "是否下载",
        "是否接电子税务局",
        "是否接财税软件",
        "是否触发n8n",
        "是否写向量库",
        "是否企业微信真实发送",
        "是否生成正式税务结论",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))
    checks.append(check("真实发送阻断原因已记录", len(preview.get("消息预演", {}).get("真实发送阻断原因", [])) >= 2, preview.get("消息预演", {}).get("真实发送阻断原因", [])))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信正式入口消息预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信正式入口消息预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
