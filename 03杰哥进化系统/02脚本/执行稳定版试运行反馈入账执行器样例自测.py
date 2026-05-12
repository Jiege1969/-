# -*- coding: utf-8 -*-
"""执行稳定版试运行反馈入账执行器样例自测。"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "93稳定版试运行反馈入账执行器样例验收包"

SAMPLES_JSON = DATA_DIR / "稳定版试运行反馈入账样例_最新.json"
RESULT_JSON = DATA_DIR / "稳定版试运行反馈入账执行器样例自测结果_最新.json"
RESULT_MD = DATA_DIR / "稳定版试运行反馈入账执行器样例自测结果_最新.md"
EXECUTOR_SCRIPT = EVOLUTION_ROOT / "02脚本" / "执行稳定版试运行反馈本地入账.py"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_executor() -> Any:
    spec = importlib.util.spec_from_file_location("trial_feedback_executor", EXECUTOR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载执行器脚本")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_md(result: dict[str, Any]) -> str:
    rows = [
        f"| {item['名称']} | {item['实际']['accepted']} | {item['实际'].get('level')} | {item['实际'].get('need_supervisor_confirm')} | {item['通过']} |"
        for item in result["样例结果"]
    ]
    return "\n".join(
        [
            "# 稳定版试运行反馈入账执行器样例自测结果",
            "",
            f"- 生成时间：{result['生成时间']}",
            f"- 总体状态：{result['总体状态']}",
            f"- 通过/总数：{result['汇总']['通过']} / {result['汇总']['总数']}",
            "",
            "| 样例 | accepted | level | 需总管确认 | 通过 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


def main() -> int:
    executor = load_executor()
    samples = read_json(SAMPLES_JSON)
    expectations = {
        "普通反馈样例": {"accepted": True, "level": "P2", "need_supervisor_confirm": False},
        "红线反馈样例": {"accepted": True, "level": "P0", "need_supervisor_confirm": True},
        "缺字段反馈样例": {"accepted": False},
    }
    sample_results = []
    for name, sample in samples.items():
        actual = executor.classify(sample)
        expected = expectations[name]
        passed = all(actual.get(key) == value for key, value in expected.items())
        sample_results.append({"名称": name, "期望": expected, "实际": actual, "通过": passed})

    passed_count = sum(1 for item in sample_results if item["通过"])
    result = {
        "名称": "稳定版试运行反馈入账执行器样例自测结果",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if passed_count == len(sample_results) else "blocked",
        "汇总": {"总数": len(sample_results), "通过": passed_count, "失败": len(sample_results) - passed_count},
        "样例结果": sample_results,
        "安全边界": {
            "写入正式待入账目录": False,
            "触发外部动作": False,
            "写正式规则": False,
        },
    }
    write_json(RESULT_JSON, result)
    write_text(RESULT_MD, build_md(result))
    print(json.dumps({"总体状态": result["总体状态"], "通过": passed_count, "失败": len(sample_results) - passed_count, "输出": str(RESULT_JSON)}, ensure_ascii=False))
    return 0 if result["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
