# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DESIGN = ROOT / "01配置" / "税收企业微信消息接收服务设计.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
REPORT_SOURCE_JSON = OUT_DIR / "税收企业微信消息接收服务设计报告_最新.json"
REPORT_SOURCE_MD = OUT_DIR / "税收企业微信消息接收服务设计报告_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信消息接收服务设计报告验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信消息接收服务设计报告验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    design = load_json(DESIGN)
    source = load_json(REPORT_SOURCE_JSON)
    safety = source.get("安全边界", {})
    deployment = source.get("当前部署状态", {})
    queue_sample = source.get("入队样例", {})
    required_queue_fields = set(design.get("消息入队字段", []))
    checks = [
        check("接收服务设计配置存在", DESIGN.exists(), str(DESIGN)),
        check("接收服务设计报告JSON存在", REPORT_SOURCE_JSON.exists(), str(REPORT_SOURCE_JSON)),
        check("接收服务设计报告Markdown存在", REPORT_SOURCE_MD.exists(), str(REPORT_SOURCE_MD)),
        check("机器人终端为杰哥工作秘书", source.get("机器人终端") == "杰哥工作秘书", source.get("机器人终端")),
        check("服务状态为design_only", source.get("服务状态") == "design_only", source.get("服务状态")),
        check("回调验签字段齐备", set(["msg_signature", "timestamp", "nonce", "echostr"]).issubset(set(source.get("回调验签字段", []))), source.get("回调验签字段", [])),
        check("消息入队样例字段齐备", required_queue_fields.issubset(set(queue_sample.keys())), {"期望": sorted(required_queue_fields), "实际": sorted(queue_sample.keys())}),
        check("入队样例进入待证据匹配", queue_sample.get("输入契约状态") == "pending_evidence_match" and queue_sample.get("处理状态") == "queued", queue_sample),
        check("拒收条件包含验签和办税执行", any("验签" in item for item in source.get("拒收条件", [])) and any("申报" in item or "退税" in item or "开票" in item for item in source.get("拒收条件", [])), source.get("拒收条件", [])),
        check("审计要求禁止记录凭据", any("Secret" in item or "Token" in item or "EncodingAESKey" in item for item in source.get("审计要求", [])), source.get("审计要求", [])),
        check("当前未启动服务未开放端口未配置真实回调", deployment.get("是否已启动服务") is False and deployment.get("是否已开放端口") is False and deployment.get("是否已配置企业微信真实回调") is False, deployment),
        check("安全边界未启动服务未新增端口", safety.get("是否启动服务") is False and safety.get("是否新增端口") is False, safety),
        check("未接真实回调未联网未读取凭据", safety.get("是否接收真实企业微信回调") is False and safety.get("是否联网") is False and safety.get("是否读取凭据") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for row in checks if row["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信消息接收服务设计报告验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信消息接收服务设计报告验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for row in checks:
        lines.append(f"- {row['检查项']}：{row['结果']}。{row['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
