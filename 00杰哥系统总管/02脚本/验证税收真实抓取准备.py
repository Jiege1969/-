"""
名称：验证税收真实抓取准备.py
作用：验证税收真实抓取攻坚阶段的灰度配置、只读计划、官方来源探测和禁止入库边界是否可用。
触发方式：python 验证税收真实抓取准备.py
依赖：Python 标准库；需要网络可访问官方站点。
所属系统：00杰哥系统总管
安全边界：只运行税收业务模块的只读探测脚本；不写入正式政策库、不写入向量库、不触发n8n、不发送企业微信。
创建/修改记录：2026-04-26 创建税收真实抓取攻坚阶段准备验收脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "05税收业务系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "税收真实抓取准备验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def run_script(script: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "税收真实抓取灰度配置.json"
    config = load_json(config_path)
    switches = config.get("抓取开关", {})
    entries = config.get("官方入口", [])

    plan_script = root / "02脚本" / "生成税收真实抓取灰度计划.py"
    probe_script = root / "02脚本" / "税收官方来源只读探测.py"
    plan_result = run_script(plan_script, 60)
    probe_result = run_script(probe_script, 180)

    latest_plan = root / "03数据" / "07抓取探测" / "税收真实抓取灰度计划_最新.json"
    latest_probe = root / "03数据" / "07抓取探测" / "税收官方来源只读探测_最新.json"
    plan_data = load_json(latest_plan) if latest_plan.exists() else {}
    probe_data = load_json(latest_probe) if latest_probe.exists() else {}
    stats = probe_data.get("统计", {})

    checks = [
        check("灰度配置存在", config_path.exists(), str(config_path)),
        check("官方入口不少于三个", len(entries) >= 3, [item.get("名称") for item in entries]),
        check("允许联网探测", switches.get("允许联网探测") is True, switches),
        check("禁止下载正文", switches.get("允许下载正文") is False, switches),
        check("禁止写入正式政策目录", switches.get("允许写入正式政策目录") is False, switches),
        check("禁止写入向量库", switches.get("允许写入向量库") is False, switches),
        check("禁止触发n8n", switches.get("允许触发n8n") is False, switches),
        check("禁止企微推送", switches.get("允许企微推送") is False, switches),
        check(
            "证书退化探测限制",
            "退化探测限制" in config.get("请求策略", {}) and switches.get("允许下载正文") is False,
            config.get("请求策略", {}).get("退化探测限制", ""),
        ),
        check("灰度计划脚本执行", plan_result.returncode == 0, (plan_result.stdout or "").strip() or (plan_result.stderr or "").strip()),
        check("只读探测脚本执行", probe_result.returncode == 0, (probe_result.stdout or "").strip() or (probe_result.stderr or "").strip()),
        check("最新灰度计划存在", latest_plan.exists(), str(latest_plan)),
        check(
            "灰度计划结构",
            "任务列表" in plan_data and plan_data.get("是否可进入真实抓取只读探测") is True and plan_data.get("是否可进入正式入库") is False,
            {"任务数量": len(plan_data.get("任务列表", [])), "正式入库": plan_data.get("是否可进入正式入库")},
        ),
        check("最新只读探测报告存在", latest_probe.exists(), str(latest_probe)),
        check(
            "只读探测报告结构",
            "结果" in probe_data and "统计" in probe_data and probe_data.get("是否写入正式政策目录") is False,
            stats,
        ),
        check(
            "官方入口连通性",
            int(stats.get("连通成功数量", 0)) >= 1,
            stats,
        ),
        check(
            "候选链接登记",
            int(stats.get("候选链接数量", 0)) >= 0,
            stats,
        ),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "tax-real-crawl-readiness-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"tax-real-crawl-readiness-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
