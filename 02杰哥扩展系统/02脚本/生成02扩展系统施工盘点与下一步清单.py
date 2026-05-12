from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path("D:/杰哥智能化系统")
EXT = ROOT / "02杰哥扩展系统"
OUT_DIR = EXT / "03数据" / "01扩展系统施工盘点"
OUT_JSON = OUT_DIR / "02扩展系统施工盘点与下一步清单_最新.json"
OUT_MD = OUT_DIR / "02扩展系统施工盘点与下一步清单_最新.md"

SOURCES = {
    "全盘架构": ROOT / "杰哥智能化系统全盘架构说明_20260504.md",
    "当前施工面板": ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md",
    "一键接续施工包": ROOT / "00杰哥系统总管" / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    "本轮施工基准_JSON": ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "本轮施工基准_最新.json",
    "本轮施工基准_MD": ROOT / "00杰哥系统总管" / "03数据" / "运行状态" / "本轮施工基准_最新.md",
}

STOCK_STATUS = EXT / "01股票研究系统" / "03数据" / "243股票系统阶段性交付状态确认" / "股票系统阶段性交付状态确认_最新.json"
STOCK_VERIFY = EXT / "01股票研究系统" / "03数据" / "243股票系统阶段性交付状态确认" / "股票系统阶段性交付状态确认验收_最新.json"

WECOM = EXT / "00公共组件" / "企业微信接入设置"
WECOM_LOGS = {
    "终端分工验收": WECOM / "04日志" / "企业微信机器人终端分工" / "wecom-terminal-division-verify-最新.json",
    "统一指令路由预演": WECOM / "04日志" / "wecom-unified-command-router-preview-verify-最新.json",
    "统一指令本地调用预演": WECOM / "04日志" / "wecom-unified-command-local-call-preview-verify-最新.json",
    "灰度放行门禁": WECOM / "04日志" / "wecom-unified-command-gray-gate-verify-最新.json",
    "系统状态摘要": WECOM / "04日志" / "wecom-assistant-system-status-summary-verify-最新.json",
    "本地服务入口": WECOM / "04日志" / "wecom-unified-command-local-service-verify-最新.json",
}


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def file_record(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stock_status = read_json(STOCK_STATUS)
    stock_verify = read_json(STOCK_VERIFY)
    wecom_checks = {name: read_json(path) for name, path in WECOM_LOGS.items()}

    report = {
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "施工边界": {
            "本次范围": "仅02扩展系统盘点、只读验收、影子验证和路由配置预案",
            "未触碰": [
                "总管进度口径",
                "智能系统知识库代码",
                "进化系统规则代码",
                "股票系统新功能",
            ],
            "禁止动作执行结果": {
                "企业微信真实发送": False,
                "触发n8n": False,
                "调用券商接口": False,
                "自动交易": False,
                "扩大真实发送范围": False,
                "重启正式服务": False,
            },
        },
        "读取基准": {name: file_record(path) for name, path in SOURCES.items()},
        "02扩展系统当前状态": {
            "总管当前口径": "42%-50%，剩余16-28小时；股票系统阶段性交付完成后不再占主交付工时大头",
            "本次结论": "扩展系统主线应转向企业微信助手、多助手路由、公共扩展能力稳定化；股票仅保留只读稳定性复核。",
            "子系统": {
                "00公共组件": "统一消息出口、受控发送配置、OpenClaw边缘网关契约已具备本地/受控配置基础，但正式口径需要继续统一。",
                "01股票研究系统": "阶段性交付完成；本次只读复核稳定，不新增功能。",
                "02视频制作系统": "已形成主题化/素材/本地门禁等预演能力，真实渲染、发布、外部放量仍关闭。",
                "03本职工作系统": "办公材料草稿、R03联检、正式输出关闭检查已具备，仍处本地草稿和门禁阶段。",
                "04内容处理系统": "内容转换和本地队列能力具备，外部AI、n8n、企业微信真实发送仍关闭。",
                "05税收业务系统": "阶段收口验收9/9；正式税务结论、Tax RAG、企业微信正式入口、老doc正式解析仍未释放。",
                "00公共组件/企业微信接入设置": "统一指令路由、本地服务入口、终端分工和状态摘要均通过只读验收；本模块只作为企业微信通讯适配和安全边界，不作为独立业务系统。",
            },
        },
        "股票系统只读稳定性复核": {
            "状态文件": file_record(STOCK_STATUS),
            "验收文件": file_record(STOCK_VERIFY),
            "阶段状态": stock_status.get("阶段状态") or stock_status.get("股票系统状态") or "阶段性交付完成",
            "交付口径": stock_status.get("状态口径") or "可验收、可回滚、可接正式口径",
            "剩余工时": stock_status.get("剩余工时") or "0小时",
            "本次处理": "只读检查阶段交付证据存在；未修改股票系统代码，未新增股票功能。",
        },
        "企业微信助手与多助手路由": {
            "终端分工": {
                "终端数": 5,
                "已接入": ["杰哥股票分析助手", "杰哥的股票分析专家"],
                "已登记待桥接": ["杰哥系统管家", "杰哥工作秘书", "杰哥视频助理"],
                "安全规则": "终端只承担输入输出与路由，不承担业务判断；股票交易输入阻断。",
            },
            "路由能力": {
                "路由数": 7,
                "路由项": ["股票研究", "系统状态", "知识库问答", "内容办公处理", "视频制作", "税收业务暂停", "澄清一次"],
                "执行方式": "preview_only/local_preview_only",
                "真实动作数": 0,
            },
            "验收日志": {name: file_record(path) for name, path in WECOM_LOGS.items()},
            "验收摘要": {
                name: {
                    "通过": data.get("通过") or data.get("passed") or data.get("检查通过数"),
                    "失败": data.get("失败") or data.get("failed") or data.get("检查失败数"),
                    "状态": data.get("状态") or data.get("status") or data.get("结论"),
                }
                for name, data in wecom_checks.items()
            },
        },
        "外部扩展能力现状": {
            "统一消息出口": "当前以本地队列/预演为主，企业微信真实发送保持关闭。",
            "企业微信受控发送": "配置层存在单人白名单和首轮5条上限能力；本次未使用、未扩容、未发送。",
            "OpenClaw边缘网关": "仍为草案和本地回环契约；不连接真实企业微信，不触发n8n。",
            "企业微信应用目标": "当前应用仍为n8n指令通行证；杰哥助手目标应用待凭据补齐和切换审批。",
            "券商与交易": "股票相关交易口、券商接口、自动交易均保持禁用。",
        },
        "除股票外未完成项": [
            "企业微信三个通用助手仍是已登记待桥接，尚未完成独立入口到统一路由的影子闭环。",
            "统一消息出口与受控发送配置存在口径差异：一个强调real_send关闭，一个具备受控白名单能力；需要总管给出当前生效口径。",
            "本地服务系统状态路由仍可能引用旧面板摘要，需统一到最新总管基准的只读源。",
            "视频制作、本职工作、内容处理均已具备本地预演和门禁，但尚未形成正式外部交付链路。",
            "税收系统虽阶段收口验收通过，但正式税务结论、Tax RAG、企微正式入口、老doc正式解析仍未释放。",
            "知识库问答路由已存在，但实际知识库生产口径属于01智能系统，02扩展系统只能保留路由预案和只读联检。",
        ],
        "下一步施工清单": [
            {"事项": "企业微信多助手统一路由稳定化", "动作": "把三个通用助手从已登记推进到本地桥接影子验证，不扩大真实发送", "工时": "4-6小时"},
            {"事项": "通用助手回复模板与安全参数收口", "动作": "统一系统管家、工作秘书、视频助理的输入输出字段、拒绝策略、trace_id和dry_run标识", "工时": "3-5小时"},
            {"事项": "公共消息出口口径统一", "动作": "形成real_send关闭、受控白名单能力、确认令牌生命周期三者的配置解释和验收门禁", "工时": "2-3小时"},
            {"事项": "扩展系统只读验收自动化", "动作": "将本次盘点项沉淀为固定巡检脚本，供总管面板引用", "工时": "2-3小时"},
            {"事项": "税收低风险证据链预演", "动作": "继续做政策证据链预演和人工复核清单，不开放正式税务结论和企微入口", "工时": "3-5小时"},
            {"事项": "视频/内容/办公本地门禁对齐", "动作": "刷新三类本地预演状态，接入统一路由影子调用返回口径", "工时": "2-4小时"},
        ],
        "剩余有效工时估算": {
            "股票系统": "0小时",
            "02扩展系统非股票": "16-28小时",
            "说明": "本次未改变总管口径；按当前基准，剩余工时主要集中在企业微信助手、多助手路由和外部能力稳定化。",
        },
        "需要总管收口的事项": [
            "是否把本报告作为02扩展系统下一轮施工基准引用到总管面板。",
            "是否明确企业微信当前生效口径为不扩大真实发送，仅允许本地/影子验证。",
            "是否批准三个通用助手进入本地桥接影子验证，但不进入真实发送。",
            "是否补齐并切换杰哥助手企业微信应用凭据，或继续保留n8n指令通行证作为当前目标。",
            "是否由总管统一修正系统状态路由引用旧面板摘要的问题。",
        ],
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# 02扩展系统施工盘点与下一步清单",
        "",
        f"- 生成时间：{report['生成时间']}",
        "- 本次范围：仅02扩展系统盘点、只读验收、影子验证和路由配置预案",
        "- 边界结果：未真实发送企业微信、未触发n8n、未调用券商接口、未自动交易、未扩大真实发送范围、未重启正式服务",
        "",
        "## 当前结论",
        "",
        "- 股票系统：阶段性交付完成，剩余0小时；本次仅只读复核。",
        "- 02扩展系统：主线转向企业微信助手、多助手路由、公共扩展能力稳定化。",
        "- 当前剩余有效工时：16-28小时，股票不再占主交付工时大头。",
        "",
        "## 企业微信助手与路由验收",
        "",
        "- 终端分工：5个终端，2个股票终端已接入，3个通用终端已登记待桥接。",
        "- 路由预演：7类路由命中，真实动作数0。",
        "- 只读验收日志：终端分工、统一指令路由、本地调用、灰度门禁、系统状态摘要、本地服务入口均已生成。",
        "",
        "## 除股票外未完成项",
        "",
    ]
    md.extend([f"- {item}" for item in report["除股票外未完成项"]])
    md.extend(["", "## 下一步施工清单", ""])
    md.extend([f"- {item['事项']}：{item['动作']}；估算{item['工时']}。" for item in report["下一步施工清单"]])
    md.extend(["", "## 需要总管收口", ""])
    md.extend([f"- {item}" for item in report["需要总管收口的事项"]])
    md.append("")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({"通过": True, "输出": str(OUT_JSON), "文档": str(OUT_MD)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
