# -*- coding: utf-8 -*-
"""
名称：验证新模块开工前置与母样本边界.py
作用：只读核查新模块开工前置规则、技术债清偿前置规则和股票母样本复用边界是否完整。
触发方式：python 验证新模块开工前置与母样本边界.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读核查并写验收报告；不创建新业务目录；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建新模块开工前置验收入口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
EVOLUTION = ROOT / "03杰哥进化系统"

NEW_MODULE_RULE = MANAGER / "01配置" / "新模块开工前置规则.json"
COPY_RULE = MANAGER / "01配置" / "新业务系统复制搭建规则.json"
DEBT_RULE = EVOLUTION / "01配置" / "技术债清偿前置规则.json"
DEBT_DOC = EVOLUTION / "07文档" / "技术债清偿三条强制前置规则_20260506.md"
OUT_DIR = MANAGER / "03数据" / "运行状态"
LOG_DIR = MANAGER / "04日志" / "制度化治理"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def has_words(path: Path, words: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return all(word in text for word in words)


def validate() -> dict[str, Any]:
    failures: list[str] = []
    for path in [NEW_MODULE_RULE, COPY_RULE, DEBT_RULE, DEBT_DOC]:
        if not path.exists():
            failures.append(f"缺少规则文件：{path}")

    new_rule = read_json(NEW_MODULE_RULE) if NEW_MODULE_RULE.exists() else {}
    copy_rule = read_json(COPY_RULE) if COPY_RULE.exists() else {}
    debt_rule = read_json(DEBT_RULE) if DEBT_RULE.exists() else {}

    pre_items = new_rule.get("开工前必须完成", [])
    pre_ids = {item.get("编号") for item in pre_items}
    expected_pre = {f"PRE-{i:03d}" for i in range(1, 8)}
    missing_pre = sorted(expected_pre - pre_ids)
    if missing_pre:
        failures.append("缺少开工前置项：" + "、".join(missing_pre))

    for item in pre_items:
        for key in ["编号", "名称", "要求", "证据", "阻断条件"]:
            if not item.get(key):
                failures.append(f"{item.get('编号', '未编号')} 缺少 {key}")

    associated = [Path(path) for path in new_rule.get("关联文档", [])]
    missing_docs = [str(path) for path in associated if not path.exists()]
    if missing_docs:
        failures.append("关联文档缺失：" + "；".join(missing_docs))

    required_docs = {
        "目录编号总图": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "目录编号总图_最新.md",
        "日志分级与保留期规则": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "日志分级与保留期规则_最新.md",
        "上线清单模板": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "上线清单模板_最新.md",
        "只读验收五问模板": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "只读验收五问模板_最新.md",
        "股票样本复用施工原则": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "股票样本复用施工原则_最新.md",
        "股票样本提纯复用矩阵": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "股票样本提纯复用矩阵_最新.md",
        "清债不添新债原则": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "清债不添新债原则_最新.md",
        "施工者自约束规则": EVOLUTION / "03数据" / "32技术债清偿强制前置规则" / "施工者自约束规则_最新.md",
    }
    for name, path in required_docs.items():
        if not path.exists():
            failures.append(f"缺少{name}：{path}")

    copy_allow = set(copy_rule.get("复制对象", {}).get("允许复制", []))
    copy_forbid = set(copy_rule.get("复制对象", {}).get("禁止复制", []))
    if not {"目录骨架模板", "验收脚本模板", "安全边界模板"}.issubset(copy_allow):
        failures.append("新业务复制规则缺少核心允许复制项")
    if not {"股票系统踩坑过程", "历史日志里的过期规则", "只服务股票的字段和评分口径"}.issubset(copy_forbid):
        failures.append("新业务复制规则缺少核心禁止复制项")

    debt_required = set(debt_rule.get("强制前置", []))
    if "只读验收五问" not in debt_required:
        failures.append("技术债清偿前置规则未列入只读验收五问")

    doc_checks = {
        "目录编号总图": has_words(required_docs["目录编号总图"], ["00总管", "01智能", "02扩展", "03进化"]),
        "日志分级与保留期规则": has_words(required_docs["日志分级与保留期规则"], ["DEBUG", "INFO", "WARN", "ERROR"]),
        "上线清单模板": has_words(required_docs["上线清单模板"], ["功能脚本", "验收", "回滚"]),
        "只读验收五问模板": has_words(required_docs["只读验收五问模板"], ["端口", "骨架", "基因", "证据", "回滚"]),
        "股票样本复用施工原则": has_words(required_docs["股票样本复用施工原则"], ["母样本", "不继承旧债"]),
        "清债不添新债原则": has_words(required_docs["清债不添新债原则"], ["无依赖", "删除"]),
    }
    for name, ok in doc_checks.items():
        if not ok:
            failures.append(f"{name} 内容核查未通过")

    report = {
        "名称": "新模块开工前置与母样本边界验收",
        "验收时间": now_text(),
        "开工前置项数量": len(pre_items),
        "开工前置项完整": not missing_pre and all(all(item.get(key) for key in ["编号", "名称", "要求", "证据", "阻断条件"]) for item in pre_items),
        "关联文档数量": len(associated),
        "关联文档缺失数量": len(missing_docs),
        "核心文档核查": doc_checks,
        "失败": failures,
        "当前结论": "通过" if not failures else "未通过",
        "安全边界": {
            "未创建新业务目录": True,
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
        },
    }
    return report


def write_reports(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "新模块开工前置与母样本边界验收_最新.json"
    md_path = OUT_DIR / "新模块开工前置与母样本边界验收_最新.md"
    log_path = LOG_DIR / "new-module-preflight-mother-sample-boundary-verify-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    json_path.write_text(text, encoding="utf-8")
    log_path.write_text(text, encoding="utf-8")

    lines = [
        "# 新模块开工前置与母样本边界验收",
        "",
        f"- 验收时间：{report['验收时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- PRE 项数量：{report['开工前置项数量']}",
        f"- 关联文档缺失数量：{report['关联文档缺失数量']}",
        "",
        "## 核查入口",
        f"- 新模块开工前置规则：`{NEW_MODULE_RULE}`",
        f"- 新业务复制搭建规则：`{COPY_RULE}`",
        f"- 技术债清偿前置规则：`{DEBT_RULE}`",
        f"- 只读验收五问模板：`{EVOLUTION / '03数据' / '32技术债清偿强制前置规则' / '只读验收五问模板_最新.md'}`",
        "",
        "## 失败项",
    ]
    if report["失败"]:
        lines.extend([f"- {item}" for item in report["失败"]])
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 安全边界",
        "- 未创建新业务目录；未触发 n8n；未发送企业微信；未调用券商接口；未自动交易。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report = validate()
    write_reports(report)
    print(json.dumps({
        "状态": report["当前结论"],
        "PRE项": report["开工前置项数量"],
        "关联文档缺失": report["关联文档缺失数量"],
        "失败数量": len(report["失败"]),
        "输出": str(OUT_DIR / "新模块开工前置与母样本边界验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if not report["失败"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
