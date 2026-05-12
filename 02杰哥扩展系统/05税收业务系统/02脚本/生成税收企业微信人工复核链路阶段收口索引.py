# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核链路阶段收口"
OUT_JSON = BASE_DIR / "税收企业微信人工复核链路阶段收口索引_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核链路阶段收口索引_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核链路阶段收口索引.json"


MODULES = [
    ("人工复核阅读包批量预演", "税收企业微信人工复核阅读包批量预演验收_最新.md", "pending_human_review_packet"),
    ("人工复核回执空白模板批量预演", "税收企业微信人工复核回执空白模板批量预演验收_最新.md", "blank_receipt_template"),
    ("复核回执到草案状态回写预演", "税收企业微信复核回执到草案状态回写预演验收_最新.md", "no_op_status_rewrite_preview"),
    ("人工复核填写规范与状态机规则", "税收企业微信人工复核填写规范与状态机规则验收_最新.md", "rule_only_state_machine"),
    ("人工复核回执填报校验器预演", "税收企业微信人工复核回执填报校验器预演验收_最新.md", "validation_only"),
    ("人工复核状态机反事实演练", "税收企业微信人工复核状态机反事实演练验收_最新.md", "counterfactual_state_guard"),
    ("人工复核校验失败整改清单", "税收企业微信人工复核校验失败整改清单验收_最新.md", "remediation_list_only"),
    ("待复核分析草案出入口状态索引", "税收企业微信待复核分析草案出入口状态索引验收_最新.md", "read_only_io_index"),
    ("人工复核整改后再校验样例模板", "税收企业微信人工复核整改后再校验样例模板验收_最新.md", "sample_template_only"),
    ("待复核分析草案出入口索引反事实校验", "税收企业微信待复核分析草案出入口索引反事实校验验收_最新.md", "io_counterfactual_guard"),
    ("人工复核样例敏感信息复扫报告", "税收企业微信人工复核样例敏感信息复扫报告验收_最新.md", "sensitive_rescan"),
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


def report_passed(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "失败数量：0" in text or "失败数量: 0" in text or "失败数量\": 0" in text


def pass_count(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "通过数量" in line:
            return line.strip()
    return ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    module_index = []
    for name, report_name, role in MODULES:
        report_path = BASE_DIR / report_name
        module_index.append({
            "模块名称": name,
            "阶段角色": role,
            "验收报告路径": str(report_path),
            "验收报告存在": report_path.exists(),
            "验收是否通过": report_passed(report_path),
            "通过数量摘要": pass_count(report_path),
            "是否可作为正式税务结论": False,
            "是否允许真实发送企业微信": False,
            "是否允许真实回写": False,
        })

    passed = sum(1 for item in module_index if item["验收是否通过"])
    missing = [item for item in module_index if not item["验收报告存在"]]
    failed = [item for item in module_index if item["验收报告存在"] and not item["验收是否通过"]]
    result = {
        "名称": "税收企业微信人工复核链路阶段收口索引",
        "生成时间": now,
        "资产身份": "dry-run人工复核链路阶段收口索引，不是真实入口放行，不写正式业务库，不是税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "模块数量": len(module_index),
        "通过数量": passed,
        "缺失数量": len(missing),
        "失败数量": len(failed),
        "模块索引": module_index,
        "阶段结论": "通过" if not missing and not failed else "待补齐",
        "阶段护栏": [
            "本阶段只完成人工复核链路的本地dry-run资产闭环。",
            "所有资产均为政策证据底座/待复核分析草案支撑材料。",
            "不得把阅读包、回执、整改清单、状态索引或敏感信息复扫结果解释为正式税务意见。",
            "不得真实发送企业微信、不得读取凭据、不得真实回写草案源文件。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信人工复核链路一键本地预检脚本。",
            "生成税收企业微信人工复核链路阶段总回传记录。"
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核链路阶段收口索引",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run阶段收口索引，不是真实入口放行，不写正式业务库，不是税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        f"- 模块数量：{len(module_index)}",
        f"- 通过数量：{passed}",
        f"- 缺失数量：{len(missing)}",
        f"- 失败数量：{len(failed)}",
        f"- 阶段结论：{result['阶段结论']}",
        "",
        "## 模块索引",
        "",
    ]
    for item in module_index:
        lines.append(f"- {item['模块名称']}：存在={item['验收报告存在']}，通过={item['验收是否通过']}，角色={item['阶段角色']}。")
    lines.extend(["", "## 阶段护栏", ""])
    for item in result["阶段护栏"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": result["阶段结论"], "报告": str(OUT_MD), "模块数量": len(module_index), "失败数量": len(failed)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
