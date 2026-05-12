"""
名称：检查旧股票系统只读桥接.py
作用：只读检查股票研究系统对 D:\\杰哥智能体操作系统 的桥接边界，确认不接管、不修改、不触发旧系统。
触发方式：python 检查旧股票系统只读桥接.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取规则和目录状态；只向新股票研究系统日志目录写入报告；不写入旧系统、不停止旧服务。
创建/修改记录：2026-04-27 创建旧股票系统只读桥接检查脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "旧股票系统只读桥接规则.json"
    config = load_json(config_path)
    old_path = Path(config["旧系统路径"])
    new_stock_path = Path(config["新股票研究系统路径"])
    false_flags = {
        "是否接管旧系统": config.get("是否接管旧系统"),
        "是否停止旧服务": config.get("是否停止旧服务"),
        "是否修改旧系统文件": config.get("是否修改旧系统文件"),
        "是否迁移旧数据": config.get("是否迁移旧数据"),
        "是否删除旧文件": config.get("是否删除旧文件"),
        "是否触发旧工作流": config.get("是否触发旧工作流"),
        "是否接入真实股票交易": config.get("是否接入真实股票交易"),
    }
    old_reference_dirs = ["07_系统文档", "08_扩展应用", "06_运行状态"]
    reference_status = [{"目录": str(old_path / name), "存在": (old_path / name).exists()} for name in old_reference_dirs]
    old_exists = old_path.exists()
    paths_isolated = new_stock_path.exists() and old_path.resolve() != new_stock_path.resolve()
    dangerous_actions_off = all(value is False for value in false_flags.values())
    passed = (
        paths_isolated
        and config.get("桥接模式") == "read_only_reference"
        and dangerous_actions_off
    )
    report = {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "old-stock-readonly-bridge",
        "旧系统路径": str(old_path),
        "新股票研究系统路径": str(new_stock_path),
        "桥接模式": config.get("桥接模式"),
        "旧系统目录存在": old_exists,
        "旧系统缺席备案": not old_exists,
        "新股票系统目录存在": new_stock_path.exists(),
        "新旧路径隔离": paths_isolated,
        "只读参考目录": reference_status,
        "保护开关": false_flags,
        "是否写入旧系统": False,
        "是否停止旧服务": False,
        "是否触发旧工作流": False,
        "是否真实交易": False,
        "只读桥接通过": passed,
        "结论": (
            "旧股票系统目录缺席，股票研究系统保持只读参考配置且不接管旧系统"
            if passed and not old_exists
            else "股票研究系统只读参考旧系统，不接管旧系统"
            if passed
            else "股票研究系统只读桥接需复核"
        ),
    }
    output_dir = root / "04日志" / "旧系统桥接"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"old-stock-readonly-bridge-{timestamp}.json"
    latest = output_dir / "old-stock-readonly-bridge-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"只读桥接通过": passed, "输出": str(output)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
