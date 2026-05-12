"""
名称：生成股票公开URL白名单确认单.py
作用：根据股票公开URL白名单模板生成小流量只读探测URL人工确认单。
触发方式：python 生成股票公开URL白名单确认单.py
依赖：Python 标准库；股票公开URL白名单模板.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成URL白名单确认单；不联网；不抓取行情；不调用券商接口；不交易；不写入旧系统；不触发n8n；不发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建股票公开URL白名单确认单脚本。
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
    template = load_json(root / "01配置" / "股票公开URL白名单模板.json")
    candidates = template.get("候选项", [])
    confirmed = [
        item for item in candidates
        if item.get("URL") and item.get("是否公开无需登录") is True and item.get("是否人工确认") is True
    ]
    form = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "股票公开URL白名单人工确认",
        "默认开关": template.get("默认开关", {}),
        "候选URL": candidates,
        "已确认URL": confirmed,
        "统计": {
            "候选数量": len(candidates),
            "已确认数量": len(confirmed),
            "是否允许联网请求": False
        },
        "人工确认要求": [
            "确认URL为公开页面或公开接口",
            "确认无需登录、Cookie或API密钥",
            "确认不是券商交易接口",
            "确认不涉及税收业务",
            "确认单轮请求数不超过3个",
            "确认输出只写入本模块03数据目录"
        ],
        "当前结论": "URL尚未人工确认，不允许联网请求。",
    }
    output_dir = root / "03数据" / "06公开数据探测"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"股票公开URL白名单确认单_{timestamp}.json"
    latest = output_dir / "股票公开URL白名单确认单_最新.json"
    write_json(output, form)
    write_json(latest, form)
    print(json.dumps({"候选数量": len(candidates), "已确认数量": len(confirmed), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
