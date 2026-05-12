# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "20正式文档解析器接入评估"
PREVIEW_JSON = OUT_DIR / "税收正式文档解析器接入评估_最新.json"
PREVIEW_MD = OUT_DIR / "税收正式文档解析器接入评估_最新.md"
REPORT_JSON = OUT_DIR / "税收正式文档解析器接入评估验收_最新.json"
REPORT_MD = OUT_DIR / "税收正式文档解析器接入评估验收_最新.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    preview = load_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    attachments = preview.get("附件评估", [])
    checks = []

    checks.append(check("评估JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)))
    checks.append(check("评估Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)))
    checks.append(check("附件数量大于0", preview.get("附件数量", 0) > 0, preview.get("附件数量", 0)))
    checks.append(check("附件评估覆盖全部附件", len(attachments) == preview.get("附件数量", 0), {"评估": len(attachments), "附件": preview.get("附件数量", 0)}))
    checks.append(check("命令行工具探测存在", all(key in preview.get("命令行工具", {}) for key in ["soffice", "libreoffice", "antiword", "pandoc"]), preview.get("命令行工具", {})))
    checks.append(check("Python模块探测存在", all(key in preview.get("Python模块", {}) for key in ["docx", "lxml", "mammoth", "olefile", "win32com", "pypandoc"]), preview.get("Python模块", {})))

    missing_plan = [item.get("标题") for item in attachments if not item.get("推荐正式解析方案")]
    checks.append(check("每个附件都有推荐正式解析方案", not missing_plan, missing_plan))

    doc_items = [item for item in attachments if item.get("后缀") == ".doc"]
    doc_has_blocker = all(any("doc" in reason.lower() or "解析器" in reason for reason in item.get("阻断原因", [])) for item in doc_items)
    checks.append(check("老式doc附件保留正式解析阻断", doc_has_blocker, [{"标题": item.get("标题"), "阻断原因": item.get("阻断原因")} for item in doc_items]))

    conclusion = preview.get("结论", "")
    checks.append(check("结论明确不正式回填", "不进入RAG" in " ".join(preview.get("推荐路线", [])) and "正式回填" in conclusion, {"结论": conclusion, "推荐路线": preview.get("推荐路线", [])}))

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
    checks.append(check("模式为只读评估", preview.get("模式") == "readonly_evaluation_no_runtime_change", preview.get("模式")))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收正式文档解析器接入评估验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收正式文档解析器接入评估验收",
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
