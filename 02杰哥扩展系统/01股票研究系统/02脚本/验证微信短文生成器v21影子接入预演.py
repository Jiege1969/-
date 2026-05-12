# -*- coding: utf-8 -*-
"""
名称：验证微信短文生成器v21影子接入预演.py
作用：验收微信短文生成器 v2.1 影子接入预演是否满足字段、短文、安全边界和正式入口不变更要求。
触发方式：python 验证微信短文生成器v21影子接入预演.py
安全边界：只读影子预演和正式入口快照；只写验收报告；不改正式入口；不重启服务；不发送企业微信；不触发n8n；不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "218微信短文生成器v21影子接入预演"
PREVIEW_JSON = OUT_DIR / "微信短文生成器v21影子接入预演_最新.json"
PREVIEW_MD = OUT_DIR / "微信短文生成器v21影子接入预演_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
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


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    preview = load_json(PREVIEW_JSON)
    md = load_text(PREVIEW_MD)
    text = json.dumps(preview, ensure_ascii=False) + "\n" + md
    fields = preview.get("字段覆盖", [])
    short = preview.get("影子短文预览", "")
    safety = preview.get("安全边界", {})
    snapshots = preview.get("正式入口快照", [])
    required_fields = ["股票名称和一句话结论", "逻辑", "财务", "观察条件", "转强条件", "失败条件", "风险", "详情路径"]
    banned_words = ["买入", "卖出", "下单", "调仓", "目标价", "收益承诺", "自动交易", "券商接口"]

    snapshot_ok = True
    snapshot_details = []
    for item in snapshots:
        path = Path(item.get("路径", ""))
        current_hash = sha256(path)
        ok = bool(item.get("存在")) and current_hash == item.get("sha256")
        snapshot_ok = snapshot_ok and ok
        snapshot_details.append(f"{path.name}:{'ok' if ok else 'changed'}")

    checks = [
        check(PREVIEW_JSON.exists() and PREVIEW_MD.exists(), "预演 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(all(field in fields for field in required_fields), "字段覆盖完整", ",".join(required_fields)),
        check("影子接入" in text and "不替换正式微信回复入口" in text, "明确仍为影子接入", ""),
        check(all(word in short for word in ["观察条件", "转强条件", "失败条件", "财务", "风险"]), "短文包含6+1关键段", ""),
        check(("估算" in short) or ("待核验" in short), "短文包含估算或待核验降级提示", ""),
        check(not any(word in short for word in banned_words), "短文不包含交易或收益承诺表达", ",".join(banned_words)),
        check(len(short) >= 300, "短文不是空壳摘要", f"长度={len(short)}"),
        check(len(snapshots) == 3 and all(item.get("存在") for item in snapshots), "三份正式入口文件存在", ""),
        check(snapshot_ok, "正式入口文件哈希与预演快照一致", ";".join(snapshot_details)),
        check(all(value is False for value in safety.values()), "安全边界全部为False", json.dumps(safety, ensure_ascii=False)),
        check("不得重启19300" in text and "不得重启19302" in text, "明确禁止重启正式入口", ""),
        check("不得发送企业微信真实消息" in text and "不得触发n8n" in text, "明确禁止真实发送和n8n", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "微信短文生成器v21影子接入预演验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        },
    }
    latest_json = OUT_DIR / "微信短文生成器v21影子接入预演验收_最新.json"
    latest_md = OUT_DIR / "微信短文生成器v21影子接入预演验收_最新.md"
    lines = [
        "# 微信短文生成器 v2.1 影子接入预演验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, report)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
