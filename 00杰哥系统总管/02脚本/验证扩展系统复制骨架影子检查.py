# -*- coding: utf-8 -*-
"""
名称：验证扩展系统复制骨架影子检查.py
作用：验收扩展系统复制骨架影子检查报告是否覆盖骨架、声明项、四系统职责、安全边界和缺口登记。
触发方式：python 验证扩展系统复制骨架影子检查.py
安全边界：只读影子检查报告；只写验收报告；不创建目录；不改业务文件；不接入入口；不触发n8n；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "扩展系统复制骨架影子检查_最新.json"
REPORT_MD = OUT_DIR / "扩展系统复制骨架影子检查_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    report = load_json(REPORT_JSON)
    md = load_text(REPORT_MD)
    text = json.dumps(report, ensure_ascii=False) + "\n" + md
    skeleton = report.get("最小骨架", [])
    required_skeleton = ["01配置", "02脚本", "03数据", "04日志", "05入口工具", "07文档"]
    declarations = report.get("新系统必须声明", [])
    responsibilities = report.get("四系统职责继承", {})
    forbidden = report.get("复制规则摘要", {}).get("禁止复制", [])
    safety = report.get("安全边界", {})
    business_status = report.get("现有扩展业务系统骨架", [])
    output_location = Path(report.get("输出位置", ""))

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "影子检查 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(all(item in skeleton for item in required_skeleton), "最小骨架覆盖标准目录", ",".join(required_skeleton)),
        check(report.get("股票成品骨架", {}).get("是否完整") is True, "股票成品骨架完整", ""),
        check(len(business_status) >= 4, "现有扩展业务系统已被识别", str(len(business_status))),
        check(len(declarations) >= 10 and all(item in declarations for item in ["业务目标", "用户入口", "验收口径", "状态面板", "不能影响哪些现有系统"]), "新系统必须声明项完整", ""),
        check(all(key in responsibilities for key in ["00总管", "01智能", "02扩展", "03进化"]), "四系统职责继承完整", ""),
        check("股票系统踩坑过程" in forbidden and "旧端口旧入口" in forbidden, "禁止复制项保留关键红线", ""),
        check("不能影响股票系统正式使用" in text, "验收红线包含不影响股票系统", ""),
        check("税收业务系统仍按暂停口径处理" in text, "税收业务暂停口径已登记", ""),
        check("不自动迁移或改名" in text or "未迁移或改名任何现有业务目录" in text, "目录缺口只登记不迁移", ""),
        check(output_location == OUT_DIR, "输出位置在00总管运行状态目录", str(output_location)),
        check(all(value is False for value in safety.values()), "安全边界全部为False", json.dumps(safety, ensure_ascii=False)),
        check("未创建新业务正式目录" in text and "未接入正式入口" in text, "明确未创建正式目录且未接入入口", ""),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    validation = {
        "名称": "扩展系统复制骨架影子检查验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "创建新业务正式目录": False,
            "写扩展系统正式文件": False,
            "接入正式入口": False,
            "新增公网入口": False,
            "新增企业微信入口": False,
            "新增n8n工作流": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "扩展系统复制骨架影子检查验收_最新.json"
    latest_md = OUT_DIR / "扩展系统复制骨架影子检查验收_最新.md"
    lines = [
        "# 扩展系统复制骨架影子检查验收",
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
    write_json(latest_json, validation)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": validation["结论"],
        "通过数量": validation["通过数量"],
        "失败数量": validation["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
