# -*- coding: utf-8 -*-
"""
名称：验证股票交付闭环规则沉淀包.py
作用：验证股票交付闭环规则沉淀包完整、证据可读、规则格式闭环，并确认安全边界未突破。
触发方式：python 验证股票交付闭环规则沉淀包.py
依赖：Python标准库；生成股票交付闭环规则沉淀包.py。
所属系统：03杰哥进化系统
安全边界：只运行03本地生成和验收；不修改股票系统核心脚本，不修改总管进度口径，不修改知识库问答代码，不发送企业微信，不触发n8n，不调用外部正式发送接口，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票交付闭环规则沉淀验收脚本。
标识：evolution-stock-delivery-loop-rule-deposit-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = system_root()
    generator = root / "02脚本" / "生成股票交付闭环规则沉淀包.py"
    latest_json = root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.json"
    latest_md = root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.md"
    log_dir = root / "04日志" / "股票交付闭环规则沉淀验收"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON规则包存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown规则包存在", latest_md.exists(), str(latest_md))
    report = load_json(latest_json) if latest_json.exists() else {}
    rules = report.get("规则清单", [])
    names = {item.get("规则名称") for item in rules}
    expected = {
        "正式覆盖前必须备份",
        "_最新 文件刷新必须有回滚证据",
        "影子验证通过后才能接正式口径",
        "企业微信真实发送必须先白名单灰度",
        "n8n、券商接口、自动交易必须分级隔离",
        "完成后必须生成最终收口验收",
    }
    sample = report.get("小样本规则沉淀验收", {})
    evidence = report.get("证据摘要", {})
    safety = report.get("安全边界", {})
    auto = report.get("自动固化建议", {})
    check_items = report.get("本地检查项候选", [])
    add_check(checks, "证据源全部存在", sample.get("证据源全部存在") is True, report.get("缺失证据"))
    add_check(checks, "237交付闭环验收15/15通过", evidence.get("237交付闭环", {}).get("验收通过") >= 15 and evidence.get("237交付闭环", {}).get("验收失败") == 0, evidence.get("237交付闭环"))
    add_check(checks, "241白名单灰度发送成功且验收通过", evidence.get("241白名单灰度", {}).get("真实发送成功") is True and evidence.get("241白名单灰度", {}).get("验收失败") == 0, evidence.get("241白名单灰度"))
    add_check(checks, "242最终收口20/20通过", evidence.get("242最终收口", {}).get("验收通过") >= 20 and evidence.get("242最终收口", {}).get("验收失败") == 0, evidence.get("242最终收口"))
    add_check(checks, "规则数量为6", int(report.get("规则数量", 0) or 0) == 6, report.get("规则数量"))
    add_check(checks, "六条目标规则全部存在", expected.issubset(names), sorted(names))
    add_check(checks, "规则闭环字段完整", all(all(rule.get(key) for key in ("问题", "复盘", "规则", "下次施工约束")) for rule in rules), rules)
    add_check(checks, "检查项数量为6", len(check_items) == 6, len(check_items))
    add_check(checks, "检查项ID唯一", len({item.get("检查项ID") for item in check_items}) == len(check_items), check_items)
    add_check(checks, "自动固化数量为3", int(report.get("自动固化数量", 0) or 0) == 3, report.get("自动固化数量"))
    add_check(checks, "人工确认或硬边界数量为3", int(report.get("人工确认或硬边界数量", 0) or 0) == 3, report.get("人工确认或硬边界数量"))
    add_check(checks, "可自动固化规则明确", set(auto.get("可自动固化", [])) == {"_最新 文件刷新必须有回滚证据", "影子验证通过后才能接正式口径", "完成后必须生成最终收口验收"}, auto)
    add_check(checks, "人工确认规则明确", set(auto.get("仍需人工确认或硬边界保留", [])) == {"正式覆盖前必须备份", "企业微信真实发送必须先白名单灰度", "n8n、券商接口、自动交易必须分级隔离"}, auto)
    add_check(checks, "小样本规则沉淀验收通过", sample.get("判定") == "通过", sample)
    add_check(checks, "未写回股票系统", safety.get("写回股票系统") is False, safety)
    add_check(checks, "未修改股票核心脚本", safety.get("修改股票核心脚本") is False, safety)
    add_check(checks, "未修改总管进度配置", safety.get("修改总管进度配置") is False, safety)
    add_check(checks, "未修改知识库问答代码", safety.get("修改知识库问答代码") is False, safety)
    add_check(checks, "未发送企业微信", safety.get("发送企业微信") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未调用外部正式发送接口", safety.get("调用外部正式发送接口") is False, safety)
    add_check(checks, "未调用券商接口", safety.get("调用券商接口") is False, safety)
    add_check(checks, "未自动交易", safety.get("自动交易") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-loop-rule-deposit-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "验收对象": str(latest_json),
    }
    output = log_dir / f"evolution-stock-delivery-loop-rule-deposit-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = log_dir / "evolution-stock-delivery-loop-rule-deposit-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
