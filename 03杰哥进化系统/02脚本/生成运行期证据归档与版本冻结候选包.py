# -*- coding: utf-8 -*-
"""生成运行期证据归档与版本冻结候选包。

只生成本地证据索引、版本冻结候选说明和验收入口，不写正式规则，
不修改运行配置，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "86运行期证据归档与版本冻结候选包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期证据归档与版本冻结候选包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用交付版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "日常与稳定最终交付收尾": EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包" / "日常可用版与稳定交付版最终交付收尾包_最新.json",
    "交付后首日观察": EVOLUTION_ROOT / "03数据" / "81交付后首日运行观察与问题登记包" / "交付后首日运行观察与问题登记包_最新.json",
    "每日开工收工": EVOLUTION_ROOT / "03数据" / "82每日开工收工清单与低风险续跑包" / "每日开工收工清单与低风险续跑包_最新.json",
    "首周运行趋势": EVOLUTION_ROOT / "03数据" / "83首周运行趋势与问题升级包" / "首周运行趋势与问题升级包_最新.json",
    "运行期问题闭环": EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json",
    "运行期周报看板": EVOLUTION_ROOT / "03数据" / "85运行期周报与状态看板数据包" / "运行期周报与状态看板数据包_最新.json",
    "每日运行日报": EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定交付版每日运行日报与次日待办包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "运行期证据归档与版本冻结候选包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期证据归档与版本冻结候选包_最新.md"
EVIDENCE_JSON = DATA_DIR / "运行期证据归档索引_最新.json"
EVIDENCE_MD = DATA_DIR / "运行期证据归档索引_最新.md"
FREEZE_MD = DATA_DIR / "版本冻结候选说明_最新.md"
HANDOFF_MD = DATA_DIR / "冻结候选交接清单_最新.md"
GEN_LOG = LOG_DIR / "生成运行期证据归档与版本冻结候选包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "写正式规则": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def status_of(data: dict[str, Any]) -> Any:
    return data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed")


def main() -> int:
    evidence = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        evidence[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": status_of(data),
            "汇总": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }
    snapshot = read_json(SOURCES["日常可用版自主巡检快照"])
    regression = read_json(SOURCES["日常可用交付版一键只读总回归"])
    snapshot_ok = snapshot.get("总体状态") == "pass" and snapshot.get("汇总", {}).get("失败", 0) == 0
    regression_ok = regression.get("通过") is True and regression.get("指标", {}).get("错误数", 0) == 0
    all_sources_exist = all(item["存在"] for item in evidence.values())
    package = {
        "名称": "运行期证据归档与版本冻结候选包",
        "生成时间": now_text(),
        "状态": "runtime_evidence_freeze_candidate_ready" if snapshot_ok and regression_ok and all_sources_exist else "runtime_evidence_freeze_candidate_blocked",
        "性质": "版本冻结候选，不是正式规则封版，不修改运行配置。",
        "冻结候选范围": [
            "日常可用交付版最终交付证据",
            "稳定交付版运行观察证据",
            "运行期问题闭环证据",
            "周报与看板数据证据",
            "每日运行日报与次日待办证据",
        ],
        "冻结前提": {
            "总巡检通过": snapshot_ok,
            "一键总回归通过": regression_ok,
            "来源全部存在": all_sources_exist,
            "红线全部关闭": all(value is False for value in SAFETY_BOUNDARY.values()),
        },
        "证据归档索引": evidence,
        "冻结候选结论": "可作为运行期稳定候选证据归档；正式规则封版仍需总管确认。",
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "证据索引JSON": str(EVIDENCE_JSON),
            "证据索引Markdown": str(EVIDENCE_MD),
            "版本冻结候选说明": str(FREEZE_MD),
            "冻结候选交接清单": str(HANDOFF_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(EVIDENCE_JSON, {"名称": "运行期证据归档索引", "证据": evidence, "安全边界": SAFETY_BOUNDARY})
    rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in evidence.items()]
    package_md = "\n".join([
        "# 运行期证据归档与版本冻结候选包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 性质：{package['性质']}",
        f"- 结论：{package['冻结候选结论']}",
        "",
        "| 证据 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(EVIDENCE_MD, package_md)
    write_text(FREEZE_MD, "\n".join([
        "# 版本冻结候选说明",
        "",
        "- 本包只声明运行期证据可归档，不声明正式规则封版。",
        "- 总巡检、一键总回归和来源存在性均通过时，才可作为冻结候选。",
        "- 后续若要转为正式规则或配置，必须另走总管确认。",
    ]))
    write_text(HANDOFF_MD, "\n".join([
        "# 冻结候选交接清单",
        "",
        "- 查看总包状态是否为 runtime_evidence_freeze_candidate_ready。",
        "- 查看证据索引中每个来源是否存在。",
        "- 查看红线状态是否全部为 false。",
        "- 明确本包不是正式规则封版。",
    ]))
    write_json(GEN_LOG, {"名称": "生成运行期证据归档与版本冻结候选包", "生成时间": now_text(), "通过": package["状态"] == "runtime_evidence_freeze_candidate_ready", "错误数": 0 if package["状态"] == "runtime_evidence_freeze_candidate_ready" else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "证据数": len(evidence), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if package["状态"] == "runtime_evidence_freeze_candidate_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
