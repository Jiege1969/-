# -*- coding: utf-8 -*-
"""
名称：生成知识库可追溯问答只读基线脚本缺口复核.py
作用：只读复核知识库可追溯问答链路的脚本、配置、证据结构和安全边界缺口。
触发方式：python 生成知识库可追溯问答只读基线脚本缺口复核.py
安全边界：只读文件与最新状态；只写总管运行状态报告；不启动批量问答、不调用模型、不生成向量、不入库、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
KB = ROOT / "01杰哥智能系统"
KB_SCRIPTS = KB / "02脚本" / "知识库"
KB_DATA = KB / "03数据" / "知识库"
KB_DOCS = KB / "07文档"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核_最新.json"
REPORT_MD = OUT_DIR / "知识库可追溯问答只读基线脚本缺口复核_最新.md"

REQUIRED_SCRIPTS = [
    "生成知识库索引清单.py",
    "生成知识库全文索引.py",
    "生成知识库入库批次报告.py",
    "生成知识库向量化前复核清单.py",
    "生成知识库人工确认队列.py",
    "生成知识库检索增强链路报告.py",
    "验证知识库检索增强链路.py",
    "生成知识库本地问答预演.py",
    "验证知识库本地问答预演.py",
    "生成知识库系统状态摘要.py",
    "验证知识库系统状态摘要.py",
    "执行知识库写库禁用态检查.py",
]

REQUIRED_MANAGER_SCRIPTS = [
    "验证知识库底座.py",
    "验证知识库写库禁用态.py",
    "验证R02知识库单文档入库候选预检单.py",
    "验证知识库本地入库前复核.py",
]

REQUIRED_DOCS = [
    "知识库设计.md",
    "知识库入库规范.md",
    "知识库检索增强链路文件登记.md",
    "知识库本地入库前复核文件登记.md",
    "R02知识库单文档入库候选预检文件登记.md",
    "R02知识库本地入库预演器文件登记.md",
]

CONFIGS = [
    "知识库配置.json",
    "知识库入库规则.json",
    "知识库人工确认规则.json",
    "知识库元数据模板.json",
    "知识库检索增强链路规则.json",
    "知识库本地问答预演规则.json",
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_status(base: Path, names: list[str]) -> list[dict[str, Any]]:
    return [{"名称": name, "路径": str(base / name), "存在": (base / name).exists()} for name in names]


def latest_report(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    return {"路径": str(path), "存在": path.exists(), "内容": data}


def qa_traceability(qa_report: dict[str, Any]) -> dict[str, Any]:
    content = qa_report.get("内容") or {}
    results = content.get("问答结果", [])
    evidence_items = [evidence for item in results for evidence in item.get("证据", [])]
    required_fields = {"文件名", "路径", "分块序号", "命中词", "内容"}
    missing_fields = []
    for evidence in evidence_items:
        missing = sorted(required_fields - set(evidence.keys()))
        if missing:
            missing_fields.append({"证据": evidence.get("文件名", ""), "缺失字段": missing})
    safety = content.get("安全边界", {})
    return {
        "问答结果数量": len(results),
        "证据数量": len(evidence_items),
        "证据字段缺口": missing_fields,
        "全部证据可追溯": bool(evidence_items) and not missing_fields,
        "安全边界": safety,
        "未调用模型": safety.get("调用模型推理") is False,
        "未生成向量": safety.get("生成向量") is False,
        "未写正式向量库": safety.get("写正式向量库") is False,
        "未触发n8n": safety.get("触发n8n") is False,
        "未发送企业微信": safety.get("企业微信真实发送") is False,
    }


def main() -> int:
    now = datetime.now()
    script_status = file_status(KB_SCRIPTS, REQUIRED_SCRIPTS)
    manager_script_status = file_status(MANAGER / "02脚本", REQUIRED_MANAGER_SCRIPTS)
    doc_status = file_status(KB_DOCS, REQUIRED_DOCS)
    config_status = file_status(KB / "01配置", CONFIGS)

    qa_latest = latest_report(KB_DATA / "06问答预演" / "knowledge-local-qa-preview-最新.json")
    status_latest = latest_report(KB_DATA / "05状态摘要" / "knowledge-system-status-summary-最新.json")
    write_disabled_latest = latest_report(KB_DATA / "06入库前复核" / "知识库写库禁用态检查_最新.json")
    retrieval_latest = latest_report(KB_DATA / "04检索缓存" / "知识库检索增强链路报告_最新.json")
    qa_trace = qa_traceability(qa_latest)
    status_content = status_latest.get("内容") or {}
    write_disabled_content = write_disabled_latest.get("内容") or {}

    missing = {
        "知识库脚本": [item for item in script_status if not item["存在"]],
        "总管验收脚本": [item for item in manager_script_status if not item["存在"]],
        "文档登记": [item for item in doc_status if not item["存在"]],
        "配置": [item for item in config_status if not item["存在"]],
    }
    safety_checks = {
        "不启动批量问答": True,
        "不调用模型推理": qa_trace["未调用模型"],
        "不生成向量": qa_trace["未生成向量"],
        "不写正式向量库": qa_trace["未写正式向量库"],
        "不写Qdrant": write_disabled_content.get("是否写入Qdrant") is False,
        "不写PostgreSQL": write_disabled_content.get("是否写入PostgreSQL") is False,
        "不触发n8n": qa_trace["未触发n8n"] and write_disabled_content.get("是否触发n8n") is False,
        "不发送企业微信": qa_trace["未发送企业微信"],
        "不读取旧系统": write_disabled_content.get("是否读取旧系统资料") is False,
    }
    checks = [
        {"检查项": "知识库脚本齐全", "通过": not missing["知识库脚本"], "说明": missing["知识库脚本"]},
        {"检查项": "总管验收脚本齐全", "通过": not missing["总管验收脚本"], "说明": missing["总管验收脚本"]},
        {"检查项": "知识库文档登记齐全", "通过": not missing["文档登记"], "说明": missing["文档登记"]},
        {"检查项": "知识库配置齐全", "通过": not missing["配置"], "说明": missing["配置"]},
        {"检查项": "最新本地问答预演报告存在", "通过": qa_latest["存在"], "说明": qa_latest["路径"]},
        {"检查项": "问答证据可追溯", "通过": qa_trace["全部证据可追溯"], "说明": qa_trace},
        {"检查项": "系统状态摘要存在", "通过": status_latest["存在"], "说明": status_latest["路径"]},
        {"检查项": "系统状态摘要健康", "通过": (status_content.get("汇总") or {}).get("状态") == "healthy", "说明": status_content.get("汇总", {})},
        {"检查项": "写库禁用态报告存在", "通过": write_disabled_latest["存在"], "说明": write_disabled_latest["路径"]},
        {"检查项": "写库禁用态明确", "通过": write_disabled_content.get("执行器状态") == "禁用态", "说明": write_disabled_content.get("执行器状态", "")},
        {"检查项": "检索增强链路报告存在", "通过": retrieval_latest["存在"], "说明": retrieval_latest["路径"]},
        {"检查项": "安全边界全部关闭", "通过": all(safety_checks.values()), "说明": safety_checks},
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "知识库可追溯问答只读基线脚本缺口复核",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "存在缺口",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "脚本状态": script_status,
        "总管验收脚本状态": manager_script_status,
        "文档状态": doc_status,
        "配置状态": config_status,
        "最新报告": {
            "本地问答预演": qa_latest["路径"],
            "系统状态摘要": status_latest["路径"],
            "写库禁用态": write_disabled_latest["路径"],
            "检索增强链路": retrieval_latest["路径"],
        },
        "可追溯证据复核": qa_trace,
        "缺口": missing,
        "检查结果": checks,
        "安全边界": {
            "启动批量问答": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式向量库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "触发n8n": False,
            "发送企业微信": False,
            "联网检索": False,
            "读取旧系统": False,
            "接入税收业务": False,
        },
    }

    lines = [
        "# 知识库可追溯问答只读基线脚本缺口复核",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        f"- 问答结果数量：{qa_trace['问答结果数量']}",
        f"- 证据数量：{qa_trace['证据数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。")
    lines.extend([
        "",
        "## 当前缺口",
        "",
    ])
    if failed:
        for item in failed:
            lines.append(f"- {item['检查项']}：{item['说明']}")
    else:
        lines.append("- 本轮未发现必须补齐的脚本、配置、文档或证据字段缺口。")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "本轮只读复核现有产物，不启动批量问答，不调用模型，不生成向量，不写 Qdrant/PostgreSQL，不触发 n8n，不发送企业微信，不联网检索，不读取旧系统。",
    ])
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
