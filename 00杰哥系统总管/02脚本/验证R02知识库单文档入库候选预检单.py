"""
名称：验证R02知识库单文档入库候选预检单.py
作用：生成并验证R02知识库单文档入库候选预检单，确认预检满足且正式写库默认不放行。
触发方式：python 验证R02知识库单文档入库候选预检单.py
依赖：Python 标准库；生成R02知识库单文档入库候选预检单.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证R02预检单；不写入正式知识库；不写入Qdrant；不写入PostgreSQL；不读取旧系统资料；不覆盖原始文档；不触发n8n；不外发资料；不接入税收。
创建/修改记录：2026-04-27 创建R02知识库单文档入库候选预检单验收脚本。
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


def knowledge_root() -> Path:
    return v3_root() / "01杰哥智能系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = knowledge_root()
    script = root / "02脚本" / "知识库" / "生成R02知识库单文档入库候选预检单.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    form_path = root / "03数据" / "知识库" / "06入库前复核" / "R02知识库单文档入库候选预检单_最新.json"
    form = load_json(form_path) if form_path.exists() else {}
    switches = form.get("默认开关", {})
    checks = [
        check("R02预检单生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("R02预检单存在", form_path.exists(), str(form_path)),
        check("预检项目全部满足", form.get("是否全部满足预检") is True, form.get("预检结果", {})),
        check("正式写库不放行", form.get("是否放行正式写库") is False, form.get("是否放行正式写库")),
        check("正式知识库写入关闭", switches.get("允许写入正式知识库") is False, switches),
        check("Qdrant写入关闭", switches.get("允许写入Qdrant") is False, switches),
        check("PostgreSQL写入关闭", switches.get("允许写入PostgreSQL") is False, switches),
        check("旧系统读取关闭", switches.get("允许读取旧系统资料") is False, switches),
        check("税收接入关闭", switches.get("允许接入税收") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "r02-knowledge-ingest-preflight-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"r02-knowledge-ingest-preflight-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
