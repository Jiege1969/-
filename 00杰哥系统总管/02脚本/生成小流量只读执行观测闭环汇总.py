"""
名称：生成小流量只读执行观测闭环汇总.py
作用：汇总小流量只读执行方案、执行前快照、执行后观测模板和回滚确认单模板的验收状态。
触发方式：python 生成小流量只读执行观测闭环汇总.py
依赖：Python 标准库；小流量只读执行相关验收日志。
所属系统：00杰哥系统总管
安全边界：只读取验收日志并生成汇总；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读执行观测闭环汇总脚本。
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


def latest_file(root: Path, pattern: str) -> Path | None:
    files = [item for item in root.rglob(pattern) if item.is_file()]
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def latest_check(log_root: Path, name: str, pattern: str) -> dict[str, Any]:
    path = latest_file(log_root, pattern)
    if not path:
        return {"名称": name, "存在": False, "通过": False, "日志": "", "汇总": {}}
    data = load_json(path)
    summary = data.get("汇总") or data.get("summary") or {}
    failed = summary.get("失败", summary.get("failed", 1))
    return {"名称": name, "存在": True, "通过": failed == 0, "日志": str(path), "汇总": summary}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    log_root = manager / "04日志"
    checks = [
        latest_check(log_root, "小流量只读执行方案", "readonly-execution-plan-verify-*.json"),
        latest_check(log_root, "执行前快照", "readonly-pre-execution-snapshot-verify-*.json"),
        latest_check(log_root, "执行后观测模板", "readonly-post-observation-template-verify-*.json"),
        latest_check(log_root, "回滚确认单模板", "readonly-rollback-template-verify-*.json"),
    ]
    failed_items = [item for item in checks if not item["通过"]]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "小流量只读执行观测闭环汇总",
        "链路": checks,
        "汇总": {
            "链路总数": len(checks),
            "通过": len(checks) - len(failed_items),
            "失败": len(failed_items),
        },
        "完成度百分比": round((len(checks) - len(failed_items)) * 100 / len(checks), 2),
        "当前结论": "小流量只读执行观测闭环已完成；下一步可进入具体批次放行单设计，真实动作仍关闭。" if not failed_items else "观测闭环未完成",
        "仍然关闭": [
            "真实联网",
            "正式库写入",
            "正式文档输出",
            "视频真实渲染",
            "内容真实转换",
            "企业微信真实发送",
            "n8n真实触发",
            "税收业务",
            "旧系统写入"
        ],
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "小流量只读执行观测闭环汇总_最新.json"
    latest = output_dir / "小流量只读执行观测闭环汇总_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"完成度百分比": report["完成度百分比"], "失败": report["汇总"]["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
