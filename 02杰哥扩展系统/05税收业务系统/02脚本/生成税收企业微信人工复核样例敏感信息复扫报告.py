# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核敏感信息复扫"
SOURCES = [
    ("人工复核整改后再校验样例模板", BASE_DIR / "税收企业微信人工复核整改后再校验样例模板_最新.json"),
    ("人工复核校验失败整改清单", BASE_DIR / "税收企业微信人工复核校验失败整改清单_最新.json"),
    ("待复核分析草案出入口状态索引", BASE_DIR / "税收企业微信待复核分析草案出入口状态索引_最新.json"),
    ("出入口索引反事实校验", BASE_DIR / "税收企业微信待复核分析草案出入口索引反事实校验_最新.json"),
]
OUT_JSON = BASE_DIR / "税收企业微信人工复核样例敏感信息复扫报告_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核样例敏感信息复扫报告_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核样例敏感信息复扫报告.json"


PATTERNS = {
    "疑似手机号": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "疑似身份证号": re.compile(r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])"),
    "疑似银行卡号": re.compile(r"(?<!\d)\d{16,19}(?!\d)"),
    "疑似Webhook地址": re.compile(r"https?://[^\s\"']*(webhook|qyapi|weixin|wechat)[^\s\"']*", re.IGNORECASE),
    "疑似Token或Secret赋值": re.compile(r"(token|secret|key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
}
FORMAL_CONCLUSION_WORDS = ["confirmed_conclusion", "formal_tax_conclusion", "一定适用", "可以享受", "金额确定", "正式税务意见"]
SAFE_RULE_LOCATIONS = [
    "禁止",
    "填写要求",
    "重新提交条件",
    "再校验步骤",
    "系统定位",
    "资产身份",
    "状态流规则",
    "场景",
    "阻断原因",
    "说明",
    "下一步",
    "限制",
]

SAFETY = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
    "是否写草案源文件": False,
    "是否真实回写状态": False,
    "是否调用模型推理": False,
    "是否接电子税务局": False,
    "是否接财税软件": False,
    "是否生成正式税务结论": False,
    "是否形成正式复核结论": False,
    "是否覆盖历史资料": False,
    "是否删除历史审计记录": False,
}


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def walk_values(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(obj, dict):
        result = []
        for key, value in obj.items():
            result.extend(walk_values(value, f"{prefix}.{key}" if prefix else str(key)))
        return result
    if isinstance(obj, list):
        result = []
        for idx, value in enumerate(obj):
            result.extend(walk_values(value, f"{prefix}[{idx}]"))
        return result
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return [(prefix, "" if obj is None else str(obj))]
    return []


def scan_source(name: str, path: Path) -> dict:
    data = load_json(path)
    values = walk_values(data)
    sensitive_hits = []
    formal_hits = []
    for location, value in values:
        for pattern_name, pattern in PATTERNS.items():
            if pattern.search(value):
                sensitive_hits.append({"位置": location, "类型": pattern_name, "片段": value[:80]})
        for word in FORMAL_CONCLUSION_WORDS:
            if word in value:
                if any(marker in location for marker in SAFE_RULE_LOCATIONS):
                    continue
                if f"不是{word}" in value or f"不得{word}" in value or f"不得把" in value:
                    continue
                formal_hits.append({"位置": location, "类型": "正式结论短语", "词": word})
    return {
        "来源名称": name,
        "路径": str(path),
        "是否存在": path.exists(),
        "扫描值数量": len(values),
        "敏感信息命中数量": len(sensitive_hits),
        "正式结论短语命中数量": len(formal_hits),
        "敏感信息命中": sensitive_hits,
        "正式结论短语命中": formal_hits,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scan_results = [scan_source(name, path) for name, path in SOURCES]
    sensitive_count = sum(item["敏感信息命中数量"] for item in scan_results)
    formal_count = sum(item["正式结论短语命中数量"] for item in scan_results)
    result = {
        "名称": "税收企业微信人工复核样例敏感信息复扫报告",
        "生成时间": now,
        "资产身份": "dry-run敏感信息复扫报告，不读取凭据，不真实发送，不写正式业务库，不是税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "扫描来源数量": len(SOURCES),
        "敏感信息命中总数": sensitive_count,
        "正式结论短语命中总数": formal_count,
        "扫描结果": scan_results,
        "复扫结论": "通过" if sensitive_count == 0 and formal_count == 0 else "待人工核查",
        "说明": [
            "本复扫使用格式化模式识别手机号、身份证号、银行卡号、Webhook地址和Token/Secret赋值形态。",
            "本复扫不读取环境变量、不读取企业微信凭据、不联网。",
            "如未来样例加入真实业务文本，应先脱敏后再进入本地校验预演。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信人工复核链路阶段收口索引。",
            "生成税收企业微信人工复核链路一键本地预检脚本。"
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核样例敏感信息复扫报告",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run复扫报告，不读取凭据，不真实发送，不写正式业务库，不是税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        f"- 扫描来源数量：{len(SOURCES)}",
        f"- 敏感信息命中总数：{sensitive_count}",
        f"- 正式结论短语命中总数：{formal_count}",
        f"- 复扫结论：{result['复扫结论']}",
        "",
        "## 扫描结果",
        "",
    ]
    for item in scan_results:
        lines.append(f"- {item['来源名称']}：存在={item['是否存在']}，扫描值={item['扫描值数量']}，敏感命中={item['敏感信息命中数量']}，正式结论短语命中={item['正式结论短语命中数量']}。")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": result["复扫结论"], "报告": str(OUT_MD), "敏感信息命中总数": sensitive_count, "正式结论短语命中总数": formal_count}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
