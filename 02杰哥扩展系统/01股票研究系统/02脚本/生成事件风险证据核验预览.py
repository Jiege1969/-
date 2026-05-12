# -*- coding: utf-8 -*-
"""
名称：生成事件风险证据核验预览.py
作用：校验事件风险证据人工核验模板，生成可进入前台风险表达的差异预览。
安全边界：只读核验模板；只写 03数据/176事件风险证据核验预览；不覆盖正式档案、不改推荐、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "材料标题",
    "材料发布日期",
    "材料来源名称",
    "材料来源URL",
    "事件类型",
    "风险等级",
    "是否发现新增重大风险",
    "是否支持当前前台结论",
    "建议前台处理",
    "核验摘要",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def record_fingerprint(item: dict[str, Any]) -> str:
    payload = {
        "人工填写": item.get("人工填写"),
        "核验人": item.get("核验人"),
        "核验日期": item.get("核验日期"),
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def already_imported(item: dict[str, Any]) -> bool:
    status = item.get("正式导入状态") if isinstance(item.get("正式导入状态"), dict) else {}
    return status.get("状态") == "已导入" and status.get("记录指纹") == record_fingerprint(item)


def validate_item(item: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    filled = item.get("人工填写") if isinstance(item.get("人工填写"), dict) else {}
    if filled.get("核验状态") != "已核验":
        errors.append("核验状态不是已核验")
    for field in REQUIRED_FIELDS:
        if not str(filled.get(field, "")).strip():
            errors.append(f"缺少{field}")
    if not str(item.get("核验人", "")).strip():
        errors.append("缺少核验人")
    if not str(item.get("核验日期", "")).strip():
        errors.append("缺少核验日期")
    return not errors, errors


def build_preview_item(item: dict[str, Any]) -> dict[str, Any]:
    filled = item["人工填写"]
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "行业": item.get("行业"),
        "事件类型": filled.get("事件类型"),
        "风险等级": filled.get("风险等级"),
        "是否发现新增重大风险": filled.get("是否发现新增重大风险"),
        "是否支持当前前台结论": filled.get("是否支持当前前台结论"),
        "建议前台处理": filled.get("建议前台处理"),
        "核验摘要": filled.get("核验摘要"),
        "证据来源": {
            "材料标题": filled.get("材料标题"),
            "材料发布日期": filled.get("材料发布日期"),
            "材料来源名称": filled.get("材料来源名称"),
            "材料来源URL": filled.get("材料来源URL"),
        },
        "核验人": item.get("核验人"),
        "核验日期": item.get("核验日期"),
        "备注": item.get("备注", ""),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 事件与风险证据核验预览 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 模板股票数：{report['模板股票数']}",
        f"- 可进入预览：{report['可预览数量']}",
        f"- 已导入且未变化：{report['已导入数量']}",
        f"- 未通过校验：{report['未通过数量']}",
        "- 本预览只给人工复核使用，不自动改推荐、不自动推送。",
        "",
        "## 二、可预览记录",
        "",
    ]
    if not report["可预览记录"]:
        lines.append("- 暂无。")
    for item in report["可预览记录"]:
        lines.extend([
            f"### {item['名称']}({item['代码']})",
            "",
            f"- 事件类型：{item['事件类型']}",
            f"- 风险等级：{item['风险等级']}",
            f"- 建议前台处理：{item['建议前台处理']}",
            f"- 核验摘要：{item['核验摘要']}",
            f"- 证据来源：{item['证据来源']['材料来源名称']} / {item['证据来源']['材料标题']}",
            "",
        ])
    lines.extend(["## 三、未通过校验", ""])
    if not report["未通过记录"]:
        lines.append("- 暂无。")
    for item in report["未通过记录"]:
        lines.append(f"- {item.get('名称')}({item.get('代码')})：{'；'.join(item.get('错误', []))}")
    lines.extend(["", "## 四、已导入且未变化", ""])
    if not report["已导入记录"]:
        lines.append("- 暂无。")
    for item in report["已导入记录"]:
        lines.append(f"- {item.get('名称')}({item.get('代码')})：{item.get('导入时间', '已导入')}")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 只生成预览，不覆盖正式档案。",
        "- 不改评分、不改推荐、不真实发送企业微信。",
        "- 不触发 n8n，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    template_path = root / "03数据" / "175事件风险证据人工核验模板" / "事件风险证据人工核验模板_最新.json"
    template_data = load_json(template_path, {})
    items = template_data.get("核验模板", []) if isinstance(template_data, dict) else []

    preview = []
    rejected = []
    imported = []
    for item in items:
        if already_imported(item):
            imported.append({
                "代码": item.get("代码"),
                "名称": item.get("名称"),
                "导入时间": item.get("正式导入状态", {}).get("导入时间"),
            })
            continue
        ok, errors = validate_item(item)
        if ok:
            preview.append(build_preview_item(item))
        else:
            rejected.append({"代码": item.get("代码"), "名称": item.get("名称"), "错误": errors})

    report = {
        "名称": "事件与风险证据核验预览",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成事件风险证据核验预览.py",
        "输入模板": str(template_path),
        "模板股票数": len(items),
        "可预览数量": len(preview),
        "已导入数量": len(imported),
        "未通过数量": len(rejected),
        "可预览记录": preview,
        "已导入记录": imported,
        "未通过记录": rejected,
        "安全边界": {
            "是否覆盖正式档案": False,
            "是否改变评分或推荐": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "176事件风险证据核验预览"
    latest_json = output_dir / "事件风险证据核验预览_最新.json"
    latest_md = output_dir / "事件风险证据核验预览_最新.md"
    markdown = build_markdown(report)
    write_json(output_dir / f"事件风险证据核验预览_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(output_dir / f"事件风险证据核验预览_{stamp}.md", markdown)
    write_text(latest_md, markdown)

    print(json.dumps({"状态": "完成", "可预览数量": len(preview), "未通过数量": len(rejected), "预览": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
