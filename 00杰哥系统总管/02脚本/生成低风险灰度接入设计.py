"""
名称：生成低风险灰度接入设计.py
作用：基于基础可用版完成判定和n8n非税收导入演练清单，生成低风险灰度接入设计。
触发方式：python 生成低风险灰度接入设计.py
依赖：Python 标准库；需已有基础可用版完成判定和n8n非税收导入演练清单。
所属系统：00杰哥系统总管
安全边界：只生成灰度设计文件；不导入n8n、不启用Webhook、不触发真实工作流、不发送企业微信、不接入税收业务。
创建/修改记录：2026-04-27 创建低风险灰度接入设计脚本。
"""

from __future__ import annotations

import json
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


def candidate_item(index: int, item: dict[str, Any], allowed_order: list[str]) -> dict[str, Any]:
    name = item.get("工作流名", "")
    return {
        "序号": index,
        "工作流名": name,
        "归属系统": item.get("归属系统"),
        "建议顺序": allowed_order.index(name) + 1 if name in allowed_order else 99,
        "当前状态": "待讨论",
        "当前允许层级": "第0层-只读设计",
        "草案文件": item.get("草案文件"),
        "Webhook路径": item.get("Webhook路径"),
        "准入条件": [
            "基础可用版完成判定通过",
            "总体验收通过",
            "草案文件可读",
            "Webhook保持关闭",
            "自动触发保持关闭",
            "回滚动作可执行",
            "不包含税收业务",
        ],
        "退出条件": [
            "任一验收失败",
            "出现真实凭据",
            "出现真实外发",
            "出现税收业务接入",
            "用户要求暂停",
        ],
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
    }


def main() -> int:
    root = v3_root()
    rules = load_json(root / "00杰哥系统总管" / "01配置" / "低风险灰度接入规则.json")
    stage = load_json(root / "00杰哥系统总管" / "03数据" / "阶段判定" / "基础可用版完成判定_最新.json")
    rehearsal = load_json(root / "01杰哥智能系统" / "03数据" / "工作流导入审查" / "n8n非税收导入演练清单_最新.json")
    allowed_order = rules.get("候选顺序", [])
    candidates = sorted(
        [candidate_item(index, item, allowed_order) for index, item in enumerate(rehearsal.get("审查清单", []), start=1)],
        key=lambda item: item["建议顺序"],
    )
    design = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "真实接入前低风险灰度设计",
        "基础可用版判定": stage.get("完成判定"),
        "总体进度估算百分比": stage.get("总体进度估算百分比"),
        "候选工作流": candidates,
        "分层策略": rules.get("分层策略", []),
        "当前开关": rules.get("当前开关", {}),
        "全局阻断条件": [
            "总体验收失败",
            "发现税收业务接入",
            "发现真实凭据写入配置或脚本",
            "发现Webhook或自动触发被启用",
            "发现统一消息出口真实发送被打开",
        ],
        "当前结论": "只允许进入真实接入前讨论和灰度设计，不允许执行真实接入。",
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
        "是否接入税收业务": False,
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "低风险灰度接入设计_最新.json"
    latest = output_dir / "低风险灰度接入设计_最新.json"
    write_json(output, design)
    write_json(latest, design)
    print(json.dumps({"候选数量": len(candidates), "输出": str(output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
