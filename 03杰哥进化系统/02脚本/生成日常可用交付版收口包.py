# -*- coding: utf-8 -*-
"""生成日常可用交付版收口包。

只生成使用说明、故障处理清单、税收接续替代包、端口诊断与重载申请模板候选。
不写正式规则、不改运行配置、不触发服务重载。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "46日常可用交付版收口包"
LATEST_JSON = OUTPUT_DIR / "日常可用交付版收口包_最新.json"
LATEST_MD = OUTPUT_DIR / "日常可用交付版收口包_最新.md"
USER_GUIDE_MD = OUTPUT_DIR / "日常使用说明_最新.md"
TROUBLESHOOTING_MD = OUTPUT_DIR / "故障处理清单_最新.md"
TAX_CONTINUATION_MD = OUTPUT_DIR / "税收业务接续替代包_最新.md"
PORT_TEMPLATE_MD = OUTPUT_DIR / "19310_19302端口诊断与重载申请模板_最新.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_package() -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usage = [
        {
            "场景": "系统状态",
            "输入样例": "系统现在进度多少",
            "预期体验": "系统管家返回当前阶段、巡检状态和剩余有效工时口径。",
            "边界": "只读状态，不重载服务。",
        },
        {
            "场景": "税收资料清单",
            "输入样例": "税收业务：研发费用加计扣除需要准备哪些资料",
            "预期体验": "工作秘书返回【税收分析助手-待复核草案摘要】。",
            "边界": "不生成正式税务结论，不登录税局，不接财税软件。",
        },
        {
            "场景": "股票研究",
            "输入样例": "分析天齐锂业",
            "预期体验": "系统管家/工作秘书转交股票助手或股票专家；前台口径不出现交易化旧词。",
            "边界": "不接券商，不交易，不给买卖点或仓位建议。",
        },
        {
            "场景": "视频预检",
            "输入样例": "生成预检 VF-20260508-005",
            "预期体验": "视频助理返回预检状态；真实渲染/发布条件不满足时 blocked。",
            "边界": "不真实渲染，不上传，不发布。",
        },
        {
            "场景": "日常巡检",
            "输入样例": "运行一键只读总回归",
            "预期体验": "总管运行总回归脚本，汇总企业微信、股票、视频、进化候选状态。",
            "边界": "不请求19302业务接口，不触发n8n，不重载19310/19302。",
        },
    ]
    troubleshooting = [
        {
            "问题": "19310 /health 不通",
            "先做": "只读读取端口状态、PID、入口命令行、最新日志。",
            "不得做": "不得直接重载；登记为需总管确认。",
            "升级条件": "health不可达且日常巡检失败。",
        },
        {
            "问题": "19302 状态异常",
            "先做": "只读读取端口状态，不请求股票业务入口。",
            "不得做": "不得触碰股票业务接口，不重载19302。",
            "升级条件": "仅登记需总管确认。",
        },
        {
            "问题": "税收三条回归失败",
            "先做": "复查19310工作秘书入口、税收新入口脚本路径、最新巡检报告。",
            "不得做": "不得登录税局，不接财税软件，不出正式结论。",
            "升级条件": "若需重载19310，登记需总管确认。",
        },
        {
            "问题": "股票展示旧口径回潮",
            "先做": "运行展示口径一致性脚本和全量扫雷脚本。",
            "不得做": "不得改评分引擎，不接券商，不交易。",
            "升级条件": "若是展示层产物，可做最小展示层修复；核心逻辑变更需另行登记。",
        },
        {
            "问题": "视频请求误放行风险",
            "先做": "读取任务ID与放行链一致性复核卡、视频真实渲染禁用态检查。",
            "不得做": "不得真实渲染、不得发布、不得访问平台账号。",
            "升级条件": "任务ID不一致或发布清单缺失时继续 blocked。",
        },
    ]
    tax_continuation = {
        "定位": "税收业务对话框已归档移除后的接续替代说明。",
        "当前已通过": [
            "税收内部新入口已通过三类主题识别。",
            "工作秘书公共路由已把手机端原始文本传给税收新入口。",
            "19310受控重载后现场接口层验收通过。",
            "输出标题统一为【税收分析助手-待复核草案摘要】。",
        ],
        "可用入口": str(ROOT / "02杰哥扩展系统" / "05税收业务系统" / "02脚本" / "生成税收企业微信正式入口消息预演.py"),
        "接续策略": [
            "日常不重建税收业务对话框也可使用工作秘书入口。",
            "需要税收施工时，新建税收业务任务对话框并贴接续包。",
            "税收线保持待复核草案，不做正式税务结论。",
        ],
        "硬边界": ["不登录电子税务局", "不接财税软件", "不生成正式税务结论", "不真实发送企业微信"],
    }
    port_template = {
        "名称": "19310/19302端口诊断与重载申请模板",
        "诊断步骤": [
            "记录19310/19302端口监听状态、PID、进程名、命令行。",
            "读取19310 /health；19302只读端口状态，不请求业务入口。",
            "读取最新一键只读总回归报告和对应失败项。",
            "判断是否只需等待、是否为脚本误判、是否为服务未加载新代码。",
        ],
        "重载申请字段": [
            "申请端口",
            "当前PID",
            "入口脚本",
            "申请原因",
            "预期验证样本",
            "不得触碰端口",
            "回滚或停止条件",
        ],
        "模板正文": [
            "需总管确认：申请受控重载 <19310或19302>。",
            "原因：<填写原因>。",
            "重载前记录：端口/PID/入口/日志。",
            "重载后验证：<列明只读验证样本>。",
            "限制：不得触碰 <另一个端口>，不得真实发送企业微信，不触发n8n，不接券商，不交易。",
        ],
    }
    return {
        "名称": "日常可用交付版收口包",
        "生成时间": now,
        "性质": "候选收口包，不是正式规则",
        "收口目标": "把日常可用交付版剩余项沉淀为使用说明、故障清单、税收接续替代、端口诊断与重载申请模板。",
        "使用说明": usage,
        "故障处理清单": troubleshooting,
        "税收业务接续替代包": tax_continuation,
        "端口诊断与重载申请模板": port_template,
        "日常巡检建议": [
            "每次自主施工阶段包完成后运行一键只读总回归。",
            "若一键总回归失败，先读取失败项，不直接重载服务。",
            "连续3轮总回归通过可作为日常可用交付版稳定证据。",
        ],
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "触发服务重载": False,
            "重载19310": False,
            "重载19302": False,
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
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }


def bullet(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def build_main_markdown(package: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 日常可用交付版收口包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 性质：{package['性质']}",
            f"- 收口目标：{package['收口目标']}",
            "",
            "## 包含内容",
            "",
            "- 日常使用说明",
            "- 故障处理清单",
            "- 税收业务接续替代包",
            "- 19310/19302端口诊断与重载申请模板",
            "- 日常巡检建议",
            "",
            "## 日常巡检建议",
            "",
            *bullet(package["日常巡检建议"]),
            "",
            "## 安全边界",
            "",
            "- 不写正式规则，不修改运行配置，不重载19310/19302。",
            "- 不真实发送企业微信，不触发n8n。",
            "- 不接券商、不交易，不登录税局、不接财税软件。",
            "- 不真实渲染或发布视频，不改总管面板和一键接续包。",
        ]
    )


def build_usage_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {item['场景']} | {item['输入样例']} | {item['预期体验']} | {item['边界']} |"
        for item in package["使用说明"]
    ]
    return "\n".join(["# 日常使用说明", "", "| 场景 | 输入样例 | 预期体验 | 边界 |", "| --- | --- | --- | --- |", *rows])


def build_troubleshooting_markdown(package: dict[str, Any]) -> str:
    rows = [
        f"| {item['问题']} | {item['先做']} | {item['不得做']} | {item['升级条件']} |"
        for item in package["故障处理清单"]
    ]
    return "\n".join(["# 故障处理清单", "", "| 问题 | 先做 | 不得做 | 升级条件 |", "| --- | --- | --- | --- |", *rows])


def build_tax_markdown(package: dict[str, Any]) -> str:
    tax = package["税收业务接续替代包"]
    return "\n".join(
        [
            "# 税收业务接续替代包",
            "",
            f"- 定位：{tax['定位']}",
            f"- 可用入口：{tax['可用入口']}",
            "",
            "## 当前已通过",
            "",
            *bullet(tax["当前已通过"]),
            "",
            "## 接续策略",
            "",
            *bullet(tax["接续策略"]),
            "",
            "## 硬边界",
            "",
            *bullet(tax["硬边界"]),
        ]
    )


def build_port_markdown(package: dict[str, Any]) -> str:
    port = package["端口诊断与重载申请模板"]
    return "\n".join(
        [
            "# 19310/19302端口诊断与重载申请模板",
            "",
            "## 诊断步骤",
            "",
            *bullet(port["诊断步骤"]),
            "",
            "## 重载申请字段",
            "",
            *bullet(port["重载申请字段"]),
            "",
            "## 模板正文",
            "",
            *bullet(port["模板正文"]),
        ]
    )


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_main_markdown(package))
    write_text(USER_GUIDE_MD, build_usage_markdown(package))
    write_text(TROUBLESHOOTING_MD, build_troubleshooting_markdown(package))
    write_text(TAX_CONTINUATION_MD, build_tax_markdown(package))
    write_text(PORT_TEMPLATE_MD, build_port_markdown(package))
    print(json.dumps({"名称": package["名称"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
