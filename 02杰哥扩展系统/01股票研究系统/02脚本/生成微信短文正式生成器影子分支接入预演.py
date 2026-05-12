# -*- coding: utf-8 -*-
"""
名称：生成微信短文正式生成器影子分支接入预演.py
作用：基于最新股票微信短文条件口径影子预览，生成正式企业微信单股短回复生成器的影子分支接入预演。
安全边界：只读正式短回复脚本、现有短回复草稿和 221 影子短文；只写 03数据/222微信短文正式生成器影子分支接入预演；不修改正式入口、不发送企业微信、不触发 n8n、不重启服务。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "222微信短文正式生成器影子分支接入预演"
SHADOW_JSON = DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览_最新.json"
SHADOW_VERIFY = DATA / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览验收_最新.json"
CURRENT_REPLY_MD = DATA / "24企业微信短回复" / "企业微信单股短回复_最新.md"
FORMAL_GENERATOR = ROOT / "02脚本" / "生成企业微信单股短回复.py"
BRIDGE_ENTRY = ROOT / "02脚本" / "股票企业微信桥接入口.py"
ASSISTANT_ENTRY = ROOT / "02脚本" / "股票助手入口.py"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


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
    if not path.exists():
        return {"路径": str(path), "存在": False, "sha256": ""}
    stat = path.stat()
    return {
        "路径": str(path),
        "存在": True,
        "大小": stat.st_size,
        "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "sha256": sha256(path),
    }


def check_words(text: str, words: list[str]) -> dict[str, bool]:
    return {word: word in text for word in words}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 微信短文正式生成器影子分支接入预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、影子分支策略",
        "",
    ]
    for item in report["影子分支策略"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 二、对照结果", ""])
    for key, value in report["对照结果"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、影子短文输出", "", report["影子短文输出"], "", "## 四、正式入口快照", ""])
    for item in report["正式入口快照"]:
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- `{item['路径']}`：{status}；sha256={item.get('sha256', '')[:12]}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 六、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    shadow = load_json(SHADOW_JSON)
    shadow_verify = load_json(SHADOW_VERIFY)
    current_reply = load_text(CURRENT_REPLY_MD)
    shadow_text = str(shadow.get("微信短文", "")).strip()
    current_words = ["操作策略", "稳住", "继续观察", "成交活跃度", "常规推荐", "图文详情"]
    shadow_required = ["观察条件", "转强条件", "失败条件", "风险", "详情", "声明"]
    banned_words = ["买入", "卖出", "下单", "调仓", "目标价", "收益承诺", "自动交易"]

    report = {
        "名称": "微信短文正式生成器影子分支接入预演",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": shadow.get("样本股票", {}),
        "当前结论": "影子分支接入预演已生成；建议正式短回复生成器先增加 shadow_v21 分支对照输出，不替换正式入口、不真实发送。",
        "读取文件": {
            "221微信短文影子预览": str(SHADOW_JSON),
            "221微信短文验收": str(SHADOW_VERIFY),
            "当前正式短回复草稿": str(CURRENT_REPLY_MD),
            "正式短回复生成器": str(FORMAL_GENERATOR),
        },
        "影子分支策略": [
            "`生成企业微信单股短回复.py` 保持 dry_run 正式草稿链路不变。",
            "新增 shadow_v21 分支时，只在本地同时写出 `正式草稿` 与 `v21影子短文` 对照包。",
            "shadow_v21 输出直接复用 221 的 6+1 条件口径短文，不触发企业微信发送。",
            "只有连续小样本对照验收通过后，才讨论正式短回复模板替换。",
            "正式入口、桥接入口、股票助手入口当前只做哈希快照，不写入、不重启。",
        ],
        "对照结果": {
            "221验收结论": shadow_verify.get("结论", "缺失"),
            "221短文长度": len(shadow_text),
            "当前正式草稿长度": len(current_reply),
            "当前草稿旧话术命中": check_words(current_reply, current_words),
            "影子短文关键字段命中": check_words(shadow_text, shadow_required),
            "影子短文禁用交易词命中": check_words(shadow_text, banned_words),
            "影子短文包含估算降级": "估算" in shadow_text and "待正式成交额源回补" in shadow_text,
            "影子短文披露成交额口径": ("估算" in shadow_text and "待正式成交额源回补" in shadow_text) or "东方财富历史K线正式成交额口径" in shadow_text,
            "影子短文保留本地详情": "D:\\杰哥智能化系统" in shadow_text,
        },
        "影子短文输出": shadow_text,
        "正式入口快照": [snapshot(FORMAL_GENERATOR), snapshot(BRIDGE_ENTRY), snapshot(ASSISTANT_ENTRY)],
        "安全边界": {
            "修改正式短回复生成器": False,
            "修改股票企业微信桥接入口": False,
            "修改股票助手入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "下一步计划": "生成影子分支接入验收；通过后进入正式成交额源补齐预演和小样本对照包，不替换正式入口。",
    }

    latest_json = OUT_DIR / "微信短文正式生成器影子分支接入预演_最新.json"
    latest_md = OUT_DIR / "微信短文正式生成器影子分支接入预演_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "221验收结论": report["对照结果"]["221验收结论"],
        "影子短文长度": len(shadow_text),
        "输出": str(latest_md),
        "未改正式入口": True,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
