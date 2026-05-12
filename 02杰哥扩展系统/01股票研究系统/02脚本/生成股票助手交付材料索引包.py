# -*- coding: utf-8 -*-
"""
名称：生成股票助手交付材料索引包.py
作用：汇总股票助手交付前的用户入口、核心材料、验收命令、未放行边界和下一步交付动作。
触发方式：python 生成股票助手交付材料索引包.py
依赖：Python标准库；股票助手交付材料索引规则.json；股票助手独立使用说明.md；股票助手交付前只读总状态面板_最新.json；股票研究日常使用包_最新.md；股票企业微信真实灰度放行前总验收包_最新.json；股票企业微信真实灰度未确认拦截包_最新.json；股票企业微信首轮真实灰度测试记录包_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付材料索引包脚本。
标识：stock-assistant-delivery-material-index-package-generate
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
        "# 股票助手交付材料索引包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 是否具备交付材料索引条件：{report['是否具备交付材料索引条件']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、用户入口",
        "",
    ]
    for item in report["用户入口"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.extend(["", "## 三、核心交付材料", ""])
    for item in report["核心交付材料"]:
        lines.append(f"- {item['名称']}：{item['存在']}｜`{item['路径']}`")
    lines.extend(["", "## 四、验收命令", ""])
    for command in report["验收命令"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## 五、未放行边界", ""])
    for item in report["未放行边界"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、下一步交付动作", ""])
    for item in report["下一步交付动作"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手交付材料索引规则.json"
    paths = {
        "股票助手独立使用说明": root / "07文档" / "股票助手独立使用说明.md",
        "股票助手交付前只读总状态面板": root / "03数据" / "48交付前只读总状态面板" / "股票助手交付前只读总状态面板_最新.json",
        "股票研究日常使用包": root / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.md",
        "股票企业微信真实灰度放行前总验收包": root / "03数据" / "44真实灰度放行前总验收" / "股票企业微信真实灰度放行前总验收包_最新.json",
        "股票企业微信真实灰度确认回执登记包": root / "03数据" / "45真实灰度确认回执登记" / "股票企业微信真实灰度确认回执登记包_最新.json",
        "股票企业微信真实灰度未确认拦截包": root / "03数据" / "46真实灰度未确认拦截" / "股票企业微信真实灰度未确认拦截包_最新.json",
        "股票企业微信首轮真实灰度测试记录包": root / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json",
    }
    rule = load_json(rule_path)
    dashboard = load_json(paths["股票助手交付前只读总状态面板"])
    guard = load_json(paths["股票企业微信真实灰度未确认拦截包"])
    test_record = load_json(paths["股票企业微信首轮真实灰度测试记录包"])
    materials = [
        {"名称": name, "路径": str(path), "存在": path.exists()}
        for name, path in paths.items()
    ]
    checks = {
        "核心交付材料均存在": all(item["存在"] for item in materials),
        "只读状态面板可继续低风险施工": dashboard.get("是否适合继续低风险施工") is True,
        "未确认拦截仍启用": guard.get("是否启用未确认拦截") is True,
        "首轮真实灰度测试未执行": test_record.get("当前测试状态") == "未执行",
    }
    validation_commands = [
        r'python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\验证股票助手交付前只读总状态面板.py"',
        r'python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\验证股票企业微信真实灰度未确认拦截包.py"',
        r'python "D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本\验证股票企业微信首轮真实灰度测试记录包.py"',
        r'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\杰哥智能化系统\00杰哥系统总管\02脚本\运行v3总体验收.ps1"',
    ]
    passed = all(checks.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "索引原则": rule.get("索引原则", []),
        "用户入口": [
            {"名称": "股票助手独立使用说明", "路径": str(paths["股票助手独立使用说明"])},
            {"名称": "股票助手交付前只读总状态面板", "路径": str(paths["股票助手交付前只读总状态面板"])},
        ],
        "核心交付材料": materials,
        "关键判定": checks,
        "验收命令": validation_commands,
        "未放行边界": rule.get("未放行边界", []),
        "下一步交付动作": [
            "提交交付材料索引和只读总状态面板供用户查看。",
            "用户明确确认后，才可进入n8n未激活导入、服务刷新或企业微信真实灰度测试等高风险边界。",
            "保持交易接口和自动下单接口关闭。",
        ],
        "是否具备交付材料索引条件": passed,
        "当前结论": "股票助手交付材料索引已形成，可作为交付前查看入口；当前仍未放行真实发送、n8n启用、OpenClaw真实桥接和交易接口。" if passed else "股票助手交付材料索引前置材料不完整，不能作为交付入口。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "49交付材料索引"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付材料索引包_{stamp}.json"
    latest_json = output_dir / "股票助手交付材料索引包_最新.json"
    output_md = output_dir / f"股票助手交付材料索引包_{stamp}.md"
    latest_md = output_dir / "股票助手交付材料索引包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备交付材料索引条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
