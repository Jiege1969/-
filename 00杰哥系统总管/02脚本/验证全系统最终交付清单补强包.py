# -*- coding: utf-8 -*-
"""
只读验证脚本：验证全系统最终交付清单补强包。

安全约束：
- 只读取 Markdown/JSON 文件。
- 不写文件，不联网，不触发 n8n/企业微信/正式库/券商接口/交易动作。
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\00杰哥系统总管")
FILES = {
    "补强包Markdown": ROOT / "03数据" / "运行状态" / "全系统最终交付清单补强包_最新.md",
    "补强包JSON": ROOT / "03数据" / "运行状态" / "全系统最终交付清单补强包_最新.json",
    "回收报告Markdown": ROOT / "03数据" / "并行回收" / "00总管_全系统最终验收补强回收报告_最新.md",
    "回收报告JSON": ROOT / "03数据" / "并行回收" / "00总管_全系统最终验收补强回收报告_最新.json",
}

REQUIRED_SCOPE = ["00总管", "01智能", "02扩展", "03进化", "股票分析only"]
REQUIRED_MD_SECTIONS = [
    "验收结论",
    "覆盖范围",
    "最终交付清单",
    "安全边界",
    "回滚证据",
    "剩余 13-23 小时拆解",
    "不可自动打开的真实动作",
]
REQUIRED_FORBIDDEN_ACTIONS = [
    "n8n",
    "企业微信主动真实发送",
    "正式库写入",
    "券商接口连接",
    "自动交易",
    "下单",
]
REQUIRED_SAFETY_KEYS = [
    "不触发n8n",
    "不发送企业微信真实消息",
    "不写正式库",
    "不调用券商接口",
    "不自动交易",
    "不下单",
    "不修改进度口径数字",
    "不回退他人修改",
]


def pass_item(results: list[dict], name: str, detail: str = "") -> None:
    results.append({"检查项": name, "状态": "通过", "详情": detail})


def fail_item(results: list[dict], name: str, detail: str) -> None:
    results.append({"检查项": name, "状态": "失败", "详情": detail})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def main() -> int:
    results: list[dict] = []

    for label, path in FILES.items():
        if path.exists() and path.is_file():
            pass_item(results, f"{label}存在", str(path))
        else:
            fail_item(results, f"{label}存在", str(path))

    if any(item["状态"] == "失败" for item in results):
        print(json.dumps({"结论": "失败", "检查结果": results}, ensure_ascii=False, indent=2))
        return 1

    package_md = read_text(FILES["补强包Markdown"])
    package_json = read_json(FILES["补强包JSON"])
    report_md = read_text(FILES["回收报告Markdown"])
    report_json = read_json(FILES["回收报告JSON"])

    for section in REQUIRED_MD_SECTIONS:
        if section in package_md:
            pass_item(results, f"Markdown章节存在：{section}")
        else:
            fail_item(results, f"Markdown章节存在：{section}", "补强包 Markdown 缺少该章节")

    for scope in REQUIRED_SCOPE:
        if scope in package_json.get("覆盖范围", {}) and scope in package_md:
            pass_item(results, f"覆盖范围存在：{scope}")
        else:
            fail_item(results, f"覆盖范围存在：{scope}", "Markdown 或 JSON 未覆盖")

    if package_json.get("当前进度口径") == "80%-87%" and package_json.get("剩余有效工时口径") == "13-23小时":
        pass_item(results, "进度与剩余工时口径正确", "80%-87%，13-23小时")
    else:
        fail_item(
            results,
            "进度与剩余工时口径正确",
            f"读取到：{package_json.get('当前进度口径')}，{package_json.get('剩余有效工时口径')}",
        )

    if package_json.get("是否重算进度") is False:
        pass_item(results, "不重算进度")
    else:
        fail_item(results, "不重算进度", "是否重算进度不为 false")

    if package_json.get("是否触发外部服务") is False and package_json.get("是否执行真实动作") is False:
        pass_item(results, "未触发外部服务且未执行真实动作")
    else:
        fail_item(results, "未触发外部服务且未执行真实动作", "JSON 标志不是 false")

    safety = package_json.get("安全边界", {})
    for key in REQUIRED_SAFETY_KEYS:
        if safety.get(key) is True:
            pass_item(results, f"安全边界保持：{key}")
        else:
            fail_item(results, f"安全边界保持：{key}", "缺失或不是 true")

    forbidden_text = "\n".join(package_json.get("不可自动打开的真实动作", [])) + "\n" + package_md
    for action in REQUIRED_FORBIDDEN_ACTIONS:
        if action in forbidden_text:
            pass_item(results, f"不可自动打开动作已列明：{action}")
        else:
            fail_item(results, f"不可自动打开动作已列明：{action}", "缺少动作项")

    if len(package_json.get("回滚证据", [])) >= 5 and "回滚证据" in package_md:
        pass_item(results, "回滚证据完整", f"{len(package_json.get('回滚证据', []))} 项")
    else:
        fail_item(results, "回滚证据完整", "少于 5 项或 Markdown 缺少回滚章节")

    work_items = package_json.get("剩余13到23小时拆解", [])
    if len(work_items) >= 6 and all(item.get("是否可自动执行") is False for item in work_items):
        pass_item(results, "剩余13-23小时拆解完整且不自动执行", f"{len(work_items)} 项")
    else:
        fail_item(results, "剩余13-23小时拆解完整且不自动执行", "拆解少于 6 项或存在可自动执行项")

    if report_json.get("结论") == "通过" and "结论：通过" in report_md:
        pass_item(results, "固定回收报告结论一致", "通过")
    else:
        fail_item(results, "固定回收报告结论一致", "Markdown 或 JSON 结论不一致")

    generated_files = report_json.get("生成文件", [])
    if all(str(path) in generated_files for path in FILES.values()):
        pass_item(results, "固定回收报告列出全部核心文件")
    else:
        fail_item(results, "固定回收报告列出全部核心文件", "生成文件列表不完整")

    failed = [item for item in results if item["状态"] == "失败"]
    conclusion = "通过" if not failed else "失败"
    print(json.dumps({"结论": conclusion, "失败数量": len(failed), "检查结果": results}, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

