# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"


DESIGN_FILES = [
    ROOT / "01配置" / "旧草案吸收规则.json",
    ROOT / "01配置" / "股票分析报告工作流_v1.0.json",
    ROOT / "01配置" / "动态样本池规则.json",
    ROOT / "01配置" / "研究决策复盘闭环规则.json",
    ROOT / "01配置" / "分层过滤规则.json",
    ROOT / "01配置" / "股票系统搭建闭环防误解规则_v1.0.json",
    ROOT / "01配置" / "股票三线分析与模型路由配置.json",
    ROOT / "01配置" / "盘后批处理资源预算规则.json",
    ROOT / "01配置" / "股票日常运行规则.json",
    ROOT / "01配置" / "股票研究最小闭环演练规则.json",
    ROOT / "01配置" / "L3_scoring_contract_v1.0.json",
    ROOT / "07文档" / "旧股票草案吸收报告.md",
    ROOT / "03数据" / "08草案吸收" / "旧股票系统核心逻辑吸收差异报告.md",
    ROOT / "07文档" / "股票研究闭环优先建设与旧系统退役方案.md",
    ROOT / "03数据" / "144交付总包" / "股票系统交付总包_最新.md",
]


POOL_FILES = [
    ("重点关注股票池", ROOT / "01配置" / "重点关注股票池.json", "用户偏好和长期关注入口"),
    ("300只试运行池", ROOT / "03数据" / "91试运行池" / "300只试运行池_最新.json", "试运行基础样本池"),
    ("L8X综合候选池", ROOT / "03数据" / "130X综合候选池" / "L8X综合候选池_最新.json", "L7统一上游入口"),
    ("L8B扩展战略样本池", ROOT / "03数据" / "130B扩展战略样本池" / "L8B扩展战略样本池_最新.json", "指数外用户增强与战略样本"),
    ("L7可交易过滤池", ROOT / "03数据" / "132可交易过滤池" / "L7可交易过滤池_最新.json", "可交易过滤后的大样本"),
    ("L6行业主题观察池", ROOT / "03数据" / "133行业主题观察池" / "L6行业主题观察池_最新.json", "行业主题与长线方向入口"),
    ("L5深度研究池", ROOT / "03数据" / "134深度研究池" / "L5深度研究池_最新.json", "晚间深度研究候选"),
    ("300只盘后轻扫描候选", ROOT / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json", "盘后短线初筛候选"),
]


INDICATOR_FILES = [
    ("重点关注池技术指标", ROOT / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json"),
    ("300只候选技术指标", ROOT / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json"),
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pick_array(data: dict):
    for key in ("股票池", "候选清单", "技术指标", "stocks", "items", "data"):
        value = data.get(key)
        if isinstance(value, list):
            return key, value
    return "", []


def stock_name(item: dict) -> str:
    return (
        item.get("name")
        or item.get("股票名称")
        or item.get("名称")
        or item.get("stock_name")
        or item.get("证券简称")
        or ""
    )


def stock_code(item: dict) -> str:
    return (
        item.get("code")
        or item.get("股票代码")
        or item.get("代码")
        or item.get("stock_code")
        or item.get("证券代码")
        or ""
    )


def stock_industry(item: dict) -> str:
    return (
        item.get("industry")
        or item.get("行业")
        or item.get("所属行业")
        or item.get("申万行业")
        or item.get("industry_name")
        or ""
    )


def stock_list(items: list[dict]) -> list[dict]:
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "code": stock_code(item),
                "name": stock_name(item),
                "industry": stock_industry(item),
            }
        )
    return result


def pool_inventory():
    rows = []
    for name, path, role in POOL_FILES:
        if not path.exists():
            rows.append({"name": name, "exists": False, "path": str(path), "role": role})
            continue
        data = load_json(path)
        array_key, items = pick_array(data if isinstance(data, dict) else {})
        stocks = stock_list(items)
        industry_counts = {}
        for s in stocks:
            industry = s.get("industry") or "未标注"
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        rows.append(
            {
                "name": name,
                "exists": True,
                "path": str(path),
                "role": role,
                "array_key": array_key,
                "count": len(items),
                "sample": stocks[:20],
                "stocks": stocks,
                "industry_top": sorted(industry_counts.items(), key=lambda x: x[1], reverse=True)[:12],
            }
        )
    return rows


def indicator_inventory():
    rows = []
    for name, path in INDICATOR_FILES:
        if not path.exists():
            rows.append({"name": name, "exists": False, "path": str(path)})
            continue
        data = load_json(path)
        array_key, items = pick_array(data if isinstance(data, dict) else {})
        keys = set()
        for item in items[:10]:
            if isinstance(item, dict):
                keys.update(item.keys())
        rows.append(
            {
                "name": name,
                "exists": True,
                "path": str(path),
                "array_key": array_key,
                "count": len(items),
                "fields_seen": sorted(keys),
                "sample": stock_list(items[:20]),
            }
        )
    return rows


def md_stock_sample(stocks: list[dict]) -> str:
    return "、".join([f"{s.get('name')}({s.get('code')})" for s in stocks[:8] if s.get("name") or s.get("code")])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pools = pool_inventory()
    indicators = indicator_inventory()

    report = {
        "generated_at": generated_at,
        "scope": "只读深扫原始设计、现有股票池、指标覆盖和三阶段报告承接关系；未触发n8n，未发送企业微信，未接券商，不交易。",
        "source_design_files": [{"path": str(p), "exists": p.exists()} for p in DESIGN_FILES],
        "original_system_thesis": [
            "股票系统的底层目标是样本研究系统，不是单纯报告机器人。",
            "先用大样本池覆盖市场，再用L8到L5分层漏斗逐级压缩，最后只把少量候选交给大模型做解释和报告。",
            "大模型负责解释证据、补充表达、生成用户可读报告；不能代替结构化评分、不能扫描全市场、不能自动改正式规则。",
            "企业微信是输入输出终端，n8n是调度和状态流转，不是股票判断的大脑。",
            "反馈闭环必须形成系统判断账、人工决策账、结果验证账、经验提炼账，经验先进入候选，不能直接改正式规则。",
        ],
        "current_pool_inventory": pools,
        "current_indicator_inventory": indicators,
        "three_stage_mapping": [
            {
                "stage": "收盘短线观察",
                "proper_inputs": ["300只试运行池", "300只盘后轻扫描候选", "L7可交易过滤池"],
                "proper_logic": "纯技术量价扫描，输出明日触发条件和止损/放弃线，不讲深基本面。",
                "current_gap": "轻扫描当前只输出10只候选，技术指标也只覆盖10只候选，未覆盖完整300只。",
            },
            {
                "stage": "深度三维研究",
                "proper_inputs": ["L6行业主题观察池", "L5深度研究池", "L3评分契约", "财报/行业/政策/市场风格证据"],
                "proper_logic": "行业趋势、公司成长、短线位置三维共振，适合隔夜决策。",
                "current_gap": "L6/L5已存在，但行业趋势、成长证据、政策事件和市场风格字段还没有稳定汇成一份三维报告。",
            },
            {
                "stage": "盘前出击排序",
                "proper_inputs": ["昨晚深度研究", "盘后短线池", "盘前消息/竞价/外盘夜盘字段"],
                "proper_logic": "按触发共振度排序，给开盘后优先级、触发价位、放弃线。",
                "current_gap": "盘前消息、竞价强弱、外盘夜盘字段未形成稳定本地输入，不能硬编。",
            },
        ],
        "priority_improvements": [
            "先补统一股票池只读索引：把重点关注、300试运行、L8X、L7、L6、L5、轻扫描候选的数量、来源、完整股票名单和用途对齐。",
            "再补技术指标映射：把MA/RSI/MACD/量比转成报告需要的支撑位、压力位、转强线、风控线、放量/缩量和平台突破字段。",
            "第三步扩大指标覆盖：从当前10只候选指标，推进到至少300只试运行池的批量指标覆盖；稳定后再考虑824/2000。",
            "第四步接三阶段报告：盘后只用量价，晚间用L6/L5和L3评分，盘前只用真实可得盘前字段，不编缺失数据。",
            "第五步把企业微信反馈入账：用户说太空泛、风险没讲清、标题不对、链接缺失时，要进入反馈账并影响下一轮报告候选提示词/模板候选。",
        ],
        "safety": {
            "trigger_n8n": False,
            "send_wecom": False,
            "broker": False,
            "trade": False,
            "modify_formal_rules": False,
        },
    }

    json_path = OUT_DIR / "股票系统原始总体思路深扫对标_最新.json"
    md_path = OUT_DIR / "股票系统原始总体思路深扫对标_最新.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 股票系统原始总体思路深扫对标",
        "",
        f"生成时间：{generated_at}",
        "",
        "## 一、结论",
        "",
        "这套股票系统当初的总体思路不是“让机器人随便写一篇股票报告”，而是：大样本股票池做市场覆盖，L8-L5分层漏斗做候选压缩，结构化指标和评分先给证据，大模型只负责少量候选的解释、表达、用户问答和报告生成，最后用复盘反馈推动经验候选沉淀。",
        "",
        "因此，三阶段报告必须接回这套底座：盘后看技术短线，晚间看行业/成长/技术三维共振，盘前看触发排序。不能脱离股票池、指标、评分和反馈账本手写样例。",
        "",
        "## 二、已核查的原始设计文件",
        "",
    ]
    for item in report["source_design_files"]:
        status = "存在" if item["exists"] else "缺失"
        lines.append(f"- {status}：`{item['path']}`")

    lines.extend(["", "## 三、当前股票池真实盘点", ""])
    lines.append("| 股票池 | 数量 | 作用 | 示例 |")
    lines.append("|---|---:|---|---|")
    for row in pools:
        count = row.get("count", 0) if row.get("exists") else "缺失"
        sample = md_stock_sample(row.get("sample", []))
        lines.append(f"| {row['name']} | {count} | {row.get('role','')} | {sample} |")

    lines.extend(["", "## 四、当前技术指标真实盘点", ""])
    lines.append("| 指标产物 | 覆盖数量 | 已见字段 | 示例 |")
    lines.append("|---|---:|---|---|")
    for row in indicators:
        count = row.get("count", 0) if row.get("exists") else "缺失"
        fields = "、".join(row.get("fields_seen", [])[:18])
        sample = md_stock_sample(row.get("sample", []))
        lines.append(f"| {row['name']} | {count} | {fields} | {sample} |")

    lines.extend(
        [
            "",
            "## 五、对标后的真实判断",
            "",
            "1. 股票池：已经有分层底座，不是空白。当前可见重点关注池、300试运行池、L8X综合候选池、L7、L6、L5、盘后轻扫描候选。问题是统一入口和三阶段报告绑定还不够紧。",
            "2. 代表性：824只L8X和823只L7已经能支撑核心样本研究；但距离原规划2000只标准大股票池还有差距。当前不应盲目扩2000，应先让300/824这层稳定产生可读报告和复盘结果。",
            "3. 技术指标：MA、RSI、MACD、成交量均线、量比已经存在；但报告需要的支撑位、压力位、转强线、风控线、平台突破、回踩确认、竞价强弱等字段还没有统一成标准指标层。",
            "4. 长线和中线：L6行业主题池、L5深度研究池已经有基础；但行业趋势、政策催化、财报成长、机构关注和市场风格还没完全合成为三维研究报告的稳定字段。",
            "5. 企业微信/n8n：企业微信应是终端，n8n应是调度器。它们不应该输出桥接运行记录给用户，只能输出最终股票分析内容。",
            "6. 反馈进化：用户对报告的批评必须进入反馈账和候选改进，不应被误判成交易指令，也不应只回复“请告诉我股票名称”。",
            "",
            "## 六、接下来施工优先级",
            "",
        ]
    )
    for idx, item in enumerate(report["priority_improvements"], 1):
        lines.append(f"{idx}. {item}")

    lines.extend(
        [
            "",
            "## 七、安全边界",
            "",
            "- 本轮只读深扫和报告落盘。",
            "- 未触发n8n，未真实发送企业微信，未接券商，不交易。",
            "- 未修改正式规则，未重载19310/19302。",
            "",
            f"完整股票名单已写入JSON：`{json_path}`",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(md_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
