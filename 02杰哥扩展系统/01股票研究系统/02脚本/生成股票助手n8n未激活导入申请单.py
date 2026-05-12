# -*- coding: utf-8 -*-
"""
名称：生成股票助手n8n未激活导入申请单.py
作用：生成股票助手真实灰度第一项高风险动作n8n未激活导入的具体申请单，固化前置材料、停止条件、回滚方案和验收方法。
触发方式：python 生成股票助手n8n未激活导入申请单.py
依赖：Python标准库；股票助手n8n未激活导入申请单规则.json；股票助手真实灰度高风险操作申请单模板_最新.json；股票企业微信n8n未激活导入预案_最新.json；股票助手真实灰度前用户检查清单_最新.json；股票助手真实灰度放行前最终只读总包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手n8n未激活导入申请单脚本。
标识：stock-assistant-n8n-inactive-import-request-generate
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
        "# 股票助手n8n未激活导入申请单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、申请结论",
        "",
        f"- 是否具备n8n未激活导入申请条件：{report['是否具备n8n未激活导入申请条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置判定",
        "",
    ]
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、申请字段", ""])
    for key, value in report["申请字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 四、拟执行动作说明", ""])
    for item in report["拟执行动作说明"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、停止条件", ""])
    for item in report["停止条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、回滚方案", ""])
    for item in report["回滚方案"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 七、验收方法", ""])
    for item in report["验收方法"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 八、仍禁止事项", ""])
    for item in report["仍禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 九、引用材料", ""])
    for item in report["引用材料"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 十、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手n8n未激活导入申请单规则.json"
    paths = {
        "高风险操作申请单模板": root / "03数据" / "62真实灰度高风险操作申请单模板" / "股票助手真实灰度高风险操作申请单模板_最新.json",
        "n8n未激活导入预案": root / "03数据" / "30n8n未激活导入预案" / "股票企业微信n8n未激活导入预案_最新.json",
        "真实灰度前用户检查清单": root / "03数据" / "61真实灰度前用户检查清单" / "股票助手真实灰度前用户检查清单_最新.json",
        "真实灰度放行前最终只读总包": root / "03数据" / "60真实灰度放行前最终只读总包" / "股票助手真实灰度放行前最终只读总包_最新.json",
    }
    rule = load_json(rule_path)
    loaded = {name: load_json(path) for name, path in paths.items()}
    actions = rule.get("安全边界", {})
    request_fields = dict(rule.get("申请字段", {}))
    request_fields["申请时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    judgement = {
        "高风险操作申请单模板通过": loaded["高风险操作申请单模板"].get("是否具备高风险操作申请单模板条件") is True,
        "n8n未激活导入预案存在": bool(loaded["n8n未激活导入预案"]),
        "真实灰度前用户检查清单通过": loaded["真实灰度前用户检查清单"].get("是否具备用户检查清单条件") is True,
        "真实灰度放行前最终只读总包通过": loaded["真实灰度放行前最终只读总包"].get("是否具备放行前最终只读总包条件") is True,
        "停止条件完整": len(rule.get("停止条件", [])) >= 6,
        "回滚方案完整": len(rule.get("回滚方案", [])) >= 4,
        "验收方法完整": len(rule.get("验收方法", [])) >= 5,
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "申请原则": rule.get("申请原则", []),
        "前置判定": judgement,
        "申请字段": request_fields,
        "拟执行动作说明": rule.get("拟执行动作说明", []),
        "停止条件": rule.get("停止条件", []),
        "回滚方案": rule.get("回滚方案", []),
        "验收方法": rule.get("验收方法", []),
        "仍禁止事项": rule.get("仍禁止事项", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备n8n未激活导入申请条件": passed,
        "当前结论": "n8n未激活导入申请单已具备；当前仅生成申请材料，未导入n8n、未启用n8n、未触发真实业务。" if passed else "n8n未激活导入申请单前置材料不完整，不能作为申请依据。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "63n8n未激活导入申请单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n未激活导入申请单_{stamp}.json"
    latest_json = output_dir / "股票助手n8n未激活导入申请单_最新.json"
    output_md = output_dir / f"股票助手n8n未激活导入申请单_{stamp}.md"
    latest_md = output_dir / "股票助手n8n未激活导入申请单_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备n8n未激活导入申请条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
