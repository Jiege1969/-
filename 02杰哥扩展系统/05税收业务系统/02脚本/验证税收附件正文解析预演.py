# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "18附件正文解析预演"
PREVIEW_JSON = OUT_DIR / "税收附件正文解析预演_最新.json"
PREVIEW_MD = OUT_DIR / "税收附件正文解析预演_最新.md"
REPORT_JSON = OUT_DIR / "税收附件正文解析预演验收_最新.json"
REPORT_MD = OUT_DIR / "税收附件正文解析预演验收_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    results = preview.get("解析结果", [])
    checks = []

    checks.append(check("预览JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("预览Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("附件数量大于0", preview.get("附件数量", 0) > 0, preview.get("附件数量", 0)))
    checks.append(check("解析结果覆盖全部附件", len(results) == preview.get("附件数量", 0), {"结果": len(results), "附件": preview.get("附件数量", 0)}))
    checks.append(check("至少一个附件有可读文本", preview.get("解析完成数量", 0) + preview.get("部分解析数量", 0) > 0, {"完成": preview.get("解析完成数量", 0), "部分": preview.get("部分解析数量", 0)}))

    missing_meta = [
        item.get("标题")
        for item in results
        if not Path(item.get("本地解析元数据路径", "")).is_file()
    ]
    checks.append(check("解析元数据文件存在", not missing_meta, missing_meta))

    bad_support = [item.get("标题") for item in results if item.get("是否可作当前适用依据") is True]
    checks.append(check("附件解析预演不得直接作为当前适用依据", not bad_support, bad_support))

    missing_blocker = [item.get("标题") for item in results if not item.get("阻断原因")]
    checks.append(check("所有附件均有阻断或复核提示", not missing_blocker, missing_blocker))

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
    checks.append(check("模式为轻量附件解析预演", preview.get("模式") == "preview_only_no_runtime_change_lightweight_attachment_parse", preview.get("模式")))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收附件正文解析预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收附件正文解析预演验收",
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
