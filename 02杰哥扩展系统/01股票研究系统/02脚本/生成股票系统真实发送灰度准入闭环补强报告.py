# -*- coding: utf-8 -*-
"""
名称：生成股票系统真实发送灰度准入闭环补强报告.py
作用：汇总真实发送灰度准入补强包，证明材料齐全但最终闸口仍拦截真实发送。
安全边界：只读股票系统本地产物；只写 03数据/238股票系统真实发送灰度准入闭环补强；不发送企业微信、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "238股票系统真实发送灰度准入闭环补强"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package(path: Path, label: str, pass_key: str | None = None) -> dict[str, Any]:
    data = load_json(path)
    passed = data.get(pass_key) if pass_key else None
    return {
        "名称": label,
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "sha256": sha256(path),
        "生成时间": data.get("生成时间"),
        "通过字段": pass_key or "",
        "通过": passed if isinstance(passed, bool) else None,
        "摘要": data.get("当前结论") or data.get("当前确认状态") or data.get("是否允许进入真实灰度") or data.get("是否允许真实发送"),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票系统真实发送灰度准入闭环补强报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总结论：{report['总结论']}",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 是否允许 n8n：{report['是否允许n8n']}",
        f"- 是否允许服务重启：{report['是否允许服务重启']}",
        "",
        "## 补强包",
        "",
    ]
    for item in report["补强包"]:
        lines.append(f"- {item['名称']}：存在={item['存在']}，通过={item['通过']}，路径={item['路径']}")
    lines.extend(["", "## 闸口结论", ""])
    for key, value in report["闸口结论"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步交接", ""])
    for item in report["下一步交接"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    final_gate_path = DATA / "36真实灰度最终闸口" / "股票企业微信真实灰度最终闸口包_最新.json"
    credential_path = DATA / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json"
    rollback_path = DATA / "41真实灰度回滚预案" / "股票企业微信真实灰度回滚预案包_最新.json"
    whitelist_path = DATA / "42真实灰度白名单试运行" / "股票企业微信真实灰度白名单试运行包_最新.json"
    human_path = DATA / "43真实灰度人工确认单" / "股票企业微信真实灰度人工确认单包_最新.json"
    receipt_path = DATA / "45真实灰度确认回执登记" / "股票企业微信真实灰度确认回执登记包_最新.json"
    guard_path = DATA / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json"
    plan_path = DATA / "236企业微信真实发送灰度准入与停止开关方案" / "企业微信真实发送灰度准入与停止开关方案_最新.json"
    plan_verify_path = DATA / "236企业微信真实发送灰度准入与停止开关方案" / "企业微信真实发送灰度准入与停止开关方案验收_最新.json"

    final_gate = load_json(final_gate_path)
    receipt = load_json(receipt_path)
    guard = load_json(guard_path)
    plan = load_json(plan_path)
    plan_verify = load_json(plan_verify_path)

    packages = [
        package(credential_path, "40凭据隔离审计", "是否通过凭据隔离审计"),
        package(rollback_path, "41真实灰度回滚预案", "是否满足灰度前回滚预案要求"),
        package(whitelist_path, "42白名单试运行", "是否满足灰度试运行材料要求"),
        package(human_path, "43人工确认单", "是否具备提交人工确认条件"),
        package(receipt_path, "45确认回执登记", "是否具备等待人工确认登记条件"),
        package(guard_path, "46未确认拦截", "是否启用未确认拦截"),
        package(final_gate_path, "36真实灰度最终闸口", "是否允许真实灰度"),
        package(plan_path, "236灰度准入与停止开关方案", "允许真实发送"),
    ]
    all_exist = all(item["存在"] for item in packages)
    positive_packages_ok = all(
        item["通过"] is True
        for item in packages
        if item["名称"] not in {"36真实灰度最终闸口", "236灰度准入与停止开关方案"}
    )
    final_gate_blocked = final_gate.get("是否允许真实灰度") is False
    plan_blocked = (
        plan.get("允许真实发送") is False
        and plan.get("允许n8n启用") is False
        and plan.get("允许服务重启") is False
    )
    receipt_unconfirmed = receipt.get("当前确认状态") == "未确认"
    guard_active = guard.get("是否启用未确认拦截") is True
    plan_verify_ok = plan_verify.get("结论") == "通过" and plan_verify.get("失败数量") == 0

    actual_actions = plan.get("实际动作", {})
    no_real_actions = all(value is False for value in actual_actions.values())

    ok = all([
        all_exist,
        positive_packages_ok,
        final_gate_blocked,
        plan_blocked,
        receipt_unconfirmed,
        guard_active,
        plan_verify_ok,
        no_real_actions,
    ])
    report = {
        "名称": "股票系统真实发送灰度准入闭环补强报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总结论": "通过" if ok else "需复核",
        "是否允许真实发送": False,
        "是否允许n8n": False,
        "是否允许服务重启": False,
        "补强包": packages,
        "闸口结论": {
            "补强包全部存在": all_exist,
            "正向准入材料均通过": positive_packages_ok,
            "最终闸口仍拦截真实灰度": final_gate_blocked,
            "236方案继续阻断真实发送n8n服务重启": plan_blocked,
            "人工确认状态": receipt.get("当前确认状态", "未知"),
            "未确认拦截生效": guard_active,
            "236验收通过": plan_verify_ok,
        },
        "实际动作": {
            **actual_actions,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启正式服务": False,
        },
        "下一步交接": [
            "当前已具备真实发送前材料闭环，但最终闸口仍明确不允许真实灰度。",
            "若未来要真实发送，必须先把45确认回执从未确认变为已确认，并重新生成36最终闸口；本轮不做该动作。",
            "若未来要接n8n，必须独立生成并验收n8n接入包；本轮不导入、不激活、不触发n8n。",
            "如果要回滚准入材料，只需保留当前最新包并回退到本轮前历史包；未发生真实发送，所以无外部消息回滚。",
        ],
    }
    write_json(OUT_DIR / "股票系统真实发送灰度准入闭环补强报告_最新.json", report)
    write_text(OUT_DIR / "股票系统真实发送灰度准入闭环补强报告_最新.md", build_markdown(report))
    print(json.dumps({
        "状态": report["总结论"],
        "补强包数量": len(packages),
        "最终闸口允许真实灰度": final_gate.get("是否允许真实灰度"),
        "输出": str(OUT_DIR / "股票系统真实发送灰度准入闭环补强报告_最新.md"),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
