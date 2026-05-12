# -*- coding: utf-8 -*-
"""
名称：验证原则能力化.py
作用：验证“原则也是方法”是否已经从文字记录转化为规则、脚本、验收和运行闭环。
触发方式：python 验证原则能力化.py
依赖：Python标准库
所属系统：03杰哥进化系统
安全边界：只读检查并写入03进化系统日志；不删除；不覆盖旧系统；不真实发送；不写正式业务库；不触发交易接口。
创建/修改记录：2026-04-29 创建原则能力化验收脚本。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return read_json(path)
    except Exception as exc:  # noqa: BLE001
        return {"读取失败": str(exc)}


def stock_acceptance_passed(report: dict[str, Any]) -> bool:
    if report.get("失败") == 0:
        return True
    text = json.dumps(report, ensure_ascii=False)
    if '"失败": 0' in text or '"失败":0' in text:
        return True
    if '"失败数": 0' in text or '"失败数":0' in text:
        return True
    if "11/11" in text and "失败" not in text:
        return True
    return False


def ps_encoding_passed(report: dict[str, Any]) -> bool:
    if report.get("status") == "pass" and report.get("failed") == 0:
        return True
    if report.get("失败") == 0:
        return True
    text = json.dumps(report, ensure_ascii=False)
    if '"失败": 0' in text or '"失败":0' in text:
        return True
    if '"失败数": 0' in text or '"失败数":0' in text:
        return True
    if "26/26" in text and "失败" not in text:
        return True
    return False


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    system_root = root.parents[0]
    manager_root = system_root / "00杰哥系统总管"
    stock_root = system_root / "02杰哥扩展系统" / "01股票研究系统"

    config = root / "01配置" / "原则能力化规则.json"
    method_doc = root / "03数据" / "04通用方法" / "先根因后治理再固化验收方法.md"
    experience_card = root / "03数据" / "历史经验" / "PowerShell中文编码系统治理经验卡片.md"
    ps_verifier = manager_root / "02脚本" / "验证PowerShell脚本UTF8BOM编码.ps1"
    ps_verify_log = manager_root / "04日志" / "PowerShell编码修复" / "powershell-utf8bom-verify-latest.json"
    stock_acceptance_log = stock_root / "04日志" / "股票系统交付使用版总验收" / "stock-delivery-total-acceptance-最新.json"

    config_data = load_json_if_exists(config)
    method_text = read_text(method_doc) if method_doc.exists() else ""
    ps_log = load_json_if_exists(ps_verify_log)
    stock_log = load_json_if_exists(stock_acceptance_log)

    capability_chain = config_data.get("能力化链路", [])
    rule_text = json.dumps(config_data, ensure_ascii=False)

    checks = [
        check("原则能力化规则配置存在", config.exists(), str(config)),
        check("能力化链路不少于7步", isinstance(capability_chain, list) and len(capability_chain) >= 7, capability_chain),
        check("配置包含已能力化判定规则", "已能力化" in rule_text and "待能力化" in rule_text, "已能力化/待能力化"),
        check("配置包含禁止机械迁移边界", "禁止机械迁移" in rule_text and "旧系统" in rule_text, "禁止机械迁移"),
        check("通用方法文档包含原则能力化检查", "原则能力化检查" in method_text and "待能力化" in method_text, str(method_doc)),
        check("PowerShell编码经验卡片存在", experience_card.exists(), str(experience_card)),
        check("PowerShell编码验收脚本存在", ps_verifier.exists(), str(ps_verifier)),
        check("PowerShell最近编码验收通过", ps_encoding_passed(ps_log), ps_log),
        check("股票系统交付总验收通过", stock_acceptance_passed(stock_log), stock_log),
    ]

    summary = {
        "通过": sum(1 for item in checks if item["结果"] == "通过"),
        "失败": sum(1 for item in checks if item["结果"] != "通过"),
        "判定": "已能力化" if all(item["结果"] == "通过" for item in checks) else "待能力化",
    }
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "principle-capability-verification",
        "说明": "验证原则是否已经融入系统逻辑，而不是停留在文字记录。",
        "汇总": summary,
        "检查结果": checks,
        "下一步规则": "失败项不自动修复为生产动作，只生成进化建议；删除、覆盖、真实发送、写旧系统、交易接口仍需人工确认。",
    }

    output_dir = root / "04日志" / "原则能力化验收"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"principle-capability-verify-{timestamp}.json"
    latest = output_dir / "principle-capability-verify-latest.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copyfile(output, latest)

    print(json.dumps(summary, ensure_ascii=False))
    print(str(output))
    return 0 if summary["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
