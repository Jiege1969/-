from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
PRIORITY_REPORT = DATA_DIR / "L3五样本证据缺口优先级报告_最新.json"
LEDGER_PATH = DATA_DIR / "industry_price_observations_ledger_v1.0.json"
QUEUE_JSON = DATA_DIR / "五样本行业价格连续观测补数队列_最新.json"
QUEUE_MD = DATA_DIR / "五样本行业价格连续观测补数队列_最新.md"


PRODUCT_MAP = {
    "sz002428": {
        "product_code": "germanium_ingot",
        "product_name": "锗锭",
        "indicator_type": "metal_price",
        "preferred_sources": ["上海有色网SMM锗价格页", "百川盈孚锗价格页", "上市公司公告中的锗产品价格说明"],
        "minimum_fields": ["price_date", "price_mid或price_range", "unit", "source_name", "source_url", "checked_at"],
        "front_usage": "不足5个连续观测点前，只能写锗价尚未形成可用趋势证据。"
    },
    "sz002466": {
        "product_code": "battery_grade_lithium_carbonate",
        "product_name": "电池级碳酸锂",
        "indicator_type": "chemical_material_price",
        "preferred_sources": ["上海有色网SMM新能源材料页", "公开锂盐价格页面", "上市公司公告中的锂盐价格说明"],
        "minimum_fields": ["price_date", "price_mid或price_range", "unit", "source_name", "source_url", "checked_at"],
        "front_usage": "1-4个观测点只能写单点或弱参考，不得写趋势反转。"
    },
    "sh688347": {
        "product_code": "wafer_foundry_cycle_indicator",
        "product_name": "晶圆代工景气指标",
        "indicator_type": "industry_cycle_indicator",
        "preferred_sources": ["公司公告中的产能利用率/ASP说明", "半导体行业协会或公开研究摘要", "公开晶圆代工价格/稼动率报道"],
        "minimum_fields": ["indicator_date", "indicator_name", "value或direction", "unit或口径", "source_name", "source_url", "checked_at"],
        "front_usage": "未结构化前只能写晶圆代工景气未接入，不能写半导体景气已经验证。"
    },
    "sz000906": {
        "product_code": "bulk_supply_chain_cycle_indicator",
        "product_name": "大宗商品/供应链景气指标",
        "indicator_type": "business_cycle_indicator",
        "preferred_sources": ["公司公告中的主营品类价格/库存周转说明", "公开大宗商品价格指数", "公开供应链景气或物流指标"],
        "minimum_fields": ["indicator_date", "indicator_name", "value或direction", "unit或口径", "source_name", "source_url", "checked_at"],
        "front_usage": "未结构化前只能写供应链景气未接入，不能用泛化大宗上涨强化结论。"
    },
    "sz300641": {
        "product_code": "trimellitic_anhydride_tma",
        "product_name": "偏苯三酸酐/TMA",
        "indicator_type": "chemical_product_price",
        "preferred_sources": ["百川盈孚TMA价格页", "卓创资讯公开化工品价格摘要", "上市公司公告中的TMA/偏苯三酸酐价格说明"],
        "minimum_fields": ["price_date", "price_mid或price_range", "unit", "source_name", "source_url", "checked_at"],
        "front_usage": "不足5个连续观测点前，只能写TMA价格未形成可用趋势证据。"
    }
}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def observations_by_product(ledger: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in ledger.get("observations", []):
        code = item.get("product_code", "")
        if code:
            counts[code] = counts.get(code, 0) + 1
    return counts


def build_task(sample: dict, counts: dict[str, int]) -> dict:
    stock = sample["stock"]
    code = stock["code"]
    product = PRODUCT_MAP.get(code)
    if not product:
        product = {
            "product_code": f"{code}_industry_indicator",
            "product_name": "行业景气指标",
            "indicator_type": "industry_indicator",
            "preferred_sources": ["上市公司公告", "公开行业价格或景气数据"],
            "minimum_fields": ["date", "value或direction", "source_name", "source_url", "checked_at"],
            "front_usage": "未结构化前只能写行业价格或景气未接入。"
        }
    current_count = counts.get(product["product_code"], 0)
    target_count = 5
    missing_count = max(target_count - current_count, 0)
    status = "trend_ready" if current_count >= 5 else ("single_observation" if current_count > 0 else "source_registered")

    return {
        "stock": stock,
        "product_code": product["product_code"],
        "product_name": product["product_name"],
        "indicator_type": product["indicator_type"],
        "current_observation_count": current_count,
        "target_min_observation_count": target_count,
        "missing_observation_count": missing_count,
        "current_status": status,
        "priority": "P0" if missing_count > 0 else "P2",
        "preferred_sources": product["preferred_sources"],
        "minimum_fields": product["minimum_fields"],
        "entry_boundary": [
            "只允许登记公开可复核或授权允许内部研究使用的数据。",
            "每条观测必须保留日期、数值或方向、单位或口径、来源名称、来源URL和采集时间。",
            "媒体摘要只能作线索，不能替代原始价格源。",
            "不足5个连续观测点前不得生成trend_ready结论。",
            "本队列不写入观测账本，只提供补数任务。"
        ],
        "front_usage": product["front_usage"],
        "linked_gap": [
            item for item in sample.get("missing", [])
            if any(key in item for key in ["价格", "价差", "景气", "观测"])
        ]
    }


def render_md(queue: dict) -> str:
    lines = [
        "# 五样本行业价格连续观测补数队列",
        "",
        f"- 生成时间：{queue['generated_at']}",
        "- 资产身份：W1补数任务队列，不是正式库，不直接写入观测账本。",
        "- 安全边界：未触发外部抓取、未发送企业微信、未重启服务、未调用券商接口、未自动交易。",
        "",
        "## 补数队列",
        "",
        "| 股票 | 观测对象 | 当前点数 | 目标点数 | 待补点数 | 当前状态 | 优先级 |",
        "|---|---|---:|---:|---:|---|---|"
    ]
    for task in queue["tasks"]:
        lines.append(
            f"| {task['stock']['name']} | {task['product_name']} | {task['current_observation_count']} | "
            f"{task['target_min_observation_count']} | {task['missing_observation_count']} | "
            f"{task['current_status']} | {task['priority']} |"
        )
    lines.extend([
        "",
        "## 统一闸口",
        "",
        "- 只补公开可复核或授权允许内部研究使用的数据。",
        "- 不足5个连续观测点前，不得写趋势确认。",
        "- 本队列只说明补数任务，不写正式库、不触发抓取、不外发。",
        "- 前台短答只能根据当前状态写缺口或弱参考，不能把任务队列当作证据结论。"
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    priority_report = read_json(PRIORITY_REPORT)
    ledger = read_json(LEDGER_PATH)
    counts = observations_by_product(ledger)
    tasks = [build_task(sample, counts) for sample in priority_report.get("samples", [])]
    queue = {
        "名称": "五样本行业价格连续观测补数队列",
        "generated_at": now,
        "asset_identity": "W1补数任务队列",
        "status": "ready",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_external_fetch": True,
        "not_formal_database_write": True,
        "tasks": tasks,
        "rule": {
            "trend_ready_min_observations": 5,
            "single_observation_range": "1-4",
            "zero_observation_status": "source_registered"
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_external_fetch": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_delete_or_move_old_assets": True,
            "not_formal_database_write": True,
            "not_broker_interface": True,
            "not_auto_trade": True
        }
    }
    write_json(QUEUE_JSON, queue)
    QUEUE_MD.write_text(render_md(queue), encoding="utf-8")
    print(json.dumps({
        "status": "completed",
        "task_count": len(tasks),
        "queue_json": str(QUEUE_JSON),
        "queue_md": str(QUEUE_MD)
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
