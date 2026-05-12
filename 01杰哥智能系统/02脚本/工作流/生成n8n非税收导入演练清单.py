"""
名称：生成n8n非税收导入演练清单.py
作用：基于n8n非税收导入候选包，生成真实导入前的人工审查清单和导入演练步骤。
触发方式：python 生成n8n非税收导入演练清单.py
依赖：Python 标准库；需已有n8n非税收导入候选包。
所属系统：01杰哥智能系统
安全边界：只生成本地演练清单；不调用n8n API、不导入工作流、不启用Webhook、不触发真实工作流。
创建/修改记录：2026-04-27 创建n8n非税收导入演练清单脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def review_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "03数据" / "工作流导入审查"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_candidate_package() -> Path:
    latest = review_dir() / "n8n非税收导入候选包_最新.json"
    if latest.exists():
        return latest
    script = Path(__file__).resolve().parent / "生成n8n非税收导入候选包.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def review_item(index: int, workflow: dict[str, Any]) -> dict[str, Any]:
    name = workflow.get("工作流名", "")
    return {
        "序号": index,
        "工作流名": name,
        "归属系统": workflow.get("归属系统"),
        "草案文件": workflow.get("草案文件"),
        "Webhook路径": workflow.get("Webhook路径"),
        "审查状态": "待人工审查",
        "是否允许导入": False,
        "是否允许启用Webhook": False,
        "是否允许真实触发": False,
        "导入前确认项": [
            "草案文件存在且可读",
            "Webhook保持关闭",
            "自动触发保持关闭",
            "不包含税收业务",
            "不包含真实凭据或生产连接串",
            "统一消息出口真实发送保持关闭",
            "回滚方案已确认",
        ],
        "演练验证项": [
            f"导入后保持 {name} 为未激活状态",
            "使用本地测试负载验证节点连线",
            "检查n8n执行日志无真实外发",
            "检查统一消息出口未产生正式发送记录",
        ],
        "失败回滚动作": [
            "立即禁用对应工作流",
            "删除测试Webhook路径",
            "恢复导入前工作流导出文件",
            "重新运行v3总体验收",
        ],
    }


def build_checklist() -> dict[str, Any]:
    package_path = ensure_candidate_package()
    package = load_json(package_path)
    candidates = package.get("候选工作流", [])
    items = [review_item(index, workflow) for index, workflow in enumerate(candidates, start=1)]
    checklist = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "候选包来源": str(package_path),
        "阶段": "基础可用版-真实导入前演练",
        "审查清单": items,
        "演练顺序": [
            "导出当前n8n工作流和凭据清单，不导出明文密钥",
            "逐个导入候选工作流草案到测试环境或保持未激活状态",
            "确认Webhook和自动触发均未启用",
            "使用本地测试负载做节点连线验证",
            "检查n8n日志、统一消息出口日志和总体验收结果",
            "通过后等待用户明确确认，再进入真实启用阶段",
        ],
        "阻断条件": [
            "出现税收业务工作流",
            "出现真实凭据或生产连接串",
            "Webhook被启用",
            "自动触发被启用",
            "统一消息出口真实发送被打开",
            "任一验收失败",
        ],
        "统计": {
            "候选数量": len(items),
            "待人工审查数量": sum(1 for item in items if item["审查状态"] == "待人工审查"),
        },
        "是否执行导入": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否包含税收业务": any("税收" in item.get("工作流名", "") for item in items),
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = review_dir() / f"n8n非税收导入演练清单_{timestamp}.json"
    latest = review_dir() / "n8n非税收导入演练清单_最新.json"
    text = json.dumps(checklist, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"review_count": len(items), "output": str(output)}, ensure_ascii=True))
    return checklist


def main() -> int:
    build_checklist()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
