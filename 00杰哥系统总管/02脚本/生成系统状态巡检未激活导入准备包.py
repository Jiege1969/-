"""
名称：生成系统状态巡检未激活导入准备包.py
作用：基于低风险灰度演练结果，为“系统状态巡检”生成第2层未激活导入前准备包。
触发方式：python 生成系统状态巡检未激活导入准备包.py
依赖：Python 标准库；需已有低风险灰度演练结果汇总和n8n非税收导入演练清单。
所属系统：00杰哥系统总管
安全边界：只生成本地准备包；不导入n8n、不启用Webhook、不触发真实工作流、不发送企业微信、不接入税收业务。
创建/修改记录：2026-04-27 创建系统状态巡检未激活导入准备包脚本。
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


def ensure_summary() -> Path:
    root = v3_root()
    latest = root / "00杰哥系统总管" / "03数据" / "灰度接入" / "低风险灰度演练结果汇总_最新.json"
    if latest.exists():
        return latest
    script = root / "00杰哥系统总管" / "02脚本" / "生成低风险灰度演练结果汇总.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def find_workflow(items: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for item in items:
        if item.get("工作流名") == name:
            return item
    return {}


def main() -> int:
    root = v3_root()
    summary_path = ensure_summary()
    summary = load_json(summary_path)
    rehearsal = load_json(root / "01杰哥智能系统" / "03数据" / "工作流导入审查" / "n8n非税收导入演练清单_最新.json")
    result_item = find_workflow(summary.get("演练结果", []), "系统状态巡检")
    review_item = find_workflow(rehearsal.get("审查清单", []), "系统状态巡检")
    eligible = result_item.get("演练判断") == "通过" and result_item.get("真实动作") is False
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "第2层前置准备-未激活导入",
        "目标工作流": "系统状态巡检",
        "演练结果来源": str(summary_path),
        "草案文件": review_item.get("草案文件"),
        "Webhook路径": review_item.get("Webhook路径"),
        "是否具备进入第2层讨论资格": eligible,
        "导入前备份清单": [
            "导出n8n当前全部工作流JSON",
            "导出n8n凭据清单但不导出明文密钥",
            "记录当前n8n容器状态",
            "记录统一消息出口真实发送开关状态",
            "记录当前v3总体验收报告路径",
        ],
        "未激活导入约束": [
            "导入后工作流必须保持未激活",
            "Webhook必须保持关闭",
            "定时触发必须保持关闭",
            "不得写入统一消息出口正式队列",
            "不得连接企业微信真实发送",
        ],
        "导入后验收清单": [
            "重新运行低风险灰度接入设计验收",
            "重新运行n8n导入前审查验收",
            "重新运行统一消息出口验收",
            "重新运行v3总体验收",
            "确认工作流仍为未激活状态",
        ],
        "失败回滚清单": [
            "停用或删除本次导入的系统状态巡检工作流",
            "恢复导入前n8n工作流JSON",
            "确认Webhook未启用",
            "确认统一消息出口无正式发送记录",
            "生成失败经验卡片候选",
        ],
        "人工确认要求": [
            "第2层未激活导入必须由用户明确确认",
            "确认前不得输出真实导入命令",
            "确认前不得调用n8n API",
        ],
        "是否允许自动进入第2层": False,
        "是否输出真实导入命令": False,
        "是否调用n8nAPI": False,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
        "是否接入税收业务": False,
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "系统状态巡检未激活导入准备包_最新.json"
    latest = output_dir / "系统状态巡检未激活导入准备包_最新.json"
    write_json(output, package)
    write_json(latest, package)
    print(json.dumps({"目标工作流": package["目标工作流"], "具备讨论资格": eligible, "输出": str(output)}, ensure_ascii=True))
    return 0 if eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
