# -*- coding: utf-8 -*-
"""
名称：task_generator.py
作用：把视频工厂聊天入口的一句话输入转换为轮次012结构化任务单。
触发方式：由 video_factory_chat.py 调用 generate_task(user_input)。
依赖：Python 标准库；01配置/视频工厂合规规则.json。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只生成本地预演任务单；默认不放行真实渲染、外部素材接口、自动发布或企业微信外发。
创建/修改记录：2026-05-07 创建轮次012视频工厂总控层任务生成器。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
RULES_PATH = ROOT / "01配置" / "视频工厂合规规则.json"
OUTPUT_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _next_sequence(today: str) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(rf"VF-{today}-(\d{{3}})")
    max_seq = 0
    for path in OUTPUT_DIR.rglob("*.json"):
        match = pattern.search(path.name)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
            continue
        try:
            data = load_json(path, {})
            task_id = str(data.get("任务ID", ""))
            match = pattern.search(task_id)
            if match:
                max_seq = max(max_seq, int(match.group(1)))
        except Exception:  # noqa: BLE001
            continue
    return max_seq + 1


def build_task_id(now: datetime | None = None) -> str:
    current = now or datetime.now()
    today = current.strftime("%Y%m%d")
    sequence = _next_sequence(today)
    return f"VF-{today}-{sequence:03d}"


def analyze_intent(user_input: str) -> dict[str, str]:
    """预留 NLP 接入口；当前先用低风险关键词规则识别主题方向。"""
    text = user_input.strip()
    rules = load_json(RULES_PATH, {})
    words = rules.get("词库", {})
    if _contains_any(text, words.get("成语故事", [])):
        return {
            "主题": text,
            "表达角度": "成语故事的古今结合解读",
            "受众人群": "喜欢传统文化和生活启发的普通用户",
            "视频类型": "成语故事短视频口播",
        }
    if _contains_any(text, words.get("经典语录", [])):
        return {
            "主题": text,
            "表达角度": "经典语录的生活化拆解",
            "受众人群": "关注人生哲理和生活感悟的用户",
            "视频类型": "经典语录短视频口播",
        }
    if any(word in text for word in ["30", "朋友", "交友", "孤独", "关系"]):
        return {
            "主题": text,
            "表达角度": "成年人关系中的共鸣与反思",
            "受众人群": "30岁上下关注关系和自我成长的用户",
            "视频类型": "短视频口播",
        }
    return {
        "主题": text,
        "表达角度": "从一个具体生活场景引出普适感悟",
        "受众人群": "关注生活常识、人生哲理和日常感悟的用户",
        "视频类型": "短视频口播",
    }


def compliance_check(user_input: str, task_definition: dict[str, Any]) -> dict[str, Any]:
    """根据独立配置词库执行轮次012合规门禁预检。"""
    rules = load_json(RULES_PATH, {})
    words = rules.get("词库", {})
    text = f"{user_input} {task_definition.get('主题', '')} {task_definition.get('表达角度', '')}"
    gate_items: list[str] = []
    advice_items = ["请在实际写作时增加一个真人生活化细节或具体场景，避免AI感堆砌"]
    result: dict[str, Any] = {
        "risk_level": "低风险",
        "reason": "未命中高风险词",
        "advice": "可进入本地脚本与分镜预演，仍需人工复核",
        "force_emotion": "",
        "gate_items": gate_items,
        "advice_items": advice_items,
        "matched_keywords": {},
    }

    # 规则来源：平台合规要求禁止封建迷信和绝对化医疗承诺。
    high_risk_words = words.get("高风险_封建迷信与绝对化医疗", [])
    matched_high = [keyword for keyword in high_risk_words if keyword and keyword in text]
    if matched_high:
        result["risk_level"] = "高风险"
        result["reason"] = "内容涉及封建迷信/绝对化医疗建议"
        result["advice"] = "建议驳回或修改主题表述"
        result["matched_keywords"]["高风险_封建迷信与绝对化医疗"] = matched_high
        gate_items.append(f"命中高风险词：{', '.join(matched_high)}；内容涉及封建迷信/绝对化医疗建议")

    # 规则来源：平台合规要求拒绝焦虑贩卖，命中后必须改写情绪基调。
    anxiety_words = words.get("焦虑诱导", [])
    matched_anxiety = [keyword for keyword in anxiety_words if keyword and keyword in text]
    if matched_anxiety:
        result["force_emotion"] = "拒绝焦虑"
        result["matched_keywords"]["焦虑诱导"] = matched_anxiety
        gate_items.append("检测到焦虑诱导词，已强制修改情绪基调，请人工确认")

    # 规则来源：成语故事类内容需要知识增量，禁止仅翻译原文或洗稿。
    idiom_words = words.get("成语故事", [])
    matched_idiom = [keyword for keyword in idiom_words if keyword and keyword in text]
    if matched_idiom:
        result["matched_keywords"]["成语故事"] = matched_idiom
        gate_items.append("成语故事主题，请强制增加古今结合原创解读，禁止仅翻译原文")

    return result


def generate_task(user_input: str, session_id: str = "") -> dict[str, Any]:
    """生成轮次012视频工厂任务单；所有高风险动作默认关闭。"""
    clean_input = user_input.strip()
    if not clean_input:
        raise ValueError("用户输入不能为空")

    rules = load_json(RULES_PATH, {})
    defaults = rules.get("默认会话", {})
    now = datetime.now()
    intent = analyze_intent(clean_input)

    # 安全规则来源：轮次012总控层默认只允许脚本与分镜预演，不放行真实渲染或自动发布。
    task = {
        "任务ID": build_task_id(now),
        "来源": "聊天对话入口",
        "会话来源": defaults.get("会话来源", "企业微信"),
        "会话ID": session_id,
        "最近指令": clean_input,
        "等待用户确认项": defaults.get("等待用户确认项", []),
        "原始输入": clean_input,
        "任务生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "预演中",
        "任务定义": {
            "主题": intent["主题"],
            "表达角度": intent["表达角度"],
            "受众人群": intent["受众人群"],
            "视频类型": intent["视频类型"],
            "目标画面比例": ["9:16", "16:9"],
            "关键情绪": "共鸣、反思、不贩卖焦虑",
        },
        "生成控制": {
            "阶段": "脚本与分镜预演",
            "允许真实渲染": False,
            "允许调用外部素材API": False,
            "允许自动发布": False,
            "人工复核状态": "待确认",
            "门禁检查项": [
                "轮次012默认只生成本地预演任务单",
                "真实渲染、自动发布和企业微信真实外发均未放行",
            ],
        },
        "生成建议": "建议先生成选题角度、脚本草案、分镜草案，再等待人工复核。",
    }
    compliance = compliance_check(clean_input, task["任务定义"])
    task["合规检查"] = compliance
    if compliance.get("risk_level") == "高风险":
        task["生成控制"]["人工复核状态"] = "高风险-需人工驳回建议"
        task["状态"] = "待人工复核"
    if compliance.get("force_emotion"):
        task["任务定义"]["关键情绪"] = compliance["force_emotion"]
    task["生成控制"]["门禁检查项"].extend(compliance.get("gate_items", []))
    for advice in compliance.get("advice_items", []):
        if advice not in task["生成建议"]:
            task["生成建议"] = f"{task['生成建议']} {advice}"
    return task


__all__ = ["analyze_intent", "compliance_check", "generate_task", "build_task_id"]
