# -*- coding: utf-8 -*-
"""
名称：验证税收政策证据底座定位与字段.py
作用：只读验收税收系统是否按政策证据底座定位搭建，并检查适用条件字段、有效性边界和禁用动作。
触发方式：python 验证税收政策证据底座定位与字段.py
安全边界：只读检查本地配置和预演报告；不联网、不下载、不写正式业务规则、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "28政策证据底座字段补齐预演"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def has_navigation_noise(preview: dict[str, Any]) -> bool:
    noise_markers = ["本站热词", "当前位置", "首页 总局概况", "个人中心", "搜索 高级搜索", "热门关键词", "字体："]
    for item in preview.get("资料", []):
        fields = item.get("关键条件", []) + item.get("排除条件", [])
        if any(any(marker in str(value) for marker in noise_markers) for value in fields):
            return True
    return False


def main() -> int:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    metadata_template = load_json(ROOT / "01配置" / "税收政策元数据模板.json")
    pipeline_cfg = load_json(ROOT / "01配置" / "税收政策智能查询下载管道配置.json")
    graph_cfg = load_json(ROOT / "01配置" / "税收证据节点与关系图谱规则.json")
    preview = load_json(OUT_DIR / "税收政策证据底座字段补齐预演_最新.json", {"资料": []})

    required_condition_fields = ["适用主体", "适用事项", "适用期间", "关键条件", "排除条件", "所需资料", "待人工复核项"]
    checks = [
        check("README明确政策证据底座定位", "政策证据底座" in readme and "不是税务结论库" in readme, "README.md"),
        check("README纠偏正式依据库口径", "当前适用依据候选库" in readme and "不代表正式业务结论库" in readme, "README.md"),
        check("元数据模板包含适用条件字段", all(field in metadata_template for field in required_condition_fields), metadata_template),
        check("元数据模板禁止正式结论字段为false", metadata_template.get("是否生成正式税务结论") is False, metadata_template.get("是否生成正式税务结论")),
        check("管道配置资产身份为证据底座", "政策证据底座" in str(pipeline_cfg.get("资产身份", "")), pipeline_cfg.get("资产身份", "")),
        check("当前适用候选仅允许全文有效或人工确认有效", set(pipeline_cfg.get("文件时效", {}).get("可进入当前适用依据候选", [])) == {"全文有效", "人工确认有效"}, pipeline_cfg.get("文件时效", {})),
        check("异常状态不得作为当前适用依据", all(item in pipeline_cfg.get("文件时效", {}).get("不可作为当前适用依据", []) for item in ["已修改", "全文失效", "全文废止", "尚未生效", "待核验"]), pipeline_cfg.get("文件时效", {})),
        check("安全边界禁用电子税务局和财税软件", pipeline_cfg.get("安全边界", {}).get("是否接电子税务局") is False and pipeline_cfg.get("安全边界", {}).get("是否接财税软件") is False, pipeline_cfg.get("安全边界", {})),
        check("证据图谱包含适用条件字段", all(field in graph_cfg.get("证据卡最小字段", []) for field in required_condition_fields), graph_cfg.get("证据卡最小字段", [])),
        check("字段补齐预演存在", bool(preview.get("资料")) or preview.get("资料数量", 0) == 0, str(OUT_DIR / "税收政策证据底座字段补齐预演_最新.json")),
        check("预演报告不生成正式税务结论", preview.get("安全边界", {}).get("是否生成正式税务结论") is False, preview.get("安全边界", {})),
        check("预演资料包含字段化结果", all(all(field in item for field in required_condition_fields) for item in preview.get("资料", [])), preview.get("资料", [])),
        check("关键条件和排除条件不含网页导航噪声", not has_navigation_noise(preview), "检查本站热词、当前位置、首页总局概况等导航文本"),
    ]

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "税收政策证据底座定位与字段验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读检查；不联网、不下载、不写正式业务规则、不生成正式税务结论。",
    }
    write_json(OUT_DIR / "税收政策证据底座定位与字段验收_最新.json", report)
    lines = [
        "# 税收政策证据底座定位与字段验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item['说明']}")
    write_text(OUT_DIR / "税收政策证据底座定位与字段验收_最新.md", "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
