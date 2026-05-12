from __future__ import annotations

import hashlib
import importlib.util
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


def as_path(text: str) -> Path:
    return Path(text.replace("/", "\\"))


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def evidence_category(source_file: str) -> str:
    lowered = source_file.lower()
    if "正式扩容批次" in source_file or "原始文档" in source_file:
        return "正式依据"
    if "问答" in source_file or "样本" in source_file:
        return "答疑材料"
    if "说明" in source_file or "设计" in source_file:
        return "解释材料"
    return "关联材料"


def load_source_trust_classifier():
    script_path = Path("D:/杰哥智能化系统/02杰哥扩展系统/00公共组件/02脚本/信息来源智能鉴别器.py")
    config_path = Path("D:/杰哥智能化系统/02杰哥扩展系统/00公共组件/01配置/信息来源可信度分层规则.json")
    if not script_path.exists() or not config_path.exists():
        return None, None
    spec = importlib.util.spec_from_file_location("source_trust_classifier", script_path)
    if spec is None or spec.loader is None:
        return None, None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = load_json(config_path)
    return module, config


def source_url_from(source: dict[str, Any]) -> str:
    for key in ["来源URL", "来源链接", "url", "URL", "链接"]:
        value = str(source.get(key, "")).strip()
        if value:
            return value
    return ""


def source_trust_fields(source: dict[str, Any], classifier: Any, trust_config: dict[str, Any] | None) -> dict[str, Any]:
    url = source_url_from(source)
    if url and classifier is not None and trust_config is not None:
        result = classifier.classify_url(url, trust_config)
        return {
            "来源URL": result.get("来源URL", url),
            "匹配域名": result.get("匹配域名", ""),
            "可信度等级": result.get("可信度等级", "S6"),
            "来源类型": result.get("来源类型", ""),
            "来源用途边界": f"{result.get('默认用途', '')}；{result.get('默认限制', '')}",
            "是否需要反向追溯": result.get("是否需要反向追溯", True),
            "是否可作正式依据候选": result.get("是否可作正式依据候选", False),
        }
    return {
        "来源URL": url,
        "匹配域名": "",
        "可信度等级": "待判定",
        "来源类型": "本地知识库来源文件",
        "来源用途边界": "仅作为已入库资料片段证据；需追溯到原始来源URL或人工登记来源后才能作正式依据。",
        "是否需要反向追溯": True,
        "是否可作正式依据候选": False,
    }


def build_short_answer(question: str, answer: str, evidence_count: int, detail_path: Path) -> dict[str, str]:
    first_line = answer.splitlines()[0] if answer else "未形成回答。"
    return {
        "结论": first_line[:160],
        "依据": f"已挂接 {evidence_count} 条来源引用；详情见证据卡。",
        "适用条件": "仅适用于已登记知识库来源文件覆盖的问题；证据之外不作确定结论。",
        "风险": "当前为本地可追溯问答框交付，不调用模型推理，不写正式向量库，不企业微信真实发送。",
        "详情入口": str(detail_path),
    }


def build_package(config: dict[str, Any]) -> dict[str, Any]:
    source_cfg = config["输入来源"]
    qa_path = as_path(source_cfg["知识库入口输出"])
    readiness_path = as_path(source_cfg["知识库路由就绪"])
    router_path = as_path(source_cfg["企业微信统一路由预演"])
    local_call_path = as_path(source_cfg["企业微信本地调用预演"])

    qa = load_json(qa_path)
    readiness = load_json(readiness_path)
    router = load_json(router_path)
    local_call = load_json(local_call_path)

    output_dir = module_root() / "03数据" / "01交付包"
    latest_detail = output_dir / "知识库可追溯问答框交付包_最新.md"
    classifier, trust_config = load_source_trust_classifier()

    cards: list[dict[str, Any]] = []
    for index, item in enumerate(qa.get("问答结果", []), 1):
        question = str(item.get("问题", ""))
        trace_id = f"kqa-{datetime.now().strftime('%Y%m%d')}-{short_hash(question)}"
        evidences: list[dict[str, Any]] = []
        relations: list[dict[str, Any]] = []
        for source_index, source in enumerate(item.get("来源引用", []), 1):
            evidence_id = f"{trace_id}-E{source_index}"
            source_file = str(source.get("来源文件", ""))
            exists = bool(source.get("来源文件存在")) and Path(source_file).exists()
            trust_fields = source_trust_fields(source, classifier, trust_config)
            evidence = {
                "证据ID": evidence_id,
                "引用编号": source.get("引用编号") or f"S{source_index}",
                "来源文件": source_file,
                "来源文件存在": exists,
                **trust_fields,
                "分块序号": source.get("分块序号"),
                "命中词": source.get("命中词", []),
                "证据摘录": source.get("证据摘录", ""),
                "资料类别": evidence_category(source_file),
                "是否支撑回答": exists and source.get("分块序号") is not None,
            }
            evidences.append(evidence)
            relations.append({
                "from": trace_id,
                "to": evidence_id,
                "关系": "引用" if evidence["是否支撑回答"] else "待复核",
                "说明": "回答引用该证据片段。",
            })

        status = item.get("状态") or ("answered_with_sources" if evidences else "no_evidence")
        answer = str(item.get("回答", ""))
        if not evidences:
            answer = config["输出要求"]["无证据降级"]
            status = "no_evidence_downgraded"

        card = {
            "序号": index,
            "trace_id": trace_id,
            "问题": question,
            "状态": status,
            "回答": answer,
            "短输出": build_short_answer(question, answer, len(evidences), latest_detail),
            "证据卡": evidences,
            "关系边": relations,
            "人工复核建议": "证据覆盖不足或来源不存在时转人工复核；正式外发前必须复核来源和口径。",
        }
        cards.append(card)

    router_hits = [
        item for item in router.get("样例结果", [])
        if item.get("命中路由") == "知识库问答" and item.get("是否命中期望") is True
    ]
    local_hits = [
        item for item in local_call.get("调用结果", [])
        if item.get("路由") == "知识库问答" and item.get("调用状态") in ("healthy", "完成")
    ]
    safety = dict(config.get("安全边界", {}))
    input_safety = qa.get("安全边界", {})
    for key in ["调用模型推理", "生成向量", "写正式向量库", "写正式数据库", "触发n8n", "企业微信真实发送", "联网检索", "读取旧系统"]:
        safety[key] = safety.get(key, False) or bool(input_safety.get(key, False))

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "extension-knowledge-traceable-qa-box-delivery",
        "所属系统": "02杰哥扩展系统/07知识库可追溯问答框",
        "输入报告": {
            "知识库入口输出": str(qa_path),
            "知识库路由就绪": str(readiness_path),
            "企业微信统一路由预演": str(router_path),
            "企业微信本地调用预演": str(local_call_path),
        },
        "公共来源判断机制": config.get("公共来源判断机制", {}),
        "汇总": {
            "状态": "ready_for_shadow_acceptance",
            "问题数量": len(cards),
            "带证据回答数量": sum(1 for item in cards if item["证据卡"]),
            "证据卡数量": sum(len(item["证据卡"]) for item in cards),
            "关系边数量": sum(len(item["关系边"]) for item in cards),
            "知识库路由命中数量": len(router_hits),
            "知识库本地调用命中数量": len(local_hits),
            "交付口径": "可验收、可追溯、可接统一路由；仍为local_preview_only，不外发、不写库。",
        },
        "问答框": cards,
        "路由接入": {
            "统一指令路由命中": router_hits,
            "统一指令本地调用命中": local_hits,
            "01知识库路由就绪结论": readiness.get("接入结论", ""),
            "仍需人工确认": readiness.get("阻塞项", []),
        },
        "安全边界": safety,
        "下一步": [
            "把该交付包作为企业微信知识库问答的本地详情入口。",
            "三个通用助手桥接时只读取本交付包或01入口输出，不直接写知识库。",
            "正式外发前补人工复核标记、来源文件覆盖率和当前生效口径确认。",
        ],
    }
    return report


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 知识库可追溯问答框交付包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 状态：{report['汇总']['状态']}",
        f"- 问题数量：{report['汇总']['问题数量']}",
        f"- 证据卡数量：{report['汇总']['证据卡数量']}",
        f"- 关系边数量：{report['汇总']['关系边数量']}",
        f"- 交付口径：{report['汇总']['交付口径']}",
        "",
        "## 安全边界",
        "",
    ]
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 问答框", ""])
    for item in report.get("问答框", []):
        lines.extend([
            f"### {item['问题']}",
            "",
            f"- trace_id：{item['trace_id']}",
            f"- 状态：{item['状态']}",
            f"- 结论：{item['短输出']['结论']}",
            f"- 依据：{item['短输出']['依据']}",
            f"- 风险：{item['短输出']['风险']}",
            "",
            "| 证据ID | 来源文件 | 分块 | 资料类别 | 支撑回答 |",
            "| --- | --- | --- | --- | --- |",
        ])
        for evidence in item.get("证据卡", []):
            lines.append(
                f"| {evidence['证据ID']} | {evidence['来源文件']} | {evidence['分块序号']} | "
                f"{evidence['资料类别']} | {evidence['是否支撑回答']} |"
            )
        lines.append("")
        lines.extend([
            "| 证据ID | 可信度等级 | 来源类型 | 是否反向追溯 | 用途边界 |",
            "| --- | --- | --- | --- | --- |",
        ])
        for evidence in item.get("证据卡", []):
            boundary = str(evidence.get("来源用途边界", "")).replace("|", "/")
            lines.append(
                f"| {evidence['证据ID']} | {evidence.get('可信度等级', '')} | {evidence.get('来源类型', '')} | "
                f"{evidence.get('是否需要反向追溯', True)} | {boundary} |"
            )
        lines.append("")
    lines.extend(["## 下一步", ""])
    for item in report.get("下一步", []):
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "知识库可追溯问答框交付规则.json"
    config = load_json(config_path)
    report = build_package(config)

    output_dir = root / "03数据" / "01交付包"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = output_dir / f"知识库可追溯问答框交付包_{stamp}.json"
    latest_json = output_dir / "知识库可追溯问答框交付包_最新.json"
    output_md = output_dir / f"知识库可追溯问答框交付包_{stamp}.md"
    latest_md = output_dir / "知识库可追溯问答框交付包_最新.md"

    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": report["汇总"]["状态"],
        "问题数量": report["汇总"]["问题数量"],
        "证据卡数量": report["汇总"]["证据卡数量"],
        "输出": str(latest_json),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
