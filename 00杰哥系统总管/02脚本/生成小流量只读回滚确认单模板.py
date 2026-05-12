"""
名称：生成小流量只读回滚确认单模板.py
作用：根据小流量只读回滚确认规则、执行前快照和执行后观测模板，生成回滚确认单模板。
触发方式：python 生成小流量只读回滚确认单模板.py
依赖：Python 标准库；小流量只读回滚确认规则.json；小流量只读执行前快照_最新.json；小流量只读执行后观测模板_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成回滚确认单模板；不删除文件；不停止服务；不重启服务；不联网；不写库；不外发；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读回滚确认单模板脚本。
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


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rules = load_json(manager / "01配置" / "小流量只读回滚确认规则.json")
    snapshot_path = manager / "03数据" / "小流量只读执行" / "小流量只读执行前快照_最新.json"
    observation_path = manager / "03数据" / "小流量只读执行" / "小流量只读执行后观测模板_最新.json"
    snapshot = load_json(snapshot_path) if snapshot_path.exists() else {}
    observation = load_json(observation_path) if observation_path.exists() else {}
    form = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行前快照": str(snapshot_path),
        "执行前快照汇总": snapshot.get("汇总", {}),
        "执行后观测模板": str(observation_path),
        "执行后观测状态": observation.get("默认状态", {}),
        "回滚触发条件": rules.get("回滚触发条件", []),
        "默认状态": rules.get("默认状态", {}),
        "回滚动作清单": [
            "保留所有输出文件，不自动删除",
            "标记本批次为停止",
            "生成异常复盘记录",
            "进入人工确认后再决定是否清理临时文件"
        ],
        "禁止动作": [
            "禁止自动删除文件",
            "禁止自动停止服务",
            "禁止自动重启服务",
            "禁止自动修改旧系统",
            "禁止自动外发消息"
        ],
        "当前结论": "回滚确认单模板已生成；未执行真实回滚动作。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "小流量只读回滚确认单模板_最新.json"
    latest = output_dir / "小流量只读回滚确认单模板_最新.json"
    write_json(output, form)
    write_json(latest, form)
    print(json.dumps({"触发条件数": len(form["回滚触发条件"]), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
