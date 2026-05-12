# -*- coding: utf-8 -*-
"""生成日常可用版与稳定交付版最终交付收尾包。

本脚本只汇总既有只读验收、交付清单和使用边界，不写正式规则，
不修改运行配置，不触发任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常可用版与稳定交付版最终交付收尾包验收"

SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
REGRESSION_JSON = EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"
DAILY_CLOSEOUT_JSON = EVOLUTION_ROOT / "04日志" / "最终日常可用交付候选回传验收" / "final-daily-usable-delivery-candidate-verify-最新.json"
STABLE_FINAL_JSON = EVOLUTION_ROOT / "04日志" / "稳定版候选正式封版申请草案与最终交付封面收紧包验收" / "stable-candidate-formal-freeze-request-draft-verify-最新.json"
STABLE_COVER_JSON = EVOLUTION_ROOT / "04日志" / "稳定版最后收口总回传与候选交付封面包验收" / "stable-final-closeout-cover-verify-最新.json"

PACKAGE_JSON = DATA_DIR / "日常可用版与稳定交付版最终交付收尾包_最新.json"
PACKAGE_MD = DATA_DIR / "日常可用版与稳定交付版最终交付收尾包_最新.md"
DAILY_MD = DATA_DIR / "日常可用版交付清单_最新.md"
STABLE_MD = DATA_DIR / "稳定交付版交付清单_最新.md"
BOUNDARY_MD = DATA_DIR / "使用边界与红线说明_最新.md"
HANDOFF_MD = DATA_DIR / "使用者接管说明_最新.md"
GEN_LOG = LOG_DIR / "生成日常可用版与稳定交付版最终交付收尾包_最新.json"

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
        return {"存在": False, "路径": str(path)}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data["存在"] = True
    data["路径"] = str(path)
    return data


def passed(data: dict[str, Any]) -> bool:
    if not data.get("存在", True):
        return False
    if data.get("通过") is True:
        metrics = data.get("指标", {})
        return metrics.get("错误数", data.get("错误数", 0)) == 0
    if data.get("总体状态") == "pass":
        summary = data.get("汇总", {})
        return summary.get("失败", data.get("错误数", 0)) == 0
    if data.get("passed") is True:
        return data.get("error_count", 0) == 0
    return data.get("错误数") == 0 and data.get("通过数", 0) > 0


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_package() -> dict[str, Any]:
    snapshot = read_json(SNAPSHOT_JSON)
    regression = read_json(REGRESSION_JSON)
    daily_closeout = read_json(DAILY_CLOSEOUT_JSON)
    stable_final = read_json(STABLE_FINAL_JSON)
    stable_cover = read_json(STABLE_COVER_JSON)
    evidence = {
        "日常可用版自主巡检快照": {
            "通过": passed(snapshot),
            "汇总": snapshot.get("汇总", {}),
            "路径": str(SNAPSHOT_JSON),
        },
        "日常可用交付版一键只读总回归": {
            "通过": passed(regression),
            "指标": regression.get("指标", {}),
            "路径": str(REGRESSION_JSON),
        },
        "最终日常可用交付候选": {
            "通过": passed(daily_closeout),
            "指标": daily_closeout.get("指标", {}),
            "路径": str(DAILY_CLOSEOUT_JSON),
        },
        "稳定版候选正式封版申请草案与最终交付封面收紧": {
            "通过": passed(stable_final),
            "指标": stable_final.get("指标", {}),
            "路径": str(STABLE_FINAL_JSON),
        },
        "稳定版最后收口总回传与候选交付封面": {
            "通过": passed(stable_cover),
            "指标": stable_cover.get("指标", {}),
            "路径": str(STABLE_COVER_JSON),
        },
    }
    all_evidence_passed = all(item["通过"] for item in evidence.values())
    return {
        "名称": "日常可用版与稳定交付版最终交付收尾包",
        "生成时间": now_text(),
        "状态": "delivery_closeout_ready" if all_evidence_passed else "delivery_closeout_blocked",
        "交付层级": {
            "日常可用交付版": {
                "状态": "可交付使用",
                "使用体验": [
                    "企业微信公共入口可做本地预演和职责分流，真实发送关闭。",
                    "税收可输出待复核草案摘要，不生成正式税务结论。",
                    "股票可做研究展示和风险复核，不接券商、不交易。",
                    "视频可做脚本、分镜、预检和阻断提示，不真实渲染、不发布。",
                    "进化系统只沉淀候选和只读验收，不自动转正式规则。",
                ],
            },
            "稳定交付版": {
                "状态": "稳定候选可交付使用",
                "使用体验": [
                    "跨业务只读巡检、回归、异常样例、接管闸口已成体系。",
                    "低风险自动续建限于候选资产、状态包、验收脚本、回归清单。",
                    "触碰外部动作、正式规则或服务重载时自动暂停并登记需总管确认。",
                    "稳定版仍保留候选/交付口径，不代表开放红线能力。",
                ],
            },
        },
        "验收证据": evidence,
        "安全边界": SAFETY_BOUNDARY,
        "交付结论": (
            "日常可用版和稳定交付版可进入交付使用；后续完全交付和真正自主运行仍需继续低风险补强与人工确认闸口。"
            if all_evidence_passed
            else "存在未通过证据，暂不声明交付。"
        ),
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "日常可用版交付清单": str(DAILY_MD),
            "稳定交付版交付清单": str(STABLE_MD),
            "使用边界与红线说明": str(BOUNDARY_MD),
            "使用者接管说明": str(HANDOFF_MD),
        },
    }


def build_md(package: dict[str, Any]) -> str:
    evidence_rows = [
        f"| {name} | {'pass' if item['通过'] else 'blocked'} | {item['路径']} |"
        for name, item in package["验收证据"].items()
    ]
    return "\n".join(
        [
            "# 日常可用版与稳定交付版最终交付收尾包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- 交付结论：{package['交付结论']}",
            "",
            "| 验收证据 | 状态 | 路径 |",
            "| --- | --- | --- |",
            *evidence_rows,
            "",
            "## 使用口径",
            "",
            "- 日常可用交付版：可作为日常参谋和本地预演系统使用。",
            "- 稳定交付版：可作为带只读巡检、回归、异常演练和人工接管闸口的稳定候选交付系统使用。",
            "- 完全交付使用版和真正自主运行版仍不声明完成。",
        ]
    )


def main() -> int:
    package = build_package()
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_md(package))
    write_text(
        DAILY_MD,
        "\n".join(
            [
                "# 日常可用版交付清单",
                "",
                "- 企业微信公共入口：可本地预演，真实发送关闭。",
                "- 税收业务：待复核草案摘要可用，不生成正式税务结论。",
                "- 股票业务：研究展示和风险复核可用，不接券商、不交易。",
                "- 视频业务：脚本、分镜、预检、阻断提示可用，不真实渲染、不发布。",
                "- 进化系统：候选记录和只读验收可用，不自动转正式规则。",
                "- 一键只读总回归：通过。",
            ]
        ),
    )
    write_text(
        STABLE_MD,
        "\n".join(
            [
                "# 稳定交付版交付清单",
                "",
                "- 跨业务巡检快照：通过。",
                "- 异常样例、失败分级、人工接管闸口：已落地为候选/只读演练资产。",
                "- 长周期巡检和三日样本：已具备继续采样模板，真实跨自然日仍随时间积累。",
                "- n8n：只保留离线蓝图和本地干跑，真实触发关闭。",
                "- 视频真实渲染：环境识别和缺口清单可用，真实渲染仍阻断。",
                "- 稳定交付结论：可交付使用，但不代表开放红线能力。",
            ]
        ),
    )
    write_text(
        BOUNDARY_MD,
        "\n".join(
            [
                "# 使用边界与红线说明",
                "",
                "- 不真实发送企业微信。",
                "- 不真实触发 n8n。",
                "- 不接券商、不交易。",
                "- 不登录电子税务局、不接财税软件。",
                "- 不真实渲染或自动发布视频。",
                "- 不写正式规则、不自动转正式规则。",
                "- 不修改总管面板、不修改一键接续包。",
                "- 19310/19302 需要重载时只登记为需总管确认。",
            ]
        ),
    )
    write_text(
        HANDOFF_MD,
        "\n".join(
            [
                "# 使用者接管说明",
                "",
                "## 日常怎么用",
                "",
                "- 把系统当作多业务参谋和本地预演平台使用。",
                "- 结果带有待复核、研究、候选、预检等口径时，需要人工最终判断。",
                "- 出现红线关键词时，以暂停闸口输出为准。",
                "",
                "## 什么时候停",
                "",
                "- 要求真实发送、真实触发、交易、登录、渲染、发布、正式规则或服务重载时停。",
                "- 需要改总管面板或一键接续包时停。",
                "- 外部凭证、账号、资金、税务账号、发布账号相关动作全部停。",
            ]
        ),
    )
    write_json(
        GEN_LOG,
        {
            "名称": "生成日常可用版与稳定交付版最终交付收尾包",
            "生成时间": now_text(),
            "通过": package["状态"] == "delivery_closeout_ready",
            "错误数": 0 if package["状态"] == "delivery_closeout_ready" else 1,
            "输出": package["输出文件"],
        },
    )
    print(json.dumps({"状态": package["状态"], "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if package["状态"] == "delivery_closeout_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
