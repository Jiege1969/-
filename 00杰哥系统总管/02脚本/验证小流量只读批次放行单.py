"""
名称：验证小流量只读批次放行单.py
作用：生成并验证小流量只读批次放行单，确认所有批次默认不放行且不允许真实动作。
触发方式：python 验证小流量只读批次放行单.py
依赖：Python 标准库；生成小流量只读批次放行单.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证批次放行单；不联网；不写库；不生成正式文档；不真实渲染；不真实转换；不真实发送企业微信；不触发n8n；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建小流量只读批次放行单验收脚本。
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
    script = manager / "02脚本" / "生成小流量只读批次放行单.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    form_path = manager / "03数据" / "小流量只读执行" / "小流量只读批次放行单_最新.json"
    form = load_json(form_path) if form_path.exists() else {}
    batches = form.get("批次放行单", [])
    checks = [
        check("放行单生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("放行单存在", form_path.exists(), str(form_path)),
        check("批次数量完整", len(batches) >= 3, len(batches)),
        check("所有批次默认不放行", all(item.get("当前是否放行") is False for item in batches), batches),
        check("不允许批量放行", form.get("是否允许批量放行") is False, form.get("是否允许批量放行")),
        check("不允许跳过人工确认", form.get("是否允许跳过人工确认") is False, form.get("是否允许跳过人工确认")),
        check("不允许真实动作", form.get("是否允许真实动作") is False, form.get("是否允许真实动作")),
        check("全局禁止包含税收", any("税收" in item for item in form.get("全局禁止", [])), form.get("全局禁止", [])),
        check("全局禁止包含旧系统", any("旧系统" in item for item in form.get("全局禁止", [])), form.get("全局禁止", [])),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "readonly-batch-release-form-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"readonly-batch-release-form-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "readonly-batch-release-form-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
