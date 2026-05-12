# -*- coding: utf-8 -*-
"""生成最终日常可用交付候选回传包。

只汇总日常可用交付候选状态，不写正式规则、不改运行配置、不触发服务重载。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "48最终日常可用交付候选回传"
LATEST_JSON = OUTPUT_DIR / "最终日常可用交付候选回传_最新.json"
LATEST_MD = OUTPUT_DIR / "最终日常可用交付候选回传_最新.md"

SOURCES = {
    "状态包": EVOLUTION_ROOT / "03数据" / "43日常可用交付版状态包" / "日常可用交付版状态包_最新.json",
    "收口包": EVOLUTION_ROOT / "03数据" / "46日常可用交付版收口包" / "日常可用交付版收口包_最新.json",
    "进度校准": EVOLUTION_ROOT / "03数据" / "47日常可用交付版收口后进度校准" / "日常可用交付版收口后进度校准_最新.json",
    "总回归": EVOLUTION_ROOT / "03数据" / "44日常可用交付版一键只读总回归" / "日常可用交付版一键只读总回归_最新.json",
    "总览快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_package() -> dict[str, Any]:
    status = read_json(SOURCES["状态包"])
    closeout = read_json(SOURCES["收口包"])
    calibration = read_json(SOURCES["进度校准"])
    regression = read_json(SOURCES["总回归"])
    snapshot = read_json(SOURCES["总览快照"])
    return {
        "名称": "最终日常可用交付候选回传",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "性质": "日常可用交付候选回传，不是正式规则封版",
        "总判断": "日常可用交付候选版通过",
        "当前进度": calibration.get("整体进度判断", {}),
        "剩余有效工时": calibration.get("剩余有效工时判断", {}),
        "通过证据": {
            "状态包": status.get("整体状态"),
            "收口包": closeout.get("性质"),
            "一键只读总回归": regression.get("汇总", {}),
            "总览快照": snapshot.get("汇总", {}),
            "可用能力": len(status.get("可用能力", [])),
            "仍阻断能力": len(status.get("仍阻断能力", [])),
            "回归卡": len(status.get("后续回归卡", [])),
        },
        "使用者可用范围": [
            "企业微信公共入口本地预演和职责分流",
            "税收待复核草案摘要",
            "股票研究分析与去交易化前台展示",
            "视频脚本、分镜、人工回执、预检和阻断检查",
            "总管自主推进低风险候选、巡检、验收和状态包",
        ],
        "仍需保持阻断": [
            "企业微信真实发送",
            "n8n真实触发",
            "券商接口和交易",
            "电子税务局登录",
            "财税软件连接",
            "视频真实渲染和真实发布",
            "候选经验自动转正式规则",
            "总管面板和一键接续包修改",
            "19310/19302未经确认重载",
        ],
        "下一阶段建议": [
            "进入稳定交付版建设：连续多日总回归、异常恢复、日志索引、失败定位卡。",
            "n8n只做沙盒编排候选，不触发真实工作流。",
            "视频真实渲染只做环境缺口说明和人工配置清单，不自动接入。",
            "正式规则治理继续保持候选、评审、确认、生效、回滚链路。",
        ],
        "来源文件": {name: str(path) for name, path in SOURCES.items()},
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "触发服务重载": False,
            "重载19310": False,
            "重载19302": False,
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
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }


def build_markdown(package: dict[str, Any]) -> str:
    progress = package["当前进度"]
    hours = package["剩余有效工时"]
    rows = []
    for version, key in [
        ("日常可用交付版", "日常可用交付版剩余"),
        ("稳定交付版", "稳定交付版剩余"),
        ("完全交付使用版", "完全交付使用版剩余"),
        ("真正自主运行版", "真正自主运行版剩余"),
    ]:
        h = hours.get(key, {})
        rows.append(f"| {version} | {progress.get(version)} | {h.get('乐观')} | {h.get('常规')} | {h.get('保守')} |")
    return "\n".join(
        [
            "# 最终日常可用交付候选回传",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 性质：{package['性质']}",
            f"- 总判断：{package['总判断']}",
            "",
            "## 进度与剩余工时",
            "",
            "| 目标版本 | 当前完成度 | 乐观 | 常规 | 保守 |",
            "| --- | ---: | ---: | ---: | ---: |",
            *rows,
            "",
            "## 通过证据",
            "",
            f"- 一键只读总回归：{package['通过证据']['一键只读总回归'].get('通过')}/{package['通过证据']['一键只读总回归'].get('总数')} pass",
            f"- 总览快照：{package['通过证据']['总览快照'].get('通过')}/{package['通过证据']['总览快照'].get('总数')} pass",
            f"- 可用能力：{package['通过证据']['可用能力']}",
            f"- 仍阻断能力：{package['通过证据']['仍阻断能力']}",
            f"- 回归卡：{package['通过证据']['回归卡']}",
            "",
            "## 使用者可用范围",
            "",
            *[f"- {item}" for item in package["使用者可用范围"]],
            "",
            "## 仍需保持阻断",
            "",
            *[f"- {item}" for item in package["仍需保持阻断"]],
            "",
            "## 下一阶段建议",
            "",
            *[f"- {item}" for item in package["下一阶段建议"]],
        ]
    )


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    print(json.dumps({"总判断": package["总判断"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
