from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path("D:/杰哥智能化系统")
EXT = ROOT / "02杰哥扩展系统"
DATA_DIR = EXT / "03数据" / "01扩展系统施工盘点"
REPORT_JSON = DATA_DIR / "02扩展系统施工盘点与下一步清单_最新.json"
REPORT_MD = DATA_DIR / "02扩展系统施工盘点与下一步清单_最新.md"
OUT_JSON = DATA_DIR / "02扩展系统施工盘点与下一步清单验收_最新.json"
OUT_MD = DATA_DIR / "02扩展系统施工盘点与下一步清单验收_最新.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, passed: bool, detail: str) -> dict:
    return {"检查项": name, "通过": bool(passed), "详情": detail}


def main() -> None:
    checks: list[dict] = []

    checks.append(check("报告JSON存在", REPORT_JSON.exists(), str(REPORT_JSON)))
    checks.append(check("报告MD存在", REPORT_MD.exists(), str(REPORT_MD)))

    report = load_json(REPORT_JSON) if REPORT_JSON.exists() else {}

    boundary = report.get("施工边界", {}).get("禁止动作执行结果", {})
    for key in ["企业微信真实发送", "触发n8n", "调用券商接口", "自动交易", "扩大真实发送范围", "重启正式服务"]:
        checks.append(check(f"禁止动作未执行：{key}", boundary.get(key) is False, str(boundary.get(key))))

    stock = report.get("股票系统只读稳定性复核", {})
    checks.append(check("股票状态文件存在", stock.get("状态文件", {}).get("exists") is True, stock.get("状态文件", {}).get("path", "")))
    checks.append(check("股票验收文件存在", stock.get("验收文件", {}).get("exists") is True, stock.get("验收文件", {}).get("path", "")))
    checks.append(check("股票剩余工时为0", str(stock.get("剩余工时")) == "0小时", str(stock.get("剩余工时"))))
    checks.append(check("股票本次只读", "只读" in stock.get("本次处理", ""), stock.get("本次处理", "")))

    route = report.get("企业微信助手与多助手路由", {}).get("路由能力", {})
    checks.append(check("企业微信路由数为7", route.get("路由数") == 7, str(route.get("路由数"))))
    checks.append(check("企业微信真实动作数为0", route.get("真实动作数") == 0, str(route.get("真实动作数"))))

    terminal = report.get("企业微信助手与多助手路由", {}).get("终端分工", {})
    checks.append(check("企业微信终端数为5", terminal.get("终端数") == 5, str(terminal.get("终端数"))))
    checks.append(check("通用助手仍为待桥接", len(terminal.get("已登记待桥接", [])) == 3, str(terminal.get("已登记待桥接", []))))

    logs = report.get("企业微信助手与多助手路由", {}).get("验收日志", {})
    for name, item in logs.items():
        checks.append(check(f"验收日志存在：{name}", item.get("exists") is True, item.get("path", "")))

    hours = report.get("剩余有效工时估算", {})
    checks.append(check("扩展系统剩余工时保留16-28小时", hours.get("02扩展系统非股票") == "16-28小时", str(hours.get("02扩展系统非股票"))))

    incomplete = report.get("除股票外未完成项", [])
    checks.append(check("记录除股票外未完成项", len(incomplete) >= 5, str(len(incomplete))))

    manager_items = report.get("需要总管收口的事项", [])
    checks.append(check("记录总管收口事项", len(manager_items) >= 4, str(len(manager_items))))

    pass_count = sum(1 for item in checks if item["通过"])
    fail_count = len(checks) - pass_count
    result = {
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "验收对象": str(REPORT_JSON),
        "通过": pass_count,
        "失败": fail_count,
        "是否通过": fail_count == 0,
        "检查项": checks,
        "安全结论": "本次仅生成02扩展系统盘点与只读验收证据，未执行真实发送、n8n、券商、自动交易或放量动作。",
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# 02扩展系统施工盘点验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 验收对象：{result['验收对象']}",
        f"- 通过：{pass_count}",
        f"- 失败：{fail_count}",
        f"- 是否通过：{result['是否通过']}",
        f"- 安全结论：{result['安全结论']}",
        "",
        "## 检查项",
        "",
    ]
    md.extend([f"- [{'通过' if item['通过'] else '失败'}] {item['检查项']}：{item['详情']}" for item in checks])
    md.append("")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({"是否通过": result["是否通过"], "通过": pass_count, "失败": fail_count, "输出": str(OUT_JSON)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
