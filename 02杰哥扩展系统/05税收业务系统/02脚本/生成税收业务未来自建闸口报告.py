# -*- coding: utf-8 -*-
"""
名称：生成税收业务未来自建闸口报告.py
作用：根据税收业务未来自建闸口规则，生成当前税收模块的安全边界和未来自建步骤报告。
触发方式：python 生成税收业务未来自建闸口报告.py
依赖：Python标准库；税收业务未来自建闸口规则.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块规则文件，只写入本模块03数据目录；不联网；不调用大模型；不触发n8n；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建税收业务未来自建闸口报告脚本。
标识：tax-future-self-build-gate-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "税收业务未来自建闸口规则.json"
    rules = load_json(rule_path)
    switches = rules.get("默认开关", {})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模块": "05税收业务系统",
        "阶段": rules.get("阶段"),
        "当前状态": rules.get("当前状态"),
        "规则文件": str(rule_path),
        "允许范围": rules.get("允许范围", []),
        "禁止范围": rules.get("禁止范围", []),
        "默认开关": switches,
        "未来自建步骤": rules.get("未来自建步骤", []),
        "验收标准": rules.get("验收标准", []),
        "本次动作": {
            "是否联网": False,
            "是否调用大模型": False,
            "是否触发n8n": False,
            "是否真实发送": False,
            "是否写正式库": False,
            "是否写旧系统": False,
            "是否执行网站抓取": False,
            "是否提交涉税业务": False
        },
        "结论": "税收业务未来自建闸口已预留；当前只允许本地材料、规则和人工复核链路建设，真实网站和正式业务动作保持关闭。"
    }
    output_dir = root / "03数据" / "09未来自建闸口"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"税收业务未来自建闸口报告_{timestamp}.json"
    latest = output_dir / "税收业务未来自建闸口报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"输出": str(output), "当前状态": report["当前状态"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
