# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = BASE_DIR / "税收企业微信人工复核链路一键本地预检_最新.json"
PREVIEW_MD = BASE_DIR / "税收企业微信人工复核链路一键本地预检_最新.md"
REPORT_JSON = BASE_DIR / "税收企业微信人工复核链路一键本地预检验收_最新.json"
REPORT_MD = BASE_DIR / "税收企业微信人工复核链路一键本地预检验收_最新.md"

SAFETY_FALSE_KEYS = [
    "是否接收真实企业微信回调",
    "是否联网",
    "是否读取凭据",
    "是否企业微信真实发送",
    "是否修改公共企业微信接入配置",
    "是否修改19310",
    "是否触发n8n",
    "是否写正式业务库",
    "是否写草案源文件",
    "是否真实回写状态",
    "是否调用模型推理",
    "是否接电子税务局",
    "是否接财税软件",
    "是否生成正式税务结论",
    "是否形成正式复核结论",
    "是否覆盖历史资料",
    "是否删除历史审计记录",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains(data: Any, keyword: str) -> bool:
    return keyword in json.dumps(data, ensure_ascii=False)


def main() -> int:
    data = load_json(PREVIEW_JSON)
    results = data.get("预检结果", [])
    safety = data.get("安全边界", {})
    checks = [
        check("一键预检JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("一键预检Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("资产身份声明为dry-run", contains(data.get("资产身份", ""), "dry-run"), data.get("资产身份", "")),
        check("系统定位包含非办税执行和非正式意见", contains(data.get("系统定位", ""), "不是办税执行系统") and contains(data.get("系统定位", ""), "不是正式税务意见"), data.get("系统定位", "")),
        check("验证脚本数量不少于12", data.get("验证脚本数量", 0) >= 12, data.get("验证脚本数量", 0)),
        check("失败数量为0", data.get("失败数量") == 0, data.get("失败数量")),
        check("预检结论通过", data.get("结论") == "通过", data.get("结论")),
        check("所有验证脚本存在", all(item.get("脚本存在") is True for item in results), results),
        check("所有验证脚本通过", all(item.get("是否通过") is True for item in results), results),
        check("下一步队列指向阶段总回传", contains(data.get("下一步低风险队列", []), "阶段总回传记录"), data.get("下一步低风险队列", [])),
        check("安全边界全部关闭", all(safety.get(key) is False for key in SAFETY_FALSE_KEYS), safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核链路一键本地预检验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核链路一键本地预检验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
