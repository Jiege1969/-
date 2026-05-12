# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
GATE_JSON = OUT_DIR / "税收企业微信正式入口发送门禁_最新.json"
GATE_MD = OUT_DIR / "税收企业微信正式入口发送门禁_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信正式入口发送门禁验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信正式入口发送门禁验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gate_report = load_json(GATE_JSON)
    gates = gate_report.get("门禁结果", [])
    gate_map = {item.get("门禁"): item for item in gates}
    safety = gate_report.get("安全边界", {})
    checks = [
        check("发送门禁JSON存在", GATE_JSON.exists(), str(GATE_JSON)),
        check("发送门禁Markdown存在", GATE_MD.exists(), str(GATE_MD)),
        check("当前真实发送已阻断", gate_report.get("结论") == "已阻断" and gate_report.get("是否真实发送") is False, {"结论": gate_report.get("结论"), "是否真实发送": gate_report.get("是否真实发送")}),
        check("机器人终端门禁已通过", gate_map.get("机器人终端", {}).get("状态") == "通过", gate_map.get("机器人终端")),
        check("入口状态门禁未通过", gate_map.get("入口状态", {}).get("状态") == "未通过", gate_map.get("入口状态")),
        check("真实发送放行门禁未通过", gate_map.get("真实发送放行", {}).get("状态") == "未通过", gate_map.get("真实发送放行")),
        check("上线变更单门禁未通过", gate_map.get("上线变更单", {}).get("状态") == "未通过", gate_map.get("上线变更单")),
        check("人工放行门禁未通过", gate_map.get("人工放行", {}).get("状态") == "未通过", gate_map.get("人工放行")),
        check("接收范围门禁未通过", gate_map.get("接收范围", {}).get("状态") == "未通过", gate_map.get("接收范围")),
        check("应急停用与回滚门禁未通过", gate_map.get("应急停用与回滚", {}).get("状态") == "未通过", gate_map.get("应急停用与回滚")),
        check("企业微信凭据门禁未通过", gate_map.get("企业微信凭据", {}).get("状态") == "未通过", gate_map.get("企业微信凭据")),
        check("凭据预检门禁未通过", gate_map.get("凭据预检", {}).get("状态") == "未通过", gate_map.get("凭据预检")),
        check("消息预演验收已通过", gate_map.get("消息预演验收", {}).get("状态") == "通过", gate_map.get("消息预演验收")),
        check("消息合规审查已通过", gate_map.get("消息合规审查", {}).get("状态") == "通过", gate_map.get("消息合规审查")),
        check("发送审计台账存在", (OUT_DIR / "税收企业微信正式入口发送审计台账_最新.json").exists(), str(OUT_DIR / "税收企业微信正式入口发送审计台账_最新.json")),
        check("未生成正式税务结论", safety.get("是否生成正式税务结论") is False, safety),
        check("未触发n8n或写向量库", safety.get("是否触发n8n") is False and safety.get("是否写向量库") is False, safety),
        check("未接电子税务局或财税软件", safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
        check("企业微信真实发送保持关闭", safety.get("是否企业微信真实发送") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信正式入口发送门禁验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信正式入口发送门禁验收",
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
