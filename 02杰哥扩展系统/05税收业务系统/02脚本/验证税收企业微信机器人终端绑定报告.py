# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
BINDING_JSON = OUT_DIR / "税收企业微信机器人终端绑定报告_最新.json"
BINDING_MD = OUT_DIR / "税收企业微信机器人终端绑定报告_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信机器人终端绑定报告验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信机器人终端绑定报告验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    binding = load_json(BINDING_JSON)
    safety = binding.get("安全边界", {})
    current = binding.get("当前收发状态", {})
    checks = [
        check("终端绑定JSON存在", BINDING_JSON.exists(), str(BINDING_JSON)),
        check("终端绑定Markdown存在", BINDING_MD.exists(), str(BINDING_MD)),
        check("机器人名称为杰哥工作秘书", binding.get("机器人名称") == "杰哥工作秘书", binding.get("机器人名称")),
        check("登记为输入输出终端", current.get("是否登记为输入终端") is True and current.get("是否登记为输出终端") is True, current),
        check("绑定状态为待集成", binding.get("绑定状态") == "configured_pending_integration", binding.get("绑定状态")),
        check("输入输出职责齐备", len(binding.get("输入职责", [])) >= 3 and len(binding.get("输出职责", [])) >= 4, {"输入": binding.get("输入职责", []), "输出": binding.get("输出职责", [])}),
        check("输入技术边界说明回调要求", "回调" in binding.get("输入技术边界", "") or "消息接收" in binding.get("输入技术边界", ""), binding.get("输入技术边界", "")),
        check("输出技术边界说明门禁", "发送门禁" in binding.get("输出技术边界", "") and "消息合规" in binding.get("输出技术边界", ""), binding.get("输出技术边界", "")),
        check("禁止职责包含正式税务意见和办税执行", any("正式税务意见" in item for item in binding.get("禁止职责", [])) and any("申报" in item or "退税" in item or "开票" in item for item in binding.get("禁止职责", [])), binding.get("禁止职责", [])),
        check("当前未真实收发", current.get("是否已接入真实输入回调") is False and current.get("是否已接入真实输出发送") is False and current.get("真实收发放行状态") == "not_released", current),
        check("未联网未读取凭据未发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False and safety.get("是否接收真实消息") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信机器人终端绑定报告验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信机器人终端绑定报告验收",
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
