# -*- coding: utf-8 -*-
"""
名称：生成企业微信短回复v21正式模板替换准入与回滚方案.py
作用：汇总220-231验收结果，生成企业微信短回复v21正式模板替换准入、灰度和回滚方案。
安全边界：只读本地验收产物和入口源码；只写03数据/234模板替换准入方案；不改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "234企业微信短回复v21正式模板替换准入"
FORMAL_GENERATOR = ROOT / "02脚本" / "生成企业微信单股短回复.py"
BRIDGE_ENTRY = ROOT / "02脚本" / "股票企业微信桥接入口.py"
ASSISTANT_ENTRY = ROOT / "02脚本" / "股票助手入口.py"


VERIFY_FILES = {
    "220价位成交额条件口径": DATA / "220价位成交额条件口径" / "股票价位成交额条件口径预览验收_最新.json",
    "221微信短文条件口径": DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览验收_最新.json",
    "222正式生成器影子分支": DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演验收_最新.json",
    "230正式成交额口径对照包": DATA / "230微信短文正式生成器正式成交额口径对照包" / "微信短文正式生成器正式成交额口径对照包验收_最新.json",
    "231参数验收": DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run参数验收_最新.json",
    "231实跑输出验收": DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json",
    "233历史K线受控刷新": DATA / "233历史K线东方财富增强受控刷新" / "重点关注池历史K线东方财富增强受控刷新验收_最新.json",
}
SHADOW_231 = DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复_shadow_v21_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "sha256": sha256(path),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信短回复 v21 正式模板替换准入与回滚方案",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、准入检查",
        "",
    ]
    for item in report["准入检查"]:
        lines.append(f"- {item['名称']}：{item['结论']}（{item['通过数量']}/{item['通过数量'] + item['失败数量']}）")
    lines.extend(["", "## 二、切换建议", ""])
    for item in report["切换建议"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、回滚方案", ""])
    for item in report["回滚方案"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    checks = []
    for name, path in VERIFY_FILES.items():
        data = load_json(path)
        checks.append({
            "名称": name,
            "路径": str(path),
            "存在": path.exists(),
            "结论": data.get("结论", "缺失"),
            "通过数量": int(data.get("通过数量", 0) or 0),
            "失败数量": int(data.get("失败数量", 1) or 1) if data.get("结论") != "通过" else int(data.get("失败数量", 0) or 0),
        })
    all_passed = all(item["存在"] and item["结论"] == "通过" and item["失败数量"] == 0 for item in checks)
    shadow = load_json(SHADOW_231)
    shadow_text = str(shadow.get("shadow_v21正式成交额口径短文", ""))
    ready = all_passed and "250.85亿元" in shadow_text and "301.02亿元" in shadow_text
    report = {
        "名称": "企业微信短回复v21正式模板替换准入与回滚方案",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": (
            "准入检查通过，可进入默认关闭的模板切换代码设计；正式默认切换和真实发送仍需人工确认。"
            if ready
            else "准入检查未全部通过，不允许进入模板切换。"
        ),
        "准入检查": checks,
        "入口快照": [snapshot(FORMAL_GENERATOR), snapshot(BRIDGE_ENTRY), snapshot(ASSISTANT_ENTRY)],
        "shadow_v21摘要": {
            "路径": str(SHADOW_231),
            "正式短回复长度": shadow.get("正式短回复长度"),
            "shadow_v21短文长度": shadow.get("shadow_v21短文长度"),
            "使用正式阈值": "250.85亿元" in shadow_text and "301.02亿元" in shadow_text,
            "未含估算降级": "估算口径" not in shadow_text and "待正式成交额源回补" not in shadow_text,
        },
        "切换建议": [
            "第一步只在 `生成企业微信单股短回复.py` 内新增默认关闭的 `--use-v21-template-dry-run` 或同等显式开关，不改变默认输出。",
            "第二步本地连续小样本 dry-run 对照通过后，再讨论是否把默认草稿模板切到 v21。",
            "第三步即使默认草稿模板切到 v21，也仍不等于企业微信真实发送；桥接入口、n8n、response_url 继续关闭。",
            "真实发送前必须另做灰度发送方案、人工确认和回滚演练。",
        ],
        "回滚方案": [
            "代码回滚：恢复 `生成企业微信单股短回复.py` 到本方案记录的入口快照前版本，或关闭新增显式开关。",
            "数据回滚：保留 `03数据/24企业微信短回复` 的旧草稿产物；如切换失败，重新运行默认旧模板草稿链路。",
            "历史K线回滚：如历史成交额刷新造成异常，可用 233 记录的刷新前备份恢复 `11历史行情` 最新快照。",
            "发送回滚：本阶段未真实发送；如未来进入灰度发送，必须先保留发送日志、response_url 指纹和人工停止开关。",
        ],
        "安全边界": {
            "修改正式短回复生成器": False,
            "修改股票企业微信桥接入口": False,
            "修改股票助手入口": False,
            "默认切换正式模板": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信短回复v21正式模板替换准入与回滚方案_最新.json"
    latest_md = OUT_DIR / "企业微信短回复v21正式模板替换准入与回滚方案_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "准入通过": ready,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
