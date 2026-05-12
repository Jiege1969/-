# -*- coding: utf-8 -*-
"""生成日常可用版自主巡检快照。

只读取本地验收日志和关键产物，生成一个可被后续状态包读取的快照。
不请求业务接口，不发送企业微信，不触发 n8n，不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
WECOM_ROOT = ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置"
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"

OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照"
LATEST_JSON = OUTPUT_DIR / "日常可用版自主巡检快照_最新.json"
LATEST_MD = OUTPUT_DIR / "日常可用版自主巡检快照_最新.md"


EXPLICIT_SOURCES: dict[str, Path] = {
    "企业微信公共接入层日常巡检": WECOM_ROOT / "03数据" / "15日常可用版只读巡检包" / "企业微信公共接入层日常只读巡检_最新.json",
    "股票展示口径一致性验收": STOCK_ROOT / "03数据" / "246展示口径修复" / "股票展示口径一致性验收_最新.json",
    "股票前台展示口径全量扫雷": STOCK_ROOT / "03数据" / "246展示口径修复" / "股票前台展示口径全量一致性扫雷_最新.json",
    "日常可用交付版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "第十二轮低风险只读调度入口并行调度索引包": EVOLUTION_ROOT / "04日志" / "第十二轮低风险只读调度入口并行调度索引包验收" / "parallel-round12-low-risk-readonly-scheduler-entry-verify-最新.json",
}

LOG_ROOTS = [
    EVOLUTION_ROOT / "04日志",
    VIDEO_ROOT / "04日志",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def checks_all_passed(items: Any) -> bool:
    if not isinstance(items, list) or not items:
        return False
    passed_values = []
    for item in items:
        if not isinstance(item, dict):
            return False
        passed_values.append(
            item.get("通过") is True
            or item.get("passed") is True
            or item.get("pass") is True
        )
    return all(passed_values)


def artifact_passed(data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    error_count = data.get("error_count", data.get("错误数", get_nested(data, "指标", "错误数", default=0)))
    failed_count = get_nested(data, "汇总", "失败", default=data.get("失败"))
    explicit_pass = (
        data.get("通过") is True
        or data.get("pass") is True
        or data.get("passed") is True
        or data.get("status") == "pass"
        or data.get("总体状态") == "pass"
        or data.get("验收结论") == "通过"
    )
    no_errors = error_count in (None, 0) and failed_count in (None, 0)
    list_pass = checks_all_passed(data.get("检查结果", data.get("检查项", data.get("checks", []))))
    passed = (explicit_pass and no_errors) or (list_pass and no_errors)
    return passed, {
        "error_count": error_count,
        "failed_count": failed_count,
        "status": data.get("status", data.get("总体状态", data.get("验收结论"))),
    }


def summarize_source(name: str, path: Path, blocking: bool = True) -> dict[str, Any]:
    if not path.exists():
        return {
            "名称": name,
            "路径": str(path),
            "存在": False,
            "通过": False,
            "参与阻断": blocking,
            "摘要": "产物不存在",
        }
    try:
        data = read_json(path)
        passed, detail = artifact_passed(data)
    except Exception as exc:  # noqa: BLE001 - snapshot should record parse failures.
        passed, detail = False, {"error": str(exc)}
    return {
        "名称": name,
        "路径": str(path),
        "存在": True,
        "通过": passed,
        "参与阻断": blocking,
        "摘要": detail,
    }


def discover_passed_logs() -> list[dict[str, Any]]:
    seen = {path.resolve() for path in EXPLICIT_SOURCES.values() if path.exists()}
    checks: list[dict[str, Any]] = []
    for root in LOG_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*最新.json")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            try:
                data = read_json(path)
                passed, detail = artifact_passed(data)
            except Exception:
                continue
            if not passed:
                continue
            checks.append(
                {
                    "名称": path.parent.name,
                    "路径": str(path),
                    "存在": True,
                    "通过": True,
                    "参与阻断": True,
                    "摘要": detail,
                }
            )
            seen.add(resolved)
    return checks


def build_markdown(snapshot: dict[str, Any]) -> str:
    rows = [
        f"| {item['名称']} | {'pass' if item['通过'] else 'blocked'} | {item['路径']} |"
        for item in snapshot["检查结果"]
    ]
    blocked = [item["名称"] for item in snapshot["检查结果"] if item["参与阻断"] and not item["通过"]]
    return "\n".join(
        [
            "# 日常可用版自主巡检快照",
            "",
            f"- 生成时间：{snapshot['生成时间']}",
            f"- 总体状态：{snapshot['总体状态']}",
            f"- 通过/总数：{snapshot['汇总']['通过']} / {snapshot['汇总']['总数']}",
            f"- 阻断项：{', '.join(blocked) if blocked else '无'}",
            "",
            "| 检查对象 | 结果 | 来源 |",
            "| --- | --- | --- |",
            *rows,
            "",
            "## 安全边界",
            "",
            "- 不请求 19302 业务接口，不接券商，不交易。",
            "- 不真实发送企业微信，不触发 n8n。",
            "- 不登录电子税务局，不接财税软件，不生成正式税务结论。",
            "- 不调用视频真实渲染，不自动发布。",
            "- 不写正式规则，不修改运行配置，不重载 19310/19302。",
        ]
    )


def main() -> int:
    checks = [summarize_source(name, path, blocking=True) for name, path in EXPLICIT_SOURCES.items()]
    checks.extend(discover_passed_logs())

    blocking_checks = [item for item in checks if item["参与阻断"]]
    blocking_passed = sum(1 for item in blocking_checks if item["通过"])
    passed = sum(1 for item in checks if item["通过"])
    blocking_failed = len(blocking_checks) - blocking_passed

    snapshot = {
        "名称": "日常可用版自主巡检快照",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if blocking_failed == 0 else "blocked",
        "汇总": {
            "总数": len(checks),
            "通过": passed,
            "失败": blocking_failed,
            "阻断检查总数": len(blocking_checks),
            "阻断检查通过": blocking_passed,
        },
        "检查结果": checks,
        "安全边界": {
            "请求19302业务接口": False,
            "接券商": False,
            "交易": False,
            "真实发送企业微信": False,
            "触发n8n": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "生成正式税务结论": False,
            "视频真实渲染": False,
            "自动发布": False,
            "写正式规则": False,
            "修改运行配置": False,
            "重载19310": False,
            "重载19302": False,
        },
        # Legacy mojibake keys kept so older generated scripts can still read the snapshot.
        "鍚嶇О": "日常可用版自主巡检快照",
        "鐢熸垚鏃堕棿": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "鎬讳綋鐘舵€?": "pass" if blocking_failed == 0 else "blocked",
        "姹囨€?": {"鎬绘暟": len(checks), "閫氳繃": passed, "澶辫触": blocking_failed},
        "妫€鏌ョ粨鏋?": [
            {"鍚嶇О": item["名称"], "璺緞": item["路径"], "瀛樺湪": item["存在"], "閫氳繃": item["通过"]}
            for item in checks
        ],
    }
    write_json(LATEST_JSON, snapshot)
    write_text(LATEST_MD, build_markdown(snapshot))
    print(json.dumps({"总体状态": snapshot["总体状态"], "通过": passed, "失败": blocking_failed, "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0 if snapshot["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
