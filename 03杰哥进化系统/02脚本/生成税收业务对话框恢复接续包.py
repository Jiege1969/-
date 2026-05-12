# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = EVOLUTION / "03数据" / "115税收业务对话框恢复接续包"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    tax_root = ROOT / "02杰哥扩展系统" / "05税收业务系统"
    wecom_root = ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置"
    tax_entry = tax_root / "02脚本" / "生成税收企业微信正式入口消息预演.py"

    recovery_instruction = """你现在接手【税收业务任务】对话框。不要从头分析，直接按以下状态继续。

当前范围：
D:\\杰哥智能化系统\\02杰哥扩展系统\\05税收业务系统

当前状态：
- 税收内部旧链路已最小修复。
- “软件产品即征即退”不再误识别为“研发费用加计扣除”。
- “增值税法依据”已能识别为“增值税法依据”。
- “研发费用加计扣除需要准备哪些资料”已能输出待复核资料清单。
- 企业微信公共接入层到税收新入口已适配并经 19310 受控重载后验收通过。
- `/wecom/work-secretary` 三条税收输入均返回 `【税收分析助手-待复核草案摘要】`。

税收新入口：
D:\\杰哥智能化系统\\02杰哥扩展系统\\05税收业务系统\\02脚本\\生成税收企业微信正式入口消息预演.py

该脚本支持：
--text
或
TAX_WECOM_INPUT_TEXT

当前红线：
- 不登录电子税务局；
- 不接财税软件；
- 不生成正式税务结论；
- 不生成金额测算；
- 不生成办理指令；
- 不真实发送企业微信；
- 不接 n8n；
- 不修改企业微信公共接入配置；
- 不修改总管面板；
- 不修改一键接续包；
- 不自行重载 19310/19302。

下一步只做低风险恢复接续：
1. 读取税收业务系统内当前最新产物和脚本状态；
2. 只做税收侧待复核口径的只读回归，不修改公共企业微信接入层；
3. 本地验证三条输入：
   - 税收业务：软件产品即征即退需要准备哪些资料
   - 税收业务：帮我查一下增值税法的依据
   - 税收业务：研发费用加计扣除需要准备哪些资料
4. 三条均应返回标题：`【税收分析助手-待复核草案摘要】`；
5. 主题分别识别为：
   - 软件产品增值税即征即退
   - 增值税法依据
   - 研发费用加计扣除
6. 输出《税收业务对话框恢复接续回传》；
7. 若发现需改公共接入层或需重载 19310，只登记为“需总管确认”，不得自行处理。
"""

    checklist = [
        {"项目": "税收业务根目录存在", "路径": str(tax_root), "通过": tax_root.exists()},
        {"项目": "企业微信公共接入层根目录存在", "路径": str(wecom_root), "通过": wecom_root.exists()},
        {"项目": "税收新入口脚本存在", "路径": str(tax_entry), "通过": tax_entry.exists()},
        {"项目": "恢复任务指令已生成", "路径": str(OUT_DIR / "税收业务对话框恢复任务指令_最新.md"), "通过": True},
    ]

    payload = {
        "名称": "税收业务对话框恢复接续包",
        "生成时间": now_text(),
        "状态": "pass" if all(item["通过"] for item in checklist) else "blocked",
        "用途": "在税收业务对话框误归档后，给新税收业务对话框提供可复制接续任务、现状边界和只读验收目标。",
        "当前已知状态": {
            "税收内部旧链路": "已最小修复",
            "公共接入层到税收新入口": "已适配并经 19310 受控重载后通过",
            "输出标题": "【税收分析助手-待复核草案摘要】",
            "税收新入口": str(tax_entry),
        },
        "恢复任务指令": recovery_instruction,
        "只读验收样本": [
            {
                "输入": "税收业务：软件产品即征即退需要准备哪些资料",
                "期望标题": "【税收分析助手-待复核草案摘要】",
                "期望事项": "软件产品增值税即征即退",
            },
            {
                "输入": "税收业务：帮我查一下增值税法的依据",
                "期望标题": "【税收分析助手-待复核草案摘要】",
                "期望事项": "增值税法依据",
            },
            {
                "输入": "税收业务：研发费用加计扣除需要准备哪些资料",
                "期望标题": "【税收分析助手-待复核草案摘要】",
                "期望事项": "研发费用加计扣除",
            },
        ],
        "接续检查清单": checklist,
        "需总管确认事项": [
            "需要修改企业微信公共接入层",
            "需要重载 19310 或 19302",
            "需要形成正式税务结论",
            "需要接电子税务局或财税软件",
        ],
        "安全边界": {
            "真实发送企业微信": False,
            "真实触发n8n": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "生成正式税务结论": False,
            "修改公共企业微信配置": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
        },
    }

    outputs = {
        "总包JSON": OUT_DIR / "税收业务对话框恢复接续包_最新.json",
        "总包Markdown": OUT_DIR / "税收业务对话框恢复接续包_最新.md",
        "恢复任务指令": OUT_DIR / "税收业务对话框恢复任务指令_最新.md",
        "税收恢复只读验收清单": OUT_DIR / "税收恢复只读验收清单_最新.md",
        "税收恢复红线边界": OUT_DIR / "税收恢复红线边界_最新.md",
    }
    payload["输出文件"] = {name: str(path) for name, path in outputs.items()}
    write_json(outputs["总包JSON"], payload)

    summary = "\n".join(
        [
            f"- 生成时间：{payload['生成时间']}",
            f"- 状态：{payload['状态']}",
            f"- 用途：{payload['用途']}",
            f"- 税收新入口：{tax_entry}",
            "",
            "## 输出文件",
            "",
            *[f"- {name}：{path}" for name, path in payload["输出文件"].items()],
        ]
    )
    write_md(outputs["总包Markdown"], "税收业务对话框恢复接续包", summary)
    write_md(outputs["恢复任务指令"], "税收业务对话框恢复任务指令", recovery_instruction)

    sample_lines = ["| 输入 | 期望标题 | 期望事项 |", "| --- | --- | --- |"]
    for sample in payload["只读验收样本"]:
        sample_lines.append(f"| {sample['输入']} | {sample['期望标题']} | {sample['期望事项']} |")
    write_md(outputs["税收恢复只读验收清单"], "税收恢复只读验收清单", "\n".join(sample_lines))

    boundary_lines = ["| 红线 | 当前状态 |", "| --- | --- |"]
    for name, value in payload["安全边界"].items():
        boundary_lines.append(f"| {name} | {value} |")
    write_md(outputs["税收恢复红线边界"], "税收恢复红线边界", "\n".join(boundary_lines))

    print(json.dumps({"status": payload["状态"], "output": str(outputs["总包JSON"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
