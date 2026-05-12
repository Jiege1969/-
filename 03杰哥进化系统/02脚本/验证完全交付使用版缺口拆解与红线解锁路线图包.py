# -*- coding: utf-8 -*-
"""验证完全交付使用版缺口拆解与红线解锁路线图候选包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "64完全交付使用版缺口拆解与红线解锁路线图包"
LOG_DIR = ROOT / "04日志" / "完全交付使用版缺口拆解与红线解锁路线图包验收"

PACKAGE_JSON = DATA_DIR / "完全交付使用版缺口拆解与红线解锁路线图包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版缺口拆解与红线解锁路线图包_最新.md"
MATRIX_CSV = DATA_DIR / "完全交付使用版缺口拆解矩阵_最新.csv"
CHECK_JSON = DATA_DIR / "完全交付使用版缺口路线图只读核对_最新.json"
VERIFY_JSON = LOG_DIR / "验证完全交付使用版缺口拆解与红线解锁路线图包_最新.json"
VERIFY_MD = LOG_DIR / "验证完全交付使用版缺口拆解与红线解锁路线图包_最新.md"

REQUIRED_MODULES = ["企业微信真实发送", "n8n编排", "券商交易", "税局财税接入", "视频真实渲染发布", "正式规则治理", "长周期稳定样本"]
FORBIDDEN_OPEN_VALUES = {"已开放", "开放", "允许真实执行", True}


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


def check_file(path: Path) -> dict[str, Any]:
    return {"检查项": f"文件存在：{path.name}", "结果": "pass" if path.exists() else "fail", "路径": str(path)}


def validate_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    modules = package.get("缺口模块", [])
    module_names = [item.get("模块") for item in modules]
    for name in REQUIRED_MODULES:
        results.append({"检查项": f"必需模块：{name}", "结果": "pass" if name in module_names else "fail"})
    for item in modules:
        name = item.get("模块", "未知模块")
        required_fields = ["当前缺口", "解锁前置", "风险等级", "是否近期需要", "预计工作量档位", "红线状态"]
        missing = [field for field in required_fields if not item.get(field)]
        results.append({"检查项": f"字段完整：{name}", "结果": "pass" if not missing else "fail", "缺失字段": missing})
        redline_closed = item.get("红线状态") not in FORBIDDEN_OPEN_VALUES and "开放" in str(item.get("红线状态"))
        if item.get("红线状态") == "未开放":
            redline_closed = True
        if item.get("红线状态") == "不涉及开放，仅做只读样本":
            redline_closed = True
        results.append({"检查项": f"红线未开放：{name}", "结果": "pass" if redline_closed else "fail", "红线状态": item.get("红线状态")})
    boundary = package.get("安全边界", {})
    boundary_closed = boundary.get("仅生成候选路线图") is True and all(
        value is False for key, value in boundary.items() if key != "仅生成候选路线图"
    )
    results.append({"检查项": "安全边界全部关闭", "结果": "pass" if boundary_closed else "fail", "安全边界": boundary})
    nature_ok = "候选" in package.get("性质", "") and "不开放" in package.get("性质", "")
    results.append({"检查项": "候选包性质明确", "结果": "pass" if nature_ok else "fail", "性质": package.get("性质")})
    return results


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 完全交付使用版缺口拆解与红线解锁路线图包验证",
        "",
        f"- 验证时间：{report['验证时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 通过/总数：{report['汇总']['通过']} / {report['汇总']['总数']}",
        "",
        "| 检查项 | 结果 |",
        "| --- | --- |",
    ]
    for item in report["检查结果"]:
        lines.append(f"| {item['检查项']} | {item['结果']} |")
    lines.extend(["", "## 验证结论", "", report["验证结论"]])
    return "\n".join(lines)


def main() -> int:
    results = [check_file(path) for path in [PACKAGE_JSON, PACKAGE_MD, MATRIX_CSV, CHECK_JSON]]
    if PACKAGE_JSON.exists():
        results.extend(validate_package(read_json(PACKAGE_JSON)))
    if CHECK_JSON.exists():
        check = read_json(CHECK_JSON)
        results.append({"检查项": "只读核对通过", "结果": "pass" if check.get("总体状态") == "pass" else "fail", "核对状态": check.get("总体状态")})
        results.append({"检查项": "只读核对红线结论", "结果": "pass" if check.get("红线结论") == "未开放任何红线" else "fail", "红线结论": check.get("红线结论")})
    passed = sum(1 for item in results if item["结果"] == "pass")
    report = {
        "名称": "完全交付使用版缺口拆解与红线解锁路线图包验证",
        "验证时间": now(),
        "总体状态": "pass" if passed == len(results) else "fail",
        "汇总": {"总数": len(results), "通过": passed, "失败": len(results) - passed},
        "检查结果": results,
        "验证结论": "候选包结构完整，红线保持关闭，可作为后续人工评审输入。" if passed == len(results) else "候选包仍有缺口，不能作为验收通过材料。",
    }
    write_json(VERIFY_JSON, report)
    write_text(VERIFY_MD, build_markdown(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": passed, "失败": len(results) - passed, "输出": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
