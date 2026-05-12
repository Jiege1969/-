# -*- coding: utf-8 -*-
"""执行多机器人企业微信需求反馈本地入账。

复用 74 三业务反馈样本闭环包，支持股票、税收、视频、办公内容、系统管家五类机器人反馈。
只写候选台账和拒收清单，不改公共接入层运行代码，不重载 19310/19302。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"
INBOX_DIR = DATA_DIR / "企业微信需求反馈待入账"
RESULT_JSON = DATA_DIR / "多机器人企业微信需求反馈本地入账结果_最新.json"
RESULT_MD = DATA_DIR / "多机器人企业微信需求反馈本地入账结果_最新.md"
LEDGER_JSON = DATA_DIR / "多机器人企业微信需求反馈候选台账_最新.json"
LEDGER_MD = DATA_DIR / "多机器人企业微信需求反馈候选台账_最新.md"
REJECT_JSON = DATA_DIR / "多机器人企业微信需求反馈拒收清单_最新.json"

BUSINESS_ALIASES = {
    "stock": "股票",
    "股票": "股票",
    "股票分析助手": "股票",
    "股票分析专家": "股票",
    "tax": "税收",
    "税收": "税收",
    "工作秘书": "税收",
    "tax-review": "税收",
    "video": "视频",
    "视频": "视频",
    "视频助理": "视频",
    "office": "办公内容",
    "办公": "办公内容",
    "办公内容": "办公内容",
    "内容处理": "办公内容",
    "system": "系统管家",
    "系统": "系统管家",
    "系统管家": "系统管家",
}
ALLOWED_BUSINESSES = {"股票", "税收", "视频", "办公内容", "系统管家"}

SAFETY_BOUNDARY = {
    "修改公共接入层运行代码": False,
    "重载19310": False,
    "重载19302": False,
    "真实发送企业微信": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "真实发布视频": False,
    "写正式规则库": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
}

BUILT_IN_SAMPLES = [
    {
        "来源机器人": "股票分析专家",
        "业务线": "股票",
        "用户原始输入": "今日观察报告里股票名称应该可以点击，能看具体分析报告",
        "系统输出摘要": "股票观察晨报已生成",
        "用户判定": "展示需求，需要可点击详情入口",
    },
    {
        "来源机器人": "杰哥工作秘书",
        "业务线": "税收",
        "用户原始输入": "税收资料清单缺少政策依据来源，不要写成正式结论",
        "系统输出摘要": "税收待复核草案摘要",
        "用户判定": "口径要更保守，并补政策来源",
    },
    {
        "来源机器人": "杰哥视频助理",
        "业务线": "视频",
        "用户原始输入": "这个脚本太平，分镜要增加故事动作和现代解读",
        "系统输出摘要": "视频脚本草案",
        "用户判定": "内容质量反馈，进入脚本改版候选",
    },
    {
        "来源机器人": "办公内容助手",
        "业务线": "办公内容",
        "用户原始输入": "这个材料框架缺少结论页，口吻要更像给领导看的汇报",
        "系统输出摘要": "本地办公草案预演",
        "用户判定": "本地草案结构和口吻需求",
    },
    {
        "来源机器人": "杰哥系统管家",
        "业务线": "系统管家",
        "用户原始输入": "进度不要只报百分比，要告诉我卡在哪里、还差多少有效工时",
        "系统输出摘要": "系统进度摘要",
        "用户判定": "状态汇报方式需要改进",
    },
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_business(value: Any, robot: Any = "") -> str:
    text = str(value or "").strip()
    robot_text = str(robot or "").strip()
    for source in (text, robot_text):
        if source in BUSINESS_ALIASES:
            return BUSINESS_ALIASES[source]
        for key, mapped in BUSINESS_ALIASES.items():
            if key and key in source:
                return mapped
    return text


def classify_problem(text: str, business: str) -> str:
    value = str(text or "")
    if any(word in value for word in ("点击", "链接", "详情入口", "具体分析报告")):
        return "展示/链接需求"
    if any(word in value for word in ("缺少", "少了", "补充", "添加", "应该有", "需要有")):
        return "摘要遗漏/内容补充"
    if any(word in value for word in ("太空泛", "太平", "不够具体", "泛泛")):
        return "表达空泛"
    if any(word in value for word in ("风险", "正式结论", "口径", "依据")):
        return "口径或风险提示"
    if business == "系统管家" and any(word in value for word in ("进度", "工时", "卡在哪里", "汇报")):
        return "状态汇报需求"
    return "其他"


def suggest_action(problem_type: str, business: str) -> str:
    matrix = {
        "展示/链接需求": "进入展示层影子改版候选，验证手机端可读性和链接可达性。",
        "摘要遗漏/内容补充": "进入内容补充候选，要求下一版输出补足用户点名缺口。",
        "表达空泛": "进入表达质量候选，要求输出包含具体对象、判断理由、缺口和下一步观察。",
        "口径或风险提示": "进入口径收紧候选，优先补依据、边界和人工复核提示。",
        "状态汇报需求": "进入系统管家汇报口径候选，增加阻断项、剩余工时和下一步动作。",
    }
    action = matrix.get(problem_type, "保留为业务反馈候选，等待复盘归纳。")
    if business == "税收":
        action += " 税收侧不得生成正式税务结论。"
    if business == "视频":
        action += " 视频侧不得真实渲染或发布。"
    if business == "股票":
        action += " 股票侧不得连接券商或形成交易指令。"
    return action


def feedback_key(item: dict[str, Any]) -> str:
    raw = "|".join(
        str(item.get(key, ""))
        for key in ("来源机器人", "业务线", "用户原始输入", "用户判定")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_item(item: dict[str, Any], source_file: str) -> tuple[dict[str, Any] | None, str]:
    robot = str(item.get("来源机器人") or item.get("机器人") or item.get("使用入口") or "").strip()
    business = normalize_business(item.get("业务线") or item.get("业务域"), robot)
    user_text = str(item.get("用户原始输入") or item.get("输入原文") or item.get("反馈原文") or item.get("text") or "").strip()
    output_summary = str(item.get("系统输出摘要") or item.get("回复摘要") or item.get("系统返回摘要") or "").strip()
    judgement = str(item.get("用户判定") or item.get("期望结果") or item.get("反馈判定") or "").strip()
    if business not in ALLOWED_BUSINESSES:
        return None, f"业务线不支持：{business or '空'}"
    if not user_text:
        return None, "缺少用户原始输入"
    problem_type = classify_problem(f"{user_text} {judgement}", business)
    normalized = {
        "来源文件": source_file,
        "来源机器人": robot or f"{business}机器人",
        "业务线": business,
        "用户原始输入": user_text,
        "系统输出摘要": output_summary,
        "用户判定": judgement,
        "问题类型": problem_type,
        "建议动作": suggest_action(problem_type, business),
        "是否触红线": False,
        "是否可自动吸收": False,
        "需人工确认": True,
        "转正式规则": False,
        "去重键": "",
        "入账时间": now_text(),
    }
    normalized["去重键"] = feedback_key(normalized)
    return normalized, ""


def collect_input_items(args: argparse.Namespace) -> list[tuple[dict[str, Any], str]]:
    items: list[tuple[dict[str, Any], str]] = []
    if args.use_built_in_samples:
        items.extend((sample, "built-in-sample") for sample in BUILT_IN_SAMPLES)
    if args.text:
        items.append(
            (
                {
                    "来源机器人": args.robot,
                    "业务线": args.business,
                    "用户原始输入": args.text,
                    "系统输出摘要": args.reply_summary,
                    "用户判定": args.judgement,
                },
                "cli",
            )
        )
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INBOX_DIR.glob("*.json")):
        try:
            data = read_json(path, {})
        except Exception as exc:  # noqa: BLE001
            items.append(({"__reject__": f"JSON不可解析：{exc}"}, str(path)))
            continue
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if isinstance(entry, dict):
                items.append((entry, str(path)))
            else:
                items.append(({"__reject__": "内容不是对象"}, str(path)))
    return items


def build_ledger_md(ledger: dict[str, Any]) -> str:
    lines = [
        "# 多机器人企业微信需求反馈候选台账",
        "",
        f"- 生成时间：{ledger['生成时间']}",
        f"- 候选数：{ledger['候选数']}",
        f"- 拒收数：{ledger['拒收数']}",
        "",
        "| 候选ID | 机器人 | 业务线 | 问题类型 | 需人工确认 | 转正式规则 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in ledger["候选"]:
        lines.append(
            f"| {item['候选ID']} | {item['来源机器人']} | {item['业务线']} | {item['问题类型']} | "
            f"{str(item['需人工确认']).lower()} | {str(item['转正式规则']).lower()} |"
        )
    if not ledger["候选"]:
        lines.append("| - | - | - | - | - | - |")
    lines.extend(["", "## 边界", "- 只写候选台账，不自动转正式规则，不重载19310/19302。"])
    return "\n".join(lines)


def build_result_md(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 多机器人企业微信需求反馈本地入账结果",
            "",
            f"- 生成时间：{result['生成时间']}",
            f"- 总体状态：{result['总体状态']}",
            f"- 扫描/输入数：{result['指标']['输入数']}",
            f"- 接收数：{result['指标']['接收数']}",
            f"- 去重拒收数：{result['指标']['去重拒收数']}",
            f"- 格式拒收数：{result['指标']['格式拒收数']}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", default="")
    parser.add_argument("--business", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--reply-summary", default="")
    parser.add_argument("--judgement", default="")
    parser.add_argument("--use-built-in-samples", action="store_true")
    args = parser.parse_args()

    existing_ledger = read_json(LEDGER_JSON, {})
    existing_candidates = existing_ledger.get("候选", []) if isinstance(existing_ledger.get("候选"), list) else []
    seen = {str(item.get("去重键")) for item in existing_candidates if item.get("去重键")}
    candidates = list(existing_candidates)
    rejects: list[dict[str, Any]] = []
    dedup_rejects: list[dict[str, Any]] = []

    raw_items = collect_input_items(args)
    for raw, source in raw_items:
        if "__reject__" in raw:
            rejects.append({"来源文件": source, "原因": raw["__reject__"]})
            continue
        normalized, reason = normalize_item(raw, source)
        if not normalized:
            rejects.append({"来源文件": source, "原因": reason, "原始项": raw})
            continue
        if normalized["去重键"] in seen:
            dedup_rejects.append({"来源文件": source, "原因": "重复反馈", "去重键": normalized["去重键"][:16]})
            continue
        seen.add(normalized["去重键"])
        normalized["候选ID"] = f"MULTI-WECOM-FB-{len(candidates) + 1:04d}"
        normalized["候选状态"] = "本地入账候选，等待影子验收和人工确认"
        candidates.append(normalized)

    ledger = {
        "名称": "多机器人企业微信需求反馈候选台账",
        "生成时间": now_text(),
        "候选数": len(candidates),
        "新增候选数": len(candidates) - len(existing_candidates),
        "拒收数": len(rejects) + len(dedup_rejects),
        "覆盖业务": sorted({item.get("业务线") for item in candidates}),
        "候选": candidates,
        "拒收": rejects,
        "去重拒收": dedup_rejects,
        "安全边界": SAFETY_BOUNDARY,
    }
    result = {
        "名称": "多机器人企业微信需求反馈本地入账结果",
        "生成时间": ledger["生成时间"],
        "总体状态": "pass",
        "指标": {
            "输入数": len(raw_items),
            "接收数": ledger["新增候选数"],
            "候选总数": ledger["候选数"],
            "去重拒收数": len(dedup_rejects),
            "格式拒收数": len(rejects),
        },
        "候选台账": str(LEDGER_JSON),
        "拒收清单": str(REJECT_JSON),
        "安全边界": SAFETY_BOUNDARY,
    }
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))
    write_json(REJECT_JSON, {"名称": "多机器人企业微信需求反馈拒收清单", "拒收": rejects, "去重拒收": dedup_rejects})
    write_json(RESULT_JSON, result)
    write_text(RESULT_MD, build_result_md(result))
    print(json.dumps({"总体状态": "pass", "新增候选数": ledger["新增候选数"], "候选总数": ledger["候选数"], "输出": str(RESULT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
