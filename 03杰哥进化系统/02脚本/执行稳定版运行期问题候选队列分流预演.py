# -*- coding: utf-8 -*-
"""执行稳定版运行期问题候选队列分流预演。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "102稳定版运行期问题候选队列分流预演包"
SAMPLES_JSON = DATA_DIR / "运行期问题分流样例_最新.json"
QUEUE_PREVIEW_JSON = DATA_DIR / "运行期问题候选队列预演_最新.json"
QUEUE_PREVIEW_MD = DATA_DIR / "运行期问题候选队列预演_最新.md"

REDLINE_KEYWORDS = ["真实发送", "接入 n8n", "触发 n8n", "券商", "交易", "登录税局", "财税软件", "正式规则", "真实发布", "重载19310", "重载19302", "重载 19310", "重载 19302"]
P1_KEYWORDS = ["红灯", "总回归失败", "运行阻断", "样本链路失败", "入账器拒收异常"]
P3_KEYWORDS = ["操作卡", "文档", "说明", "补充一句", "流程优化"]
DOMAIN_KEYWORDS = {
    "企业微信公共入口": ["企业微信", "工作秘书", "系统管家", "视频助理", "19310"],
    "税收": ["税收", "增值税", "即征即退", "研发费用"],
    "股票": ["股票", "个股", "研究价值", "风险复核"],
    "视频": ["视频", "渲染", "发布", "MoneyPrinterTurbo", "ImageMagick"],
    "智能进化": ["规则", "候选", "进化", "经验", "运行指挥台", "总回归", "操作卡"],
}


def read_json(path: Path) -> Any:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def classify_level(text: str) -> tuple[str, bool, bool, str]:
    if any(keyword in text for keyword in REDLINE_KEYWORDS):
        return "P0", True, False, "命中红线或外部真实动作关键词"
    if any(keyword in text for keyword in P1_KEYWORDS):
        return "P1", True, False, "命中稳定运行阻断关键词"
    if any(keyword in text for keyword in P3_KEYWORDS):
        return "P3", False, True, "命中文档流程优化关键词"
    return "P2", False, True, "默认进入普通试运行候选问题"


def classify_domain(text: str) -> str:
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return domain
    return "智能进化"


def build_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['问题ID']} | {item['级别']} | {item['问题域']} | {item['需总管确认']} | {item['允许自动执行']} | {item['预演通过']} |"
        for item in report["候选队列"]
    ]
    return "\n".join(
        [
            "# 运行期问题候选队列预演",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{report['总体状态']}",
            f"- 通过：{report['汇总']['通过']}/{report['汇总']['总数']}",
            "",
            "| 问题ID | 级别 | 问题域 | 需总管确认 | 允许自动执行 | 预演通过 |",
            "| --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    samples = read_json(SAMPLES_JSON)
    queue = []
    errors = []
    for sample in samples:
        text = sample.get("原始描述", "")
        level, needs_confirm, allow_auto, reason = classify_level(text)
        domain = classify_domain(text)
        passed = (
            level == sample.get("期望级别")
            and domain == sample.get("期望问题域")
            and needs_confirm is sample.get("期望需总管确认")
            and allow_auto is sample.get("期望允许自动执行")
        )
        item = {
            "问题ID": sample.get("问题ID"),
            "来源": sample.get("来源"),
            "原始描述": text,
            "级别": level,
            "问题域": domain,
            "需总管确认": needs_confirm,
            "允许自动执行": allow_auto,
            "分流原因": reason,
            "建议动作": "登记需总管确认" if needs_confirm else "进入候选队列低风险处理",
            "预演通过": passed,
        }
        if not passed:
            errors.append({"问题ID": item["问题ID"], "实际": item, "期望": sample})
        queue.append(item)
    report = {
        "名称": "运行期问题候选队列预演",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not errors else "blocked",
        "汇总": {"总数": len(queue), "通过": len(queue) - len(errors), "失败": len(errors)},
        "错误": errors,
        "候选队列": queue,
        "安全边界": {
            "执行真实修复": False,
            "写正式规则": False,
            "修改运行配置": False,
            "重载19310": False,
            "重载19302": False,
        },
    }
    write_json(QUEUE_PREVIEW_JSON, report)
    write_text(QUEUE_PREVIEW_MD, build_md(report))
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["汇总"]["通过"], "失败": report["汇总"]["失败"], "输出": str(QUEUE_PREVIEW_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
