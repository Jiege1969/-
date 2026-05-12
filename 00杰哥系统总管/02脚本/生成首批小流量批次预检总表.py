"""
名称：生成首批小流量批次预检总表.py
作用：汇总R01股票、R02知识库、R03办公材料三个首批小流量批次预检状态。
触发方式：python 生成首批小流量批次预检总表.py
依赖：Python 标准库；R01/R02/R03预检验收日志。
所属系统：00杰哥系统总管
安全边界：只读取验收日志并生成总表；不联网；不写库；不生成正式文档；不触发n8n；不真实发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批小流量批次预检总表脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_check(path: Path, name: str) -> dict[str, Any]:
    if not path.exists():
        return {"名称": name, "存在": False, "通过": False, "日志": "", "汇总": {}}
    data = load_json(path)
    summary = data.get("汇总") or {}
    return {"名称": name, "存在": True, "通过": summary.get("失败") == 0, "日志": str(path), "汇总": summary}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    log_root = manager / "04日志"
    checks = [
        latest_check(log_root / "小流量只读执行" / "r01-stock-readonly-preflight-verify-最新.json", "R01股票公开数据单URL只读探测"),
        latest_check(log_root / "小流量只读执行" / "r02-knowledge-ingest-preflight-verify-最新.json", "R02知识库单文档入库候选"),
        latest_check(log_root / "小流量只读执行" / "r03-office-draft-preflight-verify-最新.json", "R03办公材料单草稿确认"),
    ]
    failed_items = [item for item in checks if not item["通过"]]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "首批小流量批次预检总表",
        "批次预检": checks,
        "汇总": {
            "批次总数": len(checks),
            "通过": len(checks) - len(failed_items),
            "失败": len(failed_items),
        },
        "完成度百分比": round((len(checks) - len(failed_items)) * 100 / len(checks), 2),
        "是否允许真实动作": False,
        "当前结论": "首批小流量批次预检已完成；真实动作仍未放行。" if not failed_items else "首批小流量批次预检未完成",
        "仍然关闭": ["真实联网", "正式库写入", "正式文档输出", "企业微信真实发送", "n8n真实触发", "税收业务", "旧系统写入"],
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    output = output_dir / "首批小流量批次预检总表_最新.json"
    write_json(output, report)
    print(json.dumps({"完成度百分比": report["完成度百分比"], "失败": report["汇总"]["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
