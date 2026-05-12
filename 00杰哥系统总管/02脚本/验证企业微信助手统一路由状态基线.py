# -*- coding: utf-8 -*-
"""
名称：验证企业微信助手统一路由状态基线.py
作用：验收总管侧企业微信助手统一路由状态基线是否完整、低风险边界是否关闭。
触发方式：python 验证企业微信助手统一路由状态基线.py
安全边界：只读状态基线报告；只写验收报告；不发送企业微信；不触发n8n；不写正式库；不重启服务；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
BASELINE_JSON = OUT_DIR / "企业微信助手统一路由状态基线_最新.json"
BASELINE_MD = OUT_DIR / "企业微信助手统一路由状态基线_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    baseline = load_json(BASELINE_JSON)
    md = load_text(BASELINE_MD)
    text = json.dumps(baseline, ensure_ascii=False) + "\n" + md
    summary = baseline.get("汇总", {})
    script_runs = baseline.get("脚本执行", [])
    safety = baseline.get("安全边界", {})
    refs = baseline.get("引用产物", {})

    checks = [
        check(BASELINE_JSON.exists() and BASELINE_MD.exists(), "基线 JSON 与 Markdown 存在", str(OUT_DIR)),
        check(baseline.get("结论") == "通过", "基线结论通过", baseline.get("结论", "")),
        check(len(script_runs) >= 5 and all(item.get("退出码") == 0 for item in script_runs), "企业微信本地验收脚本全部通过", str(len(script_runs))),
        check(summary.get("系统状态") == "healthy", "企业微信助手系统状态 healthy", json.dumps(summary, ensure_ascii=False)),
        check(summary.get("路由状态") == "healthy" and summary.get("路由样例数量") == summary.get("路由命中期望数量") and int(summary.get("路由样例数量", 0) or 0) >= 6, "统一指令路由样例全部命中", ""),
        check(summary.get("本地调用状态") == "healthy" and summary.get("本地调用样例数量") == summary.get("本地调用成功数量") and int(summary.get("本地调用样例数量", 0) or 0) >= 6, "统一指令本地调用全部成功", ""),
        check(summary.get("本地服务状态") == "healthy" and as_int(summary.get("本地服务验收失败数量"), 99) == 0 and as_int(summary.get("本地服务验收通过数量")) >= 10, "统一指令本地服务入口验收通过", ""),
        check(summary.get("速查卡状态") == "healthy" and int(summary.get("速查卡指令数量", 0) or 0) >= 7, "统一指令速查卡覆盖常用入口", ""),
        check(as_int(summary.get("真实动作数量"), 99) == 0, "路由和本地调用无真实动作", str(summary.get("真实动作数量"))),
        check(summary.get("企业微信真实发送") is False and summary.get("触发Webhook") is False and summary.get("触发n8n") is False, "真实发送/Webhook/n8n 均关闭", json.dumps(summary, ensure_ascii=False)),
        check(all(value is False for value in safety.values()), "总管侧安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check("替换正式入口" in safety and safety.get("替换正式入口") is False, "正式入口未替换", ""),
        check(all(Path(str(path)).exists() for path in refs.values()), "引用产物均存在", json.dumps(refs, ensure_ascii=False)),
        check("不发送企业微信" in text and "不触发n8n" in text and "不重启19300" in text, "Markdown 记录关键安全边界", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    validation = {
        "名称": "企业微信助手统一路由状态基线验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "重启19300": False,
            "重启19302": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "企业微信助手统一路由状态基线验收_最新.json"
    latest_md = OUT_DIR / "企业微信助手统一路由状态基线验收_最新.md"
    lines = [
        "# 企业微信助手统一路由状态基线验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(latest_json, validation)
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": validation["结论"],
        "通过数量": validation["通过数量"],
        "失败数量": validation["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
