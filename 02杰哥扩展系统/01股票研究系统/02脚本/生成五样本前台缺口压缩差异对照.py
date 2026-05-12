from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"

PREVIEW_JSON = DATA_DIR / "五样本前台缺口压缩预演_最新.json"
ADAPTER_VALIDATION_JSON = DATA_DIR / "L3企业微信短答适配器自动验收_20260507.json"
BRIDGE_VALIDATION_JSON = DATA_DIR / "L3企业微信短答桥接dry_run验收_20260507.json"

OUTPUT_JSON = DATA_DIR / "五样本前台缺口压缩差异对照_最新.json"
OUTPUT_MD = DATA_DIR / "五样本前台缺口压缩差异对照_最新.md"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_adapter_samples(adapter: dict) -> dict[str, dict]:
    out = {}
    for item in adapter.get("samples", []):
        code = item.get("expected_code", "")
        if code:
            out[code] = item
    return out


def extract_line(reply: str, prefix: str) -> str:
    for line in reply.splitlines():
        if line.startswith(prefix):
            return line
    return ""


def classify_gap(preview_gap: str, current_missing: str, current_why: str) -> dict:
    findings = []
    low_risk_candidates = []
    blocked_formal_changes = []

    if "资金、机构和解禁减持" in preview_gap and "资金" not in current_missing:
        findings.append("当前短答缺口行未显式表达资金/机构/解禁证据位仍待采集。")
        low_risk_candidates.append("可在下一版短答缺口压缩中加入“资金/机构/解禁证据仍待采集，不能强化结论”。")
    if "政策项不能加分" in preview_gap and "政策不强" in current_why:
        findings.append("当前短答用“政策不强”，但预演要求无结构化政策时更明确写“政策项不能加分”。")
        low_risk_candidates.append("可把无匹配政策的前台口径从“政策不强”收紧为“未匹配直接政策，政策项不能加分”。")
    if "政策证据待补" in preview_gap and "政策不强" in current_why:
        findings.append("当前短答未区分“政策不强”和“政策证据待补”。")
        low_risk_candidates.append("可对候选政策型股票写“政策背景存在，但尚未结构化到单股事件”。")
    if "价格/景气" in preview_gap and "行业价" in current_why:
        findings.append("当前短答已有行业价状态，但未统一写成价格/景气连续观测口径。")
        low_risk_candidates.append("可把“行业价未入账/单点”统一成“价格/景气观测点不足，不能写趋势确认”。")
    if not findings:
        findings.append("当前短答与预演缺口口径基本一致。")

    blocked_formal_changes.append("把差异话术写入L3企业微信短答适配器属于正式候选脚本变更，应按正式脚本/W3闸口处理，本轮只登记不实施。")
    blocked_formal_changes.append("把差异话术接入真实企业微信入口或服务刷新属于红线事项，本轮只登记不实施。")

    return {
        "findings": findings,
        "low_risk_candidates": low_risk_candidates,
        "blocked_formal_changes": blocked_formal_changes
    }


def build_item(preview_item: dict, adapter_item: dict) -> dict:
    stock = preview_item.get("stock", {})
    fp = preview_item.get("front_preview", {})
    reply = adapter_item.get("reply", "")
    current_why = extract_line(reply, "为什么：")
    current_missing = extract_line(reply, "缺口：")
    preview_gap = fp.get("one_line_gap", "")
    classified = classify_gap(preview_gap, current_missing, current_why)

    return {
        "stock": stock,
        "current_reply_status": "available" if reply else "missing",
        "current_why_line": current_why,
        "current_missing_line": current_missing,
        "preview_gap_line": preview_gap,
        "alignment_findings": classified["findings"],
        "low_risk_candidates": classified["low_risk_candidates"],
        "blocked_formal_changes": classified["blocked_formal_changes"],
        "adapter_passed": adapter_item.get("passed", False),
        "reply_length": adapter_item.get("reply_length", 0),
        "line_count": adapter_item.get("line_count", 0)
    }


def render_md(result: dict) -> str:
    lines = [
        "# 五样本前台缺口压缩差异对照",
        "",
        f"- 生成时间：{result['generated_at']}",
        "- 资产身份：W1差异对照报告，不改短答适配器，不改企业微信入口。",
        "- 用途：对比“前台缺口压缩预演”和“当前L3企业微信短答适配器输出”的差异。",
        "",
        "## 总览",
        "",
        f"- 覆盖样本：{result['summary']['sample_count']}",
        f"- 可低风险吸收候选：{result['summary']['low_risk_candidate_count']}",
        f"- 正式变更阻断登记：{result['summary']['blocked_formal_change_count']}",
        "",
        "## 明细",
        ""
    ]
    for item in result["items"]:
        lines.extend([
            f"### {item['stock'].get('name')}（{item['stock'].get('code')}）",
            "",
            f"- 当前为什么：{item['current_why_line']}",
            f"- 当前缺口：{item['current_missing_line']}",
            f"- 预演缺口：{item['preview_gap_line']}",
            "- 差异发现："
        ])
        lines.extend([f"  - {x}" for x in item["alignment_findings"]])
        lines.append("- 可低风险候选：")
        if item["low_risk_candidates"]:
            lines.extend([f"  - {x}" for x in item["low_risk_candidates"]])
        else:
            lines.append("  - 暂无。")
        lines.append("- 阻断登记：")
        lines.extend([f"  - {x}" for x in item["blocked_formal_changes"]])
        lines.append("")
    lines.extend([
        "## 边界",
        "",
        "- 未修改L3企业微信短答适配器。",
        "- 未修改企业微信桥接入口。",
        "- 未发送企业微信。",
        "- 未重启服务。",
        "- 未接n8n、券商接口或自动交易。"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    preview = read_json(PREVIEW_JSON)
    adapter = read_json(ADAPTER_VALIDATION_JSON)
    bridge = read_json(BRIDGE_VALIDATION_JSON)
    adapter_by_code = index_adapter_samples(adapter)

    items = []
    for preview_item in preview.get("previews", []):
        code = preview_item.get("stock", {}).get("code", "")
        items.append(build_item(preview_item, adapter_by_code.get(code, {})))

    low_risk_count = sum(len(item["low_risk_candidates"]) for item in items)
    blocked_count = sum(len(item["blocked_formal_changes"]) for item in items)
    result = {
        "名称": "五样本前台缺口压缩差异对照",
        "generated_at": now,
        "asset_identity": "W1差异对照报告",
        "status": "ready",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_score_write": True,
        "not_adapter_write": True,
        "items": items,
        "summary": {
            "sample_count": len(items),
            "adapter_validation_status": adapter.get("status", ""),
            "bridge_validation_status": bridge.get("status", ""),
            "low_risk_candidate_count": low_risk_count,
            "blocked_formal_change_count": blocked_count
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_score_write": True,
            "not_adapter_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(OUTPUT_JSON, result)
    OUTPUT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "sample_count": len(items),
        "low_risk_candidate_count": low_risk_count,
        "blocked_formal_change_count": blocked_count,
        "json": str(OUTPUT_JSON),
        "md": str(OUTPUT_MD)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
