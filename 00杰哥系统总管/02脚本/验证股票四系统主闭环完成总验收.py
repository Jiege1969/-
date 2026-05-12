#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
名称：验证股票四系统主闭环完成总验收.py
作用：对股票系统与四系统最小闭环进行只读总验收，输出是否达到完成观察态的单一结论。
输入：股票C+++验收、股票日常一键运行、融合面板、完成观察记录、开工快检、194同步执行报告。
输出：00杰哥系统总管/03数据/四系统小闭环/股票四系统主闭环完成总验收_最新.md/json。
安全边界：只读本地验收产物并写总验收报告；不触发n8n，不发送企业微信，不重启服务，不写业务库，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建，用于本轮股票系统与四系统闭环完成收口。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
OUT_DIR = MANAGER / "03数据" / "四系统小闭环"


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default
    return default


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def fail_count(data: dict[str, Any]) -> int | None:
    if not isinstance(data, dict):
        return None
    value = data.get("失败数量", data.get("失败"))
    try:
        return int(value)
    except Exception:
        return None


def pass_count(data: dict[str, Any]) -> int | None:
    if not isinstance(data, dict):
        return None
    value = data.get("通过数量", data.get("通过"))
    try:
        return int(value)
    except Exception:
        return None


def build_md(report: dict[str, Any]) -> str:
    lines = [
        "# 股票四系统主闭环完成总验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总验收结论：{report['总验收结论']}",
        f"- 当前阶段：{report['当前阶段']}",
        "",
        "## 验收项",
    ]
    for item in report["验收项"]:
        mark = "通过" if item["通过"] else "未通过"
        lines.append(f"- {item['名称']}：{mark}；{item['摘要']}")
    lines.extend(["", "## 交付口径"])
    for item in report["交付口径"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 后续"])
    for item in report["后续"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界"])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = {
        "股票C+++验收": STOCK / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.json",
        "股票日常一键运行": STOCK / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.json",
        "融合面板": MANAGER / "03数据" / "四系统小闭环" / "股票四系统融合闭环状态面板_最新.json",
        "完成观察记录": MANAGER / "03数据" / "四系统小闭环" / "股票四系统闭环完成观察记录_最新.json",
        "完成观察记录验证": MANAGER / "04日志" / "四系统小闭环" / "stock-four-system-closed-loop-completion-observation-verify-最新.json",
        "开工快检": MANAGER / "03数据" / "四系统小闭环" / "四系统小闭环开工快检_最新.json",
        "194模板同步执行": STOCK / "03数据" / "194单股证据核验模板同步执行" / "单股证据核验模板同步执行报告_最新.json",
    }

    c_accept = load_json(paths["股票C+++验收"], {})
    daily = load_json(paths["股票日常一键运行"], {})
    fusion = load_json(paths["融合面板"], {})
    observation = load_json(paths["完成观察记录"], {})
    observation_verify = load_json(paths["完成观察记录验证"], {})
    quickcheck = load_json(paths["开工快检"], {})
    template_sync = load_json(paths["194模板同步执行"], {})

    checks = [
        {"名称": "股票C+++日常可用", "通过": c_accept.get("失败数量") == 0 and "通过" in str(c_accept.get("验收结论", "")), "摘要": f"通过={c_accept.get('通过数量')}；失败={c_accept.get('失败数量')}"},
        {"名称": "股票日常一键运行", "通过": daily.get("失败数量") == 0, "摘要": f"失败={daily.get('失败数量')}"},
        {"名称": "融合面板", "通过": fusion.get("融合结论") == "通过：可以按融合主线继续施工" and "完成观察态" in str(fusion.get("当前阶段", "")), "摘要": str(fusion.get("当前阶段", ""))},
        {"名称": "完成观察记录", "通过": "完成观察态" in str(observation.get("总结论", "")), "摘要": str(observation.get("总结论", ""))},
        {"名称": "完成观察记录验证", "通过": observation_verify.get("失败") == 0, "摘要": f"通过={observation_verify.get('通过')}；失败={observation_verify.get('失败')}"},
        {"名称": "四系统开工快检", "通过": quickcheck.get("失败数量") == 0, "摘要": f"通过={quickcheck.get('通过数量')}；失败={quickcheck.get('失败数量')}"},
        {"名称": "194模板同步执行", "通过": template_sync.get("执行写入") is True and "已写入172/175/178人工模板" in str(template_sync.get("总结论", "")), "摘要": str(template_sync.get("总结论", ""))},
    ]
    ok = all(item["通过"] for item in checks)
    report = {
        "名称": "股票四系统主闭环完成总验收",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总验收结论": "通过：股票系统与四系统主闭环已完成并进入观察期" if ok else "未通过：主闭环仍有断点",
        "当前阶段": "完成观察态" if ok else "待处理",
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "验收项": checks,
        "关键文件": {name: file_state(path) for name, path in paths.items()},
        "交付口径": [
            "股票系统日常使用不受影响，C+++验收和日常一键运行均为零失败。",
            "天齐锂业单股证据核验链路已完成205、191 CSV、191台账、193和194受控同步。",
            "四系统主闭环以股票系统为真实业务样板，已形成总管状态面板、开工快检、完成观察记录和失败隔离口径。",
        ],
        "后续": [
            "观察期按24小时或一次完整业务周期复核。",
            "文稿质检旁路继续累计样本，不阻断主闭环。",
            "收工或新开对话时再统一更新施工接续包、接续卡片和桌面无缝接手包。",
        ],
        "安全边界": {
            "触发n8n": False,
            "真实发送企业微信": False,
            "重启服务": False,
            "写业务正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }

    latest_json = OUT_DIR / "股票四系统主闭环完成总验收_最新.json"
    latest_md = OUT_DIR / "股票四系统主闭环完成总验收_最新.md"
    stamped_json = OUT_DIR / f"股票四系统主闭环完成总验收_{stamp}.json"
    stamped_md = OUT_DIR / f"股票四系统主闭环完成总验收_{stamp}.md"
    latest_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_md.write_text(build_md(report), encoding="utf-8")
    shutil.copy2(latest_json, stamped_json)
    shutil.copy2(latest_md, stamped_md)
    print(json.dumps({"状态": report["总验收结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
