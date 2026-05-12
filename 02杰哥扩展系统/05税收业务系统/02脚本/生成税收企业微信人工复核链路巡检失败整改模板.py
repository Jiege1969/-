# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路巡检失败整改模板"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路巡检失败整改模板.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路巡检失败整改模板.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板_最新.md"

DRILL_JSON = ENTRY_DIR / "税收企业微信人工复核链路持续巡检样例演练_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def template_for(kind: str, trigger: str, action: str) -> dict[str, Any]:
    return {
        "整改类型": kind,
        "触发条件": trigger,
        "处理动作": action,
        "状态流转": "blocked -> remediation_draft -> pending_human_review -> human_reviewed",
        "必填字段": [
            "问题编号",
            "发现时间",
            "触发规则",
            "影响范围",
            "整改建议",
            "整改责任人",
            "人工复核人",
            "人工复核时间",
            "复核结论",
            "后续再校验脚本",
        ],
        "禁止动作": [
            "不自动修改真实资产",
            "不修改总管文件",
            "不修改公共企业微信配置",
            "不读取或保存企业微信凭据",
            "不真实发送企业微信",
            "不写正式库",
            "不生成正式税务结论",
        ],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    drill = load_json(DRILL_JSON)
    drill_results = drill.get("样例结果", [])
    blocked_cases = [item for item in drill_results if item.get("识别结果") == "阻断"]

    templates = [
        template_for("验收报告缺失", "巡检发现必备验收报告不存在或路径不可读。", "生成缺失报告补齐清单，要求先补齐报告再运行一键本地预检。"),
        template_for("验收失败", "巡检发现任一验收报告失败数量大于0。", "登记失败检查项、失败详情和再校验脚本，禁止进入当前适用依据候选。"),
        template_for("红线漂移", "巡检发现任一安全边界从False变为True。", "登记红线阻断，停止相关链路，仅允许总管判断是否另行放行。"),
        template_for("正式结论口径", "巡检发现正式税务意见、正式结论、可以享受、金额确定等口径。", "改写为待复核分析草案口径，并列入人工复核项。"),
        template_for("总管越权修改", "巡检发现本线试图修改总管文件、公共企业微信配置、n8n、服务脚本或正式入口。", "撤回越权请求，仅生成本线对齐回传记录。"),
        template_for("已完成项回流", "巡检发现已完成事项重新进入下一步队列且无原因说明。", "要求补充回流原因、关联风险和是否重新验收。"),
    ]

    report = {
        "名称": "税收企业微信人工复核链路巡检失败整改模板",
        "生成时间": now,
        "资产身份": "税务线本地整改模板，不修改真实资产，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "引用演练": str(DRILL_JSON),
        "演练阻断样例数量": len(blocked_cases),
        "模板数量": len(templates),
        "整改模板": templates,
        "统一处置要求": [
            "所有整改项先进入remediation_draft，不得自动回写真实资产。",
            "所有整改项必须列明触发规则、影响范围、人工复核人和再校验脚本。",
            "涉及红线漂移、真实发送、凭据、总管文件或公共配置的事项只登记阻断，不实施。",
            "整改后必须重新运行对应验收脚本和当前阶段总收口验收。",
        ],
        "下一步建议": [
            "生成人工复核链路巡检整改后再校验清单，固定每类整改后的再验收脚本。",
        ],
        "安全边界": {
            "是否修改真实资产": False,
            "是否创建自动化任务": False,
            "是否启动或重启服务": False,
            "是否新增或修改端口": False,
            "是否触发n8n": False,
            "是否读取或保存企业微信凭据": False,
            "是否企业微信真实发送": False,
            "是否修改公共企业微信配置": False,
            "是否修改总管文件": False,
            "是否写正式库": False,
            "是否生成正式税务结论": False,
            "是否删除或移动旧资产": False,
        },
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检失败整改模板",
        "",
        f"- 生成时间：{now}",
        f"- 模板数量：{len(templates)}",
        f"- 演练阻断样例数量：{len(blocked_cases)}",
        "- 资产身份：税务线本地整改模板，不修改真实资产，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "",
        "## 整改模板",
        "",
    ]
    for item in templates:
        lines.append(f"### {item['整改类型']}")
        lines.append(f"- 触发条件：{item['触发条件']}")
        lines.append(f"- 处理动作：{item['处理动作']}")
        lines.append(f"- 状态流转：{item['状态流转']}")
        lines.append(f"- 必填字段：{'、'.join(item['必填字段'])}")
        lines.append(f"- 禁止动作：{'、'.join(item['禁止动作'])}")
        lines.append("")
    lines.extend(["## 统一处置要求", ""])
    for item in report["统一处置要求"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步建议", ""])
    for item in report["下一步建议"]:
        lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    copy_latest(OUT_JSON, LATEST_JSON)
    copy_latest(OUT_MD, LATEST_MD)
    print(json.dumps({"状态": "完成", "模板数量": len(templates), "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
