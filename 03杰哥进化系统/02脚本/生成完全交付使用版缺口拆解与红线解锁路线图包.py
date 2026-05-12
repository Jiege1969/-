# -*- coding: utf-8 -*-
"""生成完全交付使用版缺口拆解与红线解锁路线图候选包。

本脚本只生成候选路线图材料，不开放红线，不修改配置，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "64完全交付使用版缺口拆解与红线解锁路线图包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版缺口拆解与红线解锁路线图包验收"

LATEST_JSON = OUTPUT_DIR / "完全交付使用版缺口拆解与红线解锁路线图包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用版缺口拆解与红线解锁路线图包_最新.md"
MATRIX_CSV = OUTPUT_DIR / "完全交付使用版缺口拆解矩阵_最新.csv"
GEN_LOG = LOG_DIR / "生成完全交付使用版缺口拆解与红线解锁路线图包_最新.json"

REFERENCE_FILES = [
    EVOLUTION_ROOT / "03数据" / "45完全交付使用路线图与工时估算" / "完全交付使用路线图与工时估算包_最新.json",
    EVOLUTION_ROOT / "03数据" / "54稳定版封版候选总验收与剩余缺口清单" / "稳定版封版候选总验收与剩余缺口清单_最新.json",
    EVOLUTION_ROOT / "03数据" / "63并行施工调度索引与合并验收准备包" / "并行施工调度索引与合并验收准备包_最新.json",
]

SAFETY_BOUNDARY = {
    "仅生成候选路线图": True,
    "开放企业微信真实发送": False,
    "触发n8n": False,
    "连接券商或交易": False,
    "登录税局或连接财税软件": False,
    "真实渲染或发布视频": False,
    "转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "修改服务配置": False,
    "重载19310": False,
    "重载19302": False,
}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"存在": False, "路径": str(path)}
    try:
        return {"存在": True, "路径": str(path), "摘要": json.loads(path.read_text(encoding="utf-8-sig"))}
    except Exception as exc:  # noqa: BLE001 - 只读引用材料允许记录解析失败
        return {"存在": True, "路径": str(path), "解析失败": repr(exc)}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_gap_modules() -> list[dict[str, Any]]:
    return [
        {
            "模块": "企业微信真实发送",
            "当前缺口": "已有候选验证和只读材料，但未进入真实发送白名单、撤回、限流、审计闭环。",
            "解锁前置": [
                "总管书面确认真实发送范围、接收人白名单、消息模板和频率上限",
                "完成沙箱群或低风险测试群验证，并保留撤回、失败重试、人工复核记录",
                "建立发送凭据隔离、日志脱敏、异常停机和回滚方案",
            ],
            "风险等级": "高",
            "是否近期需要": "否，近期只保留候选方案和人工复制发送",
            "预计工作量档位": "M",
            "红线状态": "未开放",
            "候选路线": [
                "只读清点消息模板与接收场景",
                "生成白名单审批单候选",
                "灰度到测试群后再评估是否允许真实发送",
            ],
        },
        {
            "模块": "n8n编排",
            "当前缺口": "可描述编排路线，但不得触发真实工作流或接入生产凭据。",
            "解锁前置": [
                "建立禁用态工作流副本和凭据空壳",
                "完成输入输出契约、幂等、防重复触发和失败回滚设计",
                "由总管确认可触发节点、不可触发节点和人工闸口",
            ],
            "风险等级": "高",
            "是否近期需要": "否，近期只做沙箱编排候选和只读核对",
            "预计工作量档位": "M",
            "红线状态": "未开放",
            "候选路线": [
                "先画出禁用态工作流图",
                "只读核对节点清单和凭据需求",
                "通过人工闸口后再考虑沙箱触发",
            ],
        },
        {
            "模块": "券商交易",
            "当前缺口": "不得连接券商、不得下单、不得模拟成真实资金动作；只能保留复盘和人工决策材料。",
            "解锁前置": [
                "明确账户、权限、风控、合规和责任边界",
                "建立只读行情、模拟盘、人工确认、资金上限和熔断机制",
                "完成审计日志、回放证据和误触发赔付责任确认",
            ],
            "风险等级": "极高",
            "是否近期需要": "否，近期不需要也不建议解锁",
            "预计工作量档位": "XL",
            "红线状态": "未开放",
            "候选路线": [
                "仅沉淀复盘模板和人工检查清单",
                "如未来推进，先从完全离线模拟盘开始",
                "真实交易必须另立专项审批",
            ],
        },
        {
            "模块": "税局财税接入",
            "当前缺口": "不得登录电子税局，不接财税软件，不形成正式税务结论。",
            "解锁前置": [
                "确认授权主体、账号保管、数据范围和税务专业责任人",
                "建立脱敏样本、只读导入、人工复核和操作录像留痕",
                "区分资料整理、风险提示、正式申报三类边界",
            ],
            "风险等级": "极高",
            "是否近期需要": "否，近期只保留资料整理和问答草稿",
            "预计工作量档位": "L",
            "红线状态": "未开放",
            "候选路线": [
                "只读整理资料清单和缺失项",
                "用脱敏样本验证字段映射",
                "正式接入必须由税务责任人确认",
            ],
        },
        {
            "模块": "视频真实渲染发布",
            "当前缺口": "可产出脚本和素材清单，但不得真实渲染、发布或连接账号。",
            "解锁前置": [
                "确认渲染环境、素材版权、发布账号、审核人和发布窗口",
                "建立沙箱渲染、人工看片、回滚下架和日志留存流程",
                "区分草稿生成、成片渲染、真实发布三道闸口",
            ],
            "风险等级": "高",
            "是否近期需要": "否，近期只做脚本、分镜、素材缺口清单",
            "预计工作量档位": "M",
            "红线状态": "未开放",
            "候选路线": [
                "先完善草稿包和人工验收表",
                "再做本地沙箱渲染方案",
                "发布动作必须单独确认",
            ],
        },
        {
            "模块": "正式规则治理",
            "当前缺口": "候选经验和规则很多，但不得自动转正式规则。",
            "解锁前置": [
                "建立候选、评审、批准、生效、回滚、废止的完整状态机",
                "明确总管确认权、冲突检测、版本冻结和影响范围评估",
                "完成至少多轮只读回归和反例样本验证",
            ],
            "风险等级": "中高",
            "是否近期需要": "是，但近期只需要治理机制候选，不转正式规则",
            "预计工作量档位": "M",
            "红线状态": "未开放",
            "候选路线": [
                "先生成规则候选台账",
                "只读检查冲突和重复",
                "人工批准后再进入正式规则变更流程",
            ],
        },
        {
            "模块": "长周期稳定样本",
            "当前缺口": "已有短周期只读回归和候选样本，但缺少跨天、跨异常、跨业务的连续稳定证据。",
            "解锁前置": [
                "连续多日保留只读巡检、失败分级、恢复记录和趋势报告",
                "覆盖企业微信、n8n、税务、股票、视频、规则治理的非真实动作样本",
                "建立样本缺口补录和异常复盘机制",
            ],
            "风险等级": "中",
            "是否近期需要": "是，且可在不开放红线前提下近期推进",
            "预计工作量档位": "S-M",
            "红线状态": "不涉及开放，仅做只读样本",
            "候选路线": [
                "启动3到5日只读稳定样本",
                "每日汇总趋势和异常样例",
                "作为未来红线解锁审批的证据输入",
            ],
        },
    ]


def build_package() -> dict[str, Any]:
    references = [read_json_if_exists(path) for path in REFERENCE_FILES]
    modules = build_gap_modules()
    return {
        "名称": "完全交付使用版缺口拆解与红线解锁路线图候选包",
        "生成时间": now(),
        "性质": "路线图候选包，不是执行授权，不开放任何红线",
        "结论": "完全交付使用版仍受高风险外部动作、正式规则治理和长周期样本不足约束；近期应优先补只读样本和治理候选，不推进真实发送、触发、交易、登录、渲染发布。",
        "安全边界": SAFETY_BOUNDARY,
        "引用材料": references,
        "缺口模块": modules,
        "近期建议": [
            "优先推进长周期稳定样本，只做只读记录和趋势汇总",
            "补正式规则治理候选台账和人工确认闸口，不转正式规则",
            "为企业微信、n8n、视频分别准备沙箱方案，但不触发真实动作",
            "券商交易、税局财税接入继续保持红线关闭",
        ],
        "红线解锁总原则": [
            "没有总管明确授权不解锁",
            "没有沙箱或只读证据不解锁",
            "没有白名单、回滚、审计、人工确认不解锁",
            "涉及资金、税务、真实发布的一律专项审批",
        ],
        "验收口径": {
            "必须包含模块": ["企业微信真实发送", "n8n编排", "券商交易", "税局财税接入", "视频真实渲染发布", "正式规则治理", "长周期稳定样本"],
            "必须保持关闭": ["真实发送", "n8n触发", "券商交易", "税局登录", "财税软件连接", "视频真实渲染发布", "正式规则转入"],
            "允许动作": ["生成候选包", "只读核对", "验证文件结构", "写入本包数据与验收日志"],
        },
    }


def build_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 完全交付使用版缺口拆解与红线解锁路线图候选包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 性质：{package['性质']}",
        f"- 结论：{package['结论']}",
        "",
        "## 缺口模块矩阵",
        "",
        "| 模块 | 风险等级 | 是否近期需要 | 工作量档位 | 红线状态 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in package["缺口模块"]:
        lines.append(
            f"| {item['模块']} | {item['风险等级']} | {item['是否近期需要']} | {item['预计工作量档位']} | {item['红线状态']} |"
        )
    lines.extend(["", "## 解锁前置摘要", ""])
    for item in package["缺口模块"]:
        lines.append(f"### {item['模块']}")
        lines.append(f"- 当前缺口：{item['当前缺口']}")
        lines.append("- 解锁前置：")
        for precondition in item["解锁前置"]:
            lines.append(f"  - {precondition}")
        lines.append("- 候选路线：")
        for step in item["候选路线"]:
            lines.append(f"  - {step}")
        lines.append("")
    lines.extend(
        [
            "## 安全边界",
            "",
            "本包只是路线图候选，不开放红线；不真实发送企业微信，不触发 n8n，不接券商/交易，不登录税局/接财税软件，不真实渲染/发布视频，不转正式规则，不重载 19310/19302。",
        ]
    )
    return "\n".join(lines)


def build_csv(package: dict[str, Any]) -> str:
    header = "模块,风险等级,是否近期需要,预计工作量档位,红线状态,当前缺口\n"
    rows = []
    for item in package["缺口模块"]:
        values = [item["模块"], item["风险等级"], item["是否近期需要"], item["预计工作量档位"], item["红线状态"], item["当前缺口"]]
        rows.append(",".join('"' + str(value).replace('"', '""') + '"' for value in values))
    return header + "\n".join(rows) + "\n"


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    write_text(MATRIX_CSV, build_csv(package))
    log = {
        "名称": "生成完全交付使用版缺口拆解与红线解锁路线图包日志",
        "生成时间": now(),
        "状态": "pass",
        "输出": [str(LATEST_JSON), str(LATEST_MD), str(MATRIX_CSV)],
        "安全边界": SAFETY_BOUNDARY,
    }
    write_json(GEN_LOG, log)
    print(json.dumps({"状态": "pass", "输出": log["输出"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
