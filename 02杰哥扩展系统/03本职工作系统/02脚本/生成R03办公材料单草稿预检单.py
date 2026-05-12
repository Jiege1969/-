"""
名称：生成R03办公材料单草稿预检单.py
作用：根据R03办公材料单草稿预检规则和现有验收日志，生成R03最终预检单。
触发方式：python 生成R03办公材料单草稿预检单.py
依赖：Python 标准库；R03办公材料单草稿预检规则.json；相关验收日志。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只生成R03预检单；不生成正式文档；不覆盖正式文档；不读取涉密资料；不自动外发；不上传；不触发n8n；不真实发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建R03办公材料单草稿预检单脚本。
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
    manager = v3_root() / "00杰哥系统总管"
    log_root = manager / "04日志"
    rules = load_json(root / "01配置" / "R03办公材料单草稿预检规则.json")
    checks = {
        "办公材料本地生成门禁通过": latest_file(log_root, "office-local-draft-gate-verify-*.json") is not None,
        "办公材料正式输出禁用态通过": latest_file(log_root, "office-final-output-disabled-verify-*.json") is not None,
        "小流量执行设计阶段通过": latest_file(log_root, "readonly-execution-design-stage-verify-*.json") is not None,
        "执行前快照通过": latest_file(log_root, "readonly-pre-execution-snapshot-verify-*.json") is not None,
        "回滚确认单模板通过": latest_file(log_root, "readonly-rollback-template-verify-*.json") is not None,
        "总体验收通过": latest_file(log_root / "acceptance", "v3-acceptance-*.json") is not None,
    }
    form = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "批次编号": rules.get("批次编号"),
        "批次名称": rules.get("批次名称"),
        "默认开关": rules.get("默认开关", {}),
        "预检结果": checks,
        "是否全部满足预检": all(checks.values()),
        "是否放行草稿副本": False,
        "是否放行正式文档": False,
        "阻断原因": "默认不放行；需要用户明确确认R03批次后才可生成单草稿副本。",
        "当前结论": "R03预检单已生成；草稿副本和正式文档均未放行。",
    }
    output_dir = root / "03数据" / "04本地生成门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"R03办公材料单草稿预检单_{timestamp}.json"
    latest = output_dir / "R03办公材料单草稿预检单_最新.json"
    write_json(output, form)
    write_json(latest, form)
    print(json.dumps({"是否全部满足预检": form["是否全部满足预检"], "是否放行正式文档": form["是否放行正式文档"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
