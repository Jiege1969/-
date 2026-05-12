# -*- coding: utf-8 -*-
"""验证三业务反馈候选复跑去重与人工确认台账包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "77三业务反馈候选复跑去重与人工确认台账包"
LOG_DIR = ROOT / "04日志" / "三业务反馈候选复跑去重与人工确认台账包验收"

FIELD_SPEC_JSON = DATA_DIR / "复跑去重与人工确认台账字段规范_最新.json"
FIELD_SPEC_MD = DATA_DIR / "复跑去重与人工确认台账字段规范_最新.md"
LOCAL_SAMPLE_JSON = DATA_DIR / "本包复跑去重示例候选_最新.json"
LEDGER_TEMPLATE_JSON = DATA_DIR / "人工确认台账模板_最新.json"
LEDGER_TEMPLATE_MD = DATA_DIR / "人工确认台账模板_最新.md"
PACKAGE_JSON = DATA_DIR / "三业务反馈候选复跑去重与人工确认台账包_最新.json"
RERUN_RESULT_JSON = DATA_DIR / "复跑去重预演结果_最新.json"
RERUN_RESULT_MD = DATA_DIR / "复跑去重预演结果_最新.md"
LEDGER_JSON = DATA_DIR / "人工确认台账_最新.json"
LEDGER_MD = DATA_DIR / "人工确认台账_最新.md"
LOG_JSON = LOG_DIR / "three-business-feedback-rerun-dedupe-ledger-verify-最新.json"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_CANDIDATE_FIELDS = {
    "候选ID",
    "去重键",
    "业务线",
    "来源",
    "问题类型",
    "建议动作",
    "需人工确认",
    "自动生效",
}
REQUIRED_LEDGER_FIELDS = {
    "台账ID",
    "候选ID",
    "去重键",
    "业务线",
    "来源",
    "问题类型",
    "建议动作",
    "台账状态",
    "需人工确认",
    "自动生效",
}
REQUIRED_OUTPUTS = [
    FIELD_SPEC_JSON,
    FIELD_SPEC_MD,
    LOCAL_SAMPLE_JSON,
    LEDGER_TEMPLATE_JSON,
    LEDGER_TEMPLATE_MD,
    PACKAGE_JSON,
    RERUN_RESULT_JSON,
    RERUN_RESULT_MD,
    LEDGER_JSON,
    LEDGER_MD,
]
FORBIDDEN_ACTIONS = [
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
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def candidate_errors(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate))
    if missing:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 缺少候选字段：{', '.join(missing)}")
    if candidate.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 业务线不合格")
    if not candidate.get("去重键"):
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 去重键不能为空")
    if candidate.get("需人工确认") is not True:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 需人工确认必须为 true")
    if candidate.get("自动生效") is not False:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 自动生效必须为 false")
    if candidate.get("转正式规则") is not False:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 转正式规则必须为 false")
    return errors


def ledger_errors(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_LEDGER_FIELDS - set(item))
    if missing:
        errors.append(f"{item.get('台账ID', 'UNKNOWN')} 缺少台账字段：{', '.join(missing)}")
    if item.get("台账状态") != "待确认":
        errors.append(f"{item.get('台账ID', 'UNKNOWN')} 台账状态必须默认为待确认")
    if item.get("需人工确认") is not True:
        errors.append(f"{item.get('台账ID', 'UNKNOWN')} 需人工确认必须为 true")
    if item.get("自动生效") is not False:
        errors.append(f"{item.get('台账ID', 'UNKNOWN')} 自动生效必须为 false")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    field_spec = read_json(FIELD_SPEC_JSON) if FIELD_SPEC_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    rerun = read_json(RERUN_RESULT_JSON) if RERUN_RESULT_JSON.exists() else {}
    ledger = read_json(LEDGER_JSON) if LEDGER_JSON.exists() else {}
    candidates = rerun.get("候选条目", [])
    ledger_items = ledger.get("台账条目", [])

    if package.get("状态") != "three_business_feedback_rerun_dedupe_ledger_ready":
        errors.append("生成包状态不正确")
    if package.get("只读复跑") is not True or rerun.get("只读复跑") is not True:
        errors.append("必须声明只读复跑")
    if package.get("默认自动生效") is not False or field_spec.get("默认自动生效") is not False:
        errors.append("必须声明默认自动生效=false")
    if package.get("默认需人工确认") is not True or field_spec.get("默认需人工确认") is not True:
        errors.append("必须声明默认需人工确认=true")
    if package.get("不写正式规则") is not True or ledger.get("不写正式规则") is not True:
        errors.append("必须声明不写正式规则")
    if package.get("不自动吸收") is not True or ledger.get("不自动吸收") is not True:
        errors.append("必须声明不自动吸收")
    if rerun.get("总体状态") != "pass" or rerun.get("错误数") != 0:
        errors.append("复跑去重预演未通过或错误数不为 0")

    for name in FORBIDDEN_ACTIONS:
        if package.get("红线动作", {}).get(name) is not False:
            errors.append(f"红线动作 {name} 必须为 false")

    candidate_businesses = {item.get("业务线") for item in candidates}
    if candidate_businesses != REQUIRED_BUSINESSES:
        errors.append("候选必须覆盖税收/股票/视频")
    if len(candidates) < 3:
        errors.append("候选条目不得少于 3 条")

    duplicate_items = [item for item in candidates if item.get("重复状态") == "重复候选"]
    counted_duplicates = [item for item in candidates if int(item.get("重复计数", 0)) > 1]
    if not duplicate_items and not counted_duplicates:
        errors.append("重复项必须被标记或计数")
    if rerun.get("汇总", {}).get("重复项数", 0) < 1 and rerun.get("汇总", {}).get("重复键数", 0) < 1:
        errors.append("复跑汇总必须记录重复项数或重复键数")

    if len(ledger_items) != len(candidates):
        errors.append("人工确认台账条目数必须与候选条目数一致")

    candidate_ids = {item.get("候选ID") for item in candidates}
    ledger_candidate_ids = {item.get("候选ID") for item in ledger_items}
    if candidate_ids != ledger_candidate_ids:
        errors.append("人工确认台账候选ID必须与复跑候选一致")

    for candidate in candidates:
        errors.extend(candidate_errors(candidate))
    for item in ledger_items:
        errors.extend(ledger_errors(item))

    report = {
        "名称": "三业务反馈候选复跑去重与人工确认台账包验收",
        "验收时间": now_text(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "覆盖税收股票视频": candidate_businesses == REQUIRED_BUSINESSES,
            "重复项被标记或计数": bool(duplicate_items or counted_duplicates),
            "自动生效全部为false": all(item.get("自动生效") is False for item in candidates)
            and all(item.get("自动生效") is False for item in ledger_items),
            "需人工确认全部为true": all(item.get("需人工确认") is True for item in candidates)
            and all(item.get("需人工确认") is True for item in ledger_items),
            "台账状态默认待确认": all(item.get("台账状态") == "待确认" for item in ledger_items),
            "预演错误数": rerun.get("错误数"),
            "候选条目数": len(candidates),
            "台账条目数": len(ledger_items),
            "重复项数": len(duplicate_items),
            "重复计数大于1条目数": len(counted_duplicates),
        },
        "文件": {
            "字段规范": str(FIELD_SPEC_JSON),
            "本包示例候选": str(LOCAL_SAMPLE_JSON),
            "生成包": str(PACKAGE_JSON),
            "复跑去重预演结果": str(RERUN_RESULT_JSON),
            "人工确认台账JSON": str(LEDGER_JSON),
            "人工确认台账Markdown": str(LEDGER_MD),
            "验收日志": str(LOG_JSON),
        },
    }

    write_json(LOG_JSON, report)
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "日志": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
