# -*- coding: utf-8 -*-
"""
名称：生成公司概况核验导入预览.py
作用：读取公司概况人工核验模板，校验“已核验”记录并生成导入公司经营快照/公司品质档案的差异预览。
触发方式：python 生成公司概况核验导入预览.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读核验模板和正式档案；只写03数据/173公司概况导入预览；不覆盖正式档案；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-company-profile-import-preview
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_PROFILE_FIELDS = ["核心业务", "行业地位", "主营产品", "主要客户或下游", "未来方向"]
REQUIRED_SOURCE_FIELDS = ["来源类型", "来源名称", "来源日期", "来源路径或URL"]


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


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")).strip(): item for item in items if item.get("代码")}


def missing_fields(data: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if not str(data.get(field, "")).strip()]


def record_fingerprint(item: dict[str, Any]) -> str:
    payload = {
        "待填写": item.get("待填写"),
        "证据来源": item.get("证据来源"),
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
    if item.get("核验状态") != "已核验":
        errors.append("核验状态不是已核验")
    profile = item.get("待填写") if isinstance(item.get("待填写"), dict) else {}
    source = item.get("证据来源") if isinstance(item.get("证据来源"), dict) else {}
    profile_missing = missing_fields(profile, REQUIRED_PROFILE_FIELDS)
    source_missing = missing_fields(source, REQUIRED_SOURCE_FIELDS)
    if profile_missing:
        errors.append("公司概况缺字段：" + "、".join(profile_missing))
    if source_missing:
        errors.append("证据来源缺字段：" + "、".join(source_missing))
    if not str(item.get("核验人", "")).strip():
        errors.append("缺核验人")
    if not str(item.get("核验日期", "")).strip():
        errors.append("缺核验日期")
    return not errors, errors


def build_diff(item: dict[str, Any], snapshot: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    new_profile = item.get("待填写") if isinstance(item.get("待填写"), dict) else {}
    old_snapshot_profile = snapshot.get("公司概况") if isinstance(snapshot.get("公司概况"), dict) else {}
    old_quality_profile = quality.get("公司概况") if isinstance(quality.get("公司概况"), dict) else {}
    fields = []
    for field in REQUIRED_PROFILE_FIELDS:
        fields.append({
            "字段": field,
            "经营快照原值": old_snapshot_profile.get(field, "未找到"),
            "品质档案原值": old_quality_profile.get(field, "未找到"),
            "拟导入值": new_profile.get(field, ""),
        })
    return {
        "代码": item.get("代码"),
        "展示代码": item.get("展示代码"),
        "名称": item.get("名称"),
        "字段差异": fields,
        "证据来源": item.get("证据来源"),
        "核验人": item.get("核验人"),
        "核验日期": item.get("核验日期"),
        "人工备注": item.get("人工备注", ""),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 公司概况核验导入预览 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 模板股票数：{report['模板股票数']}",
        f"- 已核验且可导入预览：{report['可导入数量']}",
        f"- 已导入且未变化：{report['已导入数量']}",
        f"- 未通过校验：{report['未通过数量']}",
        "- 本脚本只生成预览，不覆盖正式档案。",
        "",
        "## 二、可导入预览",
        "",
    ]
    if not report["可导入预览"]:
        lines.append("- 暂无。")
    for item in report["可导入预览"]:
        lines.extend([
            f"### {item.get('名称')}({item.get('代码')})",
            "",
            f"- 证据来源：{item.get('证据来源')}",
            f"- 核验：{item.get('核验人')} / {item.get('核验日期')}",
            "",
            "| 字段 | 原经营快照 | 原品质档案 | 拟导入值 |",
            "|---|---|---|---|",
        ])
        for diff in item["字段差异"]:
            lines.append(
                f"| {diff['字段']} | {diff['经营快照原值']} | {diff['品质档案原值']} | {diff['拟导入值']} |"
            )
        lines.append("")

    lines.extend(["## 三、未通过校验", ""])
    if not report["未通过记录"]:
        lines.append("- 暂无。")
    for item in report["未通过记录"][:50]:
        lines.append(f"- {item.get('名称')}({item.get('代码')})：{'；'.join(item.get('错误', []))}")

    lines.extend(["", "## 四、已导入且未变化", ""])
    if not report["已导入记录"]:
        lines.append("- 暂无。")
    for item in report["已导入记录"][:50]:
        lines.append(f"- {item.get('名称')}({item.get('代码')})：{item.get('导入时间', '已导入')}")

    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 只读核验模板和正式档案。",
        "- 只写导入预览，不覆盖正式档案。",
        "- 不触发n8n，不发送企业微信，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    template_path = root / "03数据" / "172公司概况人工核验模板" / "公司概况人工核验模板_最新.json"
    snapshot_path = root / "03数据" / "166公司经营快照" / "公司经营快照_最新.json"
    quality_path = root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json"
    template_data = load_json(template_path, {})
    snapshot_data = load_json(snapshot_path, {})
    quality_data = load_json(quality_path, {})

    template_items = template_data.get("核验模板", []) if isinstance(template_data, dict) else []
    snapshot_map = index_by_code(snapshot_data.get("股票快照", []) if isinstance(snapshot_data, dict) else [])
    quality_map = index_by_code(quality_data.get("股票档案", []) if isinstance(quality_data, dict) else [])

    importable = []
    rejected = []
    imported = []
    for item in template_items:
        if already_imported(item):
            imported.append({
                "代码": item.get("代码"),
                "展示代码": item.get("展示代码"),
                "名称": item.get("名称"),
                "导入时间": item.get("正式导入状态", {}).get("导入时间"),
            })
            continue
        ok, errors = validate_item(item)
        if ok:
            importable.append(build_diff(item, snapshot_map.get(item.get("代码"), {}), quality_map.get(item.get("代码"), {})))
        else:
            rejected.append({
                "代码": item.get("代码"),
                "展示代码": item.get("展示代码"),
                "名称": item.get("名称"),
                "错误": errors,
            })

    report = {
        "名称": "公司概况核验导入预览",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成公司概况核验导入预览.py",
        "输入模板": str(template_path),
        "模板股票数": len(template_items),
        "可导入数量": len(importable),
        "已导入数量": len(imported),
        "未通过数量": len(rejected),
        "可导入预览": importable,
        "已导入记录": imported,
        "未通过记录": rejected,
        "安全边界": {
            "是否覆盖公司经营快照": False,
            "是否覆盖公司品质档案": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "173公司概况导入预览"
    output_json = output_dir / f"公司概况核验导入预览_{stamp}.json"
    output_md = output_dir / f"公司概况核验导入预览_{stamp}.md"
    latest_json = output_dir / "公司概况核验导入预览_最新.json"
    latest_md = output_dir / "公司概况核验导入预览_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "可导入数量": len(importable),
        "未通过数量": len(rejected),
        "预览": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
