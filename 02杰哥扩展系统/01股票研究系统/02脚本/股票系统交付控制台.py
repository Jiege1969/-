# -*- coding: utf-8 -*-
"""
名称：股票系统交付控制台.py
作用：统一股票主动研究系统的交付状态查看、闭环运行、n8n手动受控测试和企微复测入口。
触发方式：python 股票系统交付控制台.py [--mode status|run|n8n-test|wecom-check|all] [--real-wecom]
依赖：股票主动研究闭环、本地自检、n8n手动测试、企微灰度发送脚本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：默认不真实发送企业微信；不启用n8n；不调用券商接口；不自动交易。
标识：stock-delivery-console
"""

from __future__ import annotations

import argparse
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
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(root: Path, script: str, extra: list[str] | None = None, timeout: int = 1800) -> dict[str, Any]:
    args = [sys.executable, str(root / "02脚本" / script), *(extra or [])]
    started = datetime.now()
    completed = subprocess.run(
        args,
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "脚本": script,
        "参数": extra or [],
        "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "返回码": completed.returncode,
        "成功": completed.returncode == 0,
        "stdout": (completed.stdout or "").strip()[-3000:],
        "stderr": (completed.stderr or "").strip()[-3000:],
    }


def refresh_self_check(root: Path) -> dict[str, Any]:
    run_script(root, "生成股票系统交付自检报告.py", timeout=120)
    return load_json(root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.json", {})


def build_markdown(report: dict[str, Any]) -> str:
    status = report.get("当前状态", {})
    files = report.get("关键文件", {})
    actions = report.get("本次动作", [])
    lines = [
        f"# 股票系统交付控制台 - {report['生成时间']}",
        "",
        "## 一、当前状态",
        "",
        f"- 交付层级：{status.get('交付层级', '')}",
        f"- 本地闭环：{'通过' if status.get('本地可用') else '未通过'}",
        f"- n8n手动受控测试：{'通过' if status.get('n8n手动受控测试') else '未通过'}",
        f"- 企微通道检查：{'通过' if status.get('企微通道检查') else '未通过'}",
        f"- 企微真实发送：{'通过' if status.get('企微真实发送成功') else '未通过'}",
        "",
        "## 二、本次动作",
        "",
    ]
    if actions:
        for item in actions:
            lines.append(f"- {item.get('脚本')}：{'成功' if item.get('成功') else '失败'}")
    else:
        lines.append("- 仅刷新状态。")
    lines.extend([
        "",
        "## 三、关键文件",
        "",
    ])
    for name, path in files.items():
        lines.append(f"- {name}：`{path}`")
    lines.extend([
        "",
        "## 四、仍需处理",
        "",
    ])
    for item in report.get("仍需处理", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 默认不真实发送企业微信。",
        "- 未启用n8n。",
        "- 未调用券商接口。",
        "- 未自动交易。",
    ])
    return "\n".join(lines)


def console_report(root: Path, mode: str, actions: list[dict[str, Any]], real_wecom: bool) -> dict[str, Any]:
    self_check = refresh_self_check(root)
    layers = self_check.get("层级验收", {})
    key_files = {
        "日常速查卡": str(root / "03数据" / "145日常速查卡" / "股票系统日常使用速查卡_最新.md"),
        "质量观察面板": str(root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"),
        "质量观察历史": str(root / "03数据" / "147质量观察历史" / "股票系统质量观察历史_最新.md"),
        "模型健康检查": str(root / "03数据" / "148模型健康检查" / "股票系统模型健康检查_最新.md"),
        "金融专项复核": str(root / "03数据" / "149金融专项复核" / "股票金融专项复核_最新.md"),
        "金融专项复核索引": str(root / "03数据" / "149金融专项复核索引" / "股票金融专项复核索引_最新.md"),
        "报告安全边界检查": str(root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md"),
        "C+++日常可用总验收": str(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
        "可信IP放行后最终验收包": str(root / "03数据" / "154可信IP放行后最终验收包" / "股票系统可信IP放行后最终验收包_最新.md"),
        "可信IP状态监测": str(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md"),
        "企微真实推送复测控制器": str(root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.md"),
        "AI报告": str(root / "03数据" / "135分层日报" / "AI分析报告_最新.md"),
        "企微推送草案": str(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"),
        "交付自检": str(root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.md"),
        "可信IP修复包": str(root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.md"),
        "n8n手动测试记录": str(root / "04日志" / "n8n本地手动测试" / "stock-active-research-n8n-local-manual-execute-最新.json"),
    }
    real_ok = bool(layers.get("D真实灰度可用", {}).get("是否通过"))
    pending = []
    if not real_ok:
        pending.append("企业微信应用主动消息仍需可信IP白名单放行；当前修复包已生成。")
    if not bool(layers.get("C3n8n手动受控测试", {}).get("是否通过")):
        pending.append("n8n手动受控测试未通过，需要先修复桥接。")
    report = {
        "名称": "股票系统交付控制台",
        "版本": "2026-05-01",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "运行模式": mode,
        "real_wecom": real_wecom,
        "当前状态": {
            "交付层级": self_check.get("当前交付层级", ""),
            "本地可用": bool(layers.get("A本地可用", {}).get("是否通过")),
            "企微通道检查": bool(layers.get("B2企业微信通道检查", {}).get("是否通过")),
            "n8n已导入未激活": bool(layers.get("C2n8n未激活导入", {}).get("是否通过")),
            "n8n手动受控测试": bool(layers.get("C3n8n手动受控测试", {}).get("是否通过")),
            "企微真实发送成功": real_ok,
        },
        "本次动作": actions,
        "关键文件": key_files,
        "仍需处理": pending,
        "安全边界": {
            "是否真实发送企业微信": bool(real_wecom),
            "是否启用n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    return report


def maybe_open(path: str) -> None:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["status", "run", "n8n-test", "wecom-check", "all"], default="status")
    parser.add_argument("--real-wecom", action="store_true", help="仅用于可信IP修复后复测真实发送")
    parser.add_argument("--open-report", action="store_true", help="运行后打开控制台报告")
    args = parser.parse_args()

    root = module_root()
    actions: list[dict[str, Any]] = []

    if args.mode in {"run", "all"}:
        actions.append(run_script(root, "运行股票主动研究闭环_本地.py", ["--no-complex"], timeout=1800))
    if args.mode in {"n8n-test", "all"}:
        actions.append(run_script(root, "执行股票主动研究n8n本地手动测试.py", timeout=2400))
    if args.mode in {"wecom-check", "all"}:
        actions.append(run_script(root, "生成企业微信可信IP修复包.py", timeout=120))
        extra = ["--real-send"] if args.real_wecom else []
        actions.append(run_script(root, "执行股票主动研究企微灰度发送.py", extra, timeout=180))
    if args.mode in {"run", "all"}:
        actions.append(run_script(root, "检查股票系统报告安全边界.py", timeout=120))
        actions.append(run_script(root, "生成股票系统可信IP状态监测.py", timeout=120))
        actions.append(run_script(root, "生成股票系统质量观察面板.py", timeout=120))
        actions.append(run_script(root, "记录股票系统质量观察历史.py", timeout=120))
        actions.append(run_script(root, "验证股票系统C加加加日常可用总验收.py", timeout=120))
        actions.append(run_script(root, "生成股票系统可信IP放行后最终验收包.py", timeout=120))

    report = console_report(root, args.mode, actions, args.real_wecom)
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    output_dir = root / "03数据" / "143交付控制台"
    output_json = output_dir / f"股票系统交付控制台_{stamp}.json"
    output_md = output_dir / f"股票系统交付控制台_{stamp}.md"
    latest_json = output_dir / "股票系统交付控制台_最新.json"
    latest_md = output_dir / "股票系统交付控制台_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    if args.open_report:
        maybe_open(str(latest_md))
    ok = all(item.get("成功") for item in actions) if actions else True
    print(json.dumps({
        "状态": "完成" if ok else "存在失败动作",
        "模式": args.mode,
        "交付层级": report["当前状态"]["交付层级"],
        "控制台报告": str(latest_md),
        "动作数": len(actions),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
