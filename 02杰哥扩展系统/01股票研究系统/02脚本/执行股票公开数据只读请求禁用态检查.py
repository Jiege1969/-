"""
名称：执行股票公开数据只读请求禁用态检查.py
作用：读取股票公开URL白名单确认单，生成只读请求执行器禁用态检查报告；未人工确认前阻断所有联网请求。
触发方式：python 执行股票公开数据只读请求禁用态检查.py
依赖：Python 标准库；股票公开URL白名单确认单_最新.json；股票公开数据只读探测规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成禁用态检查报告；不联网；不抓取行情；不调用券商接口；不交易；不写入旧系统；不触发n8n；不发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建股票公开数据只读请求执行器禁用态检查脚本。
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
    rules = load_json(root / "01配置" / "股票公开数据只读探测规则.json")
    confirmation_path = root / "03数据" / "06公开数据探测" / "股票公开URL白名单确认单_最新.json"
    confirmation = load_json(confirmation_path) if confirmation_path.exists() else {}
    confirmed_urls = confirmation.get("已确认URL", [])
    request_boundary = rules.get("请求边界", {})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "股票公开数据只读请求执行器禁用态检查",
        "确认单": str(confirmation_path),
        "已确认URL数量": len(confirmed_urls),
        "请求边界": request_boundary,
        "是否执行联网请求": False,
        "阻断原因": "未进入联网放行阶段；当前只允许禁用态检查。" if not confirmed_urls else "虽有确认URL，仍需总闸门放行后另行执行。",
        "禁用开关": {
            "联网请求": False,
            "行情抓取": False,
            "券商接口": False,
            "自动交易": False,
            "旧系统写入": False,
            "n8n触发": False,
            "企业微信发送": False,
            "税收接入": False
        },
        "执行器状态": "禁用态",
        "当前结论": "执行器骨架可用，但未放行联网请求。",
    }
    output_dir = root / "03数据" / "06公开数据探测"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"股票公开数据只读请求禁用态检查_{timestamp}.json"
    latest = output_dir / "股票公开数据只读请求禁用态检查_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否执行联网请求": report["是否执行联网请求"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
