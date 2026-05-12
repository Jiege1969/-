# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信真实灰度放行前总验收包.py
作用：汇总股票企业微信真实灰度前各安全门材料，生成提交人工确认前的总验收报告。
触发方式：python 生成股票企业微信真实灰度放行前总验收包.py
依赖：Python标准库；股票企业微信真实灰度放行前总验收规则.json；真实灰度最终闸口包、凭据隔离审计包、回滚预案包、白名单试运行包、人工确认单包、n8n导入前只读审计包、OpenClaw桥接沙盒验收包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度放行前总验收包脚本。
标识：stock-wework-real-gray-final-preflight-package-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信真实灰度放行前总验收包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备提交人工确认条件：{report['是否具备提交人工确认条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置材料验收",
        "",
    ]
    for item in report["前置材料验收"]:
        lines.append(f"- {item['名称']}：{item['通过']}｜{item['说明']}")
    lines.extend(["", "## 三、总验收原则", ""])
    for item in report["总验收原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、仍需人工确认", ""])
    for item in report["仍需人工确认"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票企业微信真实灰度放行前总验收规则.json"
    paths = {
        "真实灰度最终闸口包": root / "03数据" / "36真实灰度最终闸口" / "股票企业微信真实灰度最终闸口包_最新.json",
        "n8n导入前只读审计包": root / "03数据" / "38n8n导入前只读审计" / "股票n8n未激活导入前只读审计包_最新.json",
        "OpenClaw桥接沙盒验收包": root / "03数据" / "39OpenClaw桥接沙盒验收" / "OpenClaw股票桥接沙盒验收包_最新.json",
        "真实发送凭据隔离审计包": root / "03数据" / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json",
        "真实灰度回滚预案包": root / "03数据" / "41真实灰度回滚预案" / "股票企业微信真实灰度回滚预案包_最新.json",
        "真实灰度白名单试运行包": root / "03数据" / "42真实灰度白名单试运行" / "股票企业微信真实灰度白名单试运行包_最新.json",
        "真实灰度人工确认单包": root / "03数据" / "43真实灰度人工确认单" / "股票企业微信真实灰度人工确认单包_最新.json",
    }
    rule = load_json(rule_path)
    packages = {name: load_json(path) for name, path in paths.items()}
    checks = [
        {
            "名称": "真实灰度最终闸口包",
            "通过": paths["真实灰度最终闸口包"].exists(),
            "说明": str(paths["真实灰度最终闸口包"]),
        },
        {
            "名称": "n8n导入前只读审计包",
            "通过": paths["n8n导入前只读审计包"].exists(),
            "说明": str(paths["n8n导入前只读审计包"]),
        },
        {
            "名称": "OpenClaw桥接沙盒验收包",
            "通过": paths["OpenClaw桥接沙盒验收包"].exists(),
            "说明": str(paths["OpenClaw桥接沙盒验收包"]),
        },
        {
            "名称": "真实发送凭据隔离审计通过",
            "通过": packages["真实发送凭据隔离审计包"].get("是否通过凭据隔离审计") is True,
            "说明": str(paths["真实发送凭据隔离审计包"]),
        },
        {
            "名称": "真实灰度回滚预案具备",
            "通过": packages["真实灰度回滚预案包"].get("是否满足灰度前回滚预案要求") is True,
            "说明": str(paths["真实灰度回滚预案包"]),
        },
        {
            "名称": "真实灰度白名单试运行材料具备",
            "通过": packages["真实灰度白名单试运行包"].get("是否满足灰度试运行材料要求") is True,
            "说明": str(paths["真实灰度白名单试运行包"]),
        },
        {
            "名称": "真实灰度人工确认单具备",
            "通过": packages["真实灰度人工确认单包"].get("是否具备提交人工确认条件") is True,
            "说明": str(paths["真实灰度人工确认单包"]),
        },
        {
            "名称": "真实发送仍未放行",
            "通过": "未放行" in str(packages["真实发送凭据隔离审计包"].get("当前结论", "")),
            "说明": "总验收通过只代表可提交人工确认，不代表真实发送已经开启。",
        },
    ]
    passed = all(item["通过"] for item in checks)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "总验收原则": rule.get("总验收原则", []),
        "前置材料": {name: str(path) for name, path in paths.items()},
        "前置材料验收": checks,
        "仍需人工确认": [
            "确认企业微信真实接收人ID。",
            "确认n8n是否允许未激活导入。",
            "确认是否允许指定时间窗口启用n8n。",
            "确认OpenClaw真实桥接仍只做转发。",
            "确认首轮最多5条测试消息。",
            "确认异常时立即退回本地队列。",
        ],
        "是否具备提交人工确认条件": passed,
        "当前结论": "真实灰度放行前材料已形成闭环，可提交人工确认；当前未执行任何真实发送、导入、启用或重启动作。" if passed else "真实灰度放行前材料不完整，不能提交人工确认。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "44真实灰度放行前总验收"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票企业微信真实灰度放行前总验收包_{stamp}.json"
    latest_json = output_dir / "股票企业微信真实灰度放行前总验收包_最新.json"
    output_md = output_dir / f"股票企业微信真实灰度放行前总验收包_{stamp}.md"
    latest_md = output_dir / "股票企业微信真实灰度放行前总验收包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备提交人工确认条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
