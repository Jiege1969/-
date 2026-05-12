# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路巡检整改闭环阶段总回传"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录_最新.md"

INDEX_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段收口索引_最新.json"
TOTAL_JSON = ROOT / "03数据" / "21当前阶段收口" / "税收系统当前阶段收口验收与下一步队列_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    index = load_json(INDEX_JSON)
    total = load_json(TOTAL_JSON)

    record = {
        "名称": "税收企业微信人工复核链路巡检整改闭环阶段总回传记录",
        "生成时间": now,
        "资产身份": "税务线内部对齐回传记录，只供总管只读吸收；不是正式入口放行，不写正式库，不是真实发送记录，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "本轮做了什么": [
            "汇总巡检整改闭环阶段收口索引。",
            "汇总当前阶段总收口状态。",
            "形成税务线内部阶段总回传记录，供总管只读整合参考。",
        ],
        "来源文件": {
            "巡检整改闭环阶段收口索引": str(INDEX_JSON),
            "当前阶段总收口": str(TOTAL_JSON),
        },
        "阶段摘要": {
            "巡检整改闭环模块数量": index.get("模块数量", 0),
            "巡检整改闭环通过数量": index.get("通过数量", 0),
            "巡检整改闭环缺失数量": index.get("缺失数量", 0),
            "巡检整改闭环失败数量": index.get("失败数量", 0),
            "当前阶段总收口报告数量": total.get("验收报告数量", 0),
            "当前阶段总收口通过数量": total.get("通过数量", 0),
            "当前阶段总收口缺失数量": total.get("缺失数量", 0),
            "当前阶段总收口失败数量": total.get("失败数量", 0),
        },
        "回传口径": {
            "风险等级": "W2低风险",
            "是否触发真实系统": False,
            "是否需要总管整合": True,
            "总管整合方式": "只读吸收本回传记录；如需修改总管面板、正式入口或公共企业微信配置，应由总管线判断。",
            "是否允许自动实施总管修改": False,
        },
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
        "总管回传要点": [
            "人工复核链路巡检整改闭环已形成阶段索引。",
            "当前全部产物仍为dry-run、待复核分析草案与政策证据底座支撑材料。",
            "真实发送、凭据接入、公共路由修改、服务启动和正式税务意见均未实施。",
        ],
        "下一步建议": [
            "生成税收企业微信人工复核链路巡检整改闭环持续巡检入口说明。",
        ],
    }
    OUT_JSON.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改闭环阶段总回传记录",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：税务线内部对齐回传记录，只供总管只读吸收；不是正式入口放行，不写正式库，不是真实发送记录，不是正式税务结论。",
        "",
        "## 阶段摘要",
        "",
    ]
    for key, value in record["阶段摘要"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 回传口径", ""])
    for key, value in record["回传口径"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in record["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 总管回传要点", ""])
    for item in record["总管回传要点"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步建议", ""])
    for item in record["下一步建议"]:
        lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    copy_latest(OUT_JSON, LATEST_JSON)
    copy_latest(OUT_MD, LATEST_MD)
    print(json.dumps({"状态": "完成", "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
