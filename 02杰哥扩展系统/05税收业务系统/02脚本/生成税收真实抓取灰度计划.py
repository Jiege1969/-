"""
名称：生成税收真实抓取灰度计划.py
作用：读取税收真实抓取灰度配置，生成只读探测阶段的执行计划、风险边界和人工确认清单。
触发方式：python 生成税收真实抓取灰度计划.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块配置，只写入本模块抓取探测报告；不联网、不下载正文、不入正式政策库。
创建/修改记录：2026-04-26 创建真实抓取攻坚阶段灰度计划脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_plan() -> dict[str, Any]:
    root = module_root()
    config_path = root / "01配置" / "税收真实抓取灰度配置.json"
    config = load_json(config_path)
    output_dir = root / "03数据" / "07抓取探测"
    output_dir.mkdir(parents=True, exist_ok=True)

    switches = config.get("抓取开关", {})
    entries = config.get("官方入口", [])
    tasks = []
    for index, entry in enumerate(entries, start=1):
        tasks.append(
            {
                "序号": index,
                "任务": f"只读探测：{entry.get('名称')}",
                "入口": entry.get("入口"),
                "允许域名": entry.get("允许域名", []),
                "产物": "候选链接清单和连通状态",
                "禁止动作": [
                    "不得写入正式政策目录",
                    "不得写入向量库",
                    "不得触发n8n",
                    "不得企微推送",
                ],
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "配置来源": str(config_path),
        "阶段": config.get("阶段"),
        "执行原则": config.get("总原则", []),
        "抓取开关": switches,
        "任务列表": tasks,
        "人工确认清单": config.get("入库前置门槛", []),
        "阻断规则": config.get("阻断规则", []),
        "是否可进入真实抓取只读探测": bool(switches.get("允许联网探测")) and not bool(switches.get("允许写入正式政策目录")),
        "是否可进入正式入库": False,
        "安全说明": "本计划只允许做官方入口只读探测；正式抓取正文、清洗入库和依据标记必须另行验收。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"税收真实抓取灰度计划_{timestamp}.json"
    latest = output_dir / "税收真实抓取灰度计划_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"task_count": len(tasks), "readonly_probe": report["是否可进入真实抓取只读探测"], "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_plan()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
