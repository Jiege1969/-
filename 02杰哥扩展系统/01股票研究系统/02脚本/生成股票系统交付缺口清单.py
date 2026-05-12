# -*- coding: utf-8 -*-
"""
名称：生成股票系统交付缺口清单.py
作用：汇总股票研究系统距离可交付使用仍需完成的缺口、风险边界和下一步低风险施工任务。
触发方式：python 生成股票系统交付缺口清单.py
依赖：Python标准库；进度回答标准.json；v3总体验收日志；股票助手刷新预案；股票企业微信n8n未激活导入预案。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地报告并生成缺口清单；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不调用OpenClaw；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票系统交付缺口清单脚本。
标识：stock-delivery-gap-list-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def latest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    files = list(root.glob(pattern))
    return max(files, key=lambda item: item.stat().st_mtime) if files else None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    done = "\n".join(f"- {item}" for item in report["已具备能力"])
    gaps = "\n".join(f"- {item['缺口']}：{item['处理方式']}（风险边界：{item['风险边界']}）" for item in report["交付缺口"])
    next_steps = "\n".join(f"- {item}" for item in report["下一步低风险施工"])
    blocked = "\n".join(f"- {item}" for item in report["必须停止等待确认的动作"])
    return f"""# 股票系统交付缺口清单

生成时间：{report['生成时间']}

当前结论：{report['当前结论']}

## 一、已具备能力

{done}

## 二、交付缺口

{gaps}

## 三、下一步低风险施工

{next_steps}

## 四、必须停止等待确认的动作

{blocked}
"""


def main() -> int:
    root = module_root()
    v3_root = system_root()
    manager = v3_root / "00杰哥系统总管"
    progress_rules = load_json(manager / "01配置" / "进度回答标准.json", {})
    acceptance = load_json(latest_file(manager / "04日志" / "acceptance", "v3-acceptance-最新.json"), {})
    refresh_plan = load_json(root / "03数据" / "22助手刷新预案" / "股票助手接口刷新预案_最新.json", {})
    inactive_plan = load_json(root / "03数据" / "30n8n未激活导入预案" / "股票企业微信n8n未激活导入预案_最新.json", {})
    stock_progress = next((item for item in progress_rules.get("重点子系统", []) if item.get("子系统") == "股票分析系统"), {})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前进度": stock_progress.get("当前进度", "66%-74%"),
        "可交付使用还需有效工作时间": stock_progress.get("可交付使用还需有效工作时间", "12-20小时"),
        "最新v3验收": acceptance.get("summary", {}),
        "当前结论": "股票系统研究、报告、语音容错、企业微信禁用态、n8n草案和灰度导入准备已较完整；真正交付还差服务刷新、未激活导入、真实灰度接入和稳定观测。",
        "已具备能力": [
            "19只重点关注股数据健康度优秀，技术指标成功19/19。",
            "单股即时研究报告、重点关注池报告索引、L5深度研究和日常使用包已可本地生成。",
            "企业微信文字、语音追问、语音确认学习、统一路由均有禁用态草稿。",
            "n8n路由契约、适配器禁用态、工作流草案、灰度导入许可令和未激活导入预案已完成。",
            "旧系统保持只读参考，不写入旧系统。",
        ],
        "交付缺口": [
            {
                "缺口": "本地股票助手运行进程未加载/data-health、/status-summary、/daily-package新接口",
                "处理方式": "需要刷新本地股票助手进程后重新验收",
                "风险边界": "属于服务重启边界，需停止说明原因后再执行"
            },
            {
                "缺口": "n8n工作流仍为草案，尚未导入未激活工作流",
                "处理方式": "人工确认后执行未激活导入，并保持active=false",
                "风险边界": "属于n8n导入边界，需停止说明原因"
            },
            {
                "缺口": "OpenClaw尚未真实转发企业微信消息到n8n",
                "处理方式": "后续先做OpenClaw沙盒转发或禁用态桥接验证",
                "风险边界": "调用OpenClaw和真实企业微信链路需停止确认"
            },
            {
                "缺口": "统一消息出口尚未真实发送企业微信回复",
                "处理方式": "先做发送前凭据隔离和沙盒验收",
                "风险边界": "真实发送企业微信必须停止确认"
            },
            {
                "缺口": "盘后批量样本池和2000只代表股尚未进入日常批处理",
                "处理方式": "先做样本池分层和资源预算，再做只读批处理计划",
                "风险边界": "真实大批量抓取需先做只读限流和数据源许可"
            }
        ],
        "下一步低风险施工": [
            "补股票样本池分层资源预算和盘后批处理禁用态计划。",
            "补OpenClaw股票消息桥接禁用态契约，不调用真实OpenClaw。",
            "补企业微信统一消息出口禁用态股票回复包，不真实发送。",
            "补股票系统交付验收清单，把本地可用、企业微信可用、n8n可用分开。"
        ],
        "必须停止等待确认的动作": [
            "刷新或重启本地股票助手进程。",
            "导入n8n工作流。",
            "启用Webhook或触发n8n。",
            "调用OpenClaw真实网关。",
            "真实发送企业微信。",
            "写正式库、写旧系统、调用券商接口、自动交易。"
        ],
        "引用": {
            "股票助手刷新预案": str(root / "03数据" / "22助手刷新预案" / "股票助手接口刷新预案_最新.md"),
            "n8n未激活导入预案": str(root / "03数据" / "30n8n未激活导入预案" / "股票企业微信n8n未激活导入预案_最新.md"),
        },
        "实际动作": {
            "调用n8nAPI": False,
            "导入n8n": False,
            "启用Webhook": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "重启服务": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "31交付缺口清单"
    log_dir = root / "04日志" / "交付缺口清单"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "股票系统交付缺口清单_最新.json"
    latest_json = output_dir / "股票系统交付缺口清单_最新.json"
    md_path = output_dir / "股票系统交付缺口清单_最新.md"
    latest_md = output_dir / "股票系统交付缺口清单_最新.md"
    log_path = log_dir / "stock-delivery-gap-list-generate-最新.json"
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, build_markdown(report))
    write_text(latest_md, build_markdown(report))
    write_json(log_path, report)
    print(json.dumps({"当前进度": report["当前进度"], "缺口数量": len(report["交付缺口"]), "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
