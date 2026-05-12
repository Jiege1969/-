# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
REWRITE_DIR = DATA_DIR / "复核回执状态回写预演"
SOURCE_JSON = DATA_DIR / "税收企业微信复核回执到草案状态回写预演_最新.json"
SOURCE_MD = DATA_DIR / "税收企业微信复核回执到草案状态回写预演_最新.md"
REWRITE_JSON = REWRITE_DIR / "税收企业微信复核回执到草案状态回写预演.json"
OUT_JSON = DATA_DIR / "税收企业微信复核回执到草案状态回写预演验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信复核回执到草案状态回写预演验收_最新.md"

REQUIRED_FIELDS = [
    "回写预演ID",
    "回执ID",
    "阅读包ID",
    "摘要ID",
    "来源草案ID",
    "业务事项",
    "回执状态",
    "当前阅读包状态",
    "目标阅读包状态",
    "是否具备回写条件",
    "阻断原因",
    "需要人工填写字段",
    "回写动作",
    "回写限制",
]

PROHIBITED_PHRASES = [
    "可以享受",
    "不能享受",
    "应纳税额",
    "退税金额",
    "请立即申报",
    "请办理退税",
    "请开票",
    "无需人工复核",
    "本预演为正式税务意见",
    "正式复核结果：通过",
]


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def has_required_fields(row: dict[str, Any]) -> bool:
    return all(field in row and row.get(field) not in ("", None, []) for field in REQUIRED_FIELDS)


def main() -> int:
    source = load(SOURCE_JSON)
    rewrite_copy = load(REWRITE_JSON)
    text = SOURCE_MD.read_text(encoding="utf-8", errors="ignore") if SOURCE_MD.exists() else ""
    rows = source.get("回写预演", [])
    boundaries = source.get("安全边界", {})
    json_text = json.dumps(source, ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [
        check("回写预演JSON存在", SOURCE_JSON.exists(), str(SOURCE_JSON)),
        check("回写预演Markdown存在", SOURCE_MD.exists(), str(SOURCE_MD)),
        check("回写预演归档副本存在", REWRITE_JSON.exists(), str(REWRITE_JSON)),
        check("归档副本与最新文件数量一致", len(rewrite_copy.get("回写预演", [])) == len(rows), len(rewrite_copy.get("回写预演", []))),
        check("回写预演数量为5", source.get("回写预演数量") == 5 and len(rows) == 5, {"回写预演数量": source.get("回写预演数量"), "明细": len(rows)}),
        check("可回写数量为0", source.get("可回写数量") == 0, source.get("可回写数量")),
        check("阻断数量为5", source.get("阻断数量") == 5, source.get("阻断数量")),
        check("全部回写预演字段完整", all(has_required_fields(item) for item in rows), rows),
        check("全部为空白回执且不具备回写条件", all(item.get("是否空白回执") is True and item.get("是否具备回写条件") is False for item in rows), rows),
        check("全部保持no-op回写动作", all(item.get("回写动作") == "no_op_shadow_preview" for item in rows), [item.get("回写动作") for item in rows]),
        check("全部未写源文件未写库未发消息未生成结论未升级状态", all(item.get("是否回写草案源文件") is False and item.get("是否写正式业务库") is False and item.get("是否企业微信真实发送") is False and item.get("是否生成正式税务结论") is False and item.get("是否自动升级为human_reviewed") is False for item in rows), rows),
        check("全部阻断原因指向人工未填写", all("人工复核回执仍为空白待填写" in str(item.get("阻断原因", "")) for item in rows), [item.get("阻断原因") for item in rows]),
        check("安全边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("未命中正式结论或办税执行短语", not any(phrase in json_text for phrase in PROHIBITED_PHRASES), PROHIBITED_PHRASES),
        check("Markdown声明no-op且不写真库不生成税务结论", "no-op" in text and "不写正式库" in text and "不生成正式税务结论" in text, "边界声明"),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "税收企业微信复核回执到草案状态回写预演验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信复核回执到草案状态回写预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.extend(["", "## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
