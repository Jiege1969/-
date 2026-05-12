"""
名称：生成低风险灰度演练结果汇总.py
作用：汇总低风险灰度演练包，生成第1层导入前演练结果和进入第2层前的讨论材料。
触发方式：python 生成低风险灰度演练结果汇总.py
依赖：Python 标准库；需已有低风险灰度演练包。
所属系统：00杰哥系统总管
安全边界：只生成本地汇总报告；不导入n8n、不启用Webhook、不触发真实工作流、不发送企业微信、不接入税收业务。
创建/修改记录：2026-04-27 创建低风险灰度演练结果汇总脚本。
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


def ensure_rehearsal() -> Path:
    root = v3_root()
    latest = root / "00杰哥系统总管" / "03数据" / "灰度接入" / "低风险灰度演练包_最新.json"
    if latest.exists():
        return latest
    script = root / "00杰哥系统总管" / "02脚本" / "生成低风险灰度演练包.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def evaluate_item(item: dict[str, Any]) -> dict[str, Any]:
    payload = item.get("测试负载", {})
    expected = item.get("预期响应", {})
    rollback_items = item.get("回滚核对表", [])
    passed = (
        payload.get("mode") == "local-dry-run"
        and payload.get("require_real_send") is False
        and expected.get("real_action") is False
        and len(rollback_items) >= 5
        and item.get("是否导入n8n") is False
        and item.get("是否启用Webhook") is False
        and item.get("是否触发真实工作流") is False
    )
    return {
        "工作流名": item.get("工作流名"),
        "演练判断": "通过" if passed else "失败",
        "测试模式": payload.get("mode"),
        "真实动作": expected.get("real_action"),
        "回滚核对项数量": len(rollback_items),
        "建议": "可进入第2层前讨论" if passed else "阻断，需修正演练包",
    }


def main() -> int:
    root = v3_root()
    rehearsal_path = ensure_rehearsal()
    rehearsal = load_json(rehearsal_path)
    results = [evaluate_item(item) for item in rehearsal.get("演练项", [])]
    failed = [item for item in results if item["演练判断"] != "通过"]
    summary = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "第1层-导入前演练结果汇总",
        "演练包来源": str(rehearsal_path),
        "演练结果": results,
        "汇总": {
            "演练项数量": len(results),
            "通过数量": len(results) - len(failed),
            "失败数量": len(failed),
        },
        "第2层前讨论问题": [
            "是否先导入系统状态巡检且保持未激活",
            "是否仍保持知识库问答增强、办公材料生成、视频素材处理为候选等待",
            "是否需要先导出n8n现有工作流和凭据清单",
            "是否确认企业微信真实发送继续关闭",
        ],
        "进入第2层条件": [
            "用户明确确认",
            "总体验收通过",
            "n8n导入前审查通过",
            "统一消息出口真实发送关闭",
            "回滚核对表已确认",
        ],
        "是否允许自动进入第2层": False,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否触发真实工作流": False,
        "是否发送企业微信": False,
        "是否接入税收业务": False,
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "灰度接入"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "低风险灰度演练结果汇总_最新.json"
    latest = output_dir / "低风险灰度演练结果汇总_最新.json"
    write_json(output, summary)
    write_json(latest, summary)
    print(json.dumps({"通过数量": summary["汇总"]["通过数量"], "失败数量": summary["汇总"]["失败数量"], "输出": str(output)}, ensure_ascii=True))
    return 0 if summary["汇总"]["失败数量"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
