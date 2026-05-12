from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EXT = Path("D:/杰哥智能化系统/02杰哥扩展系统")
DATA_DIR = EXT / "03数据" / "02知识库问答与多助手路由本轮交付"
REPORT = DATA_DIR / "02扩展知识库问答与多助手路由本轮交付包_最新.json"
REPORT_MD = DATA_DIR / "02扩展知识库问答与多助手路由本轮交付包_最新.md"
LOG_DIR = EXT / "04日志" / "02知识库问答与多助手路由本轮交付"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    checks: list[dict[str, Any]] = [
        check("交付包JSON存在", REPORT.exists(), str(REPORT)),
        check("交付包Markdown存在", REPORT_MD.exists(), str(REPORT_MD)),
    ]
    report = load_json(REPORT) if REPORT.exists() else {}

    sources = report.get("读取来源", {})
    for name, item in sources.items():
        checks.append(check(f"读取来源存在：{name}", item.get("exists") is True, item.get("path")))

    qa = report.get("小样本问答清单", [])
    routes = report.get("多助手路由影子预案", [])
    checks.append(check("小样本问答不少于5条", len(qa) >= 5, len(qa)))
    checks.append(check("多助手路由不少于5条", len(routes) >= 5, len(routes)))

    for item in qa:
        question = item.get("问题", "")
        checks.extend([
            check(f"问答有回答结论：{question}", bool(item.get("回答结论")), item.get("回答结论")),
            check(f"问答有来源文件：{question}", bool(item.get("来源文件")) and Path(item.get("来源文件", "")).exists(), item.get("来源文件")),
            check(f"问答有来源章节或字段：{question}", bool(item.get("来源章节或字段")), item.get("来源章节或字段")),
            check(f"问答有验收状态：{question}", bool(item.get("验收状态")), item.get("验收状态")),
            check(f"问答有风险边界：{question}", bool(item.get("风险边界")), item.get("风险边界")),
            check(f"问答证据不少于1条：{question}", len(item.get("证据", [])) >= 1, len(item.get("证据", []))),
        ])
        for ev in item.get("证据", []):
            checks.append(check(f"证据来源存在：{question}/{ev.get('来源名称')}", ev.get("来源文件存在") is True and Path(ev.get("来源文件", "")).exists(), ev.get("来源文件")))
            checks.append(check(f"证据字段非空：{question}/{ev.get('来源名称')}", bool(ev.get("字段")), ev.get("字段")))

    required_assistants = {"股票助手", "总管助手", "知识库助手", "进化规则助手", "默认兜底助手"}
    assistants = {item.get("助手") for item in routes}
    checks.append(check("五类助手齐全", required_assistants.issubset(assistants), sorted(assistants)))

    for item in routes:
        assistant = item.get("助手", "")
        checks.append(check(f"{assistant}有目标路由", bool(item.get("目标路由")), item.get("目标路由")))
        checks.append(check(f"{assistant}有影子验证状态", bool(item.get("影子验证")), item.get("影子验证")))
        checks.append(check(f"{assistant}有正式放量说明", bool(item.get("正式放量")), item.get("正式放量")))
        if assistant in {"进化规则助手", "知识库助手", "总管助手"}:
            checks.append(check(f"{assistant}未正式放量", "不能" in item.get("正式放量", "") or "暂不" in item.get("正式放量", ""), item.get("正式放量")))

    allowed_shadow = report.get("哪些可以影子验证", [])
    no_formal = report.get("哪些不能正式放量", [])
    checks.append(check("记录可影子验证清单", len(allowed_shadow) >= 5, len(allowed_shadow)))
    checks.append(check("记录不可正式放量清单", len(no_formal) >= 5, len(no_formal)))

    untouched = report.get("未触碰边界确认", {})
    for key in [
        "修改00总管进度口径文件",
        "修改01智能系统中台代码",
        "修改03进化系统规则代码",
        "企业微信真实发送",
        "扩大真实发送范围",
        "触发n8n",
        "调用券商接口",
        "自动交易",
        "继续给股票系统加新功能",
    ]:
        checks.append(check(f"边界未触碰：{key}", untouched.get(key) is False, untouched.get(key)))

    hours = report.get("剩余有效工时", {})
    checks.append(check("股票工时为0", hours.get("股票系统") == "0小时", hours))
    checks.append(check("给出02扩展建议剩余工时", bool(hours.get("02扩展系统建议剩余")), hours))

    manager_items = report.get("需要总管收口的事项", [])
    checks.append(check("总管收口事项不少于5条", len(manager_items) >= 5, len(manager_items)))

    pass_count = sum(1 for item in checks if item["通过"])
    fail_count = len(checks) - pass_count
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "extension-knowledge-qa-and-multi-assistant-route-delivery-verify",
        "所属系统": "02杰哥扩展系统",
        "验收对象": str(REPORT),
        "汇总": {
            "状态": "pass" if fail_count == 0 else "fail",
            "通过数量": pass_count,
            "失败数量": fail_count,
        },
        "检查项": checks,
        "安全结论": "本轮只生成02扩展系统知识库可追溯问答小样本、多助手路由影子预案和验收报告；未改总管进度口径，未改01中台代码，未改03规则代码，未真实发送，未触发n8n。",
    }

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_json = LOG_DIR / f"02扩展知识库问答与多助手路由本轮交付验收_{stamp}.json"
    latest_json = LOG_DIR / "02扩展知识库问答与多助手路由本轮交付验收_最新.json"
    out_md = LOG_DIR / f"02扩展知识库问答与多助手路由本轮交付验收_{stamp}.md"
    latest_md = LOG_DIR / "02扩展知识库问答与多助手路由本轮交付验收_最新.md"
    write_json(out_json, result)
    write_json(latest_json, result)

    lines = [
        "# 02扩展知识库问答与多助手路由本轮交付验收",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 状态：{result['汇总']['状态']}",
        f"- 通过：{pass_count}",
        f"- 失败：{fail_count}",
        f"- 安全结论：{result['安全结论']}",
        "",
        "## 检查项",
        "",
    ]
    for item in checks:
        lines.append(f"- [{'通过' if item['通过'] else '失败'}] {item['检查项']}：{item['详情']}")
    lines.append("")
    write_text(out_md, "\n".join(lines))
    write_text(latest_md, "\n".join(lines))

    print(json.dumps({"状态": result["汇总"]["状态"], "通过": pass_count, "失败": fail_count, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
