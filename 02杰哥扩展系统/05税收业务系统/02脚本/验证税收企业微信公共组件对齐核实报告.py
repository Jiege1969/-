# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
REPORT_JSON = OUT_DIR / "税收企业微信公共组件对齐核实报告_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信公共组件对齐核实报告_最新.md"
VERIFY_JSON = OUT_DIR / "税收企业微信公共组件对齐核实报告验收_最新.json"
VERIFY_MD = OUT_DIR / "税收企业微信公共组件对齐核实报告验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = load_json(REPORT_JSON)
    rows = report.get("核实结果", [])
    row_names = {item.get("核实项") for item in rows}
    safety = report.get("安全边界", {})
    required = {
        "未读取公共私密配置",
        "公共杰哥工作秘书配置存在",
        "公共终端公网路径为work-secretary",
        "公共税收路由已由暂停改为待复核分析",
        "公共本地调用指向税收待复核摘要",
        "税收配置登记公共组件入口",
        "税收接收服务不另开公网回调",
        "税收全链路真实发送仍阻断",
    }
    checks = [
        check("对齐报告JSON存在", REPORT_JSON.exists(), str(REPORT_JSON)),
        check("对齐报告Markdown存在", REPORT_MD.exists(), str(REPORT_MD)),
        check("对齐报告结论通过", report.get("结论") == "通过", report.get("结论")),
        check("核实项齐备", required.issubset(row_names), sorted(row_names)),
        check("全部核实项对齐", all(item.get("是否对齐") is True for item in rows), rows),
        check("公共入口为work-secretary", report.get("对齐口径", {}).get("企业微信公网入口") == "/wecom/work-secretary", report.get("对齐口径", {})),
        check("不读取私密配置不联网不启动服务", safety.get("是否读取私密配置") is False and safety.get("是否联网") is False and safety.get("是否启动服务") is False, safety),
        check("不新增端口不真实发送不触发n8n", safety.get("是否新增端口") is False and safety.get("是否企业微信真实发送") is False and safety.get("是否触发n8n") is False, safety),
        check("不生成正式结论不接办税系统", safety.get("是否生成正式税务结论") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    verify = {
        "名称": "税收企业微信公共组件对齐核实报告验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    VERIFY_JSON.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信公共组件对齐核实报告验收",
        "",
        f"- 生成时间：{verify['生成时间']}",
        f"- 结论：{verify['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    VERIFY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": verify["结论"], "通过数量": passed, "失败数量": failed, "报告": str(VERIFY_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
