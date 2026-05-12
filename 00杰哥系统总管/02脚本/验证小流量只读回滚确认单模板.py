"""
名称：验证小流量只读回滚确认单模板.py
作用：生成并验证小流量只读回滚确认单模板，确认不会自动删除文件、停止服务、重启服务、外发消息或修改旧系统。
触发方式：python 验证小流量只读回滚确认单模板.py
依赖：Python 标准库；生成小流量只读回滚确认单模板.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证回滚确认单模板；不删除文件；不停止服务；不重启服务；不联网；不写库；不外发；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读回滚确认单模板验收脚本。
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


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成小流量只读回滚确认单模板.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    form_path = manager / "03数据" / "小流量只读执行" / "小流量只读回滚确认单模板_最新.json"
    form = load_json(form_path) if form_path.exists() else {}
    state = form.get("默认状态", {})
    checks = [
        check("回滚确认单生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("回滚确认单存在", form_path.exists(), str(form_path)),
        check("未执行真实动作", state.get("是否已经执行真实动作") is False, state),
        check("默认不需要回滚", state.get("是否需要回滚") is False, state),
        check("默认未回滚", state.get("是否已经回滚") is False, state),
        check("不自动删除文件", state.get("是否删除文件") is False, state),
        check("不自动停止服务", state.get("是否停止服务") is False, state),
        check("不自动重启服务", state.get("是否重启服务") is False, state),
        check("禁止动作完整", len(form.get("禁止动作", [])) >= 5, form.get("禁止动作", [])),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "readonly-rollback-template-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"readonly-rollback-template-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "readonly-rollback-template-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
