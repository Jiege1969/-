# -*- coding: utf-8 -*-
"""
名称：验证税收政策智能查询下载管道.py
作用：验收税收政策智能查询下载管道的配置、脚本、自测、官方查询、小批量下载和分层索引，确认其定位为政策证据底座而非税务结论库。
触发方式：python 验证税收政策智能查询下载管道.py
安全边界：只运行自测和小批量官方查询下载；不触发 n8n；不推送企业微信；不写向量库；不调用模型推理。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收政策智能查询下载管道验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "税收政策智能查询下载管道配置.json"
    script = root / "02脚本" / "税收政策智能查询下载管道.py"
    config = load_json(config_path)
    data_dir = root / config.get("本地资料分层", {}).get("数据目录", "03数据/13智能政策下载管道")
    report_latest = data_dir / "运行报告" / "税收政策智能查询下载管道报告_最新.json"
    report_success = data_dir / "运行报告" / "税收政策智能查询下载管道报告_最近成功.json"
    report_failure = data_dir / "运行报告" / "税收政策智能查询下载管道报告_最近失败.json"
    formal_index = data_dir / "正式依据库" / "正式依据索引_最新.json"

    checks: list[dict[str, Any]] = [
        check("配置存在", config_path.exists(), str(config_path)),
        check("脚本存在", script.exists(), str(script)),
        check("官方搜索接口为国家税务总局搜索接口", "chinatax.gov.cn/search5/search/s" in json.dumps(config, ensure_ascii=False), config.get("官方搜索", {})),
        check("资产身份为政策证据底座", "政策证据底座" in str(config.get("资产身份", "")), config.get("资产身份", "")),
        check("正式依据库口径已纠偏", "不代表正式业务结论库" in json.dumps(config.get("正式依据库口径纠偏", {}), ensure_ascii=False), config.get("正式依据库口径纠偏", {})),
        check("运行报告快照策略已配置", "最近失败报告" in json.dumps(config.get("运行报告快照策略", {}), ensure_ascii=False) and "不覆盖稳定最新报告" in json.dumps(config.get("运行报告快照策略", {}), ensure_ascii=False), config.get("运行报告快照策略", {})),
        check("当前适用候选仅允许全文有效或人工确认有效", set(config.get("文件时效", {}).get("可进入当前适用依据候选", [])) == {"全文有效", "人工确认有效"}, config.get("文件时效", {})),
        check("废止失效尚未生效不作为当前适用依据", all(x in config.get("文件时效", {}).get("不可作为当前适用依据", []) for x in ["全文失效", "全文废止", "尚未生效", "待核验"]), config.get("文件时效", {})),
        check("适用条件字段齐备", all(x in config.get("适用条件字段", []) for x in ["适用主体", "适用事项", "适用期间", "关键条件", "排除条件", "所需资料", "待人工复核项"]), config.get("适用条件字段", [])),
        check("安全边界关闭", all(value is False for value in config.get("安全边界", {}).values()), config.get("安全边界", {})),
    ]

    compile_run = run_cmd([sys.executable, "-m", "py_compile", str(script)], root)
    checks.append(check("脚本编译通过", compile_run.returncode == 0, compile_run.stderr.strip()))

    self_run = run_cmd([sys.executable, str(script), "--self-test"], root)
    checks.append(check("脚本自测通过", self_run.returncode == 0 and "通过" in self_run.stdout, self_run.stdout.strip() or self_run.stderr.strip()))

    live_run = run_cmd([sys.executable, str(script), "--keyword", "研发费用加计扣除", "--download", "--max-results", "2", "--force-search"], root)
    checks.append(check("官方查询下载小样本执行", live_run.returncode == 0, live_run.stdout.strip() or live_run.stderr.strip()))

    valid_run = run_cmd([sys.executable, str(script), "--keyword", "企业所得税", "--aging", "全文有效", "--download", "--max-results", "2", "--force-search"], root)
    checks.append(check("全文有效筛选小样本执行", valid_run.returncode == 0, valid_run.stdout.strip() or valid_run.stderr.strip()))

    latest = load_json(report_latest, {})
    checks.append(check("最新运行报告存在", report_latest.exists(), str(report_latest)))
    checks.append(check("最近成功报告快照存在", report_success.exists(), str(report_success)))
    if report_failure.exists():
        failure = load_json(report_failure, {})
        checks.append(check("失败查询单独留痕", failure.get("运行状态") == "官方查询失败", failure.get("当前结论", "")))
    checks.append(check("稳定最新报告不是失败查询", latest.get("运行状态") != "官方查询失败", latest.get("运行状态", "")))
    checks.append(check("官方候选数量大于0", int(latest.get("官方查询", {}).get("返回数量", 0) or 0) > 0, latest.get("官方查询", {}).get("返回数量")))
    checks.append(check("执行过下载", int(latest.get("下载数量", 0) or 0) > 0, latest.get("下载数量")))
    checks.append(check("分层结果数量一致", int(latest.get("下载数量", 0) or 0) == int(latest.get("正式入库数量", 0) or 0) + int(latest.get("异常待核验数量", 0) or 0), latest))
    formal = load_json(formal_index, {})
    checks.append(check("正式依据索引存在", formal_index.exists(), str(formal_index)))
    checks.append(check("正式依据索引可读", isinstance(formal.get("资料", []), list), formal.get("资料数量")))
    checks.append(check(
        "下载结果有时效或已阻断",
        all(item.get("文件时效") or "文件时效" in "；".join(item.get("阻断原因", [])) for item in latest.get("下载结果", [])),
        latest.get("下载结果", [])
    ))
    checks.append(check("下载结果包含原始文件和解析文本路径", all(item.get("保存路径", {}).get("原始文件") and item.get("保存路径", {}).get("解析文本") for item in latest.get("下载结果", [])), latest.get("下载结果", [])))
    checks.append(check("下载结果不生成正式税务结论", all(item.get("是否生成正式税务结论") is False for item in latest.get("下载结果", [])), latest.get("下载结果", [])))
    checks.append(check("当前适用依据候选字段存在", all("是否当前适用依据候选" in item for item in latest.get("下载结果", [])), latest.get("下载结果", [])))
    checks.append(check("未触发高风险动作", all(value is False for value in latest.get("安全边界", {}).values()), latest.get("安全边界", {})))

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "税收政策智能查询下载管道验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写向量库": False,
            "是否调用模型推理": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否重启服务": False
        },
    }
    out_dir = data_dir / "运行报告"
    latest_json = out_dir / "税收政策智能查询下载管道验收_最新.json"
    latest_md = out_dir / "税收政策智能查询下载管道验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
