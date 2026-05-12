# -*- coding: utf-8 -*-
"""
名称：验证旧路径口径全局巡检.py
作用：验收旧路径口径全局巡检报告是否确认旧根目录不存在、无 Docker 旧挂载、无未标记旧路径风险。
触发方式：python 验证旧路径口径全局巡检.py
安全边界：只读巡检报告；只写验收报告；不删除文件、不移除容器、不改入口、不发送企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "旧路径口径全局巡检_最新.json"
REPORT_MD = OUT_DIR / "旧路径口径全局巡检_最新.md"
VALIDATION_JSON = OUT_DIR / "旧路径口径全局巡检验收_最新.json"
VALIDATION_MD = OUT_DIR / "旧路径口径全局巡检验收_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
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


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    report = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    docker_scan = report.get("Docker巡检", {})
    safety = report.get("安全边界", {})
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "旧路径口径巡检报告存在", str(REPORT_JSON)),
        check(report.get("结论") == "通过", "巡检结论通过", report.get("结论", "")),
        check(report.get("当前统一根路径") == str(ROOT), "当前统一根路径正确", report.get("当前统一根路径", "")),
        check(report.get("旧D盘根目录存在") is False, "旧D盘根目录不存在", report.get("旧D盘根目录存在")),
        check(report.get("正式智能系统路径存在") is True, "正式智能系统路径存在", report.get("正式智能系统路径存在")),
        check(report.get("旧路径口径风险数量") == 0, "无未标记旧路径口径风险", report.get("旧路径口径风险", [])),
        check(docker_scan.get("旧挂载命中数量") == 0, "Docker 无旧路径挂载命中", docker_scan),
        check("历史记录可保留为根因证据" in "\n".join(report.get("处理建议", [])), "处理建议保留历史证据但防误判", ""),
        check(all(value is False for value in safety.values()), "安全边界均为False", safety),
        check("不删除文件" in md and "不移除容器" in md and "不修改入口" in md, "Markdown 记录只读安全边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "旧路径口径全局巡检验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "删除文件": False,
            "移除容器": False,
            "修改入口": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 旧路径口径全局巡检验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(VALIDATION_JSON, validation)
    write_text(VALIDATION_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": validation["结论"], "通过数量": validation["通过数量"], "失败数量": validation["失败数量"], "报告": str(VALIDATION_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
