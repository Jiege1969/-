# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SRC_JSON = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转_最新.json"
SRC_MD = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转_最新.md"
QUEUE_JSON = DATA_DIR / "输入队列" / "税收企业微信脱敏样例批量输入队列_预演.json"
SHADOW_JSON = DATA_DIR / "证据匹配影子流转" / "税收企业微信脱敏样例批量证据匹配影子流转_预演.json"
OUT_JSON = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信脱敏样例批量入队影子流转验收_最新.md"


REQUIRED_QUEUE_FIELDS = [
    "入队ID",
    "消息ID",
    "入队时间",
    "机器人名称",
    "提问人标识",
    "消息类型",
    "脱敏文本",
    "附件元数据",
    "分流结果",
    "处理状态",
    "拒收原因",
    "输入契约状态",
    "审计编号",
    "来源通道",
]
REQUIRED_SHADOW_FIELDS = [
    "流转ID",
    "入队ID",
    "消息ID",
    "来源机器人",
    "脱敏文本",
    "原队列状态",
    "原输入契约状态",
    "影子流转状态",
    "业务事项猜测",
    "适用税种猜测",
    "候选证据主题",
    "依据层级要求",
    "待补充事实",
    "待人工复核项",
    "禁止动作",
    "下一步建议",
    "是否写正式业务库",
    "是否生成正式税务结论",
]
SENSITIVE_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"\b\d{15,18}[0-9Xx]\b"),
    re.compile(r"\b\d{16,19}\b"),
]


def check(name: str, passed: bool, detail) -> dict:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = []
    data = load(SRC_JSON)
    queue_data = load(QUEUE_JSON)
    shadow_data = load(SHADOW_JSON)
    text = SRC_MD.read_text(encoding="utf-8", errors="ignore") if SRC_MD.exists() else ""
    serialized = json.dumps(data, ensure_ascii=False)

    queue_records = data.get("队列记录", [])
    shadow_tasks = data.get("影子任务", [])
    rejected = data.get("拒绝流转留痕", [])
    boundaries = data.get("安全边界", {})

    checks.append(check("主JSON存在", SRC_JSON.exists(), str(SRC_JSON)))
    checks.append(check("主Markdown存在", SRC_MD.exists(), str(SRC_MD)))
    checks.append(check("队列JSON存在", QUEUE_JSON.exists(), str(QUEUE_JSON)))
    checks.append(check("影子流转JSON存在", SHADOW_JSON.exists(), str(SHADOW_JSON)))
    checks.append(check("主JSON可解析", bool(data), data.get("名称", "未解析")))
    checks.append(check("队列JSON可解析", bool(queue_data), queue_data.get("名称", "未解析")))
    checks.append(check("影子流转JSON可解析", bool(shadow_data), shadow_data.get("名称", "未解析")))
    checks.append(check("样例数量为6", data.get("样例数量") == 6, data.get("样例数量")))
    checks.append(check("队列记录数量为6", len(queue_records) == 6 and queue_data.get("记录数量") == 6, len(queue_records)))
    checks.append(check("影子任务数量为5", len(shadow_tasks) == 5 and shadow_data.get("影子任务数量") == 5, len(shadow_tasks)))
    checks.append(check("拒绝流转数量为1", len(rejected) == 1 and shadow_data.get("拒绝流转数量") == 1, len(rejected)))
    checks.append(check("队列字段齐备", all(all(field in item for field in REQUIRED_QUEUE_FIELDS) for item in queue_records), [item.get("消息ID") for item in queue_records if not all(field in item for field in REQUIRED_QUEUE_FIELDS)]))
    checks.append(check("影子任务字段齐备", all(all(field in item for field in REQUIRED_SHADOW_FIELDS) for item in shadow_tasks), [item.get("消息ID") for item in shadow_tasks if not all(field in item for field in REQUIRED_SHADOW_FIELDS)]))
    checks.append(check("全部影子任务来源杰哥工作秘书", all(item.get("来源机器人") == "杰哥工作秘书" for item in shadow_tasks), [item.get("消息ID") for item in shadow_tasks if item.get("来源机器人") != "杰哥工作秘书"]))
    checks.append(check("影子任务不写正式库", all(item.get("是否写正式业务库") is False for item in shadow_tasks), "是否写正式业务库=False"))
    checks.append(check("影子任务不生成正式结论", all(item.get("是否生成正式税务结论") is False for item in shadow_tasks), "是否生成正式税务结论=False"))
    checks.append(check("拒绝项不进入影子任务", all(item.get("消息ID") not in {task.get("消息ID") for task in shadow_tasks} for item in rejected), rejected))
    checks.append(check("包含多税种场景", any("增值税" in item.get("适用税种猜测", []) for item in shadow_tasks) and any("企业所得税" in item.get("适用税种猜测", []) for item in shadow_tasks), [item.get("适用税种猜测") for item in shadow_tasks]))
    checks.append(check("包含资料补充流转", any(item.get("影子流转状态") == "pending_fact_completion" for item in shadow_tasks), [item.get("影子流转状态") for item in shadow_tasks]))
    checks.append(check("未发现未脱敏手机号身份证银行卡模式", not any(pattern.search(serialized) for pattern in SENSITIVE_PATTERNS), "sensitive-pattern-scan"))
    checks.append(check("硬边界全部为False", all(value is False for value in boundaries.values()), boundaries))
    checks.append(check("Markdown声明不是真实发送和税务结论", "不是真实发送记录" in text and "不是税务结论" in text, "资产身份声明"))

    failed = [item for item in checks if item["结果"] != "通过"]
    result = {
        "名称": "税收企业微信脱敏样例批量入队影子流转验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信脱敏样例批量入队影子流转验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
