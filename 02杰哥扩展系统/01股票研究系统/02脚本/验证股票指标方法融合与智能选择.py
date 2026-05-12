# -*- coding: utf-8 -*-
"""
验证股票分析指标方法融合规则与智能选择引擎产物。

边界：只读配置和产物；只写本地验收报告；不触发企业微信、n8n、券商接口或交易链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"
OUT_DIR = DATA / "018股票分析指标方法融合"

FUSION_RULE_PATH = CONFIG / "股票分析指标方法融合规则_v1.0.json"
FUSION_REPORT_PATH = OUT_DIR / "股票分析指标方法融合报告_最新.json"
SMART_ENGINE_PATH = DATA / "282股票指标智能选择引擎" / "股票指标智能选择引擎_最新.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    problems: list[str] = []
    checks: list[dict[str, Any]] = []

    fusion_rule = read_json(FUSION_RULE_PATH)
    fusion_report = read_json(FUSION_REPORT_PATH)
    engine = read_json(SMART_ENGINE_PATH)

    layers = fusion_rule.get("分析方法层", [])
    scenes = fusion_rule.get("场景到方法映射", [])
    scene_outputs_missing = [item.get("场景") for item in scenes if not item.get("输出")]

    checks.append({"项目": "方法层数量", "状态": "通过" if len(layers) >= 7 else "失败", "值": len(layers)})
    checks.append({"项目": "场景映射数量", "状态": "通过" if len(scenes) >= 6 else "失败", "值": len(scenes)})
    checks.append({"项目": "场景输出完整", "状态": "通过" if not scene_outputs_missing else "失败", "缺失": scene_outputs_missing})

    if len(layers) < 7:
        problems.append("方法层不足7层，可能缺少数据可信、风险或跟踪闭环。")
    if len(scenes) < 6:
        problems.append("场景映射不足6类，盘中、盘后、推荐榜或环境状态可能不完整。")
    if scene_outputs_missing:
        problems.append(f"以下场景缺少输出说明：{', '.join(scene_outputs_missing)}")

    engine_market = engine.get("市场状态")
    engine_combo = engine.get("当前方法组合", {}).get("方法组合")
    if engine_market == "震荡市/中性市" and engine_combo == "强趋势延续组合":
        problems.append("震荡市/中性市不应默认使用强趋势延续组合。")

    engine_fusion = engine.get("指标方法融合", {})
    checks.append(
        {
            "项目": "智能选择引擎已接入融合规则",
            "状态": "通过" if engine_fusion.get("方法层数量") >= 7 else "失败",
            "方法层数量": engine_fusion.get("方法层数量"),
        }
    )
    if engine_fusion.get("方法层数量", 0) < 7:
        problems.append("智能选择引擎未完整接入指标方法融合规则。")

    checks.append(
        {
            "项目": "震荡市默认组合",
            "状态": "通过" if not (engine_market == "震荡市/中性市" and engine_combo == "强趋势延续组合") else "失败",
            "市场状态": engine_market,
            "当前方法组合": engine_combo,
        }
    )

    status = "通过" if not problems else "失败"
    report = {
        "名称": "股票指标方法融合与智能选择验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": status,
        "检查项": checks,
        "问题": problems,
        "输入": {
            "指标方法融合规则": str(FUSION_RULE_PATH),
            "指标方法融合报告": str(FUSION_REPORT_PATH),
            "智能选择引擎": str(SMART_ENGINE_PATH),
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(OUT_DIR / f"股票指标方法融合与智能选择验收_{timestamp}.json", report)
    write_json(OUT_DIR / "股票指标方法融合与智能选择验收_最新.json", report)
    print(json.dumps({"状态": status, "问题数": len(problems), "报告": str(OUT_DIR / "股票指标方法融合与智能选择验收_最新.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
