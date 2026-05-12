"""
名称：生成企业微信接入检查清单.py
作用：读取企业微信助手配置、凭据隔离规则、只读测试规则和回滚方案，生成真实接入前检查清单。
触发方式：python 生成企业微信接入检查清单.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只读取本模块配置，只写入本模块接入检查数据；不读取真实凭据、不连接企业微信、不触发n8n。
创建/修改记录：2026-04-27 创建企业微信接入检查清单脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_checklist() -> dict[str, Any]:
    root = module_root()
    config = load_json(root / "01配置" / "企业微信助手配置.json")
    credential_rules = load_json(root / "01配置" / "企业微信凭据隔离规则.json")
    readonly_rules = load_json(root / "01配置" / "企业微信只读接入测试规则.json")
    rollback = load_json(root / "01配置" / "企业微信回滚方案.json")
    output_dir = root / "03数据" / "01接入检查"
    output_dir.mkdir(parents=True, exist_ok=True)

    switches = config.get("接入开关", {})
    checklist = [
        {
            "检查项": "真实凭据读取关闭",
            "是否通过": switches.get("允许读取真实凭据") is False,
            "依据": "第一阶段只允许占位符和环境变量名称",
        },
        {
            "检查项": "企业微信连接关闭",
            "是否通过": switches.get("允许连接企业微信") is False,
            "依据": "尚未进入真实接入",
        },
        {
            "检查项": "企业微信发送关闭",
            "是否通过": switches.get("允许发送企业微信") is False,
            "依据": "主动推送只能经统一消息出口，且当前真实发送关闭",
        },
        {
            "检查项": "n8n真实触发关闭",
            "是否通过": switches.get("允许触发n8n真实工作流") is False,
            "依据": "当前只做本地回环预演",
        },
        {
            "检查项": "凭据环境变量占位完整",
            "是否通过": len(credential_rules.get("环境变量占位", {})) >= 5,
            "依据": list(credential_rules.get("环境变量占位", {}).keys()),
        },
        {
            "检查项": "只读测试规则存在",
            "是否通过": bool(readonly_rules.get("预演要求")),
            "依据": readonly_rules.get("测试模式"),
        },
        {
            "检查项": "回滚动作清单存在",
            "是否通过": len(rollback.get("回滚动作清单", [])) >= 3,
            "依据": rollback.get("回滚动作清单", []),
        },
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": config.get("阶段"),
        "检查清单": checklist,
        "汇总": {
            "检查项数量": len(checklist),
            "通过数量": sum(1 for item in checklist if item["是否通过"]),
            "失败数量": sum(1 for item in checklist if not item["是否通过"]),
        },
        "是否允许真实接入": False,
        "安全说明": "本清单通过只表示企业微信助手具备进入本地回环预演的条件，不表示允许真实连接企业微信。",
    }
    latest = output_dir / "企业微信接入检查清单_最新.json"
    output = latest
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"passed": report["汇总"]["通过数量"], "failed": report["汇总"]["失败数量"], "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_checklist()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
