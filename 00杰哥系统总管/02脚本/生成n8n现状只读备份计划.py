"""
名称：生成n8n现状只读备份计划.py
作用：为第2层未激活导入前生成n8n现状只读备份计划和人工核对口径。
触发方式：python 生成n8n现状只读备份计划.py
依赖：Python 标准库；需已有系统状态巡检未激活导入准备包。
所属系统：00杰哥系统总管
安全边界：只生成本地备份计划；不执行导出、不调用n8n API、不读取凭据明文、不导入n8n、不启用Webhook。
创建/修改记录：2026-04-27 创建n8n现状只读备份计划脚本。
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
    prepare_path = root / "00杰哥系统总管" / "03数据" / "灰度接入" / "系统状态巡检未激活导入准备包_最新.json"
    prepare = load_json(prepare_path)
    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "第2层前置准备-n8n现状只读备份计划",
        "准备包来源": str(prepare_path),
        "目标工作流": prepare.get("目标工作流"),
        "备份范围": [
            "n8n当前全部工作流JSON",
            "n8n凭据清单元数据，不包含明文密钥",
            "n8n当前激活工作流列表",
            "n8n相关容器状态",
            "统一消息出口真实发送开关状态",
            "v3总体验收报告路径",
        ],
        "建议备份目录": "F:\\系统备份\\灰度接入备份_YYYYMMDD",
        "备份文件命名建议": [
            "n8n工作流导出_YYYYMMDD_HHMMSS.json",
            "n8n凭据清单_不含明文_YYYYMMDD_HHMMSS.json",
            "n8n激活状态清单_YYYYMMDD_HHMMSS.json",
            "v3验收报告路径_YYYYMMDD_HHMMSS.txt"
        ],
        "人工核对项": [
            "确认备份目录存在且可写",
            "确认不导出明文密钥",
            "确认系统状态巡检工作流导入后仍保持未激活",
            "确认Webhook保持关闭",
            "确认统一消息出口真实发送保持关闭",
        ],
        "禁止事项": [
            "不得自动执行备份命令",
            "不得调用n8n API",
            "不得读取或导出明文凭据",
            "不得导入n8n工作流",
            "不得启用Webhook",
        ],
        "是否执行备份": False,
        "是否调用n8nAPI": False,
        "是否读取明文凭据": False,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "n8n现状只读备份计划_最新.json"
    latest = output_dir / "n8n现状只读备份计划_最新.json"
    write_json(output, plan)
    write_json(latest, plan)
    print(json.dumps({"目标工作流": plan["目标工作流"], "备份范围数量": len(plan["备份范围"]), "输出": str(output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
