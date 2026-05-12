# -*- coding: utf-8 -*-
"""生成《股票展示口径修复回传》。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA = ROOT / "03数据"
OUT_DIR = DATA / "246展示口径修复"
RETURN_MD = OUT_DIR / "股票展示口径修复回传_最新.md"
RETURN_JSON = OUT_DIR / "股票展示口径修复回传_最新.json"


CHANGED_FILES = [
    ROOT / "02脚本" / "stock_frontend_caliber.py",
    ROOT / "02脚本" / "股票助手入口.py",
    ROOT / "02脚本" / "生成股票图形报告PNG.ps1",
    ROOT / "02脚本" / "验证股票展示口径一致性.py",
    ROOT / "02脚本" / "生成股票展示口径修复回传.py",
]

REGENERATED_PRODUCTS = [
    DATA / "185专家市场总览" / "股票专家市场总览_最新.md",
    DATA / "185专家市场总览" / "股票专家市场总览_最新.json",
    DATA / "86图形报告" / "股票图形报告_最新.json",
    DATA / "86图形报告" / "股票图形报告_最新.svg",
    DATA / "86图形报告" / "股票图形报告_最新.png",
    DATA / "86图形报告" / "sz002466_最新_png参数.json",
    DATA / "86图形报告" / "sz002466_最新.svg",
    DATA / "86图形报告" / "sz002466_最新.png",
    DATA / "135分层日报" / "单股标准报告v2_天齐锂业_sz002466_最新.md",
    DATA / "135分层日报" / "单股标准报告v2_最新.md",
    DATA / "24企业微信短回复" / "企业微信单股短回复_最新.md",
    DATA / "24企业微信短回复" / "企业微信单股短回复_最新.json",
]


def load_validation() -> dict:
    path = OUT_DIR / "股票展示口径一致性验收_最新.json"
    if not path.exists():
        return {"通过": False, "错误": ["一致性验收未生成"]}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    validation = load_validation()
    payload = {
        "名称": "股票展示口径修复回传",
        "生成时间": now,
        "范围": str(ROOT),
        "本轮做了什么": [
            "只修改股票研究系统前台展示生成层，未修改核心评分引擎和推荐名单生成逻辑。",
            "修复天齐锂业展示层中机会类信号与风险复核/回避状态并存的问题：当前状态为风险复核或回避时，图形报告参数强制展示为风险复核信号。",
            "专家总览去掉重点关注、常规推荐等容易误解为买卖建议的词，改为研究价值评分 + 当前操作建议。",
            "图形报告参数去掉买入研究信号/卖出研究信号，改为研究价值信号或风险复核信号。",
            "新增展示层一致性校验，命中推荐类词与风险/回避类词并存时标记冲突。",
            "重新生成专家总览、天齐锂业图形报告参数/图形报告和企业微信单股短回复最新产物。",
        ],
        "改动文件": [str(path) for path in CHANGED_FILES],
        "重新生成或刷新产物": [str(path) for path in REGENERATED_PRODUCTS],
        "标记过期说明": [
            "历史带时间戳的旧前台展示产物不删除、不移动；以本次最新产物和一致性验收结果作为当前有效版本。",
            "若旧产物仍含重点关注/常规推荐/买入研究信号等旧词，视为展示口径修复前历史样本，不作为当前前台输出依据。",
        ],
        "风险等级": "W2：前台展示生成层修复，不触发真实系统。",
        "是否触发真实系统": False,
        "红线确认": {
            "未接券商": True,
            "未交易": True,
            "未生成买卖指令": True,
            "未修改核心评分引擎": True,
            "未修改推荐名单生成逻辑": True,
            "未接n8n": True,
            "未改企业微信公共配置": True,
            "未真实发送企业微信": True,
        },
        "一致性验收": validation,
    }
    RETURN_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票展示口径修复回传",
        "",
        f"- 生成时间：{now}",
        f"- 范围：{ROOT}",
        f"- 风险等级：{payload['风险等级']}",
        f"- 是否触发真实系统：{payload['是否触发真实系统']}",
        f"- 一致性验收：{'通过' if validation.get('通过') else '未通过'}",
        "",
        "## 1. 本轮做了什么",
        "",
    ]
    lines.extend([f"- {item}" for item in payload["本轮做了什么"]])
    lines.extend(["", "## 2. 改了哪些文件", ""])
    lines.extend([f"- {item}" for item in payload["改动文件"]])
    lines.extend(["", "## 3. 重新生成或刷新产物", ""])
    lines.extend([f"- {item}" for item in payload["重新生成或刷新产物"]])
    lines.extend(["", "## 4. 过期标记", ""])
    lines.extend([f"- {item}" for item in payload["标记过期说明"]])
    lines.extend(["", "## 5. 红线确认", ""])
    lines.extend([f"- {key}：{value}" for key, value in payload["红线确认"].items()])
    lines.extend(["", "## 6. 一致性验收错误", ""])
    lines.extend([f"- {item}" for item in validation.get("错误", [])] or ["- 无"])
    RETURN_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"状态": "完成", "回传": str(RETURN_MD), "一致性验收通过": validation.get("通过")}, ensure_ascii=False))
    return 0 if validation.get("通过") else 1


if __name__ == "__main__":
    raise SystemExit(main())
