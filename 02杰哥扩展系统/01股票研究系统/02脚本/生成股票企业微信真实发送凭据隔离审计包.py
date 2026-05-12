# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实发送凭据隔离审计包.py
作用：检查股票回复进入企业微信真实发送前的统一消息出口配置、股票回复包安全字段和明文敏感信息风险。
触发方式：python 生成股票企业微信真实发送凭据隔离审计包.py
依赖：Python标准库；股票企业微信真实发送凭据隔离审计规则.json；统一消息出口配置.json；股票统一消息出口禁用态回复包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地回复包并写入股票模块03数据目录；不读取真实密钥内容；不调用企业微信接口；不真实发送企业微信；不触发n8n；不调用OpenClaw；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建股票企业微信真实发送凭据隔离审计包脚本。
标识：stock-wework-real-send-credential-isolation-audit-package-generate
"""

from __future__ import annotations

import json
import re
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


def scan_sensitive_text(text: str, keywords: list[str], allowed: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for keyword in keywords:
        if keyword in allowed:
            continue
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        if pattern.search(text):
            hits.append({"关键词": keyword, "说明": "产物中出现敏感关键词，需人工核实是否为说明性文本或真实凭据。"})
    return hits


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信真实发送凭据隔离审计包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否通过凭据隔离审计：{report['是否通过凭据隔离审计']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、统一消息出口配置审计",
        "",
    ]
    for key, value in report["统一消息出口配置审计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、股票回复包审计", ""])
    for key, value in report["股票回复包审计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、敏感信息扫描", ""])
    if report["敏感关键词命中"]:
        for hit in report["敏感关键词命中"]:
            lines.append(f"- {hit['关键词']}：{hit['说明']}")
    else:
        lines.append("- 未命中需阻断的敏感关键词。")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    rule_path = root / "01配置" / "股票企业微信真实发送凭据隔离审计规则.json"
    outlet_config_path = sys_root / "02杰哥扩展系统" / "00公共组件" / "01配置" / "统一消息出口配置.json"
    stock_package_path = root / "03数据" / "34统一消息出口禁用态" / "股票统一消息出口禁用态回复包_最新.json"
    rule = load_json(rule_path)
    outlet_config = load_json(outlet_config_path)
    stock_package = load_json(stock_package_path)

    strategy = outlet_config.get("出口策略", {})
    config_audit = {
        "唯一出口": strategy.get("唯一出口") is True,
        "当前发送模式": strategy.get("当前发送模式"),
        "是否允许真实发送": strategy.get("是否允许真实发送"),
        "安全边界说明": outlet_config.get("安全边界", ""),
        "禁止内容": outlet_config.get("禁止内容", []),
    }
    package_audit = {
        "real_send": stock_package.get("real_send"),
        "trigger_n8n": stock_package.get("trigger_n8n"),
        "call_openclaw": stock_package.get("call_openclaw"),
        "write_official_db": stock_package.get("write_official_db"),
        "write_old_system": stock_package.get("write_old_system"),
        "trade": stock_package.get("trade"),
        "统一消息出口脚本": stock_package.get("统一消息出口脚本", ""),
        "队列文件": stock_package.get("队列文件", ""),
        "合并预览文件": stock_package.get("合并预览文件", ""),
    }
    scan_text = json.dumps({
        "股票回复包安全字段": package_audit,
        "股票回复内容": stock_package.get("content", ""),
    }, ensure_ascii=False)
    hits = scan_sensitive_text(scan_text, rule.get("敏感关键词", []), rule.get("允许出现的说明性关键词", []))
    passed = (
        config_audit["唯一出口"] is True
        and config_audit["当前发送模式"] == "本地队列"
        and config_audit["是否允许真实发送"] is False
        and package_audit["real_send"] is False
        and package_audit["trigger_n8n"] is False
        and package_audit["call_openclaw"] is False
        and package_audit["write_official_db"] is False
        and package_audit["write_old_system"] is False
        and package_audit["trade"] is False
        and not hits
    )
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "统一消息出口配置": str(outlet_config_path),
        "股票回复包": str(stock_package_path),
        "审计原则": rule.get("审计原则", []),
        "说明性敏感词来源": {
            "统一消息出口禁止内容": outlet_config.get("禁止内容", []),
            "处理方式": "仅作为禁止项名单和风险边界说明，不作为凭据内容扫描。",
        },
        "统一消息出口配置审计": config_audit,
        "股票回复包审计": package_audit,
        "敏感关键词命中": hits,
        "是否通过凭据隔离审计": passed,
        "当前结论": "当前仍处于本地队列和禁用态回复包模式，未发现需阻断的明文凭据风险；真实发送仍未放行。" if passed else "凭据隔离审计存在风险，不能进入真实发送评审。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "40真实发送凭据隔离审计"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实发送凭据隔离审计包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实发送凭据隔离审计包_最新.json"
    output_md = output_dir / f"股票企业微信真实发送凭据隔离审计包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实发送凭据隔离审计包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否通过凭据隔离审计": passed, "命中数量": len(hits), "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
