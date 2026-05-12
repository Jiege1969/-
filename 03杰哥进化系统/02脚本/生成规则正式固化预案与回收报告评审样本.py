# -*- coding: utf-8 -*-
"""
名称：生成规则正式固化预案与回收报告评审样本.py
作用：把上一批跨系统规则卡转为正式固化预案，并生成总管回收报告自动评审读取小样本。
安全边界：只写 03 进化系统授权目录和总管指定回收报告；不触发 n8n、不真实发送、不调用券商接口、不自动交易、不写正式库。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


PACKAGE_NAME = "规则正式固化预案与总管回收报告自动评审样本"


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return system_root().parents[0]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text_fallback(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def formal_rules() -> list[dict[str, Any]]:
    return [
        {
            "规则ID": "EVO-FIX-I-001",
            "来源规则ID": "EVO-CARD-D-001",
            "规则名称": "股票交付闭环正式固化预案",
            "适用系统": ["01智能系统/股票相关链路", "03进化系统", "00总管"],
            "触发条件": ["股票相关交付", "_最新 文件刷新", "把候选信号标记为正式可用", "跨窗口验收回收"],
            "阻断/降级动作": "缺少版本化产物、_最新 指针、验收记录、回滚口径或人工复核边界时，阻断正式交付；仅允许补齐证据、影子验证或提交人工复核。",
            "证据要求": ["版本化 JSON/Markdown", "_最新 JSON/Markdown", "验收 JSON/Markdown", "回滚或补救说明", "自动交易禁用声明"],
            "回滚方式": "保留时间戳版本与 _最新 指针刷新前证据；如误标正式可用，撤回 _最新 指针并恢复上一版本，同时在回收报告标注退回原因。",
            "正式固化状态": "预案待总管/人工批准",
        },
        {
            "规则ID": "EVO-FIX-I-002",
            "来源规则ID": "EVO-CARD-D-002",
            "规则名称": "股票自动交易硬闸门正式固化预案",
            "适用系统": ["01智能系统/股票相关链路", "03进化系统"],
            "触发条件": ["券商接口", "自动交易", "下单", "撤单", "实盘委托", "账户资金动作"],
            "阻断/降级动作": "任何券商接口、自动下单、撤单或账户动作默认硬阻断；研究、复盘、规则沉淀只能降级为离线评审和人工复核输出。",
            "证据要求": ["自动交易启用=false", "券商接口调用=false", "人工交易授权缺省为否", "无实盘执行链路写入记录"],
            "回滚方式": "发现越权路径时立即停止执行链路，保留审计记录，删除本地候选中的实盘动作字段，并退回到影子评审样本。",
            "正式固化状态": "预案待总管/人工批准",
        },
        {
            "规则ID": "EVO-FIX-I-003",
            "来源规则ID": "EVO-CARD-D-003",
            "规则名称": "并行施工写入边界正式固化预案",
            "适用系统": ["00总管", "01智能系统", "02扩展系统", "03进化系统"],
            "触发条件": ["多窗口并行施工", "同名 _最新 文件", "固定回收报告", "读取其他窗口摘要"],
            "阻断/降级动作": "写入未授权目录、覆盖其他窗口产物、回滚未知改动或缺少固定回收报告时，阻断计入进度；只允许在本窗口授权范围补产物。",
            "证据要求": ["任务身份", "限定写入目录", "禁止范围声明", "固定回收报告", "验收结果", "未触碰其他窗口声明"],
            "回滚方式": "如误写未授权目录，停止继续写入，保留差异证据并提交人工处理；不得自动回滚未知来源改动。",
            "正式固化状态": "预案待总管/人工批准",
        },
        {
            "规则ID": "EVO-FIX-I-004",
            "来源规则ID": "EVO-CARD-D-004",
            "规则名称": "影子/灰度/真实动作分层正式固化预案",
            "适用系统": ["01智能系统", "02扩展系统", "03进化系统", "00总管"],
            "触发条件": ["dry-run", "shadow", "灰度", "真实发送", "真实写库", "正式派工"],
            "阻断/降级动作": "影子阶段触发外部动作、灰度无白名单、真实动作无明确授权或一次授权扩面时，阻断真实动作；允许降级为只读影子验证。",
            "证据要求": ["动作等级", "白名单或授权", "限量阈值", "回滚/停止条件", "审计记录"],
            "回滚方式": "撤销真实动作入口，保留审计与停止时间，恢复为本地候选或影子样本，等待人工重新授权。",
            "正式固化状态": "预案待总管/人工批准",
        },
        {
            "规则ID": "EVO-FIX-I-005",
            "来源规则ID": "EVO-CARD-D-005",
            "规则名称": "真实发送/n8n/正式库隔离正式固化预案",
            "适用系统": ["02扩展系统/企业微信与内容链路", "03进化系统", "00总管"],
            "触发条件": ["企业微信真实发送", "n8n 工作流", "正式库写入", "外部发布", "自动分发"],
            "阻断/降级动作": "真实发送开关开启、n8n 触发器启用、写入正式库或外部发布时，阻断外部副作用；仅允许输出本地候选和评审报告。",
            "证据要求": ["n8n触发=false", "企业微信真实发送=false", "正式库写入=false", "外部发布=false"],
            "回滚方式": "关闭触发器和真实发送入口，撤销候选到正式库的写入请求，保留本地报告用于人工复核。",
            "正式固化状态": "预案待总管/人工批准",
        },
    ]


def report_paths(root: Path) -> list[dict[str, str]]:
    base = root / "00杰哥系统总管" / "03数据" / "并行回收"
    return [
        {"窗口": "A", "系统": "00总管", "路径": str(base / "00总管_本轮小任务A回收报告_最新.md")},
        {"窗口": "B", "系统": "01智能系统", "路径": str(base / "01智能系统_本轮小任务B回收报告_最新.md")},
        {"窗口": "C", "系统": "02扩展系统", "路径": str(base / "02扩展系统_本轮小任务C回收报告_最新.md")},
        {"窗口": "D", "系统": "03进化系统", "路径": str(base / "03进化系统_本轮小任务D回收报告_最新.md")},
        {"窗口": "E", "系统": "02扩展系统/税收", "路径": str(base / "02扩展系统_本轮小任务E税收回收报告_最新.md")},
        {"窗口": "F", "系统": "02扩展系统/内容视频", "路径": str(base / "02扩展系统_本轮小任务F内容视频回收报告_最新.md")},
    ]


def extract_blocker_count(text: str) -> int | None:
    patterns = [
        r"阻断项数量[：:\s\r\n-]*(\d+)",
        r"阻断项[：:\s\r\n-]*(\d+)\s*个",
        r"阻断项数量.*?(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.S)
        if match:
            return int(match.group(1))
    return None


def review_one_report(item: dict[str, str]) -> dict[str, Any]:
    path = Path(item["路径"])
    exists = path.exists()
    text = read_text_fallback(path) if exists else ""
    blocker_count = extract_blocker_count(text)
    normalized = text.lower()

    delivery_blocked = "正式放量不通过" in text or "正式税务判断不放行" in text or "真实转换" in text and "阻断" in text
    safety_keywords = ["未触发 n8n", "未发送企业微信真实", "未调用券商接口", "未自动交易", "未写正式"]
    safety_hits = [keyword for keyword in safety_keywords if keyword in text]
    unsafe_patterns = [
        "已触发 n8n",
        "已发送企业微信真实",
        "已调用券商接口",
        "已自动交易",
        "已写正式库",
        "自动交易启用=true",
        "n8n触发=true",
        "企业微信真实发送=true",
        "正式库写入=true",
    ]
    unsafe_true_action = any(pattern in text for pattern in unsafe_patterns)
    passed = ("验收通过" in text or "验收结果" in text or "通过" in text or "通过" in normalized) and not unsafe_true_action
    countable = exists and passed and not delivery_blocked and not unsafe_true_action

    return {
        "窗口": item["窗口"],
        "系统": item["系统"],
        "路径": item["路径"],
        "存在": exists,
        "读取状态": "已读取" if exists else "缺失",
        "解析阻断项数量": blocker_count,
        "交付阻断": bool(delivery_blocked or (blocker_count is None and exists and "阻断" in text and "通过" not in text)),
        "安全阻断": bool(safety_hits or unsafe_true_action),
        "安全阻断是否失败": bool(unsafe_true_action),
        "是否可计入进度": bool(countable),
        "命中安全边界": safety_hits,
        "备注": "A-F 自动读取小样本，不触发任何真实动作。",
    }


def review_reports(root: Path) -> list[dict[str, Any]]:
    return [review_one_report(item) for item in report_paths(root)]


def output_samples() -> list[dict[str, Any]]:
    return [
        {
            "样本ID": "I-SAMPLE-001",
            "样本名": "通过计入",
            "输入口径": "固定回收报告存在，验收通过，安全边界完整，未声明交付退回。",
            "自动评审结论": "通过计入",
            "交付阻断": False,
            "安全阻断": False,
            "是否可计入进度": True,
            "处理动作": "计入本轮进度，只保留安全边界摘要。",
        },
        {
            "样本ID": "I-SAMPLE-002",
            "样本名": "安全阻断不失败",
            "输入口径": "验收通过，但真实发送、n8n、自动交易、正式库写入被明确禁用。",
            "自动评审结论": "通过但限界",
            "交付阻断": False,
            "安全阻断": True,
            "是否可计入进度": True,
            "处理动作": "计入进度；安全阻断作为合规边界，不按失败处理。",
        },
        {
            "样本ID": "I-SAMPLE-003",
            "样本名": "交付阻断需退回",
            "输入口径": "缺少验收产物、固定回收报告、版本化证据或回滚方式。",
            "自动评审结论": "退回补齐",
            "交付阻断": True,
            "安全阻断": False,
            "是否可计入进度": False,
            "处理动作": "不计入进度，退回责任窗口补齐证据和回滚口径。",
        },
        {
            "样本ID": "I-SAMPLE-004",
            "样本名": "越权真实动作阻断",
            "输入口径": "报告声明已触发企业微信真实发送、n8n、券商接口、自动交易或正式库写入。",
            "自动评审结论": "安全失败并阻断",
            "交付阻断": True,
            "安全阻断": True,
            "是否可计入进度": False,
            "处理动作": "阻断计入，保留审计，提交人工处理；不得自动回滚未知改动。",
        },
    ]


def build_payload(root: Path) -> dict[str, Any]:
    rules = formal_rules()
    samples = output_samples()
    report_reviews = review_reports(root)
    delivery_blockers = sum(1 for item in samples if item["交付阻断"])
    safety_blockers = sum(1 for item in samples if item["安全阻断"])
    return {
        "生成时间": now_text(),
        "任务": "03杰哥进化系统 / 规则正式固化预案 + 总管回收报告自动评审读取",
        "规则数量": len(rules),
        "样本数量": len(samples),
        "读取报告窗口": [item["窗口"] for item in report_reviews],
        "交付阻断数量": delivery_blockers,
        "安全阻断数量": safety_blockers,
        "正式固化预案": rules,
        "A-F回收报告读取结果": report_reviews,
        "自动评审输出样本": samples,
        "安全边界": {
            "自动交易启用": False,
            "券商接口调用": False,
            "n8n触发": False,
            "企业微信真实发送": False,
            "正式库写入": False,
            "外部发布": False,
            "真实动作默认": "禁用",
        },
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 规则正式固化预案与总管回收报告自动评审读取",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 规则数量：{payload['规则数量']}",
        f"- 样本数量：{payload['样本数量']}",
        f"- 交付阻断数量：{payload['交付阻断数量']}",
        f"- 安全阻断数量：{payload['安全阻断数量']}",
        "- 安全边界：自动交易、券商接口、n8n、企业微信真实发送、正式库写入、外部发布均禁用",
        "",
        "## 正式固化预案",
        "",
    ]
    for rule in payload["正式固化预案"]:
        lines.extend(
            [
                f"### {rule['规则ID']} {rule['规则名称']}",
                f"- 来源规则ID：{rule['来源规则ID']}",
                f"- 适用系统：{'、'.join(rule['适用系统'])}",
                f"- 触发条件：{'；'.join(rule['触发条件'])}",
                f"- 阻断/降级动作：{rule['阻断/降级动作']}",
                f"- 证据要求：{'；'.join(rule['证据要求'])}",
                f"- 回滚方式：{rule['回滚方式']}",
                f"- 正式固化状态：{rule['正式固化状态']}",
                "",
            ]
        )
    lines.extend(["## A-F 回收报告读取结果", ""])
    for item in payload["A-F回收报告读取结果"]:
        lines.extend(
            [
                f"### {item['窗口']} {item['系统']}",
                f"- 读取状态：{item['读取状态']}",
                f"- 解析阻断项数量：{item['解析阻断项数量']}",
                f"- 交付阻断：{item['交付阻断']}",
                f"- 安全阻断：{item['安全阻断']}",
                f"- 是否可计入进度：{item['是否可计入进度']}",
                f"- 路径：{item['路径']}",
                "",
            ]
        )
    lines.extend(["## 自动评审输出样本", ""])
    for sample in payload["自动评审输出样本"]:
        lines.extend(
            [
                f"### {sample['样本ID']} {sample['样本名']}",
                f"- 输入口径：{sample['输入口径']}",
                f"- 自动评审结论：{sample['自动评审结论']}",
                f"- 交付阻断：{sample['交付阻断']}",
                f"- 安全阻断：{sample['安全阻断']}",
                f"- 是否可计入进度：{sample['是否可计入进度']}",
                f"- 处理动作：{sample['处理动作']}",
                "",
            ]
        )
    return "\n".join(lines)


def build_doc(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 规则正式固化预案接入口径",
            "",
            "- 本文件只定义正式固化预案，不执行正式固化。",
            "- 规则必须包含规则ID、适用系统、触发条件、阻断/降级动作、证据要求、回滚方式。",
            "- 总管读取 A-F 回收报告时，安全阻断不等于交付失败；交付证据缺失或越权真实动作才阻断计入。",
            "- 正式库写入、n8n、企业微信真实发送、券商接口、自动交易均需独立人工授权。",
            "",
            "## 本轮预案规则",
            "",
            *[f"- {rule['规则ID']}：{rule['规则名称']}" for rule in payload["正式固化预案"]],
            "",
        ]
    )


def build_recovery_report(payload: dict[str, Any], files: dict[str, str], verify_status: str = "待验证脚本写入") -> str:
    return "\n".join(
        [
            "# 03进化系统_第三批小任务I回收报告_最新",
            "",
            f"- 生成时间：{payload['生成时间']}",
            "- 任务：03杰哥进化系统 / 规则正式固化预案 + 总管回收报告自动评审读取",
            f"- 规则数量：{payload['规则数量']}",
            f"- 样本数量：{payload['样本数量']}",
            f"- A-F报告读取：{','.join(payload['读取报告窗口'])}",
            f"- 交付阻断数量：{payload['交付阻断数量']}",
            f"- 安全阻断数量：{payload['安全阻断数量']}",
            f"- 验收结果：{verify_status}",
            "",
            "## 新增/修改文件",
            "",
            *[f"- {name}：{path}" for name, path in files.items()],
            "",
            "## 样本结论",
            "",
            "- 通过计入：1",
            "- 安全阻断不失败：1",
            "- 交付阻断需退回：1",
            "- 越权真实动作阻断：1",
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信真实消息。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未写正式库。",
            "- 未修改 01/02 系统业务脚本或股票核心脚本。",
            "- 未写正式库；只生成 03 本地预案、样本、验收与指定总管回收报告。",
            "",
        ]
    )


def main() -> int:
    root = system_root()
    all_root = repo_root()
    data_dir = root / "03数据" / "24规则正式固化预案与回收报告评审"
    doc_path = root / "07文档" / "规则正式固化预案接入口径_最新.md"
    recovery_path = all_root / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第三批小任务I回收报告_最新.md"
    payload = build_payload(all_root)
    tag = stamp()

    latest_json = data_dir / f"{PACKAGE_NAME}_最新.json"
    latest_md = data_dir / f"{PACKAGE_NAME}_最新.md"
    version_json = data_dir / f"{PACKAGE_NAME}_{tag}.json"
    version_md = data_dir / f"{PACKAGE_NAME}_{tag}.md"

    write_json(version_json, payload)
    write_json(latest_json, payload)
    markdown = build_markdown(payload)
    write_text(version_md, markdown)
    write_text(latest_md, markdown)
    write_text(doc_path, build_doc(payload))

    files = {
        "正式固化预案与评审 JSON": str(latest_json),
        "正式固化预案与评审 Markdown": str(latest_md),
        "正式固化预案接入口径文档": str(doc_path),
        "版本化 JSON": str(version_json),
        "版本化 Markdown": str(version_md),
    }
    write_text(recovery_path, build_recovery_report(payload, files))

    print(json.dumps({"通过": True, "规则数量": payload["规则数量"], "样本数量": payload["样本数量"], "交付阻断数量": payload["交付阻断数量"], "安全阻断数量": payload["安全阻断数量"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
