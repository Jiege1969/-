# -*- coding: utf-8 -*-
"""
名称：生成股票助手首轮真实灰度测试消息样例.py
作用：生成股票助手首轮真实企业微信灰度测试的最多5条白名单消息样例、预期回复要点、验收标准和回滚建议。
触发方式：python 生成股票助手首轮真实灰度测试消息样例.py
依赖：Python标准库；股票助手首轮真实灰度测试消息样例规则.json；股票助手真实灰度执行手册草案_最新.json；股票助手真实灰度前只读环境快照_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手首轮真实灰度测试消息样例脚本。
标识：stock-assistant-first-real-gray-test-message-samples-generate
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
        "# 股票助手首轮真实灰度测试消息样例",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、样例结论",
        "",
        f"- 是否具备测试消息样例条件：{report['是否具备测试消息样例条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、前置判定",
        "",
    ]
    for key, value in report["前置判定"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、测试消息样例", ""])
    for item in report["测试消息"]:
        lines.extend([
            f"### {item['编号']} {item['类型']}",
            "",
            f"- 输入：{item['输入']}",
            f"- 预期路由：{item['预期路由']}",
            f"- 预期回复要点：{'；'.join(item['预期回复要点'])}",
            f"- 失败判定：{'；'.join(item['失败判定'])}",
            f"- 回滚建议：{item['回滚建议']}",
            "",
        ])
    lines.extend(["## 四、验收标准", ""])
    for item in report["验收标准"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手首轮真实灰度测试消息样例规则.json"
    paths = {
        "真实灰度执行手册草案": root / "03数据" / "55真实灰度执行手册草案" / "股票助手真实灰度执行手册草案_最新.json",
        "真实灰度前只读环境快照": root / "03数据" / "56真实灰度前只读环境快照" / "股票助手真实灰度前只读环境快照_最新.json",
        "首轮真实灰度测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
    }
    rule = load_json(rule_path)
    manual = load_json(paths["真实灰度执行手册草案"])
    snapshot = load_json(paths["真实灰度前只读环境快照"])
    test_record = load_json(paths["首轮真实灰度测试记录包"])
    actions = rule.get("安全边界", {})
    messages = rule.get("测试消息", [])
    judgement = {
        "执行手册草案通过": manual.get("是否具备执行手册草案条件") is True,
        "只读环境快照通过": snapshot.get("是否具备只读环境快照条件") is True,
        "首轮真实灰度测试仍未执行": test_record.get("当前测试状态") == "未执行",
        "测试消息不超过5条": len(messages) <= 5,
        "包含交易拦截样例": any(item.get("类型") == "交易意图拦截" for item in messages),
        "真实动作仍关闭": all(actions.values()),
    }
    passed = all(judgement.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "样例原则": rule.get("样例原则", []),
        "前置判定": judgement,
        "测试消息": messages,
        "验收标准": rule.get("验收标准", []),
        "引用材料": [{"名称": name, "路径": str(path)} for name, path in paths.items()],
        "是否具备测试消息样例条件": passed,
        "当前结论": "首轮真实灰度测试消息样例已具备，可作为人工放行后的测试清单；当前不发送企业微信、不触发n8n、不调用OpenClaw。" if passed else "首轮真实灰度测试消息样例前置材料不完整，不能作为测试清单。",
        "实际动作": actions,
    }
    output_dir = root / "03数据" / "57首轮真实灰度测试消息样例"
    latest_json = output_dir / "股票助手首轮真实灰度测试消息样例_最新.json"
    latest_md = output_dir / "股票助手首轮真实灰度测试消息样例_最新.md"
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备测试消息样例条件": passed, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
