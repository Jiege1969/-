# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路巡检整改闭环阶段收口索引"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引_最新.md"

MODULES = [
    ("持续巡检规则", ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则验收_最新.md", ENTRY_DIR / "税收企业微信人工复核链路持续巡检规则_最新.json"),
    ("持续巡检样例演练", ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练验收_最新.md", ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练_最新.json"),
    ("巡检失败整改模板", ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板验收_最新.md", ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板_最新.json"),
    ("巡检整改后再校验清单", ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单验收_最新.md", ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单_最新.json"),
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def report_passed(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "失败数量：0" in text or '"失败数量": 0' in text or "失败数量\": 0" in text


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    module_index = []
    for name, validation_path, data_path in MODULES:
        data = load_json(data_path)
        module_index.append({
            "模块名称": name,
            "数据路径": str(data_path),
            "验收报告路径": str(validation_path),
            "数据是否存在": data_path.exists(),
            "验收报告是否存在": validation_path.exists(),
            "验收是否通过": report_passed(validation_path),
            "是否可作为正式税务结论": False,
            "是否允许真实发送企业微信": False,
            "是否允许修改真实资产": False,
            "资产身份": data.get("资产身份", ""),
        })

    passed = sum(1 for item in module_index if item["验收是否通过"])
    missing = sum(1 for item in module_index if not item["数据是否存在"] or not item["验收报告是否存在"])
    failed = len(module_index) - passed
    report = {
        "名称": "税收企业微信人工复核链路巡检整改闭环阶段收口索引",
        "生成时间": now,
        "资产身份": "税务线本地阶段收口索引，不修改真实资产，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "模块数量": len(module_index),
        "通过数量": passed,
        "缺失数量": missing,
        "失败数量": failed,
        "模块索引": module_index,
        "阶段结论": "通过" if failed == 0 and missing == 0 else "待整改",
        "阶段护栏": [
            "本阶段只完成巡检整改闭环的本地资产闭环。",
            "所有产物均为政策证据底座 / 待复核分析草案支撑材料。",
            "不得把巡检、整改、再校验或阶段收口解释为正式税务意见。",
            "不得真实发送企业微信，不得读取凭据，不得修改总管或公共企业微信配置。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信人工复核链路巡检整改闭环阶段总回传记录。",
        ],
        "安全边界": {
            "是否修改真实资产": False,
            "是否创建自动化任务": False,
            "是否启动或重启服务": False,
            "是否新增或修改端口": False,
            "是否触发n8n": False,
            "是否读取或保存企业微信凭据": False,
            "是否企业微信真实发送": False,
            "是否修改公共企业微信配置": False,
            "是否修改总管文件": False,
            "是否写正式库": False,
            "是否生成正式税务结论": False,
            "是否删除或移动旧资产": False,
        },
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改闭环阶段收口索引",
        "",
        f"- 生成时间：{now}",
        f"- 模块数量：{len(module_index)}",
        f"- 通过数量：{passed}",
        f"- 缺失数量：{missing}",
        f"- 失败数量：{failed}",
        f"- 阶段结论：{report['阶段结论']}",
        "- 资产身份：税务线本地阶段收口索引，不修改真实资产，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "",
        "## 模块索引",
        "",
    ]
    for item in module_index:
        lines.append(f"- {item['模块名称']}：数据存在={item['数据是否存在']}，验收存在={item['验收报告是否存在']}，验收通过={item['验收是否通过']}，路径={item['验收报告路径']}")
    lines.extend(["", "## 阶段护栏", ""])
    for item in report["阶段护栏"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in report["下一步低风险队列"]:
        lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    copy_latest(OUT_JSON, LATEST_JSON)
    copy_latest(OUT_MD, LATEST_MD)
    print(json.dumps({"状态": "完成", "通过数量": passed, "缺失数量": missing, "失败数量": failed, "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
