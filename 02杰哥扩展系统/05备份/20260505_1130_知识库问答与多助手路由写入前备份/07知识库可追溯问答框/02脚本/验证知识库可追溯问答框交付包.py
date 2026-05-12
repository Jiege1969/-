from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    root = module_root()
    report_path = root / "03数据" / "01交付包" / "知识库可追溯问答框交付包_最新.json"
    report_md = root / "03数据" / "01交付包" / "知识库可追溯问答框交付包_最新.md"
    log_dir = root / "04日志"

    checks: list[dict[str, Any]] = [
        check("交付包JSON存在", report_path.exists(), str(report_path)),
        check("交付包Markdown存在", report_md.exists(), str(report_md)),
    ]

    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    qa_items = report.get("问答框", [])

    checks.extend([
        check("交付状态为影子验收就绪", summary.get("状态") == "ready_for_shadow_acceptance", summary.get("状态")),
        check("至少1个问答样本", summary.get("问题数量", 0) >= 1, summary.get("问题数量")),
        check("至少1张证据卡", summary.get("证据卡数量", 0) >= 1, summary.get("证据卡数量")),
        check("知识库统一路由命中", summary.get("知识库路由命中数量", 0) >= 1, summary.get("知识库路由命中数量")),
        check("知识库本地调用命中", summary.get("知识库本地调用命中数量", 0) >= 1, summary.get("知识库本地调用命中数量")),
    ])

    for item in qa_items:
        question = item.get("问题", "")
        evidences = item.get("证据卡", [])
        checks.append(check(f"问答包含trace_id：{question}", bool(item.get("trace_id")), item.get("trace_id")))
        checks.append(check(f"短输出包含详情入口：{question}", bool(item.get("短输出", {}).get("详情入口")), item.get("短输出", {})))
        if item.get("状态") == "answered_with_sources":
            checks.append(check(f"有来源回答包含证据卡：{question}", len(evidences) >= 1, len(evidences)))
        for evidence in evidences:
            evidence_name = evidence.get("证据ID", "")
            checks.append(check(f"证据来源文件存在：{evidence_name}", evidence.get("来源文件存在") is True and Path(evidence.get("来源文件", "")).exists(), evidence.get("来源文件")))
            checks.append(check(f"证据包含分块序号：{evidence_name}", evidence.get("分块序号") is not None, evidence.get("分块序号")))
            checks.append(check(f"证据摘录非空：{evidence_name}", bool(str(evidence.get("证据摘录", "")).strip()), str(evidence.get("证据摘录", ""))[:80]))

    safety = report.get("安全边界", {})
    for key in [
        "修改01智能系统知识库代码",
        "覆盖正式知识库",
        "调用模型推理",
        "生成向量",
        "写正式向量库",
        "写正式数据库",
        "触发n8n",
        "企业微信真实发送",
        "联网检索",
        "读取旧系统",
        "修改股票研究系统",
        "自动交易",
    ]:
        checks.append(check(f"安全边界关闭：{key}", safety.get(key) is False, safety.get(key)))

    pass_count = sum(1 for item in checks if item["通过"])
    fail_count = len(checks) - pass_count
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "extension-knowledge-traceable-qa-box-delivery-verify",
        "所属系统": "02杰哥扩展系统/07知识库可追溯问答框",
        "验收对象": str(report_path),
        "汇总": {
            "状态": "pass" if fail_count == 0 else "fail",
            "通过数量": pass_count,
            "失败数量": fail_count,
        },
        "检查项": checks,
        "安全结论": "本次只做02扩展侧知识库可追溯问答框交付验收；未修改01知识库代码，未写正式库，未触发n8n，未企业微信真实发送。",
    }

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = log_dir / f"knowledge-traceable-qa-box-delivery-verify-{stamp}.json"
    latest_json = log_dir / "knowledge-traceable-qa-box-delivery-verify-最新.json"
    output_md = log_dir / f"知识库可追溯问答框交付验收_{stamp}.md"
    latest_md = log_dir / "知识库可追溯问答框交付验收_最新.md"

    write_json(output_json, result)
    write_json(latest_json, result)

    lines = [
        "# 知识库可追溯问答框交付验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 状态：{result['汇总']['状态']}",
        f"- 通过：{pass_count}",
        f"- 失败：{fail_count}",
        f"- 安全结论：{result['安全结论']}",
        "",
        "## 检查项",
        "",
    ]
    for item in checks:
        lines.append(f"- [{'通过' if item['通过'] else '失败'}] {item['名称']}：{item['详情']}")
    lines.append("")
    write_text(output_md, "\n".join(lines))
    write_text(latest_md, "\n".join(lines))

    print(json.dumps({"状态": result["汇总"]["状态"], "通过": pass_count, "失败": fail_count, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
