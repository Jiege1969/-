# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
CHECK_JSON = OUT_DIR / "税收企业微信入口配置一致性巡检_最新.json"
CHECK_MD = OUT_DIR / "税收企业微信入口配置一致性巡检_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信入口配置一致性巡检验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信入口配置一致性巡检验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inspection = load_json(CHECK_JSON)
    rows = inspection.get("巡检结果", [])
    row_names = {row.get("巡检项") for row in rows}
    required = {
        "配置主文件存在",
        "公共组件接入口径存在",
        "消息合规规则存在",
        "输入消息契约存在",
        "消息接收服务设计存在",
        "本地输入队列规则存在",
        "输入队列证据匹配影子流转规则存在",
        "证据匹配到分析契约输入包规则存在",
        "分析契约输入包到待复核草案骨架规则存在",
        "待复核草案骨架到分析摘要预演规则存在",
        "配置章节齐备",
        "入口默认dry_run_only",
        "真实发送默认未放行",
        "机器人终端为杰哥工作秘书",
        "输入契约绑定杰哥工作秘书",
        "接收服务为设计状态且不新增端口",
        "输入队列为dry_run且绑定杰哥工作秘书",
        "真实发送门禁短语齐备",
        "凭据规则不落盘",
        "接收范围禁止外部和全员",
        "合规规则含边界声明和敏感模式",
        "输入队列证据匹配影子流转为shadow且不写正式库",
        "证据匹配到分析契约输入包为shadow且不调用模型",
        "待复核草案骨架为shadow且不调用模型",
        "待复核分析摘要预演为shadow且不调用模型",
        "关键验收报告全部存在",
        "关键验收报告全部通过",
    }
    safety = inspection.get("安全边界", {})
    checks = [
        check("一致性巡检JSON存在", CHECK_JSON.exists(), str(CHECK_JSON)),
        check("一致性巡检Markdown存在", CHECK_MD.exists(), str(CHECK_MD)),
        check("巡检结论通过", inspection.get("巡检结论") == "通过", inspection.get("巡检结论")),
        check("巡检项齐备", len(rows) >= 20 and required.issubset(row_names), rows),
        check("全部巡检项一致", all(row.get("是否一致") is True for row in rows), rows),
        check("失败数量为0", inspection.get("失败数量") == 0, inspection.get("失败数量")),
        check("报告状态全部存在且通过", all(item.get("是否存在") is True and item.get("结论") == "通过" for item in inspection.get("报告状态", {}).values()), inspection.get("报告状态", {})),
        check("未联网未读取凭据未发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未修改配置", safety.get("是否修改配置") is False, safety),
        check("未生成正式税务结论且未接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信入口配置一致性巡检验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信入口配置一致性巡检验收",
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
