# -*- coding: utf-8 -*-
"""
名称：验证子系统全闭环继承状态.py
作用：验证子系统全闭环继承状态报告是否生成且安全边界有效。
触发方式：python 验证子系统全闭环继承状态.py
依赖：Python标准库；子系统全闭环继承状态_最新.json。
所属系统：00杰哥系统总管
安全边界：只读验证，不删除、不覆盖、不触发n8n、不发送企业微信、不写正式库、不接交易接口。
创建/修改记录：2026-04-28 创建。
标识：subsystem-full-cycle-inheritance-verify
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
REPORT = ROOT / "00杰哥系统总管" / "03数据" / "全闭环保障" / "子系统全闭环继承状态_最新.json"
RULE = ROOT / "00杰哥系统总管" / "01配置" / "子系统全闭环继承规则.json"
GENERAL_TEMPLATE = ROOT / "03杰哥进化系统" / "03数据" / "04通用方法" / "四系统小闭环_通用施工模板_20260503.md"
EVOLUTION_MECHANISM = ROOT / "03杰哥进化系统" / "03数据" / "04通用方法" / "影子试验_逐步组合_失败隔离通用进化机制_20260503.md"
DESIGN_MECHANISM = ROOT / "00杰哥系统总管" / "07文档" / "设计纲领" / "影子试验逐步组合失败隔离通用进化机制_20260503.md"


def main() -> int:
    checks: list[dict[str, object]] = [
        {"name": "报告存在", "ok": REPORT.exists()},
        {"name": "通用施工模板存在", "ok": GENERAL_TEMPLATE.exists()},
        {"name": "总纲进化机制存在", "ok": DESIGN_MECHANISM.exists()},
        {"name": "通用进化方法存在", "ok": EVOLUTION_MECHANISM.exists()},
        {"name": "继承规则存在", "ok": RULE.exists()},
    ]
    if REPORT.exists():
        data = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        design_text = DESIGN_MECHANISM.read_text(encoding="utf-8-sig") if DESIGN_MECHANISM.exists() else ""
        evolution_text = EVOLUTION_MECHANISM.read_text(encoding="utf-8-sig") if EVOLUTION_MECHANISM.exists() else ""
        summary = data.get("汇总", {})
        checks.append({"name": "子系统数量不少于10", "ok": summary.get("总数", 0) >= 10})
        checks.append({"name": "至少股票系统已纳入扫描", "ok": any("01股票研究系统" in item.get("路径", "") for item in data.get("子系统", []))})
        checks.append({"name": "至少一个系统已继承", "ok": summary.get("已继承", 0) >= 1})
        template_state = data.get("通用施工模板", {})
        checks.append({"name": "报告已纳入通用施工模板", "ok": template_state.get("存在") is True})
        inheritance = data.get("继承要求", {})
        required_keys = {"样板任务", "闸口链路", "智能旁路", "进化慎入库"}
        evolution_keys = {"影子试验", "逐步组合", "失败隔离", "稳定优先"}
        checks.append({"name": "四类闭环继承要求齐全", "ok": required_keys.issubset(set(inheritance.keys()))})
        checks.append({"name": "四类通用进化要求齐全", "ok": evolution_keys.issubset(set(inheritance.keys()))})
        checks.append({"name": "报告已纳入总纲进化机制", "ok": data.get("总纲进化机制", {}).get("存在") is True})
        checks.append({"name": "报告已纳入通用进化方法", "ok": data.get("通用进化机制", {}).get("存在") is True})
        checks.append({"name": "总纲覆盖脚本命令工作流代码粒度", "ok": all(word in design_text for word in ["每个脚本", "每条命令", "每个工作流", "每段代码"])})
        checks.append({"name": "进化方法覆盖脚本命令工作流代码粒度", "ok": all(word in evolution_text for word in ["每个脚本", "每条命令", "每个工作流", "每段代码"])})
        strategy = data.get("策略", {})
        checks.append({"name": "接续固化边界已纳入策略", "ok": "接续固化" in strategy})
        safety = data.get("安全边界", {})
        checks.append({"name": "安全边界全部禁止", "ok": all(value is False for value in safety.values())})
    ok = all(item["ok"] for item in checks)
    print(json.dumps({"ok": ok, "passed": sum(1 for item in checks if item["ok"]), "total": len(checks), "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
