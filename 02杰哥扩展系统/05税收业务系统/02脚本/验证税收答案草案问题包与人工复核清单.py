# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收答案草案问题包规则.json"
OUT_DIR = ROOT / "03数据" / "17问题包与人工复核清单"
PREVIEW_JSON = OUT_DIR / "税收答案草案问题包与人工复核清单_最新.json"
PREVIEW_MD = OUT_DIR / "税收答案草案问题包与人工复核清单_最新.md"
REPORT_JSON = OUT_DIR / "税收答案草案问题包与人工复核清单验收_最新.json"
REPORT_MD = OUT_DIR / "税收答案草案问题包与人工复核清单验收_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE) if RULE.exists() else {}
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    items = preview.get("问题包复核清单", [])
    checks = []

    checks.append(check("规则文件存在", RULE.exists(), str(RULE)))
    checks.append(check("预览JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("预览Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("问题包数量不少于3", len(rule.get("问题包", [])) >= 3, len(rule.get("问题包", []))))
    checks.append(check("复核清单覆盖全部问题包", len(items) == len(rule.get("问题包", [])), {"清单": len(items), "规则": len(rule.get("问题包", []))}))
    checks.append(check("至少一个可形成判断", preview.get("可形成判断数量", 0) >= 1, preview.get("可形成判断数量", 0)))
    checks.append(check("至少一个需降级或待补", preview.get("需降级或待补数量", 0) >= 1, preview.get("需降级或待补数量", 0)))

    required_review = set(rule.get("复核字段", []))
    missing_review = []
    for item in items:
        present = set(["问题ID", "问题", "适用税种", "能否形成当前适用判断"]) | set(item.get("人工复核清单", {}).keys())
        miss = sorted(field for field in required_review if field not in present)
        if miss:
            missing_review.append({"问题ID": item.get("问题ID"), "缺字段": miss})
    checks.append(check("人工复核字段齐备", not missing_review, missing_review))

    bad_positive = [
        item.get("问题ID")
        for item in items
        if item.get("能否形成当前适用判断") and item.get("已匹配正式依据数量", 0) < item.get("最低正式依据数量", 1)
    ]
    checks.append(check("可形成判断满足最低正式依据数量", not bad_positive, bad_positive))

    bad_degraded = [
        item.get("问题ID")
        for item in items
        if not item.get("能否形成当前适用判断") and not item.get("当前阻断原因")
    ]
    checks.append(check("降级项必须有阻断原因", not bad_degraded, bad_degraded))

    safety = preview.get("安全边界", {})
    required_false = [
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否写向量库",
        "是否调用模型推理",
        "是否生成正式税务结论",
        "是否新增端口",
        "是否重启服务",
        "是否影响股票系统",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))
    checks.append(check("禁止规则包含不绕过企业微信门禁和不写向量库", all(word in rule.get("输出规则", {}).get("禁止", []) for word in ["绕过企业微信正式入口门禁发送", "写入向量库"]), rule.get("输出规则", {}).get("禁止", [])))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收答案草案问题包与人工复核清单验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收答案草案问题包与人工复核清单验收",
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
