from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path("D:/杰哥智能化系统")
EXT = ROOT / "02杰哥扩展系统"
WECOM = EXT / "00公共组件" / "企业微信接入设置"
CONFIG = WECOM / "01配置" / "企业微信多助手统一路由影子预案规则.json"
TERMINALS = WECOM / "01配置" / "企业微信机器人终端分工总表.json"
ROUTER = WECOM / "03数据" / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"
LOCAL_CALL = WECOM / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"
STATUS = WECOM / "03数据" / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json"
STOCK_STATUS = EXT / "01股票研究系统" / "03数据" / "243股票系统阶段性交付状态确认" / "股票系统阶段性交付状态确认_最新.json"
KNOWLEDGE_BOX = EXT / "07知识库系统" / "08可追溯问答框" / "03数据" / "01交付包" / "知识库可追溯问答框交付包_最新.json"
EXT_INVENTORY = EXT / "03数据" / "01扩展系统施工盘点" / "02扩展系统施工盘点与下一步清单_最新.json"
MESSAGE_OUTLET = EXT / "00公共组件" / "01配置" / "统一消息出口配置.json"
OUT_DIR = WECOM / "03数据" / "12多助手统一路由影子预案"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None,
    }


def first_local_call(route: str, local_call: dict[str, Any]) -> dict[str, Any]:
    for item in local_call.get("调用结果", []):
        if item.get("路由") == route:
            return item
    return {}


def main() -> int:
    config = load_json(CONFIG)
    terminals = load_json(TERMINALS)
    router = load_json(ROUTER)
    local_call = load_json(LOCAL_CALL)
    status = load_json(STATUS)
    stock = load_json(STOCK_STATUS)
    knowledge_box = load_json(KNOWLEDGE_BOX)
    inventory = load_json(EXT_INVENTORY)
    message_outlet = load_json(MESSAGE_OUTLET)
    safety = config.get("统一路由安全参数", {})

    terminal_rows = terminals.get("终端列表", [])
    terminal_status = {item.get("名称"): item.get("启用状态") for item in terminal_rows}
    shadow_samples: list[dict[str, Any]] = []

    for terminal in config.get("终端影子映射", []):
        for route in terminal.get("影子路由", []):
            call = first_local_call(route, local_call)
            shadow_samples.append({
                "助手": terminal.get("助手"),
                "当前登记状态": terminal_status.get(terminal.get("助手"), terminal.get("当前状态")),
                "影子路由": route,
                "本轮动作": terminal.get("本轮动作"),
                "样例输入": terminal.get("样例输入", []),
                "路由层状态": call.get("调用状态") or "route_plan_only",
                "回复预演": call.get("回复预演", "未生成本地调用回复，仅保留路由预案。"),
                "来源": call.get("来源", "影子预案规则"),
                "dry_run": safety.get("dry_run") is True,
                "shadow": safety.get("shadow") is True,
                "local_preview_only": safety.get("local_preview_only") is True,
                "真实发送企业微信": False,
                "扩大真实发送范围": False,
                "触发Webhook": False,
                "触发n8n": False,
                "写正式库": False,
                "写旧系统": False,
                "调用券商接口": False,
                "自动交易": False,
                "真实动作": False,
            })

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-multi-assistant-unified-route-shadow-plan",
        "所属系统": "02杰哥扩展系统/00公共组件/企业微信接入设置",
        "施工范围": "企业微信多助手统一路由影子预案；不正式放量。",
        "读取来源": {
            "规则": file_record(CONFIG),
            "终端分工": file_record(TERMINALS),
            "统一路由预演": file_record(ROUTER),
            "本地调用预演": file_record(LOCAL_CALL),
            "企业微信接入状态": file_record(STATUS),
            "股票阶段状态": file_record(STOCK_STATUS),
            "知识库可追溯问答框": file_record(KNOWLEDGE_BOX),
            "扩展系统盘点": file_record(EXT_INVENTORY),
            "统一消息出口配置": file_record(MESSAGE_OUTLET),
        },
        "当前状态盘点": {
            "02扩展系统": inventory.get("02扩展系统当前状态", {}),
            "股票系统": {
                "当前状态": stock.get("当前状态"),
                "状态口径": stock.get("状态口径"),
                "剩余工时": "0小时",
                "本轮处理": "只读复核，不新增股票功能。",
            },
            "企业微信接入设置": {
                "终端数量": len(terminal_rows),
                "已接入终端": [name for name, value in terminal_status.items() if "已接入" in str(value)],
                "未接入终端": [name for name, value in terminal_status.items() if "已接入" not in str(value)],
                "状态摘要": status.get("汇总", {}),
            },
            "外部扩展能力": {
                "统一消息出口": {
                    "状态": message_outlet.get("状态"),
                    "当前发送模式": message_outlet.get("出口策略", {}).get("当前发送模式"),
                    "是否允许真实发送": message_outlet.get("出口策略", {}).get("是否允许真实发送"),
                },
                "知识库可追溯问答框": {
                    "状态": knowledge_box.get("汇总", {}).get("状态"),
                    "问题数量": knowledge_box.get("汇总", {}).get("问题数量"),
                    "证据卡数量": knowledge_box.get("汇总", {}).get("证据卡数量"),
                },
            },
        },
        "影子预案": {
            "执行模式": config.get("执行模式"),
            "终端影子映射": config.get("终端影子映射", []),
            "样例": shadow_samples,
            "准入门槛": config.get("准入门槛", []),
            "回滚方式": config.get("回滚方式", []),
        },
        "自然交流基础体验要求": {
            "定位": "企业微信机器人是用户日常自然入口；用户只负责提出需求，系统负责识别、转交、回答和留痕。",
            "用户体验": [
                "用户不需要记脚本路径、端口、数据产物或任务对话框。",
                "用户按直觉找相关机器人提问即可。",
                "机器人应识别问题类型，并转到正确业务系统或明确提示正确机器人。",
                "回答应围绕用户当下要了解的信息，不把内部施工细节当成主要内容。",
                "跨业务问题允许转交，但不得让用户自己判断发给谁。",
                "用户反馈应进入对应业务日志和进化候选，而不是只停留在一次回答里。",
            ],
            "机器人分工": [
                {"机器人": "杰哥系统管家", "职责": "回答总进度、服务状态、红线状态和跨系统转交建议。", "边界": "不直接回答股票个股分析，不绕过总管确认重载服务。"},
                {"机器人": "杰哥工作秘书", "职责": "承接办公、内容处理、税收待复核草案和日常工作类问题。", "边界": "不生成正式税务结论，不登录税局，不接财税软件。"},
                {"机器人": "杰哥视频助理", "职责": "处理视频想法、脚本、分镜、人工复核、渲染预检和发布门禁。", "边界": "不自动真实渲染，不自动发布；系统状态问题转交系统管家。"},
                {"机器人": "杰哥私人股票分析顾问", "职责": "统一承接股票推荐、市场方向和个股图文报告入口。", "边界": "不接券商，不交易，不输出买卖指令，不群发。"},
                {"机器人": "杰哥的股票分析专家", "职责": "回答市场总览、行业方向、研究价值、夜间规律和晨报候选。", "边界": "不替用户下单，不把研究价值写成交易建议，不绕过晨报灰度闸口。"},
            ],
        },
        "未完成项": [
            "杰哥系统管家、杰哥工作秘书、杰哥视频助理已登记公网回调并可走本机统一路由预演/查询；真实发送、n8n、自动业务执行和业务最终判断仍未放开。",
            "统一消息出口当前为本地队列模式，真实发送仍不扩大；受控发送能力与当前禁用态口径需总管统一解释。",
            "系统状态路由本地调用仍引用旧日常可用版总览摘要，需要总管统一最新只读源。",
            "知识库问答已有02扩展侧可追溯问答框，但正式知识库覆盖和写库仍属于01智能系统后续工作。",
            "视频、办公、内容处理具备本地预演，尚未形成正式外部交付链路。",
            "税收业务已进入政策证据底座和企业微信dry-run待复核入口阶段，正式税务结论、真实发送、Tax RAG和办税执行仍未释放。",
        ],
        "剩余有效工时估算": {
            "股票系统": "0小时",
            "02扩展系统非股票": "12-22小时",
            "拆分": [
                {"事项": "三个通用助手本地桥接影子验证", "工时": "3-5小时"},
                {"事项": "多助手回复模板、trace_id、dry_run字段统一", "工时": "2-4小时"},
                {"事项": "统一消息出口与受控发送口径收口", "工时": "2-3小时"},
                {"事项": "知识库可追溯问答框接入工作秘书本地详情入口", "工时": "2-4小时"},
                {"事项": "视频/办公/内容处理本地预演统一返回格式", "工时": "2-4小时"},
                {"事项": "税收待复核分析路由与未来灰度门禁说明收口", "工时": "1-2小时"},
            ],
            "说明": "本估算仅为02扩展下一轮非股票施工口径；总管进度和全盘工时仍由00总管统一回收重算。",
        },
        "安全边界": {
            "企业微信真实发送": False,
            "扩大真实发送范围": False,
            "触发Webhook": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "继续给股票系统加新功能": False,
            "修改总管进度口径": False,
            "修改智能系统知识库代码": False,
            "修改进化系统规则代码": False,
            "重启正式服务": False,
        },
        "需要总管收口": [
            "是否认可02扩展系统非股票剩余工时从16-28小时细化为12-22小时，最终是否下调由总管决定。",
            "是否认可三个通用助手保持本机统一路由预演/查询口径，真实发送和正式放量继续关闭。",
            "是否统一系统状态路由的数据源，避免本地调用继续引用旧日常可用版总览摘要。",
            "是否明确统一消息出口与受控发送配置的当前生效口径：本轮只允许本地/影子，不扩大真实发送。",
            "是否把知识库可追溯问答框作为工作秘书知识库问答的本地详情入口。",
        ],
    }

    latest_json = OUT_DIR / "企业微信多助手统一路由影子预案_最新.json"
    latest_md = OUT_DIR / "企业微信多助手统一路由影子预案_最新.md"
    write_json(latest_json, report)

    lines = [
        "# 企业微信多助手统一路由影子预案",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 执行模式：{report['影子预案']['执行模式']}",
        "- 边界：不真实发送、不触发 n8n、不调用券商、不自动交易、不扩大真实发送范围。",
        "",
        "## 当前状态",
        "",
        f"- 股票系统：{stock.get('当前状态')}；剩余 0 小时；本轮只读复核。",
        f"- 企业微信终端：{len(terminal_rows)} 个；已接入 {len(report['当前状态盘点']['企业微信接入设置']['已接入终端'])} 个，未接入 {len(report['当前状态盘点']['企业微信接入设置']['未接入终端'])} 个。",
        f"- 统一路由：{router.get('汇总', {}).get('状态')}；样例 {router.get('汇总', {}).get('样例数量')}；真实动作 {router.get('汇总', {}).get('真实动作数量')}。",
        f"- 本地调用：{local_call.get('汇总', {}).get('状态')}；成功 {local_call.get('汇总', {}).get('调用成功数量')}；真实动作 {local_call.get('汇总', {}).get('真实动作数量')}。",
        "",
        "## 影子映射",
        "",
    ]
    for item in report["影子预案"]["终端影子映射"]:
        lines.append(f"- {item['助手']}：{', '.join(item['影子路由'])}；{item['本轮动作']}。")
    lines.extend(["", "## 自然交流基础体验", ""])
    lines.append(f"- {report['自然交流基础体验要求']['定位']}")
    for item in report["自然交流基础体验要求"]["用户体验"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 机器人自然分工", ""])
    for item in report["自然交流基础体验要求"]["机器人分工"]:
        lines.append(f"- {item['机器人']}：{item['职责']}边界：{item['边界']}")
    lines.extend(["", "## 未完成项", ""])
    for item in report["未完成项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 剩余有效工时", ""])
    lines.append(f"- 股票系统：{report['剩余有效工时估算']['股票系统']}")
    lines.append(f"- 02扩展系统非股票：{report['剩余有效工时估算']['02扩展系统非股票']}")
    lines.extend(["", "## 需要总管收口", ""])
    for item in report["需要总管收口"]:
        lines.append(f"- {item}")
    lines.append("")
    write_text(latest_md, "\n".join(lines))

    print(json.dumps({"状态": "shadow_plan_ready", "样例数量": len(shadow_samples), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

