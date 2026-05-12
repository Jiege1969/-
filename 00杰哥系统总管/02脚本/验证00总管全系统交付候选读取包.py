# -*- coding: utf-8 -*-
"""只读验证00总管全系统交付候选读取包。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"

PACKAGE_JSON = STATE / "全系统交付候选读取包_最新.json"
PACKAGE_MD = STATE / "全系统交付候选读取包_最新.md"
RECOVERY_JSON = RECOVERY / "00总管_全系统交付候选读取回收报告_最新.json"
RECOVERY_MD = RECOVERY / "00总管_全系统交付候选读取回收报告_最新.md"

CURRENT_PROGRESS = "84%-90%"
CURRENT_REMAINING = "9-17小时"
REQUIRED_TOPICS = [
    "任务契约层",
    "生命周期状态机",
    "Redis评估",
    "n8n门禁",
    "最终交付清单补强",
    "股票analysis-only",
    "安全边界",
]
FORBIDDEN_TRUE_KEYS = [
    "是否重算进度",
    "是否修改进度口径",
    "是否触发外部服务",
    "是否执行真实动作",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    text = read_text(path)
    if not text:
        return {}
    return json.loads(text)


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    package = load_json(PACKAGE_JSON)
    recovery = load_json(RECOVERY_JSON)
    package_md = read_text(PACKAGE_MD)
    recovery_md = read_text(RECOVERY_MD)

    checks: list[dict[str, Any]] = []
    checks.append(check(PACKAGE_JSON.exists(), "读取包JSON存在", str(PACKAGE_JSON)))
    checks.append(check(PACKAGE_MD.exists(), "读取包Markdown存在", str(PACKAGE_MD)))
    checks.append(check(RECOVERY_JSON.exists(), "固定回收报告JSON存在", str(RECOVERY_JSON)))
    checks.append(check(RECOVERY_MD.exists(), "固定回收报告Markdown存在", str(RECOVERY_MD)))
    checks.append(check(package.get("当前口径", {}).get("全盘当前进度") == CURRENT_PROGRESS, "当前进度口径未漂移", package.get("当前口径")))
    checks.append(check(package.get("当前口径", {}).get("全盘剩余有效工时") == CURRENT_REMAINING, "剩余工时口径未漂移", package.get("当前口径")))
    checks.append(check(recovery.get("当前进度口径") == CURRENT_PROGRESS, "回收报告进度口径未漂移", recovery.get("当前进度口径")))
    checks.append(check(recovery.get("剩余有效工时") == CURRENT_REMAINING, "回收报告剩余工时未漂移", recovery.get("剩余有效工时")))

    for key in FORBIDDEN_TRUE_KEYS:
        checks.append(check(package.get(key) is False, f"{key}为false", package.get(key)))

    topic_names = [item.get("主题") for item in package.get("关键证据汇总", [])]
    for topic in REQUIRED_TOPICS:
        checks.append(check(topic in topic_names, f"覆盖主题：{topic}", topic_names))

    gaps = package.get("交付候选缺口清单", [])
    recommendations = package.get("下一步最终收口建议", [])
    checks.append(check(len(gaps) >= 6, "交付候选缺口清单已生成", len(gaps)))
    checks.append(check(len(recommendations) >= 5, "下一步最终收口建议已生成", len(recommendations)))
    checks.append(check(any("旧口径" in item.get("缺口", "") for item in gaps), "旧口径资料一致性缺口已标注", gaps))

    safety = package.get("安全边界", {})
    checks.append(check(bool(safety) and all(value is True for value in safety.values()), "安全边界全部保持关闭口径", safety))

    output_files = package.get("输出文件", {})
    required_outputs = {str(PACKAGE_JSON), str(PACKAGE_MD), str(RECOVERY_JSON), str(RECOVERY_MD)}
    checks.append(check(required_outputs.issubset(set(output_files.values())), "输出文件路径登记完整", output_files))
    checks.append(check("交付候选缺口清单" in package_md and "下一步最终收口建议" in package_md, "Markdown包含缺口与建议章节", ""))
    checks.append(check("交付候选缺口" in recovery_md and "下一步最终收口建议" in recovery_md, "回收Markdown包含缺口与建议摘要", ""))
    checks.append(check(recovery.get("结论") == "通过", "固定回收报告结论通过", recovery.get("结论")))
    checks.append(check(recovery.get("外部服务") == "未触发" and recovery.get("真实动作") == "未执行", "未触发外部服务且未执行真实动作", recovery))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "00总管全系统交付候选读取包只读验证",
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "读取模式": "read_only_local_parse",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
