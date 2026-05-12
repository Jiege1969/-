# -*- coding: utf-8 -*-
"""
名称：生成股票统一消息出口禁用态回复包.py
作用：把股票企业微信统一路由禁用态回复草稿包装为统一消息出口本地队列消息，并生成股票侧禁用态回复包。
触发方式：python 生成股票统一消息出口禁用态回复包.py
依赖：Python标准库；股票统一消息出口禁用态规则.json；00公共组件/02脚本/统一消息出口.py；企业微信股票消息统一路由禁用态_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写入股票模块03数据和00公共组件本地待发送队列/合并预览；不触发n8n；不调用OpenClaw；不真实发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建股票统一消息出口禁用态回复包脚本。
标识：stock-unified-message-outlet-disabled-package-generate
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


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


def load_message_outlet(common_script: Path) -> Any:
    spec = importlib.util.spec_from_file_location("jage_unified_message_outlet", common_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载统一消息出口脚本：{common_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def latest_route_payload(root: Path) -> dict[str, Any]:
    route_path = root / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.json"
    payload = load_json(route_path)
    if payload.get("reply_text"):
        payload["来源文件"] = str(route_path)
        return payload
    brief_path = root / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.json"
    brief = load_json(brief_path)
    brief["reply_text"] = brief.get("短回复", "")
    brief["need_clarification"] = False
    brief["real_send"] = False
    brief["trade"] = False
    brief["来源文件"] = str(brief_path)
    return brief


def build_markdown(package: dict[str, Any]) -> str:
    return f"""# 股票统一消息出口禁用态回复包

生成时间：{package['生成时间']}

## 一、结论

- 当前结论：{package['当前结论']}
- 真实发送：{package['real_send']}
- 触发n8n：{package['trigger_n8n']}
- 调用OpenClaw：{package['call_openclaw']}
- 交易：{package['trade']}

## 二、回复草稿

{package['content']}

## 三、统一消息出口

- 入队消息ID：{package['统一消息出口'].get('消息ID')}
- 合并消息数量：{package['合并预览'].get('消息数量')}
- 队列文件：{package['队列文件']}
- 合并预览：{package['合并预览文件']}

## 四、安全边界

- 不真实发送企业微信。
- 不触发n8n。
- 不调用OpenClaw。
- 不写正式库。
- 不写旧系统。
- 不调用券商接口。
- 不自动交易。
"""


def main() -> int:
    root = module_root()
    sys_root = system_root()
    rule_path = root / "01配置" / "股票统一消息出口禁用态规则.json"
    rule = load_json(rule_path)
    common_root = sys_root / "02杰哥扩展系统" / "00公共组件"
    outlet_script = common_root / "02脚本" / "统一消息出口.py"
    outlet = load_message_outlet(outlet_script)
    source = latest_route_payload(root)
    defaults = rule.get("默认字段", {})
    content = source.get("reply_text", "")
    if not content:
        raise RuntimeError("未找到可包装的股票回复草稿。")
    message = outlet.enqueue_message(
        source_system=defaults.get("source_system", "02杰哥扩展系统/01股票研究系统"),
        business_type=defaults.get("business_type", "股票研究"),
        priority=defaults.get("priority", "中"),
        title=defaults.get("title", "股票研究回复草稿"),
        content=content,
    )
    merged = outlet.build_merged_message(limit=20)
    latest_merged = common_root / "03数据" / "02合并消息" / "统一消息合并_最新.json"
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "来源文件": source.get("来源文件", ""),
        "content": content,
        "need_clarification": bool(source.get("need_clarification")),
        "real_send": False,
        "trigger_n8n": False,
        "call_openclaw": False,
        "write_official_db": False,
        "write_old_system": False,
        "trade": False,
        "统一消息出口脚本": str(outlet_script),
        "统一消息出口": message,
        "队列文件": str(outlet.today_queue_file()),
        "合并预览": merged,
        "合并预览文件": str(latest_merged),
        "当前结论": "股票回复草稿已进入统一消息出口本地队列和合并预览；真实发送仍关闭。",
    }
    output_dir = root / "03数据" / "34统一消息出口禁用态"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票统一消息出口禁用态回复包_{stamp}.json"
    latest_json = output_dir / "股票统一消息出口禁用态回复包_最新.json"
    output_md = output_dir / f"股票统一消息出口禁用态回复包_{stamp}.md"
    latest_md = output_dir / "股票统一消息出口禁用态回复包_最新.md"
    write_json(output_json, package)
    write_json(latest_json, package)
    markdown = build_markdown(package)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"入队消息ID": message.get("消息ID"), "真实发送": False, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
