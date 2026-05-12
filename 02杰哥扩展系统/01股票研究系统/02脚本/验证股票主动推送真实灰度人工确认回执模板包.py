# -*- coding: utf-8 -*-
"""
名称：验证股票主动推送真实灰度人工确认回执模板包.py
作用：运行250模板包生成脚本，并验证模板待人工确认、真实发送关闭和安全边界。
触发方式：python 验证股票主动推送真实灰度人工确认回执模板包.py
依赖：Python标准库；生成股票主动推送真实灰度人工确认回执模板包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地248规则包、运行本地250生成脚本并写04日志；不调用企业微信API；不真实发送；不启用或触发n8n；不接券商；不交易；不登录税局；不写正式规则；不重载19310/19302；不改总管面板；不改一键接续包。
创建/修改记录：2026-05-09 创建股票主动推送真实灰度人工确认回执模板包验收脚本。
标识：stock-active-push-real-gray-human-confirmation-receipt-template-package-verify
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_TEMPLATE_FIELDS = [
    "确认人",
    "确认时间",
    "目标用户",
    "单人白名单确认",
    "首轮消息条数",
    "频率确认",
    "内容边界确认",
    "熔断规则确认",
    "回滚方式确认",
    "是否允许真实发送",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送真实灰度人工确认回执模板包验收",
        "",
        f"生成时间：{result['生成时间']}",
        "",
        f"- 总体状态：{result['总体状态']}",
        f"- 通过：{result['通过']}",
        f"- 失败：{result['失败']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}，{item['说明']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    source_248 = root / "03数据" / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json"
    before_248_hash = file_sha256(source_248)
    generator = root / "02脚本" / "生成股票主动推送真实灰度人工确认回执模板包.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(generator)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env=env,
    )
    after_248_hash = file_sha256(source_248)
    latest = root / "03数据" / "250主动推送真实灰度人工确认回执模板包" / "股票主动推送真实灰度人工确认回执模板包_最新.json"
    report = load_json(latest)
    template = report.get("确认回执模板", {})
    actions = report.get("实际动作", {})
    required_missing = [field for field in REQUIRED_TEMPLATE_FIELDS if field not in template]
    danger_keys = [
        "调用企业微信API",
        "真实发送企业微信",
        "启用n8n",
        "触发n8n",
        "调用券商接口",
        "自动交易",
        "登录税局",
        "写正式规则库",
        "重载19310",
        "重载19302",
        "修改总管面板",
        "修改一键接续包",
    ]
    dangerous = [key for key in danger_keys if actions.get(key) is not False]
    confirmation_false_fields = [
        "单人白名单确认",
        "频率确认",
        "内容边界确认",
        "熔断规则确认",
        "回滚方式确认",
        "是否允许真实发送",
    ]

    checks = [
        check("生成脚本返回成功", completed.returncode == 0, {"returncode": completed.returncode, "stderr": completed.stderr.strip()}),
        check("模板包存在", latest.exists(), str(latest)),
        check("模板待人工确认未生效", report.get("模板状态") == "待人工确认，未生效", report.get("模板状态")),
        check("顶层真实发送=false", report.get("是否允许真实发送") is False, report.get("是否允许真实发送")),
        check("模板真实发送=false", template.get("是否允许真实发送") is False, template.get("是否允许真实发送")),
        check("n8n=false", report.get("是否启用n8n") is False and report.get("是否触发n8n") is False and actions.get("启用n8n") is False and actions.get("触发n8n") is False, {"是否启用n8n": report.get("是否启用n8n"), "是否触发n8n": report.get("是否触发n8n")}),
        check("券商/交易=false", report.get("是否接券商") is False and report.get("是否交易") is False and actions.get("调用券商接口") is False and actions.get("自动交易") is False, {"是否接券商": report.get("是否接券商"), "是否交易": report.get("是否交易")}),
        check("必填字段齐全", not required_missing, required_missing),
        check("确认项默认未确认", all(template.get(field) is False for field in confirmation_false_fields), {field: template.get(field) for field in confirmation_false_fields}),
        check("确认人时间目标用户为空", template.get("确认人") == "" and template.get("确认时间") == "" and template.get("目标用户") == "", {"确认人": template.get("确认人"), "确认时间": template.get("确认时间"), "目标用户": template.get("目标用户")}),
        check("首轮消息条数为1", template.get("首轮消息条数") == 1, template.get("首轮消息条数")),
        check("危险动作全部关闭", not dangerous, dangerous),
        check("未修改正式规则", before_248_hash != "" and before_248_hash == after_248_hash and actions.get("写正式规则库") is False and report.get("是否写正式规则") is False, {"248生成前sha256": before_248_hash, "248生成后sha256": after_248_hash}),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查结果": checks,
        "模板包": str(latest),
        "来源248规则包": str(source_248),
        "生成脚本输出": completed.stdout.strip(),
    }

    log_dir = root / "04日志" / "主动推送真实灰度人工确认回执模板包"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = log_dir / f"stock-active-push-real-gray-human-confirmation-receipt-template-package-verify-{stamp}.json"
    latest_json = log_dir / "stock-active-push-real-gray-human-confirmation-receipt-template-package-verify-最新.json"
    output_md = log_dir / f"stock-active-push-real-gray-human-confirmation-receipt-template-package-verify-{stamp}.md"
    latest_md = log_dir / "stock-active-push-real-gray-human-confirmation-receipt-template-package-verify-最新.md"
    write_json(output_json, result)
    write_json(latest_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": result["总体状态"], "通过": result["通过"], "失败": result["失败"], "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
