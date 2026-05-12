# -*- coding: utf-8 -*-
"""执行稳定版试运行反馈本地入账。

读取 92 包待入账目录中的 JSON 文件，生成候选台账和拒收清单。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包"
INBOX_DIR = DATA_DIR / "待入账回传"

RESULT_JSON = DATA_DIR / "稳定版试运行反馈本地入账结果_最新.json"
RESULT_MD = DATA_DIR / "稳定版试运行反馈本地入账结果_最新.md"
LEDGER_JSON = DATA_DIR / "稳定版试运行反馈候选台账_最新.json"
LEDGER_MD = DATA_DIR / "稳定版试运行反馈候选台账_最新.md"
REJECT_JSON = DATA_DIR / "稳定版试运行反馈拒收清单_最新.json"

REQUIRED_FIELDS = [
    "回传日期",
    "使用入口",
    "业务域",
    "用户原始输入",
    "系统返回摘要",
    "期望结果",
    "实际结果",
    "是否影响日常使用",
    "是否疑似红线",
    "复现步骤",
    "相关截图或文件路径",
    "建议处理级别",
]

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "是", "有"}
    return bool(value)


def classify(item: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in item]
    if missing:
        return {"accepted": False, "reason": f"缺少字段：{', '.join(missing)}"}
    red_line = normalize_bool(item.get("是否疑似红线"))
    level = str(item.get("建议处理级别") or "").strip() or ("P0" if red_line else "P2")
    if red_line and level != "P0":
        level = "P0"
    return {
        "accepted": True,
        "level": level,
        "need_supervisor_confirm": red_line or level == "P0",
        "red_line": red_line,
    }


def build_ledger_md(ledger: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['业务域']} | {item['级别']} | {item['需总管确认']} | {item['来源文件']} |"
        for item in ledger["候选问题"]
    ]
    return "\n".join(
        [
            "# 稳定版试运行反馈候选台账",
            "",
            f"- 生成时间：{ledger['生成时间']}",
            f"- 候选问题数：{ledger['候选问题数']}",
            f"- 需总管确认数：{ledger['需总管确认数']}",
            "",
            "| 编号 | 业务域 | 级别 | 需总管确认 | 来源文件 |",
            "| --- | --- | --- | --- | --- |",
            *(rows if rows else ["| - | 无 | - | - | - |"]),
            "",
        ]
    )


def build_result_md(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版试运行反馈本地入账结果",
            "",
            f"- 生成时间：{result['生成时间']}",
            f"- 总体状态：{result['总体状态']}",
            f"- 扫描文件数：{result['指标']['扫描文件数']}",
            f"- 接收数：{result['指标']['接收数']}",
            f"- 拒收数：{result['指标']['拒收数']}",
            f"- 需总管确认数：{result['指标']['需总管确认数']}",
            "",
        ]
    )


def main() -> int:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    candidates = []
    rejects = []
    json_files = sorted(path for path in INBOX_DIR.glob("*.json") if path.is_file())
    for path in json_files:
        try:
            data = read_json(path)
        except Exception as exc:  # noqa: BLE001
            rejects.append({"来源文件": str(path), "原因": f"JSON不可解析：{exc}"})
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                rejects.append({"来源文件": str(path), "原因": "内容不是对象"})
                continue
            classified = classify(item)
            if not classified["accepted"]:
                rejects.append({"来源文件": str(path), "原因": classified["reason"]})
                continue
            candidates.append(
                {
                    "编号": f"TRIAL-FB-{len(candidates) + 1:04d}",
                    "来源文件": str(path),
                    "回传日期": item.get("回传日期"),
                    "使用入口": item.get("使用入口"),
                    "业务域": item.get("业务域"),
                    "用户原始输入": item.get("用户原始输入"),
                    "系统返回摘要": item.get("系统返回摘要"),
                    "期望结果": item.get("期望结果"),
                    "实际结果": item.get("实际结果"),
                    "级别": classified["level"],
                    "疑似红线": classified["red_line"],
                    "需总管确认": classified["need_supervisor_confirm"],
                    "处理状态": "候选入账，等待只读复现",
                }
            )

    supervisor_count = sum(1 for item in candidates if item["需总管确认"])
    ledger = {
        "名称": "稳定版试运行反馈候选台账",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "候选问题数": len(candidates),
        "需总管确认数": supervisor_count,
        "候选问题": candidates,
        "安全边界": SAFETY_BOUNDARY,
    }
    result = {
        "名称": "稳定版试运行反馈本地入账结果",
        "生成时间": ledger["生成时间"],
        "总体状态": "pass",
        "指标": {
            "扫描文件数": len(json_files),
            "接收数": len(candidates),
            "拒收数": len(rejects),
            "需总管确认数": supervisor_count,
        },
        "拒收清单": rejects,
        "候选台账": str(LEDGER_JSON),
        "安全边界": SAFETY_BOUNDARY,
    }
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))
    write_json(REJECT_JSON, {"名称": "稳定版试运行反馈拒收清单", "拒收数": len(rejects), "拒收项": rejects})
    write_json(RESULT_JSON, result)
    write_text(RESULT_MD, build_result_md(result))
    print(json.dumps({"总体状态": result["总体状态"], "扫描文件数": len(json_files), "接收数": len(candidates), "拒收数": len(rejects), "输出": str(RESULT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
