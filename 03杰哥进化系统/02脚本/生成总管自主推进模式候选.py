# -*- coding: utf-8 -*-
"""
名称：生成总管自主推进模式候选.py
作用：记录用户授权后的总管自主推进工作方式，作为候选材料保存，供后续接续参考。
安全边界：只写候选记录和说明，不写正式规则，不改运行配置，不触发服务重载。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
OUTPUT_DIR = ROOT / "03数据" / "41总管自主推进模式候选"
LATEST_JSON = OUTPUT_DIR / "总管自主推进模式候选_最新.json"
LATEST_MD = OUTPUT_DIR / "总管自主推进模式候选_最新.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_candidate() -> dict[str, Any]:
    return {
        "名称": "总管自主推进模式候选",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "性质": "候选记录，不是正式规则",
        "用户授权摘要": [
            "总管主控可自主运行搭建，不再要求用户搬运任务给其他对话框。",
            "用户输入任意文字信息时，默认视同继续搭建。",
            "总管可自行采取并行任务和本地工具完成低风险施工、巡检、验收和候选沉淀。",
        ],
        "自主推进默认动作": [
            "直接判断回传是否通过、未通过或需总管确认。",
            "直接选择下一项低风险任务并执行。",
            "优先补只读巡检、验收脚本、状态快照、候选记录、边界清单。",
            "遇到跨系统风险时先做只读探测和候选登记。",
        ],
        "硬刹车": [
            "不接券商、不交易、不生成买卖指令。",
            "不登录电子税务局、不接财税软件、不生成正式税务结论。",
            "不自动发布视频，不绕过人工复核。",
            "不把进化候选自动转正式规则。",
            "不修改总管面板，不修改一键接续包。",
            "不随意重载19310/19302；需要重载时登记为需总管确认。",
            "不真实发送企业微信给非白名单对象；当前仍保持real_send=false。",
            "n8n保持检查项可读，真实触发关闭；启用真实编排需单独候选和门禁。",
        ],
        "适合自主推进的任务类型": [
            "只读巡检包和健康快照。",
            "已有验收脚本复跑和汇总。",
            "低风险展示层口径检查。",
            "视频真实渲染/发布阻断状态复核。",
            "进化候选材料整理。",
            "接续包、边界清单、回归测试建议整理。",
        ],
        "不适合自动推进的任务类型": [
            "真实外部系统接入。",
            "正式规则写入。",
            "常驻服务重载。",
            "账号、凭据、资金、税务申报、视频发布相关真实动作。",
        ],
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "重载19310": False,
            "重载19302": False,
            "真实发送企业微信": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "自动发布视频": False,
        },
    }


def build_markdown(candidate: dict[str, Any]) -> str:
    def bullet(items: list[str]) -> list[str]:
        return [f"- {item}" for item in items]

    return "\n".join(
        [
            "# 总管自主推进模式候选",
            "",
            f"- 生成时间：{candidate['生成时间']}",
            f"- 性质：{candidate['性质']}",
            "",
            "## 用户授权摘要",
            *bullet(candidate["用户授权摘要"]),
            "",
            "## 自主推进默认动作",
            *bullet(candidate["自主推进默认动作"]),
            "",
            "## 硬刹车",
            *bullet(candidate["硬刹车"]),
            "",
            "## 适合自主推进的任务类型",
            *bullet(candidate["适合自主推进的任务类型"]),
            "",
            "## 不适合自动推进的任务类型",
            *bullet(candidate["不适合自动推进的任务类型"]),
            "",
            "本记录只作为候选和接续参考，不写入正式规则。",
        ]
    )


def main() -> int:
    candidate = build_candidate()
    write_json(LATEST_JSON, candidate)
    write_text(LATEST_MD, build_markdown(candidate))
    print(json.dumps({"名称": candidate["名称"], "性质": candidate["性质"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
