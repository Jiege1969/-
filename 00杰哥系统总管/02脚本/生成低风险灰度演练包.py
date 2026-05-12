"""
名称：生成低风险灰度演练包.py
作用：基于低风险灰度接入设计，生成第1层导入前演练测试负载、预期响应和回滚核对表。
触发方式：python 生成低风险灰度演练包.py
依赖：Python 标准库；需已有低风险灰度接入设计。
所属系统：00杰哥系统总管
安全边界：只生成本地演练包；不导入n8n、不启用Webhook、不触发真实工作流、不发送企业微信、不接入税收业务。
创建/修改记录：2026-04-27 创建低风险灰度演练包脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_design() -> Path:
    root = v3_root()
    latest = root / "00杰哥系统总管" / "03数据" / "灰度接入" / "低风险灰度接入设计_最新.json"
    if latest.exists():
        return latest
    script = root / "00杰哥系统总管" / "02脚本" / "生成低风险灰度接入设计.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def payload_for(item: dict[str, Any]) -> dict[str, Any]:
    name = item.get("工作流名", "")
    return {
        "工作流名": name,
        "Webhook路径": item.get("Webhook路径"),
        "测试负载": {
            "source": "jiege-v3-gray-rehearsal",
            "mode": "local-dry-run",
            "workflow": name,
            "message": f"本地演练请求：{name}",
            "require_real_send": False,
        },
        "预期响应": {
            "status": "dry_run_only",
            "workflow": name,
            "real_action": False,
            "message": "只返回本地演练结果，不触发真实动作",
        },
        "回滚核对表": [
            "确认工作流保持未激活",
            "确认Webhook未启用",
            "确认自动触发未启用",
            "确认统一消息出口未真实发送",
            "确认总体验收通过",
        ],
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
    }


def main() -> int:
    root = v3_root()
    design_path = ensure_design()
    design = load_json(design_path)
    candidates = design.get("候选工作流", [])
    rehearsal = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "第1层-导入前演练",
        "设计来源": str(design_path),
        "演练项": [payload_for(item) for item in candidates],
        "全局验收口径": [
            "测试负载只在本地文件中生成",
            "预期响应不代表真实n8n执行结果",
            "任何真实导入必须另行确认",
            "任一真实动作开关被打开则停止",
        ],
        "统计": {
            "演练项数量": len(candidates),
            "回滚核对项数量": sum(len(payload_for(item)["回滚核对表"]) for item in candidates),
        },
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
        "是否接入税收业务": False,
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "低风险灰度演练包_最新.json"
    latest = output_dir / "低风险灰度演练包_最新.json"
    write_json(output, rehearsal)
    write_json(latest, rehearsal)
    print(json.dumps({"演练项数量": len(rehearsal["演练项"]), "输出": str(output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
