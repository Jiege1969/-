# -*- coding: utf-8 -*-
"""
名称：验证柏基长期成长框架融合.py
作用：验收柏基长期成长分析框架是否已接入股票系统配置、文档和单股报告生成器。
触发方式：python 验证柏基长期成长框架融合.py
安全边界：只读配置、文档和脚本；只写03数据/运行验收报告；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"项目": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 柏基长期成长框架融合验收 - {report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 验收项",
        "",
    ]
    for item in report["验收项"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['项目']}：{mark}。{item.get('说明', '')}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 本次验收未发送企业微信。",
        "- 本次验收未触发 n8n。",
        "- 本次验收未调用券商接口。",
        "- 本次验收未自动交易。",
        "- 柏基框架只作为长期成长质量复核层，不改变系统评分。",
    ])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    framework_path = ROOT / "01配置" / "柏基长期成长分析框架_v1.json"
    frontend_path = ROOT / "01配置" / "股票前台输出标准_v2.json"
    template_path = ROOT / "01配置" / "股票报告模板.json"
    method_doc_path = ROOT / "07文档" / "股票分析方法与报告标准_v2_结合现有系统.md"
    assistant_path = ROOT / "02脚本" / "股票助手入口.py"

    framework = load_json(framework_path)
    frontend = load_json(frontend_path)
    template = load_json(template_path)
    method_doc = load_text(method_doc_path)
    assistant_text = load_text(assistant_path)
    compile_ok = True
    compile_detail = ""
    try:
        py_compile.compile(str(assistant_path), doraise=True)
    except Exception as exc:  # pragma: no cover - diagnostic path
        compile_ok = False
        compile_detail = str(exc)

    checks = [
        check(framework.get("名称") == "柏基长期成长分析框架", "框架配置文件存在", str(framework_path)),
        check("加速回报定律关键词" in framework, "配置包含加速回报三定律关键词", "摩尔/弗拉特利/莱特"),
        check("长期主题关键词" in framework, "配置包含欧拉图长期主题关键词", "多主题重叠识别"),
        check("尽调十问四模块" in framework, "配置包含尽调十问四模块", "市场、文化、护城河、财务纪律"),
        check("魔鬼代言人" in json.dumps(framework, ensure_ascii=False), "配置包含魔鬼代言人反证机制", "反确认偏误"),
        check("柏基长期成长框架" in frontend, "前台输出标准已登记柏基框架", str(frontend_path)),
        check("禁用口径" in frontend.get("柏基长期成长框架", {}), "前台标准包含禁用口径", "不输出指令化长期买卖话术"),
        check("柏基长期成长框架" in template, "报告模板已登记柏基框架", str(template_path)),
        check("长期成长质量框架" in assistant_text, "单股报告生成器包含长期成长质量章节", str(assistant_path)),
        check("build_baillie_growth_assessment" in assistant_text, "单股报告生成器包含框架评估函数", "只做定性雷达，不改评分"),
        check("不改变系统评分" in assistant_text, "运行入口保留不改变评分边界", "非交易、非评分替代"),
        check("柏基长期成长框架接入" in method_doc, "分析方法文档已写入接入说明", str(method_doc_path)),
        check(compile_ok, "股票助手入口语法编译通过", compile_detail),
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "柏基长期成长框架融合验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "验收项": checks,
        "安全边界": {
            "是否发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否改变系统评分": False,
        },
    }

    output_dir = ROOT / "03数据" / "运行验收"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_json = output_dir / f"柏基长期成长框架融合验收_{stamp}.json"
    output_md = output_dir / f"柏基长期成长框架融合验收_{stamp}.md"
    latest_json = output_dir / "柏基长期成长框架融合验收_最新.json"
    latest_md = output_dir / "柏基长期成长框架融合验收_最新.md"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output_json.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    markdown = build_markdown(report)
    output_md.write_text(markdown, encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
