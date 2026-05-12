# -*- coding: utf-8 -*-
"""生成稳定版运行期问题分级与处置路线包。

只形成试运行问题的分级、转交、候选队列和总管确认闸口，不写正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "101稳定版运行期问题分级与处置路线包"

LATEST_JSON = OUTPUT_DIR / "稳定版运行期问题分级与处置路线包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定版运行期问题分级与处置路线包_最新.md"
ROUTE_MD = OUTPUT_DIR / "运行期问题分级与处置路线_最新.md"
GATE_MATRIX_JSON = OUTPUT_DIR / "总管确认闸口矩阵_最新.json"
QUEUE_TEMPLATE_JSON = OUTPUT_DIR / "候选任务队列模板_最新.json"

FEEDBACK_RESULT_JSON = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账结果_最新.json"
FEEDBACK_LEDGER_JSON = EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈候选台账_最新.json"
KEEPALIVE_RESULT_JSON = EVOLUTION_ROOT / "03数据" / "100稳定版样本等待期低风险保活巡检包" / "稳定版样本等待期低风险保活巡检执行结果_最新.json"
DAILY_ENTRY_CARD = EVOLUTION_ROOT / "03数据" / "98稳定版每日唯一入口操作卡同步包" / "稳定版每日唯一入口操作卡_最新.md"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "接n8n": False,
    "触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "写正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def pick(data: dict[str, Any], *keys: str, default: Any = 0) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return default


def build_levels() -> list[dict[str, Any]]:
    return [
        {
            "级别": "P0",
            "名称": "红线或外部真实动作风险",
            "触发条件": ["请求真实发送企业微信", "请求接入或触发 n8n", "请求券商交易", "请求登录税局或接财税软件", "请求正式规则自动生效", "请求视频真实发布", "请求重载 19310/19302"],
            "处置": "停止自动施工，登记为需总管确认，只输出可复制确认项",
            "需总管确认": True,
            "允许自动执行": False,
        },
        {
            "级别": "P1",
            "名称": "稳定运行阻断",
            "触发条件": ["一键只读总回归失败", "运行指挥台红灯", "反馈入账器拒收异常增多", "自然日样本链路失败"],
            "处置": "只读定位、生成复跑建议和回滚路线；涉及重载或配置改动时升级总管确认",
            "需总管确认": True,
            "允许自动执行": False,
        },
        {
            "级别": "P2",
            "名称": "普通试运行问题",
            "触发条件": ["回复口径不清", "前台展示不一致", "说明文档不够顺手", "用户体验反馈"],
            "处置": "进入候选任务队列，先本地复现和候选修复，不自动改正式规则",
            "需总管确认": False,
            "允许自动执行": True,
        },
        {
            "级别": "P3",
            "名称": "文档和流程优化",
            "触发条件": ["入口说明需要补充", "操作卡文字优化", "巡检报告字段补充"],
            "处置": "低风险补充候选文档和验收建议，不触碰运行配置",
            "需总管确认": False,
            "允许自动执行": True,
        },
    ]


def build_routes() -> list[dict[str, Any]]:
    return [
        {"问题域": "企业微信公共入口", "判断关键词": ["工作秘书", "系统管家", "视频助理", "19310", "企业微信"], "承接方式": "公共接入层候选任务", "红线提示": "真实发送或重载必须总管确认"},
        {"问题域": "税收", "判断关键词": ["税收", "增值税", "即征即退", "研发费用"], "承接方式": "税收待复核候选任务", "红线提示": "不登录税局、不接财税软件、不出正式税务结论"},
        {"问题域": "股票", "判断关键词": ["股票", "个股", "研究价值", "风险复核"], "承接方式": "股票展示或研究候选任务", "红线提示": "不接券商、不交易、不输出下单指令"},
        {"问题域": "视频", "判断关键词": ["视频", "渲染", "发布", "MoneyPrinterTurbo", "ImageMagick"], "承接方式": "视频预检或环境候选任务", "红线提示": "不真实渲染、不自动发布"},
        {"问题域": "智能进化", "判断关键词": ["规则", "候选", "进化", "经验"], "承接方式": "进化候选任务", "红线提示": "不自动转正式规则"},
    ]


def build_queue_template(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "队列字段": ["问题ID", "来源", "问题域", "级别", "原始描述", "复现证据", "建议动作", "是否需总管确认", "是否允许自动执行"],
            "默认流转": "先入候选队列，再复现，再按级别决定是否施工",
            "问题域列表": [item["问题域"] for item in routes],
        }
    ]


def build_route_md(report: dict[str, Any]) -> str:
    level_rows = [
        f"| {item['级别']} | {item['名称']} | {item['需总管确认']} | {item['允许自动执行']} | {item['处置']} |"
        for item in report["问题分级"]
    ]
    route_rows = [
        f"| {item['问题域']} | {'、'.join(item['判断关键词'])} | {item['承接方式']} | {item['红线提示']} |"
        for item in report["问题域路线"]
    ]
    return "\n".join(
        [
            "# 运行期问题分级与处置路线",
            "",
            "## 问题分级",
            "",
            "| 级别 | 名称 | 需总管确认 | 允许自动执行 | 处置 |",
            "| --- | --- | --- | --- | --- |",
            *level_rows,
            "",
            "## 问题域路线",
            "",
            "| 问题域 | 判断关键词 | 承接方式 | 红线提示 |",
            "| --- | --- | --- | --- |",
            *route_rows,
            "",
        ]
    )


def build_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定版运行期问题分级与处置路线包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 当前反馈扫描文件数：{report['当前反馈摘要']['扫描文件数']}",
            f"- 当前需总管确认数：{report['当前反馈摘要']['需总管确认数']}",
            f"- 保活巡检状态：{report['等待期保活摘要'].get('总体状态')}",
            "",
            "## 输出文件",
            "",
            *[f"- {key}：{value}" for key, value in report["输出文件"].items()],
            "",
        ]
    )


def main() -> int:
    feedback_result = read_json(FEEDBACK_RESULT_JSON)
    feedback_ledger = read_json(FEEDBACK_LEDGER_JSON)
    keepalive = read_json(KEEPALIVE_RESULT_JSON)
    levels = build_levels()
    routes = build_routes()
    queue_template = build_queue_template(routes)
    gate_matrix = {
        "P0": {"需总管确认": True, "允许自动执行": False, "说明": "红线或外部真实动作风险"},
        "P1": {"需总管确认": True, "允许自动执行": False, "说明": "稳定运行阻断"},
        "P2": {"需总管确认": False, "允许自动执行": True, "说明": "候选修复或候选文档"},
        "P3": {"需总管确认": False, "允许自动执行": True, "说明": "文档流程优化"},
    }
    report = {
        "名称": "稳定版运行期问题分级与处置路线包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_runtime_issue_triage_route_ready",
        "当前反馈摘要": {
            "扫描文件数": pick(feedback_result, "扫描文件数", "鎵弿鏂囦欢鏁?", default=0),
            "接收数": pick(feedback_result, "接收数", "鎺ユ敹鏁?", default=0),
            "拒收数": pick(feedback_result, "拒收数", "鎷掓敹鏁?", default=0),
            "需总管确认数": pick(feedback_result, "需总管确认数", "闇€鎬荤纭鏁?", default=0),
            "候选台账存在": bool(feedback_ledger),
        },
        "等待期保活摘要": {
            "总体状态": keepalive.get("总体状态"),
            "执行失败": keepalive.get("汇总", {}).get("失败"),
            "今天是否允许新增自然日样本": keepalive.get("等待期摘要", {}).get("今天是否允许新增自然日样本"),
        },
        "问题分级": levels,
        "问题域路线": routes,
        "总管确认闸口矩阵": gate_matrix,
        "候选任务队列模板": queue_template,
        "来源文件": {
            "反馈入账结果": str(FEEDBACK_RESULT_JSON),
            "反馈候选台账": str(FEEDBACK_LEDGER_JSON),
            "等待期保活巡检": str(KEEPALIVE_RESULT_JSON),
            "每日唯一入口操作卡": str(DAILY_ENTRY_CARD),
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "运行期问题分级与处置路线": str(ROUTE_MD),
            "总管确认闸口矩阵": str(GATE_MATRIX_JSON),
            "候选任务队列模板": str(QUEUE_TEMPLATE_JSON),
        },
    }
    write_json(GATE_MATRIX_JSON, gate_matrix)
    write_json(QUEUE_TEMPLATE_JSON, queue_template)
    write_json(LATEST_JSON, report)
    write_text(ROUTE_MD, build_route_md(report))
    write_text(LATEST_MD, build_md(report))
    print(json.dumps({"状态": report["状态"], "问题分级": len(levels), "问题域路线": len(routes), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
