# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信首轮真实灰度测试记录包.py
作用：生成股票企业微信首轮真实灰度测试记录模板、未执行状态、测试用例和异常回滚记录口径。
触发方式：python 生成股票企业微信首轮真实灰度测试记录包.py
依赖：Python标准库；股票企业微信首轮真实灰度测试记录规则.json；真实灰度未确认拦截包_最新.json；真实灰度确认回执登记包_最新.json；真实灰度放行前总验收包_最新.json；真实灰度白名单试运行包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信首轮真实灰度测试记录包脚本。
标识：stock-wework-first-real-gray-test-record-package-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信首轮真实灰度测试记录包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备测试记录模板条件：{report['是否具备测试记录模板条件']}",
        f"- 当前测试状态：{report['当前测试状态']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、测试记录模板",
        "",
    ]
    for item in report["测试记录模板"]:
        lines.append(f"- {item['编号']}｜{item['类型']}｜{item['输入']}｜状态：{item['执行状态']}｜合格标准：{item['合格标准']}")
    lines.extend(["", "## 三、异常记录模板", ""])
    for key, value in report["异常记录模板"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信首轮真实灰度测试记录规则.json"
    guard_path = root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json"
    receipt_path = root / "03数据" / "45真实灰度确认回执登记" / "股票企业微信真实灰度确认回执登记包_最新.json"
    preflight_path = root / "03数据" / "44真实灰度放行前总验收" / "股票企业微信真实灰度放行前总验收包_最新.json"
    trial_path = root / "03数据" / "42真实灰度白名单试运行" / "股票企业微信真实灰度白名单试运行包_最新.json"

    rule = load_json(rule_path)
    guard = load_json(guard_path)
    receipt = load_json(receipt_path)
    preflight = load_json(preflight_path)
    trial = load_json(trial_path)
    default_state = rule.get("默认状态", {})
    cases = rule.get("测试用例", [])
    records = [
        {
            "编号": item.get("编号"),
            "输入": item.get("输入"),
            "类型": item.get("类型"),
            "合格标准": item.get("合格标准"),
            "执行状态": "未执行",
            "发送时间": "",
            "返回时间": "",
            "是否合格": "",
            "异常说明": "",
            "是否触发回滚": False,
        }
        for item in cases
    ]
    prerequisites = {
        "未确认拦截包存在": guard_path.exists(),
        "未确认拦截已启用": guard.get("是否启用未确认拦截") is True,
        "确认回执登记包存在": receipt_path.exists(),
        "确认状态仍为未确认": receipt.get("当前确认状态") == "未确认",
        "放行前总验收包存在": preflight_path.exists(),
        "放行前总验收可提交人工确认": preflight.get("是否具备提交人工确认条件") is True,
        "白名单试运行材料具备": trial.get("是否满足灰度试运行材料要求") is True,
        "默认测试状态未执行": default_state.get("测试状态") == "未执行",
        "默认真实发送关闭": default_state.get("是否允许真实发送") is False,
        "默认交易关闭": default_state.get("是否允许交易") is False,
    }
    passed = all(prerequisites.values()) and len(records) == 5 and all(item.get("执行状态") == "未执行" for item in records)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "依赖材料": {
            "未确认拦截包": str(guard_path),
            "确认回执登记包": str(receipt_path),
            "放行前总验收包": str(preflight_path),
            "白名单试运行包": str(trial_path),
        },
        "前置条件": prerequisites,
        "测试原则": rule.get("测试原则", []),
        "默认状态": default_state,
        "当前测试状态": default_state.get("测试状态", "未执行"),
        "测试记录模板": records,
        "异常记录模板": {
            "异常编号": "",
            "关联测试编号": "",
            "异常现象": "",
            "初步原因": "",
            "处置动作": "按真实灰度回滚预案退回本地队列",
            "是否纳入进化样本": True,
        },
        "是否具备测试记录模板条件": passed,
        "当前结论": "首轮真实灰度测试记录模板已具备；当前仍为未执行状态，不发送企业微信、不触发n8n、不调用OpenClaw。" if passed else "首轮真实灰度测试记录模板前置条件不足，不能进入测试记录阶段。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "47首轮真实灰度测试记录"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信首轮真实灰度测试记录包_{stamp}.json"
    latest_json = output_dir / "股票企业微信首轮真实灰度测试记录包_最新.json"
    output_md = output_dir / f"股票企业微信首轮真实灰度测试记录包_{stamp}.md"
    latest_md = output_dir / "股票企业微信首轮真实灰度测试记录包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备测试记录模板条件": passed, "当前测试状态": report["当前测试状态"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
