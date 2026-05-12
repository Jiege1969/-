# ============================================================
# 脚本名称：验证杰哥推荐方法学习链路.py
# 所属系统：02杰哥扩展系统/01股票研究系统/02脚本
# 功能描述：验证股票助手是否真正学会【杰哥推荐】方法取材流程：
#           2000候选识别 -> 单股材料包 -> 标准报告v2证据段 -> 19302桥接读取19300本体结果。
# 创建日期：2026-05-10
# 安全边界：仅访问127.0.0.1本地服务；不真实发送企业微信、不触发n8n、不调用券商接口、不自动交易。
# ============================================================

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
OUT_DIR = ROOT / "03数据" / "277杰哥推荐方法学习链路验收"


def post_json(url: str, data: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# 杰哥推荐方法学习链路验收",
        "",
        f"验收时间：{report['验收时间']}",
        f"结论：{report['结论']}",
        "",
        "## 检查项",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['名称']}：{'通过' if item['通过'] else '失败'}")
        if item.get("说明"):
            lines.append(f"  {item['说明']}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "- 未真实发送企业微信。",
            "- 未触发n8n。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未输出买卖指令。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, note: str = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "说明": note})


def main() -> int:
    query = "分析 永鼎股份"
    health = get_json("http://127.0.0.1:19300/health")
    assistant = post_json(
        "http://127.0.0.1:19300/analyze",
        {"问题": query, "入口角色": "助手", "不记录上下文": True},
    )
    bridge = post_json(
        "http://127.0.0.1:19302/wecom-bot/message",
        {"content": query, "real_send": False},
    )

    report_path = Path(str(assistant.get("标准报告v2路径") or ""))
    report_text = report_path.read_text(encoding="utf-8-sig", errors="replace") if report_path.exists() else ""
    assistant_reply = str(assistant.get("回复") or "")
    bridge_content = str(bridge.get("企业微信内容") or "")
    bridge_actions = bridge.get("实际动作", {}) if isinstance(bridge.get("实际动作"), dict) else {}
    assistant_material = assistant.get("杰哥推荐后台材料包", {}) if isinstance(assistant.get("杰哥推荐后台材料包"), dict) else {}
    bridge_material = bridge.get("杰哥推荐后台材料包", {}) if isinstance(bridge.get("杰哥推荐后台材料包"), dict) else {}

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "19300健康页暴露2000候选识别能力",
        health.get("杰哥推荐候选识别数量") == 2000
        and "杰哥推荐2000只候选识别" in health.get("能力", []),
        f"候选识别数量={health.get('杰哥推荐候选识别数量')}",
    )
    add_check(
        checks,
        "19300单股分析可直接识别杰哥推荐候选股",
        assistant.get("状态") == "完成" and "需要补充股票" not in assistant_reply,
        assistant_reply.splitlines()[0] if assistant_reply else "",
    )
    add_check(
        checks,
        "19300本体生成杰哥推荐后台材料包",
        assistant_material.get("状态") == "完成",
        str(assistant_material.get("材料包路径") or ""),
    )
    add_check(
        checks,
        "单股标准报告v2包含方法材料包证据段",
        "【杰哥推荐】方法材料包" in report_text and "相近强势样本" in report_text and "失败对照校验" in report_text,
        str(report_path),
    )
    add_check(
        checks,
        "19302桥接读取19300本体材料包而非重复取材",
        bridge_actions.get("材料包真源") == "19300股票助手本体" and bridge_material.get("状态") == "完成",
        str(bridge_actions.get("材料包真源") or ""),
    )
    add_check(
        checks,
        "企业微信前台不回退旧壳",
        "需要补充股票" not in bridge_content and "研究等级=重点研究" in bridge_content and "当前状态=等待承接" in bridge_content,
        "已检查前台摘要关键词",
    )
    add_check(
        checks,
        "安全边界保持关闭",
        bridge.get("真实回传") is False
        and bridge_actions.get("尝试response_url回传") is False
        and bridge_actions.get("调用券商接口") is False
        and bridge_actions.get("自动交易") is False,
        "real_send=false；无券商/交易动作",
    )

    conclusion = "通过" if all(item["通过"] for item in checks) else "需复核"
    report = {
        "验收时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "名称": "杰哥推荐方法学习链路验收",
        "结论": conclusion,
        "样例问题": query,
        "检查项": checks,
        "样例输出": {
            "19300回复前12行": "\n".join(assistant_reply.splitlines()[:12]),
            "19302企业微信内容前12行": "\n".join(bridge_content.splitlines()[:12]),
            "标准报告v2路径": str(report_path),
        },
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "输出买卖指令": False,
        },
    }

    json_path = OUT_DIR / "杰哥推荐方法学习链路验收_最新.json"
    md_path = OUT_DIR / "杰哥推荐方法学习链路验收_最新.md"
    write_json(json_path, report)
    write_md(md_path, report)

    print(f"验收结论：{conclusion}")
    print(f"验收JSON：{json_path}")
    print(f"验收Markdown：{md_path}")
    return 0 if conclusion == "通过" else 2


if __name__ == "__main__":
    raise SystemExit(main())
