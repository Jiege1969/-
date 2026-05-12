# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = DATA_DIR / "税收企业微信dry-run阶段收口索引_最新.json"
OUT_MD = DATA_DIR / "税收企业微信dry-run阶段收口索引_最新.md"


SOURCE_REPORTS = [
    ("机器人终端绑定", "税收企业微信机器人终端绑定报告验收_最新.json"),
    ("公共组件对齐核实", "税收企业微信公共组件对齐核实报告验收_最新.json"),
    ("输入消息契约样例", "税收企业微信输入消息契约样例验收_最新.json"),
    ("消息接收服务设计", "税收企业微信消息接收服务设计报告验收_最新.json"),
    ("本地输入队列预演", "税收企业微信本地输入队列预演验收_最新.json"),
    ("输入队列证据匹配影子流转", "税收企业微信输入队列证据匹配影子流转验收_最新.json"),
    ("证据匹配到分析契约输入包", "税收企业微信证据匹配到分析契约输入包验收_最新.json"),
    ("分析契约输入包到待复核草案骨架", "税收企业微信分析契约输入包到待复核草案骨架验收_最新.json"),
    ("待复核草案骨架到分析摘要预演", "税收企业微信待复核草案骨架到分析摘要预演验收_最新.json"),
    ("正式入口消息预演", "税收企业微信正式入口消息预演验收_最新.json"),
    ("消息合规审查", "税收企业微信消息合规审查报告验收_最新.json"),
    ("凭据接入预检", "税收企业微信凭据接入预检验收_最新.json"),
    ("接收范围与消息分级", "税收企业微信接收范围与消息分级验收_最新.json"),
    ("应急停用与回滚预案", "税收企业微信应急停用与回滚预案验收_最新.json"),
    ("真实发送准备清单", "税收企业微信真实发送准备清单验收_最新.json"),
    ("真实发送上线变更单", "税收企业微信真实发送上线变更单验收_最新.json"),
    ("正式入口发送门禁", "税收企业微信正式入口发送门禁验收_最新.json"),
    ("发送审计台账汇总", "税收企业微信发送审计台账汇总验收_最新.json"),
    ("上线就绪度矩阵", "税收企业微信上线就绪度矩阵验收_最新.json"),
    ("门禁反事实演练", "税收企业微信门禁反事实演练验收_最新.json"),
    ("正式入口全链路预检", "税收企业微信正式入口全链路预检验收_最新.json"),
    ("入口配置一致性巡检", "税收企业微信入口配置一致性巡检验收_最新.json"),
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"解析失败": True}


def is_passed(data: dict) -> bool:
    if not data:
        return False
    if data.get("解析失败"):
        return False
    conclusion = str(data.get("结论", data.get("状态", data.get("巡检结论", ""))))
    failed = data.get("失败数量")
    if failed == 0:
        return True
    return conclusion in {"通过", "已生成", "pass", "passed"}


def source_status() -> list[dict]:
    rows = []
    for name, filename in SOURCE_REPORTS:
        path = DATA_DIR / filename
        data = load_json(path)
        rows.append(
            {
                "名称": name,
                "路径": str(path),
                "是否存在": path.exists(),
                "是否通过": is_passed(data),
                "失败数量": data.get("失败数量", "未读取"),
                "通过数量": data.get("通过数量", data.get("步骤数量", "未读取")),
            }
        )
    return rows


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sources = source_status()
    missing = [item for item in sources if not item["是否存在"]]
    failed = [item for item in sources if item["是否存在"] and not item["是否通过"]]

    hard_boundaries = {
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "是否重启服务": False,
        "是否修改19310": False,
        "是否接入真实账号": False,
        "是否读取或保存企业微信凭据": False,
        "是否修改公共企业微信接入配置": False,
        "是否修改总管文件": False,
        "是否写正式库": False,
        "是否生成正式税务结论": False,
    }

    required_contract_fields = [
        "政策依据",
        "依据层级",
        "有效状态",
        "适用条件",
        "业务事实",
        "missing",
        "confidence",
        "人工复核项",
    ]

    package = {
        "名称": "税收企业微信dry-run阶段收口索引",
        "生成时间": now,
        "资产身份": "税收业务系统本线dry-run收口索引，不是正式入口配置，不是企业微信真实发送许可。",
        "总体结论": "dry_run_evidence_ready_pending_human_review" if not missing and not failed else "dry_run_needs_fix",
        "适用范围": "仅适用于税收业务系统目录内的杰哥工作秘书输入输出干跑链路复核。",
        "不适用范围": [
            "不作为企业微信真实发送放行",
            "不作为公共组件路由修改依据",
            "不作为服务脚本或19310修改依据",
            "不作为正式税务结论",
            "不作为n8n接入许可",
        ],
        "来源报告数量": len(sources),
        "来源报告通过数量": sum(1 for item in sources if item["是否通过"]),
        "来源报告缺失数量": len(missing),
        "来源报告失败数量": len(failed),
        "来源报告状态": sources,
        "dry_run链路阶段": [
            "企业微信公共组件接收后路由到税收本地输入队列的口径已在税收本线形成对齐材料。",
            "税收侧只接收本地队列样例，不登记新的公网回调，不读取公共凭据。",
            "输入消息按契约进入脱敏、分级、证据匹配、分析契约输入包和待复核草案骨架。",
            "输出仅停留在消息预演和待复核摘要，不真实发送。",
        ],
        "待复核输出最低字段": required_contract_fields,
        "可交付状态": {
            "本线dry_run链路": "可复核",
            "正式企业微信入口": "未放行",
            "真实发送": "阻断",
            "税务结论": "仅待复核草案",
            "总管整合": "需要总管只读吸收，不由税收线自行改总管。",
        },
        "阻断事项": [
            "真实发送凭据接入必须交回总管判断。",
            "公共路由、服务脚本、19310、n8n和正式配置修改必须交回总管判断。",
            "待复核草案不得升级为正式税务意见。",
            "RAG或模型正式问答链路未放行。",
        ],
        "硬边界": hard_boundaries,
        "下一步建议": [
            "继续用本索引核对税收企业微信dry-run链路是否完整。",
            "补充更多脱敏涉税问题样例时，必须保留政策依据、依据层级、有效状态、适用条件、业务事实、missing、confidence和人工复核项。",
            "如需真实发送、公共路由或服务变更，暂停并交回总管对话框。",
        ],
    }

    OUT_JSON.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信dry-run阶段收口索引",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：税收业务系统本线dry-run收口索引，不是正式入口配置，不是企业微信真实发送许可。",
        f"- 总体结论：{package['总体结论']}",
        f"- 来源报告：{package['来源报告通过数量']}/{package['来源报告数量']} 通过，缺失 {len(missing)}，失败 {len(failed)}",
        "",
        "## dry-run链路阶段",
    ]
    lines.extend(f"- {item}" for item in package["dry_run链路阶段"])
    lines.extend(["", "## 待复核输出最低字段"])
    lines.extend(f"- {item}" for item in required_contract_fields)
    lines.extend(["", "## 可交付状态"])
    lines.extend(f"- {key}：{value}" for key, value in package["可交付状态"].items())
    lines.extend(["", "## 阻断事项"])
    lines.extend(f"- {item}" for item in package["阻断事项"])
    lines.extend(["", "## 硬边界"])
    lines.extend(f"- {key}：{value}" for key, value in hard_boundaries.items())
    lines.extend(["", "## 来源报告状态"])
    for item in sources:
        status = "通过" if item["是否通过"] else "未通过"
        lines.append(f"- {item['名称']}：{status}；存在={item['是否存在']}；路径={item['路径']}")
    lines.extend(["", "## 下一步建议"])
    lines.extend(f"- {item}" for item in package["下一步建议"])
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"状态": package["总体结论"], "输出": str(OUT_MD), "来源报告失败数量": len(failed)}, ensure_ascii=False))
    return 0 if not missing and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
