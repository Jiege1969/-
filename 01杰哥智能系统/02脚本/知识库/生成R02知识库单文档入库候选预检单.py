"""
名称：生成R02知识库单文档入库候选预检单.py
作用：根据R02知识库单文档入库候选预检规则和现有验收日志，生成R02最终预检单。
触发方式：python 生成R02知识库单文档入库候选预检单.py
依赖：Python 标准库；R02知识库单文档入库候选预检规则.json；相关验收日志。
所属系统：01杰哥智能系统/知识库
安全边界：只生成R02预检单；不写入正式知识库；不写入Qdrant；不写入PostgreSQL；不读取旧系统资料；不覆盖原始文档；不触发n8n；不外发资料；不接入税收。
创建/修改记录：2026-04-27 创建R02知识库单文档入库候选预检单脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def v3_root() -> Path:
    return system_root().parent


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def required_latest(path: Path) -> bool:
    return path.exists() and path.is_file()


def main() -> int:
    root = system_root()
    manager = v3_root() / "00杰哥系统总管"
    log_root = manager / "04日志"
    rules = load_json(root / "01配置" / "R02知识库单文档入库候选预检规则.json")
    required_logs = {
        "知识库本地入库前复核通过": log_root / "知识库入库前复核" / "knowledge-local-ingest-review-verify-最新.json",
        "知识库写库禁用态通过": log_root / "知识库入库前复核" / "knowledge-write-disabled-verify-最新.json",
        "小流量执行设计阶段通过": log_root / "小流量只读执行" / "readonly-execution-design-stage-verify-最新.json",
        "执行前快照通过": log_root / "小流量只读执行" / "readonly-pre-execution-snapshot-verify-最新.json",
        "回滚确认单模板通过": log_root / "小流量只读执行" / "readonly-rollback-template-verify-最新.json",
        "总体验收通过": log_root / "acceptance" / "v3-acceptance-最新.json",
    }
    checks = {name: required_latest(path) for name, path in required_logs.items()}
    form = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "批次编号": rules.get("批次编号"),
        "批次名称": rules.get("批次名称"),
        "默认开关": rules.get("默认开关", {}),
        "预检结果": checks,
        "预检依据": {name: str(path) for name, path in required_logs.items()},
        "是否全部满足预检": all(checks.values()),
        "是否放行正式写库": False,
        "阻断原因": "默认不放行；需要用户明确确认R02批次后才可生成单文档入库候选。",
        "当前结论": "R02预检单已生成；正式写库未放行。",
    }
    output_dir = root / "03数据" / "知识库" / "06入库前复核"
    output = output_dir / "R02知识库单文档入库候选预检单_最新.json"
    write_json(output, form)
    print(json.dumps({"是否全部满足预检": form["是否全部满足预检"], "是否放行正式写库": form["是否放行正式写库"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
