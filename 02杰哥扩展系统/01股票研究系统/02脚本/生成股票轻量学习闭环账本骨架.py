# -*- coding: utf-8 -*-
"""
名称：生成股票轻量学习闭环账本骨架.py
作用：初始化股票标准报告 v2 与轻量学习闭环所需的账本文件。
触发方式：python 生成股票轻量学习闭环账本骨架.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只创建或补齐本地 03数据/04日志 文件；不触发 n8n；不发送企业微信；不调用券商接口；不自动交易；不写正式数据库。
标识：stock-light-learning-ledger-skeleton
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    # 本脚本约定放在 股票研究系统/02脚本 下，因此 parents[1] 为股票研究系统根目录。
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def now_values() -> tuple[datetime, str, str]:
    now = datetime.now()
    return now, now.strftime("%Y%m%d_%H%M%S"), now.strftime("%Y-%m-%d %H:%M:%S")


def stock_quality_archive(created_at: str) -> dict[str, Any]:
    return {
        "名称": "公司品质档案",
        "版本": "v1.0",
        "定位": "只为进入过L5深度研究池、用户增强池或人工指定股票建立公司品质摘要，不追求全市场一次性覆盖。",
        "生成时间": created_at,
        "更新方式": "覆盖最新状态，历史版本保留时间戳文件。",
        "安全边界": safety_boundary(),
        "字段说明": {
            "公司品质档位": "高/中/低/待核验，初期可人工维护，后续再接入财报规则。",
            "周期属性": "成长/周期/防御/待核验。",
            "证据状态": "已接入/部分接入/待接入/人工核验。",
        },
        "股票档案": [],
    }


def index_learning_book(created_at: str) -> dict[str, Any]:
    return {
        "名称": "指数样本学习账",
        "版本": "v1.0",
        "定位": "沉淀沪深300、中证500等指数成分股变化，用于学习市场如何筛选核心资产。",
        "生成时间": created_at,
        "更新方式": "按季度调仓或指数事件更新；覆盖最新状态，历史版本保留时间戳文件。",
        "安全边界": safety_boundary(),
        "学习目标": [
            "观察哪些公司被调入核心指数。",
            "观察哪些公司被调出核心指数。",
            "比较调仓前后的行业、规模、流动性和经营特征。",
            "为L8B扩展战略样本池提供参考，不自动改规则。",
        ],
        "指数调仓事件": [],
        "成分股历史": [],
    }


def safety_boundary() -> dict[str, bool]:
    return {
        "是否自动交易": False,
        "是否调用券商接口": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "是否写旧系统": False,
        "是否写正式库": False,
    }


def replay_record_template() -> dict[str, Any]:
    return {
        "股票代码": "示例：sz002466",
        "股票名称": "示例：天齐锂业",
        "报告日期": "YYYY-MM-DD",
        "判断主因": "技术/资金信号、行业景气、公司品质、事件/催化剂、风险复核之一",
        "辅因": [],
        "关注等级": "高优先级研究对象/常规跟踪对象/暂缓跟踪/风险复核对象",
        "证据完整度": "高/中/低",
        "公司品质档位": "高/中/低/待核验",
        "原始报告路径": "",
        "应验证周期": [],
        "验证结果_T5": None,
        "验证结果_T20": None,
        "验证结果_T60": None,
        "验证结果_T120": None,
        "人工评价": None,
        "备注": "",
    }


def validation_record_template() -> dict[str, Any]:
    return {
        "股票代码": "示例：sz002466",
        "判断日期": "YYYY-MM-DD",
        "验证周期": "T5/T20/T60/T120",
        "基准指数": "沪深300",
        "个股区间涨跌幅": None,
        "基准区间涨跌幅": None,
        "超额收益": None,
        "初步验证建议": "有效/部分有效/无效/未验证",
        "人工确认结果": None,
        "备注": "",
    }


def experience_candidate_template() -> dict[str, Any]:
    return {
        "候选经验": "示例：公司品质待核验的股票，若仅因短线放量进入L5，后续延续率需要降低权重观察。",
        "依据": "示例：过去4周同类样本N次，T20跑赢基准比例X%。",
        "提议动作": "示例：调低该类股票技术/资金短线加权，或延长冷却期。",
        "状态": "待人工确认",
        "生成日期": "YYYY-MM-DD",
    }


def ensure_latest_and_snapshot(latest_path: Path, snapshot_path: Path, default_data: Any) -> dict[str, Any]:
    existed = latest_path.exists()
    data = load_json(latest_path, default_data) if existed else default_data
    write_json(latest_path, data)
    write_json(snapshot_path, data)
    return {
        "文件": str(latest_path),
        "时间戳备份": str(snapshot_path),
        "原已存在": existed,
    }


def write_readme(root: Path, stamp: str, created_at: str) -> Path:
    path = root / "03数据" / "运行固化记录" / f"股票轻量学习闭环账本骨架生成记录_{stamp}.md"
    latest = root / "03数据" / "运行固化记录" / "股票轻量学习闭环账本骨架生成记录_最新.md"
    text = f"""# 股票轻量学习闭环账本骨架生成记录

生成时间：{created_at}

## 本次动作

- 初始化或补齐 `03数据/168公司品质档案/公司品质档案_最新.json`
- 初始化或补齐 `04日志/复盘/判断复盘账_最新.json`
- 初始化或补齐 `04日志/复盘/验证结果账_最新.json`
- 初始化或补齐 `04日志/复盘/经验候选账_最新.json`
- 初始化或补齐 `03数据/169指数样本学习账/指数样本学习账_最新.json`

## 机制定位

本机制服务于股票标准报告 v2：后台保留分析与验证素材，前台报告保持结论驱动。

核心链路：

`样本学习 -> 判断主因 -> 分层复盘 -> 公司品质校准 -> 经验候选 -> 人工确认 -> 规则微调`

## 安全边界

- 不触发 n8n。
- 不发送企业微信。
- 不调用券商接口。
- 不自动交易。
- 不写正式数据库。
- 不修改旧系统。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    root = module_root()
    _, stamp, created_at = now_values()

    quality_latest = root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json"
    quality_snapshot = root / "03数据" / "168公司品质档案" / f"公司品质档案_{stamp}.json"

    replay_latest = root / "04日志" / "复盘" / "判断复盘账_最新.json"
    replay_snapshot = root / "04日志" / "复盘" / f"判断复盘账_{stamp}.json"

    validation_latest = root / "04日志" / "复盘" / "验证结果账_最新.json"
    validation_snapshot = root / "04日志" / "复盘" / f"验证结果账_{stamp}.json"

    experience_latest = root / "04日志" / "复盘" / "经验候选账_最新.json"
    experience_snapshot = root / "04日志" / "复盘" / f"经验候选账_{stamp}.json"

    index_latest = root / "03数据" / "169指数样本学习账" / "指数样本学习账_最新.json"
    index_snapshot = root / "03数据" / "169指数样本学习账" / f"指数样本学习账_{stamp}.json"

    outputs = [
        ensure_latest_and_snapshot(quality_latest, quality_snapshot, stock_quality_archive(created_at)),
        ensure_latest_and_snapshot(replay_latest, replay_snapshot, []),
        ensure_latest_and_snapshot(validation_latest, validation_snapshot, []),
        ensure_latest_and_snapshot(experience_latest, experience_snapshot, []),
        ensure_latest_and_snapshot(index_latest, index_snapshot, index_learning_book(created_at)),
    ]

    schema_path = root / "07文档" / "股票轻量学习闭环账本字段说明_v1.0.md"
    schema_text = f"""# 股票轻量学习闭环账本字段说明 v1.0

更新时间：{created_at}

## 判断复盘账

用途：记录“当时为什么关注这只股票”，不记录冗长分析过程。

示例字段：

```json
{json.dumps(replay_record_template(), ensure_ascii=False, indent=2)}
```

## 验证结果账

用途：记录 T5/T20/T60/T120 的后验表现，供周复盘或月复盘使用。

```json
{json.dumps(validation_record_template(), ensure_ascii=False, indent=2)}
```

## 经验候选账

用途：只生成候选经验，不自动修改规则；规则微调必须经人工确认。

```json
{json.dumps(experience_candidate_template(), ensure_ascii=False, indent=2)}
```

## 公司品质档案

用途：沉淀公司品质、行业地位、财务质量、周期属性等摘要。初期只覆盖进入过L5或用户增强池的股票。

## 指数样本学习账

用途：学习沪深300、中证500等指数成分股的调入调出规律，为扩展战略样本池提供参考。
"""
    schema_path.write_text(schema_text, encoding="utf-8")

    readme_path = write_readme(root, stamp, created_at)

    result = {
        "状态": "完成",
        "生成时间": created_at,
        "输出": outputs,
        "字段说明": str(schema_path),
        "固化记录": str(readme_path),
        "安全边界": safety_boundary(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
