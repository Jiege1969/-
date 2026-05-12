# -*- coding: utf-8 -*-
"""
名称：生成微信短文正式生成器正式成交额口径对照包.py
作用：汇总旧正式草稿、222当前v21正式口径版和229正式成交额口径版，生成正式生成器影子分支对照包。
安全边界：只读本地草稿和影子产物；只写 03数据/230微信短文正式生成器正式成交额口径对照包；不改正式入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "230微信短文正式生成器正式成交额口径对照包"
CURRENT_REPLY_MD = DATA / "24企业微信短回复" / "企业微信单股短回复_最新.md"
SHADOW_222_JSON = DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演_最新.json"
SHADOW_222_VERIFY = DATA / "222微信短文正式生成器影子分支接入预演" / "微信短文正式生成器影子分支接入预演验收_最新.json"
FORMAL_229_JSON = DATA / "229微信短文正式成交额口径影子重跑" / "微信短文正式成交额口径影子重跑_最新.json"
FORMAL_229_VERIFY = DATA / "229微信短文正式成交额口径影子重跑" / "微信短文正式成交额口径影子重跑验收_最新.json"
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


def word_hits(text: str, words: list[str]) -> dict[str, bool]:
    return {word: word in text for word in words}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 微信短文正式生成器正式成交额口径对照包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、对照结果",
        "",
    ]
    for key, value in report["对照结果"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、正式成交额口径影子短文", "", report["正式成交额口径影子短文"], "", "## 三、入口快照", ""])
    for item in report["正式入口快照"]:
        lines.append(f"- `{item['路径']}`：sha256={item.get('sha256', '')[:12]}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    current_reply = load_text(CURRENT_REPLY_MD)
    shadow_222 = load_json(SHADOW_222_JSON)
    shadow_222_verify = load_json(SHADOW_222_VERIFY)
    formal_229 = load_json(FORMAL_229_JSON)
    formal_229_verify = load_json(FORMAL_229_VERIFY)
    old_v21_text = str(shadow_222.get("影子短文输出", ""))
    formal_text = str(formal_229.get("微信短文", ""))
    required = ["观察条件", "转强条件", "失败条件", "风险", "详情", "声明"]
    banned = ["买入", "卖出", "下单", "调仓", "目标价", "收益承诺"]
    report = {
        "名称": "微信短文正式生成器正式成交额口径对照包",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": formal_229.get("样本股票", {}),
        "当前结论": "正式生成器影子分支已具备正式成交额口径对照包；默认正式入口仍不替换、不发送。",
        "读取文件": {
            "当前正式短回复草稿": str(CURRENT_REPLY_MD),
            "222当前v21影子分支": str(SHADOW_222_JSON),
            "222验收": str(SHADOW_222_VERIFY),
            "229正式成交额口径短文": str(FORMAL_229_JSON),
            "229验收": str(FORMAL_229_VERIFY),
        },
        "对照结果": {
            "222验收通过": shadow_222_verify.get("结论") == "通过",
            "229验收通过": formal_229_verify.get("结论") == "通过",
            "旧正式草稿长度": len(current_reply),
            "222当前v21正式口径版长度": len(old_v21_text),
            "229正式成交额口径版长度": len(formal_text),
            "222当前v21已移除估算降级": "估算口径" not in old_v21_text and "待正式成交额源回补" not in old_v21_text,
            "229正式口径版移除估算降级": "估算口径" not in formal_text and "待正式成交额源回补" not in formal_text,
            "222当前v21使用正式阈值": "250.85亿元" in old_v21_text and "301.02亿元" in old_v21_text,
            "229正式口径版使用阈值": "250.85亿元" in formal_text and "301.02亿元" in formal_text,
            "正式口径版关键字段命中": word_hits(formal_text, required),
            "正式口径版禁用交易词命中": word_hits(formal_text, banned),
            "建议默认切换正式入口": False,
            "建议仅实现默认关闭dry_run双写": True,
        },
        "旧正式草稿": current_reply,
        "222当前v21正式口径影子短文": old_v21_text,
        "正式成交额口径影子短文": formal_text,
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
        "下一步计划": "如继续推进，只能实现默认关闭的 --shadow-v21-dry-run 双写参数；正式入口替换和真实发送继续停下报告。",
    }
    latest_json = OUT_DIR / "微信短文正式生成器正式成交额口径对照包_最新.json"
    latest_md = OUT_DIR / "微信短文正式生成器正式成交额口径对照包_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "222当前v21正式口径版长度": len(old_v21_text),
        "229正式成交额口径版长度": len(formal_text),
        "建议默认切换正式入口": False,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
