from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


WECOM = Path("D:/杰哥智能化系统/02杰哥扩展系统/00公共组件/企业微信接入设置")
REPORT = WECOM / "03数据" / "12多助手统一路由影子预案" / "企业微信多助手统一路由影子预案_最新.json"
REPORT_MD = WECOM / "03数据" / "12多助手统一路由影子预案" / "企业微信多助手统一路由影子预案_最新.md"
LOG_DIR = WECOM / "04日志" / "多助手统一路由影子预案"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    checks: list[dict[str, Any]] = [
        check("影子预案JSON存在", REPORT.exists(), str(REPORT)),
        check("影子预案Markdown存在", REPORT_MD.exists(), str(REPORT_MD)),
    ]

    report = load_json(REPORT) if REPORT.exists() else {}
    current = report.get("当前状态盘点", {})
    stock = current.get("股票系统", {})
    wecom = current.get("企业微信接入设置", current.get("企业微信助手", {}))
    samples = report.get("影子预案", {}).get("样例", [])
    natural = report.get("自然交流基础体验要求", {})
    natural_text = json.dumps(natural, ensure_ascii=False)
    safety = report.get("安全边界", {})
    hours = report.get("剩余有效工时估算", {})

    checks.extend([
        check("股票仍为阶段性交付完成", stock.get("当前状态") == "阶段性交付完成", stock),
        check("股票剩余工时为0", stock.get("剩余工时") == "0小时", stock.get("剩余工时")),
        check("企业微信终端数量为5", wecom.get("终端数量") == 5, wecom.get("终端数量")),
        check("通用助手不再登记为未接入", len(wecom.get("未接入终端", [])) == 0, wecom.get("未接入终端", [])),
        check("统一路由健康", wecom.get("状态摘要", {}).get("统一指令路由状态") == "healthy", wecom.get("状态摘要", {})),
        check("统一路由真实动作数为0", wecom.get("状态摘要", {}).get("路由真实动作数量") == 0, wecom.get("状态摘要", {})),
        check("本地调用健康", wecom.get("状态摘要", {}).get("统一指令本地调用状态") == "healthy", wecom.get("状态摘要", {})),
        check("本地调用真实动作数为0", wecom.get("状态摘要", {}).get("本地调用真实动作数量") == 0, wecom.get("状态摘要", {})),
        check("影子样例不少于7条", len(samples) >= 7, len(samples)),
        check("剩余工时包含02扩展非股票估算", hours.get("02扩展系统非股票") == "12-22小时", hours),
        check("自然交流基础体验已并入12包", "企业微信机器人是用户日常自然入口" in natural_text, natural),
        check("用户无需记脚本端口", "用户不需要记脚本路径" in natural_text and "端口" in natural_text, natural),
        check("跨业务转交不让用户判断", "不得让用户自己判断发给谁" in natural_text, natural),
        check("反馈进入业务日志和进化候选", "进化候选" in natural_text and "反馈" in natural_text, natural),
    ])

    required_routes = {"股票研究", "系统状态", "知识库问答", "内容办公处理", "视频制作", "税收业务待复核分析"}
    routes = {item.get("影子路由") for item in samples}
    checks.append(check("关键路由均在影子样例中", required_routes.issubset(routes), sorted(routes)))
    required_robots = {"杰哥系统管家", "杰哥工作秘书", "杰哥视频助理", "杰哥私人股票分析顾问", "杰哥的股票分析专家"}
    natural_robots = {item.get("机器人") for item in natural.get("机器人分工", []) if isinstance(item, dict)}
    checks.append(check("自然交流覆盖五类机器人", required_robots.issubset(natural_robots), sorted(natural_robots)))

    for index, item in enumerate(samples, 1):
        prefix = f"样例{index}:{item.get('助手')}->{item.get('影子路由')}"
        checks.extend([
            check(f"{prefix} dry_run为true", item.get("dry_run") is True, item.get("dry_run")),
            check(f"{prefix} shadow为true", item.get("shadow") is True, item.get("shadow")),
            check(f"{prefix} local_preview_only为true", item.get("local_preview_only") is True, item.get("local_preview_only")),
            check(f"{prefix} 不真实发送", item.get("真实发送企业微信") is False, item.get("真实发送企业微信")),
            check(f"{prefix} 不触发n8n", item.get("触发n8n") is False, item.get("触发n8n")),
            check(f"{prefix} 不调用券商", item.get("调用券商接口") is False, item.get("调用券商接口")),
            check(f"{prefix} 不自动交易", item.get("自动交易") is False, item.get("自动交易")),
            check(f"{prefix} 真实动作false", item.get("真实动作") is False, item.get("真实动作")),
        ])

    for key in [
        "企业微信真实发送",
        "扩大真实发送范围",
        "触发Webhook",
        "触发n8n",
        "调用券商接口",
        "自动交易",
        "继续给股票系统加新功能",
        "修改总管进度口径",
        "修改智能系统知识库代码",
        "修改进化系统规则代码",
        "重启正式服务",
    ]:
        checks.append(check(f"安全边界关闭：{key}", safety.get(key) is False, safety.get(key)))

    pass_count = sum(1 for item in checks if item["通过"])
    fail_count = len(checks) - pass_count
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-multi-assistant-unified-route-shadow-plan-verify",
        "所属系统": "02杰哥扩展系统/00公共组件/企业微信接入设置",
        "验收对象": str(REPORT),
        "汇总": {
            "状态": "pass" if fail_count == 0 else "fail",
            "通过数量": pass_count,
            "失败数量": fail_count,
        },
        "检查项": checks,
        "安全结论": "本次仅验收多助手统一路由影子预案；未真实发送、未扩大发送范围、未触发n8n、未调用券商、未自动交易、未修改总管进度口径。",
    }

    latest_json = LOG_DIR / "wecom-multi-assistant-route-shadow-plan-verify-最新.json"
    latest_md = LOG_DIR / "企业微信多助手统一路由影子预案验收_最新.md"
    write_json(latest_json, result)

    lines = [
        "# 企业微信多助手统一路由影子预案验收",
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
        lines.append(f"- [{'通过' if item['通过'] else '失败'}] {item['名称']}：{item['详情']}")
    lines.append("")
    write_text(latest_md, "\n".join(lines))

    print(json.dumps({"状态": result["汇总"]["状态"], "通过": pass_count, "失败": fail_count, "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

