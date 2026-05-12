# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "02脚本"
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核链路一键本地预检"
OUT_JSON = BASE_DIR / "税收企业微信人工复核链路一键本地预检_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核链路一键本地预检_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核链路一键本地预检.json"


VALIDATORS = [
    ("人工复核阅读包批量预演", "验证税收企业微信人工复核阅读包批量预演.py"),
    ("人工复核回执空白模板批量预演", "验证税收企业微信人工复核回执空白模板批量预演.py"),
    ("复核回执到草案状态回写预演", "验证税收企业微信复核回执到草案状态回写预演.py"),
    ("人工复核填写规范与状态机规则", "验证税收企业微信人工复核填写规范与状态机规则.py"),
    ("人工复核回执填报校验器预演", "验证税收企业微信人工复核回执填报校验器预演.py"),
    ("人工复核状态机反事实演练", "验证税收企业微信人工复核状态机反事实演练.py"),
    ("人工复核校验失败整改清单", "验证税收企业微信人工复核校验失败整改清单.py"),
    ("待复核分析草案出入口状态索引", "验证税收企业微信待复核分析草案出入口状态索引.py"),
    ("人工复核整改后再校验样例模板", "验证税收企业微信人工复核整改后再校验样例模板.py"),
    ("待复核分析草案出入口索引反事实校验", "验证税收企业微信待复核分析草案出入口索引反事实校验.py"),
    ("人工复核样例敏感信息复扫报告", "验证税收企业微信人工复核样例敏感信息复扫报告.py"),
    ("人工复核链路阶段收口索引", "验证税收企业微信人工复核链路阶段收口索引.py"),
]

SAFETY = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
    "是否写草案源文件": False,
    "是否真实回写状态": False,
    "是否调用模型推理": False,
    "是否接电子税务局": False,
    "是否接财税软件": False,
    "是否生成正式税务结论": False,
    "是否形成正式复核结论": False,
    "是否覆盖历史资料": False,
    "是否删除历史审计记录": False,
}


def run_validator(name: str, filename: str) -> dict:
    path = SCRIPT_DIR / filename
    if not path.exists():
        return {
            "模块名称": name,
            "脚本路径": str(path),
            "脚本存在": False,
            "退出码": None,
            "是否通过": False,
            "stdout": "",
            "stderr": "validator missing",
        }
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    return {
        "模块名称": name,
        "脚本路径": str(path),
        "脚本存在": True,
        "退出码": completed.returncode,
        "是否通过": completed.returncode == 0,
        "stdout": completed.stdout.strip()[-1000:],
        "stderr": completed.stderr.strip()[-1000:],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = [run_validator(name, filename) for name, filename in VALIDATORS]
    passed = sum(1 for item in results if item["是否通过"])
    failed = [item for item in results if not item["是否通过"]]
    report = {
        "名称": "税收企业微信人工复核链路一键本地预检",
        "生成时间": now,
        "资产身份": "dry-run一键本地预检，只运行本线验证脚本，不真实发送，不读取凭据，不写正式业务库，不是税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "验证脚本数量": len(results),
        "通过数量": passed,
        "失败数量": len(failed),
        "预检结果": results,
        "结论": "通过" if not failed else "失败",
        "下一步低风险队列": [
            "生成税收企业微信人工复核链路阶段总回传记录。",
            "生成税收企业微信人工复核链路持续巡检规则。"
        ],
        "安全边界": SAFETY,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核链路一键本地预检",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run本地预检，只运行本线验证脚本，不真实发送，不读取凭据，不写正式业务库，不是税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        f"- 验证脚本数量：{len(results)}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{len(failed)}",
        f"- 结论：{report['结论']}",
        "",
        "## 预检结果",
        "",
    ]
    for item in results:
        lines.append(f"- {item['模块名称']}：脚本存在={item['脚本存在']}，退出码={item['退出码']}，通过={item['是否通过']}。")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in report["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": len(failed), "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
