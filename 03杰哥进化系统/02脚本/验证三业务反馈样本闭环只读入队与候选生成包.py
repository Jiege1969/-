# -*- coding: utf-8 -*-
"""验证三业务反馈样本闭环只读入队与候选生成包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"
LOG_DIR = ROOT / "04日志" / "三业务反馈样本闭环只读入队与候选生成包验收"

FIELD_SPEC_JSON = DATA_DIR / "三业务反馈样本字段规范_最新.json"
FIELD_SPEC_MD = DATA_DIR / "三业务反馈样本字段规范_最新.md"
SAMPLE_JSON = DATA_DIR / "三业务反馈示例样本_最新.json"
CANDIDATE_RULE_MD = DATA_DIR / "候选生成规则说明_最新.md"
PACKAGE_JSON = DATA_DIR / "三业务反馈样本闭环只读入队与候选生成包_最新.json"
PREVIEW_JSON = DATA_DIR / "候选入队预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "候选入队预演结果_最新.md"
LOG_JSON = LOG_DIR / "three-business-feedback-readonly-queue-candidate-verify-最新.json"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_CANDIDATE_FIELDS = {"来源", "业务线", "问题类型", "建议动作", "需人工确认"}
REQUIRED_OUTPUTS = [
    FIELD_SPEC_JSON,
    FIELD_SPEC_MD,
    SAMPLE_JSON,
    CANDIDATE_RULE_MD,
    PACKAGE_JSON,
    PREVIEW_JSON,
    PREVIEW_MD,
]
FORBIDDEN_TRUE_FLAGS = {
    "真实发送企业微信",
    "接n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载服务",
    "触发业务接口",
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def candidate_errors(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate))
    if missing:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 缺少候选字段：{', '.join(missing)}")
    if candidate.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 业务线不合格")
    if candidate.get("需人工确认") is not True:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 需人工确认必须为 true")
    if candidate.get("是否可自动吸收") is not False:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 是否可自动吸收必须为 false")
    if candidate.get("转正式规则") is not False:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 转正式规则必须为 false")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    field_spec = read_json(FIELD_SPEC_JSON) if FIELD_SPEC_JSON.exists() else {}
    samples = read_json(SAMPLE_JSON).get("样本列表", []) if SAMPLE_JSON.exists() else []
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    preview = read_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    candidates = preview.get("候选条目", [])

    if package.get("状态") != "three_business_feedback_readonly_queue_candidate_ready":
        errors.append("生成包状态不正确")
    if package.get("默认不自动吸收") is not True or field_spec.get("默认不自动吸收") is not True:
        errors.append("必须声明默认不自动吸收")
    if package.get("不转正式规则") is not True or field_spec.get("不转正式规则") is not True:
        errors.append("必须声明不转正式规则")
    if preview.get("总体状态") != "pass" or preview.get("错误数") != 0:
        errors.append("候选入队预演未通过或错误数不为 0")

    sample_businesses = {item.get("业务线") for item in samples}
    candidate_businesses = {item.get("业务线") for item in candidates}
    if sample_businesses != REQUIRED_BUSINESSES:
        errors.append("示例样本必须覆盖税收/股票/视频")
    if candidate_businesses != REQUIRED_BUSINESSES:
        errors.append("候选条目必须覆盖税收/股票/视频")
    if len(candidates) < 3:
        errors.append("候选条目不得少于 3 条")

    for flag in sorted(FORBIDDEN_TRUE_FLAGS):
        if package.get("安全边界", {}).get(flag) is not False:
            errors.append(f"安全边界 {flag} 必须为 false")

    for candidate in candidates:
        errors.extend(candidate_errors(candidate))

    report = {
        "名称": "三业务反馈样本闭环只读入队与候选生成包验收",
        "验收时间": now_text(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "覆盖税收股票视频": candidate_businesses == REQUIRED_BUSINESSES,
            "默认不自动吸收": package.get("默认不自动吸收") is True and all(item.get("是否可自动吸收") is False for item in candidates),
            "不转正式规则": package.get("不转正式规则") is True and all(item.get("转正式规则") is False for item in candidates),
            "候选条目数": len(candidates),
            "候选条目字段完整": all(REQUIRED_CANDIDATE_FIELDS <= set(item) for item in candidates),
            "候选需人工确认全部为true": all(item.get("需人工确认") is True for item in candidates),
            "预演错误数": preview.get("错误数"),
        },
        "文件": {
            "字段规范": str(FIELD_SPEC_JSON),
            "示例样本": str(SAMPLE_JSON),
            "候选生成规则说明": str(CANDIDATE_RULE_MD),
            "生成包": str(PACKAGE_JSON),
            "候选入队预演结果": str(PREVIEW_JSON),
            "验收日志": str(LOG_JSON),
        },
    }

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "日志": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
