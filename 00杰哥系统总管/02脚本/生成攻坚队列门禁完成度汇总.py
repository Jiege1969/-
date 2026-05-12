"""
名称：生成攻坚队列门禁完成度汇总.py
作用：汇总真实攻坚候选队列中股票、知识库、办公、视频、内容和企业微信六条门禁链路的最新验收状态。
触发方式：python 生成攻坚队列门禁完成度汇总.py
依赖：Python 标准库；各门禁验收日志；最新v3总体验收日志。
所属系统：00杰哥系统总管
安全边界：只读取验收日志并生成汇总；不创建系统计划任务；不重启服务；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建攻坚队列门禁完成度汇总脚本。
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
    summary = data.get("汇总") or data.get("summary") or {}
    failed = summary.get("失败", summary.get("failed", 1))
    return {"名称": name, "存在": True, "通过": failed == 0, "日志": str(path), "汇总": summary}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    log_root = manager / "04日志"
    checks = [
        latest_check(log_root / "真实接入闸门" / "real-access-master-gate-verify-最新.json", "真实接入总闸门"),
        latest_check(log_root / "真实攻坚队列" / "real-assault-candidate-queue-verify-最新.json", "真实攻坚候选队列"),
        latest_check(log_root / "股票公开数据探测" / "stock-public-readonly-probe-verify-最新.json", "股票公开数据只读探测"),
        latest_check(log_root / "知识库入库前复核" / "knowledge-local-ingest-review-verify-最新.json", "知识库本地入库前复核"),
        latest_check(log_root / "办公材料门禁" / "office-local-draft-gate-verify-最新.json", "办公材料本地生成"),
        latest_check(log_root / "视频素材门禁" / "video-local-material-gate-verify-最新.json", "视频素材本地整理"),
        latest_check(log_root / "内容处理门禁" / "content-local-convert-gate-verify-最新.json", "内容处理本地转换"),
        latest_check(log_root / "企业微信沙箱门禁" / "wework-sandbox-loop-gate-verify-最新.json", "企业微信沙箱回环"),
    ]
    acceptance_path = log_root / "acceptance" / "v3-acceptance-最新.json"
    acceptance = load_json(acceptance_path) if acceptance_path.exists() else {}
    failed_items = [item for item in checks if not item["通过"]]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "攻坚队列门禁完成度汇总",
        "总体验收": {"路径": str(acceptance_path) if acceptance_path.exists() else "", "汇总": acceptance.get("summary", {})},
        "门禁链路": checks,
        "汇总": {
            "门禁总数": len(checks),
            "通过": len(checks) - len(failed_items),
            "失败": len(failed_items),
        },
        "完成度百分比": round((len(checks) - len(failed_items)) * 100 / len(checks), 2),
        "当前结论": "攻坚候选门禁全部完成；仍保持真实动作关闭，下一步进入小流量只读接入方案细化。" if not failed_items else "攻坚候选门禁未全部完成",
        "仍然关闭": [
            "税收业务搭建和真实抓取",
            "旧系统写入或迁移",
            "系统计划任务创建",
            "服务重启",
            "Webhook自动触发",
            "企业微信真实发送",
            "n8n真实触发"
        ],
    }
    output_dir = manager / "03数据" / "真实攻坚队列"
    output = output_dir / "攻坚队列门禁完成度汇总_最新.json"
    write_json(output, report)
    print(json.dumps({"完成度百分比": report["完成度百分比"], "失败": report["汇总"]["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed_items else 1


if __name__ == "__main__":
    raise SystemExit(main())
