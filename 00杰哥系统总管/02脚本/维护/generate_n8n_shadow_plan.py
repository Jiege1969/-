# -*- coding: utf-8 -*-
"""
名称：generate_n8n_shadow_plan.py
作用：生成 n8n 影子试验预案，只列出影子端口、独立数据目录、导出路径和人工确认命令清单。
触发方式：python generate_n8n_shadow_plan.py
依赖：upgrade_governance_common.py；upgrade_rules.json；version_ledger.json。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/n8n_shadow_plan_latest.json|md。
安全边界：只生成预案；不创建容器、不导出工作流、不导入工作流、不启停服务、不挂正式数据目录。
创建/修改记录：2026-05-03 创建版本治理 V1.1 预案脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-n8n-shadow-plan
"""

from __future__ import annotations

import json

from upgrade_governance_common import LOG_DIR, MANAGER, NO_ACTION_BOUNDARY, now_stamp, write_json, write_text


def main() -> int:
    now, _stamp = now_stamp()
    shadow_dir = MANAGER / "03数据" / "n8n_shadow"
    export_path = LOG_DIR / "n8n_workflows_export_latest.json"
    plan = {
        "名称": "n8n影子试验预案",
        "版本": "V1.1",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "正式端口": "127.0.0.1:28679",
        "影子端口": "127.0.0.1:5679",
        "影子数据目录": str(shadow_dir),
        "工作流导出建议路径": str(export_path),
        "禁止事项": [
            "不得挂载正式n8n数据目录",
            "不得启用正式Webhook",
            "不得触发企业微信真实发送",
            "不得把影子测试结果自动切换为正式版本",
        ],
        "人工确认后才可执行的命令清单": [
            f"curl -s http://127.0.0.1:28679/rest/workflows -o \"{export_path}\"",
            f"mkdir \"{shadow_dir}\"",
            "docker run -d --name n8n-shadow --network ai-platform_ai-network -p 5679:5678 -v \"<影子数据目录>:/home/node/.n8n\" n8nio/n8n:<候选版本>",
            "在 http://127.0.0.1:5679 手动导入工作流 JSON 并禁用真实外发节点",
            "测试完成后人工执行：docker stop n8n-shadow && docker rm n8n-shadow",
        ],
        "验收样本": [
            "只读打开n8n影子界面",
            "导入工作流后保持禁用态",
            "手动跑测试节点，确认不会调用真实企业微信",
            "生成测试报告，不污染正式数据",
        ],
        "安全边界": NO_ACTION_BOUNDARY,
        "结论": "本文件只是预案；未创建容器、未导出工作流、未停启服务。",
    }
    latest_json = LOG_DIR / "n8n_shadow_plan_latest.json"
    latest_md = LOG_DIR / "n8n_shadow_plan_latest.md"
    lines = [
        "# n8n影子试验预案",
        "",
        f"- 生成时间：{plan['生成时间']}",
        f"- 影子端口：{plan['影子端口']}",
        f"- 影子数据目录：{plan['影子数据目录']}",
        f"- 工作流导出建议路径：{plan['工作流导出建议路径']}",
        "",
        "## 禁止事项",
        "",
        *[f"- {item}" for item in plan["禁止事项"]],
        "",
        "## 人工确认后才可执行的命令清单",
        "",
        *[f"{idx}. `{cmd}`" for idx, cmd in enumerate(plan["人工确认后才可执行的命令清单"], 1)],
        "",
        "## 结论",
        "",
        plan["结论"],
        "",
    ]
    write_json(latest_json, plan)
    write_text(latest_md, "\n".join(lines))
    print(json.dumps({"状态": "完成", "报告": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
