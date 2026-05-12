"""
名称：生成R01股票公开数据只读探测预检单.py
作用：根据R01股票公开数据只读探测预检规则和现有验收日志，生成R01最终预检单。
触发方式：python 生成R01股票公开数据只读探测预检单.py
依赖：Python 标准库；R01股票公开数据只读探测预检规则.json；相关验收日志。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成R01预检单；不联网；不抓取行情；不调用券商接口；不交易；不写入旧系统；不触发n8n；不发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建R01股票公开数据只读探测预检单脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def v3_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [item for item in root.rglob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def main() -> int:
    root = module_root()
    system_root = v3_root()
    manager = system_root / "00杰哥系统总管"
    log_root = manager / "04日志"
    rules = load_json(root / "01配置" / "R01股票公开数据只读探测预检规则.json")
    url_form = root / "03数据" / "06公开数据探测" / "股票公开URL白名单确认单_最新.json"
    checks = {
        "URL白名单确认单存在": url_form.exists(),
        "小流量执行设计阶段通过": latest_file(log_root, "readonly-execution-design-stage-verify-*.json") is not None,
        "执行前快照通过": latest_file(log_root, "readonly-pre-execution-snapshot-verify-*.json") is not None,
        "回滚确认单模板通过": latest_file(log_root, "readonly-rollback-template-verify-*.json") is not None,
        "旧系统保护通过": latest_file(log_root, "old-system-protection-verify-*.json") is not None,
        "总体验收通过": latest_file(log_root / "acceptance", "v3-acceptance-*.json") is not None,
    }
    form = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "批次编号": rules.get("批次编号"),
        "批次名称": rules.get("批次名称"),
        "默认开关": rules.get("默认开关", {}),
        "预检结果": checks,
        "是否全部满足预检": all(checks.values()),
        "是否放行真实联网": False,
        "阻断原因": "默认不放行；需要用户明确确认R01批次后才可执行单URL只读请求。",
        "当前结论": "R01预检单已生成；真实联网未放行。",
    }
    output_dir = root / "03数据" / "06公开数据探测"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"R01股票公开数据只读探测预检单_{timestamp}.json"
    latest = output_dir / "R01股票公开数据只读探测预检单_最新.json"
    write_json(output, form)
    write_json(latest, form)
    print(json.dumps({"是否全部满足预检": form["是否全部满足预检"], "是否放行真实联网": form["是否放行真实联网"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
