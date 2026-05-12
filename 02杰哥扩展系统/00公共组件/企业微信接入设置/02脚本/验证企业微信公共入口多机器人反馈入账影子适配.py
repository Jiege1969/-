# -*- coding: utf-8 -*-
"""
名称：验证企业微信公共入口多机器人反馈入账影子适配.py
作用：不访问运行中19310，直接加载最新代码，验证反馈类文本可进入多机器人反馈本地入账器。
边界：不重载19310/19302，不触发n8n，不真实发送企业微信，不写正式规则。
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "02脚本" / "企业微信统一指令本地服务入口.py"
LOG_DIR = ROOT / "04日志" / "公共入口多机器人反馈入账影子验收"
REPORT_JSON = ROOT / "03数据" / "16公共入口多机器人反馈入账影子适配" / "公共入口多机器人反馈入账影子验收_最新.json"
REPORT_MD = ROOT / "03数据" / "16公共入口多机器人反馈入账影子适配" / "公共入口多机器人反馈入账影子验收_最新.md"


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("wecom_unified_local_shadow_feedback", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    now = datetime.now()
    module = load_module()
    stamp = now.strftime("%Y%m%d%H%M%S")
    samples = [
        ("system-manager", f"进度不要只报百分比，要告诉我卡在哪里和剩余工时 {stamp}"),
        ("work-secretary", f"税收资料清单缺少政策依据来源，不要写成正式结论 {stamp}"),
        ("video-assistant", f"这个脚本太平，分镜要增加故事动作和现代解读 {stamp}"),
    ]
    checks: list[dict[str, Any]] = []

    add_check(checks, "普通税收查询不误判为反馈", module.is_feedback_intake_message("税收业务：软件产品即征即退需要准备哪些资料") is False)
    add_check(checks, "股票报告链接需求可识别", module.is_feedback_intake_message("报告里股票名称应该可以点击，能看具体分析报告") is True)
    add_check(checks, "反馈入口脚本存在", module.FEEDBACK_INTAKE_SCRIPT.exists(), str(module.FEEDBACK_INTAKE_SCRIPT))

    results = []
    for entry, text in samples:
        if entry == "video-assistant":
            result = module.execute_video_assistant_command(text)
        else:
            result = module.execute_command(text, entry=entry)
        results.append(result)
        add_check(checks, f"{entry}反馈入账完成", result.get("状态") == "完成" and result.get("路由") == "多机器人企业微信需求反馈本地入账", result)
        safety = result.get("安全边界", {}) if isinstance(result.get("安全边界"), dict) else {}
        add_check(checks, f"{entry}未触发n8n", safety.get("触发n8n") is False, safety)
        add_check(checks, f"{entry}未真实发送企业微信", safety.get("真实发送企业微信") is False, safety)
        add_check(checks, f"{entry}未自动转正式规则", safety.get("自动转正式规则") is False, safety)
        add_check(checks, f"{entry}未交易", safety.get("交易接口") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "企业微信公共入口多机器人反馈入账影子验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "样本结果": results,
        "说明": "本验收直接加载最新代码，不代表运行中19310已生效；如需线上生效，需受控重载19310。",
        "安全边界": {
            "重载19310": False,
            "重载19302": False,
            "真实发送企业微信": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "写正式规则": False,
        },
    }
    output = LOG_DIR / f"wecom-public-feedback-intake-shadow-verify-{now.strftime('%Y%m%d-%H%M%S')}.json"
    latest_log = LOG_DIR / "wecom-public-feedback-intake-shadow-verify-最新.json"
    write_json(output, report)
    write_json(latest_log, report)
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join([
        "# 企业微信公共入口多机器人反馈入账影子验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 通过：{passed}",
        f"- 失败：{failed}",
        "- 结论：公共入口代码具备反馈入账能力；运行中19310需受控重载后生效。" if failed == 0 else "- 结论：仍有失败项。",
        "",
        "## 边界",
        "- 未重载19310/19302；未触发n8n；未真实发送企业微信；未写正式规则。",
    ]))
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(REPORT_JSON)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
