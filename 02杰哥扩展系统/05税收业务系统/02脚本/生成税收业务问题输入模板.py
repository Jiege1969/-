# -*- coding: utf-8 -*-
"""
名称：生成税收业务问题输入模板.py
作用：生成用户填写税收业务问题的JSON模板。
触发方式：python 生成税收业务问题输入模板.py
依赖：Python标准库；税收问题驱动取证工作流规则.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只写本地问题输入模板；不联网、不下载、不入库、不触发n8n、不推送企微、不生成正式税务结论。
创建/修改记录：2026-04-30 创建税收业务问题输入模板脚本。
标识：tax-question-input-template-generate
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
    rule = load_json(root / "01配置" / "税收问题驱动取证工作流规则.json")
    output_dir = root / rule["输出"]["数据目录"]
    latest = output_dir / rule["输出"]["问题输入模板"]
    if latest.exists():
        print(json.dumps({"输出": str(latest), "状态": "已存在，未覆盖"}, ensure_ascii=False))
        return 0
    template = {
        "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "问题编号": "TAX-Q-20260430-001",
        "业务问题": "一般纳税人销售使用过的固定资产，增值税能否简易计税？能不能开专票？",
        "纳税人类型": "一般纳税人",
        "涉及地区": "待填写",
        "业务发生时间": "待填写",
        "交易对象": "待填写",
        "金额口径": "待填写",
        "发票情况": "待填写",
        "合同或凭证": "待填写",
        "已知事实": [
            "待填写"
        ],
        "希望回答": [
            "适用税种",
            "适用政策依据",
            "能否适用简易计税",
            "发票开具限制",
            "风险点和待补充资料"
        ],
        "允许动作": {
            "允许联网检索": False,
            "允许下载资料": False,
            "允许外部问答窗口提问": False,
            "允许生成答案草案": True,
            "允许生成正式结论": False
        },
        "说明": "当前模板用于离线生成问题驱动取证任务包；不执行真实联网检索、下载或外部提问。"
    }
    write_json(latest, template)
    print(json.dumps({"输出": str(latest), "状态": "已创建"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
