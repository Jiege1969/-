# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PRECHECK_JSON = OUT_DIR / "税收企业微信凭据接入预检_最新.json"
PRECHECK_MD = OUT_DIR / "税收企业微信凭据接入预检_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信凭据接入预检验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信凭据接入预检验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    precheck = load_json(PRECHECK_JSON)
    md_text = PRECHECK_MD.read_text(encoding="utf-8", errors="ignore") if PRECHECK_MD.exists() else ""
    webhook = precheck.get("机器人Webhook预检", {})
    app_status = precheck.get("应用凭据预检", [])
    safety = precheck.get("安全边界", {})
    raw_secret_patterns = [
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+",
        r"corpsecret=[A-Za-z0-9_-]+",
        r"secret[=:][A-Za-z0-9_-]{12,}",
    ]
    leaked = [pattern for pattern in raw_secret_patterns if re.search(pattern, md_text, flags=re.IGNORECASE)]
    checks = [
        check("凭据预检JSON存在", PRECHECK_JSON.exists(), str(PRECHECK_JSON)),
        check("凭据预检Markdown存在", PRECHECK_MD.exists(), str(PRECHECK_MD)),
        check("机器人Webhook字段齐备", all(key in webhook for key in ["环境变量名", "是否存在", "字符长度", "是否已脱敏", "值预览", "格式是否疑似企业微信机器人Webhook"]), webhook),
        check("应用凭据字段齐备", all(all(key in item for key in ["环境变量名", "是否存在", "字符长度", "是否已脱敏", "值预览"]) for item in app_status), app_status),
        check("报告不泄露Webhook或Secret原文", not leaked, leaked),
        check("凭据值预览均脱敏", webhook.get("值预览") in {"[已设置-不显示]", "[未设置]"} and all(item.get("值预览") in {"[已设置-不显示]", "[未设置]"} for item in app_status), {"webhook": webhook, "app": app_status}),
        check("预检只作为凭据形态判断", precheck.get("凭据预检结论") in {"具备凭据形态", "未具备凭据形态"}, precheck.get("凭据预检结论")),
        check("不联网不发送", safety.get("是否联网") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("不保存或输出凭据原文", safety.get("是否保存凭据") is False and safety.get("是否输出凭据原文") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信凭据接入预检验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信凭据接入预检验收",
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
