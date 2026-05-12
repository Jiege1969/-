# -*- coding: utf-8 -*-
"""
名称：验证股票报告证据源映射预览.py
作用：验收股票报告证据源映射预览是否覆盖报告、行情、微信契约、正式入口快照、正式依据缺口和非交易边界。
安全边界：只读影子映射产物和正式入口快照；只写验收报告；不改正式入口，不重启服务，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "219股票报告证据源映射"
PREVIEW_JSON = OUT_DIR / "股票报告证据源映射预览_最新.json"
PREVIEW_MD = OUT_DIR / "股票报告证据源映射预览_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票报告证据源映射预览验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    preview = load_json(PREVIEW_JSON)
    md = read_text(PREVIEW_MD)
    fields = preview.get("字段证据映射", [])
    blockers = preview.get("正式依据缺口", [])
    sources = preview.get("证据源清单", [])
    safety = preview.get("安全边界", {})
    stock = preview.get("样本股票", {})
    market = preview.get("行情源", {})
    formal_snapshot = preview.get("正式入口快照", [])

    snapshot_ok = True
    snapshot_details: list[str] = []
    for item in formal_snapshot:
        path = Path(item.get("路径", ""))
        current_hash = sha256(path)
        ok = bool(item.get("存在")) and current_hash == item.get("sha256")
        snapshot_ok = snapshot_ok and ok
        snapshot_details.append(f"{path.name}:{'ok' if ok else 'changed'}")

    field_names = [item.get("字段", "") for item in fields]
    source_roles = [item.get("证据角色", "") for item in sources]
    blocker_names = [item.get("缺口", "") for item in blockers]
    text = json.dumps(preview, ensure_ascii=False) + "\n" + md

    checks = [
        check(PREVIEW_JSON.exists() and PREVIEW_MD.exists(), "预览 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(stock.get("代码") == "300502" and "新易盛" in stock.get("名称", ""), "样本股票识别正确", json.dumps(stock, ensure_ascii=False)),
        check(len(sources) >= 4 and {"报告正文证据", "公开行情快照", "微信短文v2.1契约影子预演"}.issubset(set(source_roles)), "证据源角色覆盖报告、行情、微信契约", ",".join(source_roles)),
        check(market.get("来源") == "东方财富公开行情接口", "行情源为东方财富公开行情接口", str(market.get("来源"))),
        check(bool(market.get("样本行情")) and float(market.get("样本行情", {}).get("最新价", 0)) > 0, "样本行情包含有效当前价", json.dumps(market.get("样本行情", {}), ensure_ascii=False)),
        check(any("当前价" in name for name in field_names) and any("承接区" in name for name in field_names), "字段映射包含行情和价位字段", ",".join(field_names)),
        check(any("财务支持度" in name for name in field_names) and any("行业景气" in name for name in field_names), "字段映射包含财务和行业缺口", ",".join(field_names)),
        check(len(blockers) >= 5, "正式依据缺口数量足够", f"缺口数量={len(blockers)}"),
        check(any("上市公司正式公告" in name for name in blocker_names) and any("财务指标" in name for name in blocker_names), "缺口覆盖公告和财务", ",".join(blocker_names)),
        check(any("行业景气" in name for name in blocker_names) and any("人工复核" in name for name in blocker_names), "缺口覆盖行业和人工复核", ",".join(blocker_names)),
        check(len(formal_snapshot) == 3 and snapshot_ok, "正式入口快照哈希一致", ";".join(snapshot_details)),
        check(all(value is False for key, value in safety.items() if key != "本步骤仅生成影子映射"), "高风险安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check(safety.get("本步骤仅生成影子映射") is True, "明确本步骤仅生成影子映射", json.dumps(safety, ensure_ascii=False)),
        check("不能升级为强推荐" in text and "正式微信入口仍不替换" in text, "明确结论降级和入口保护", ""),
    ]

    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "股票报告证据源映射预览验收",
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
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "股票报告证据源映射预览验收_最新.json"
    latest_md = OUT_DIR / "股票报告证据源映射预览验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
