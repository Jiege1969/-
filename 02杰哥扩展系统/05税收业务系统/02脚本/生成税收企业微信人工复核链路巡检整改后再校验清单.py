# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路巡检整改后再校验清单"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路巡检整改后再校验清单.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路巡检整改后再校验清单.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改后再校验清单_最新.md"

TEMPLATE_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检失败整改模板_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template = load_json(TEMPLATE_JSON)
    templates = template.get("整改模板", [])

    common_scripts = [
        "验证税收企业微信人工复核链路巡检失败整改模板.py",
        "验证税收企业微信人工复核链路持续巡检样例演练.py",
        "验证税收企业微信人工复核链路持续巡检规则.py",
        "验证税收企业微信人工复核链路一键本地预检.py",
        "生成税收系统当前阶段收口验收与下一步队列.py",
        "验证税收系统当前阶段收口验收与下一步队列.py",
    ]
    extra_by_type = {
        "验收报告缺失": ["补齐缺失验收报告后，先运行对应模块生成脚本，再运行对应模块验证脚本。"],
        "验收失败": ["修正失败检查项后，先运行对应模块验证脚本，再运行人工复核链路一键本地预检。"],
        "红线漂移": ["确认安全边界恢复为False后，运行持续巡检规则验证和总收口验证。"],
        "正式结论口径": ["修正为待复核分析草案口径后，运行消息合规审查或相关草案验收脚本。"],
        "总管越权修改": ["撤回越权动作后，生成本线对齐回传记录，并运行总收口验证。"],
        "已完成项回流": ["补充回流原因或移出无原因回流项后，重新生成当前阶段总收口。"],
    }
    rechecks = []
    for item in templates:
        kind = item.get("整改类型", "")
        rechecks.append({
            "整改类型": kind,
            "再校验前置条件": [
                "整改项状态为remediation_draft。",
                "已填写问题编号、触发规则、影响范围、整改建议、人工复核人和后续再校验脚本。",
                "未修改真实资产、总管文件、公共企业微信配置、n8n、服务脚本或正式入口。",
            ],
            "专项再校验动作": extra_by_type.get(kind, ["运行对应模块验证脚本。"]),
            "统一再校验脚本": common_scripts,
            "通过标准": [
                "对应整改类型不再命中阻断。",
                "相关验收报告失败数量为0。",
                "安全边界全部保持False。",
                "当前阶段总收口缺失数量为0、失败数量为0。",
            ],
            "未通过处理": "保持blocked或remediation_draft状态，补充人工复核项，不得自动回写真实资产。",
        })

    report = {
        "名称": "税收企业微信人工复核链路巡检整改后再校验清单",
        "生成时间": now,
        "资产身份": "税务线本地再校验清单，不修改真实资产，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "引用整改模板": str(TEMPLATE_JSON),
        "整改类型数量": len(templates),
        "再校验清单数量": len(rechecks),
        "再校验清单": rechecks,
        "总收口复跑顺序": [
            "运行对应模块生成脚本。",
            "运行对应模块验证脚本。",
            "运行人工复核链路一键本地预检。",
            "运行当前阶段总收口生成脚本。",
            "运行当前阶段总收口验收脚本。",
            "生成本线对齐回传记录。",
        ],
        "下一步建议": [
            "生成人工复核链路巡检整改闭环阶段收口索引，汇总巡检规则、样例演练、整改模板和再校验清单。",
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
        "# 税收企业微信人工复核链路巡检整改后再校验清单",
        "",
        f"- 生成时间：{now}",
        f"- 整改类型数量：{len(templates)}",
        f"- 再校验清单数量：{len(rechecks)}",
        "- 资产身份：税务线本地再校验清单，不修改真实资产，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "",
        "## 再校验清单",
        "",
    ]
    for item in rechecks:
        lines.append(f"### {item['整改类型']}")
        lines.append(f"- 前置条件：{'；'.join(item['再校验前置条件'])}")
        lines.append(f"- 专项再校验动作：{'；'.join(item['专项再校验动作'])}")
        lines.append(f"- 统一再校验脚本：{'、'.join(item['统一再校验脚本'])}")
        lines.append(f"- 通过标准：{'；'.join(item['通过标准'])}")
        lines.append(f"- 未通过处理：{item['未通过处理']}")
        lines.append("")
    lines.extend(["## 总收口复跑顺序", ""])
    for item in report["总收口复跑顺序"]:
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
    print(json.dumps({"状态": "完成", "再校验清单数量": len(rechecks), "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
