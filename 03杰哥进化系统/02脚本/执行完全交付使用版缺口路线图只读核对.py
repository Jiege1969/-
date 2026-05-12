# -*- coding: utf-8 -*-
"""执行完全交付使用版缺口路线图只读核对。

仅读取候选包并生成核对记录，不触发任何真实外部动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "64完全交付使用版缺口拆解与红线解锁路线图包"
LOG_DIR = ROOT / "04日志" / "完全交付使用版缺口拆解与红线解锁路线图包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版缺口拆解与红线解锁路线图包_最新.json"
CHECK_JSON = DATA_DIR / "完全交付使用版缺口路线图只读核对_最新.json"
CHECK_MD = DATA_DIR / "完全交付使用版缺口路线图只读核对_最新.md"
CHECK_LOG = LOG_DIR / "执行完全交付使用版缺口路线图只读核对_最新.json"

REQUIRED_MODULES = ["企业微信真实发送", "n8n编排", "券商交易", "税局财税接入", "视频真实渲染发布", "正式规则治理", "长周期稳定样本"]
HIGH_RISK_MODULES = {"企业微信真实发送", "n8n编排", "券商交易", "税局财税接入", "视频真实渲染发布"}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def evaluate_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    modules = {item.get("模块"): item for item in package.get("缺口模块", [])}
    results: list[dict[str, Any]] = []
    for name in REQUIRED_MODULES:
        item = modules.get(name)
        if not item:
            results.append({"核对项": name, "结果": "fail", "说明": "缺少模块"})
            continue
        has_preconditions = bool(item.get("解锁前置"))
        has_risk = item.get("风险等级") in {"中", "中高", "高", "极高"}
        has_recent_need = bool(item.get("是否近期需要"))
        has_effort = item.get("预计工作量档位") in {"S", "S-M", "M", "L", "XL"}
        redline_closed = item.get("红线状态") in {"未开放", "不涉及开放，仅做只读样本"}
        high_risk_closed = name not in HIGH_RISK_MODULES or item.get("红线状态") == "未开放"
        passed = all([has_preconditions, has_risk, has_recent_need, has_effort, redline_closed, high_risk_closed])
        results.append(
            {
                "核对项": name,
                "结果": "pass" if passed else "fail",
                "说明": {
                    "有解锁前置": has_preconditions,
                    "有风险等级": has_risk,
                    "有近期需要判断": has_recent_need,
                    "有工作量档位": has_effort,
                    "红线保持关闭": redline_closed,
                    "高风险模块未开放": high_risk_closed,
                },
            }
        )
    boundary = package.get("安全边界", {})
    boundary_pass = (
        boundary.get("仅生成候选路线图") is True
        and all(value is False for key, value in boundary.items() if key != "仅生成候选路线图")
    )
    results.append({"核对项": "安全边界未开放", "结果": "pass" if boundary_pass else "fail", "说明": boundary})
    nature_pass = "候选" in package.get("性质", "") and "不开放" in package.get("性质", "")
    results.append({"核对项": "候选性质声明", "结果": "pass" if nature_pass else "fail", "说明": package.get("性质", "")})
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 完全交付使用版缺口路线图只读核对",
        "",
        f"- 核对时间：{report['核对时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
        "",
        "| 核对项 | 结果 |",
        "| --- | --- |",
    ]
    for item in report["核对结果"]:
        lines.append(f"| {item['核对项']} | {item['结果']} |")
    lines.extend(["", "## 说明", "", "本核对为只读核对，不真实发送、不触发、不交易、不登录、不渲染发布、不转正式规则。"])
    return "\n".join(lines)


def main() -> int:
    package = read_json(PACKAGE_JSON)
    results = evaluate_package(package)
    passed = sum(1 for item in results if item["结果"] == "pass")
    report = {
        "名称": "完全交付使用版缺口路线图只读核对",
        "核对时间": now(),
        "总体状态": "pass" if passed == len(results) else "fail",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "候选包路径": str(PACKAGE_JSON),
        "核对结果": results,
        "红线结论": "未开放任何红线",
    }
    write_json(CHECK_JSON, report)
    write_text(CHECK_MD, build_markdown(report))
    write_json(CHECK_LOG, report)
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "输出": str(CHECK_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
