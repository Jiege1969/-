# -*- coding: utf-8 -*-
"""
名称：生成四系统股票小闭环历史观察面板.py
作用：汇总四系统股票小闭环一键执行历史，识别最近成功率、失败动作、融合链路状态、完成观察态和反复断点。
触发方式：python 生成四系统股票小闭环历史观察面板.py
依赖：03数据/四系统小闭环/四系统股票小闭环一键执行_*.json；股票四系统融合面板、开工快检、完成观察记录和主闭环总验收。
所属系统：00杰哥系统总管
输出：03数据/四系统小闭环/四系统股票小闭环历史观察面板_最新.json 与 .md。
安全边界：只读取00总管03数据/四系统小闭环历史记录；只写历史观察面板；不重启服务；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不更新施工接续包。
标识：four-system-stock-loop-history-panel-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default if default is not None else {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def execution_files(loop_dir: Path) -> list[Path]:
    files = [
        item for item in loop_dir.glob("四系统股票小闭环一键执行_*.json")
    ]
    return sorted(files, key=lambda item: item.name)


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def action_summary(action: dict[str, Any]) -> dict[str, Any]:
    data = action.get("状态数据") if isinstance(action.get("状态数据"), dict) else {}
    return {
        "名称": action.get("名称"),
        "成功": bool(action.get("成功")),
        "返回码": action.get("返回码"),
        "开始时间": action.get("开始时间"),
        "结束时间": action.get("结束时间"),
        "公网状态": data.get("status") if data else "",
        "本地桥接": data.get("local_bridge_ok") if data else None,
        "SSH隧道": data.get("ssh_tunnel_ok") if data else None,
        "公网探针": data.get("public_callback_ok") if data else None,
    }


def build_record(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    actions = data.get("动作", []) if isinstance(data.get("动作"), list) else []
    failed_actions = [action_summary(item) for item in actions if not item.get("成功")]
    public_actions = [action_summary(item) for item in actions if str(item.get("名称", "")).endswith("查看股票公网回调状态.ps1")]
    fusion_action_names = {
        "执行四系统小闭环开工快检.py",
        "验证四系统小闭环开工快检.py",
        "生成股票四系统融合闭环状态面板.py",
        "验证股票四系统融合闭环状态面板.py",
    }
    fusion_actions = [action_summary(item) for item in actions if item.get("名称") in fusion_action_names]
    return {
        "文件": str(path),
        "生成时间": data.get("生成时间") or path.stem,
        "执行结论": data.get("执行结论", ""),
        "失败数量": int(data.get("失败数量") or 0),
        "动作数": len(actions),
        "失败动作": failed_actions,
        "公网回调动作": public_actions[-1] if public_actions else {},
        "融合链路动作数": len(fusion_actions),
        "融合链路失败数": sum(1 for item in fusion_actions if not item.get("成功")),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 四系统股票小闭环历史观察面板 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 历史结论：{report['历史结论']}",
        f"- 覆盖执行次数：{report['覆盖执行次数']}",
        f"- 成功次数：{report['成功次数']}",
        f"- 失败次数：{report['失败次数']}",
        f"- 最近一次：{report['最近一次结论']}",
        "",
        "## 二、完成观察态",
        "",
        f"- 主闭环总验收：{report['主闭环总验收'].get('总验收结论', '未生成')}",
        f"- 当前阶段：{report['主闭环总验收'].get('当前阶段', '未确认')}",
        f"- 完成观察记录：{report['完成观察记录'].get('总结论', '未生成')}",
        f"- 观察期状态：{report['完成观察记录'].get('观察期状态', '未确认')}",
        f"- 观察起点：{report['完成观察记录'].get('观察起点', '未确认')}",
        "",
        "## 三、最近执行记录",
        "",
        "| 时间 | 结论 | 动作数 | 融合动作 | 失败数 | 公网回调 | 失败动作 |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in report["最近记录"]:
        public_status = row.get("公网回调动作", {}).get("公网状态") or "未检查"
        failed_names = "、".join(item["名称"] for item in row.get("失败动作", [])) or "无"
        lines.append(f"| {row['生成时间']} | {row['执行结论']} | {row['动作数']} | {row.get('融合链路动作数', 0)} | {row['失败数量']} | {public_status} | {failed_names} |")

    lines.extend(["", "## 四、反复断点", ""])
    if report["失败动作统计"]:
        for item in report["失败动作统计"]:
            lines.append(f"- {item['动作']}：失败 {item['次数']} 次；建议：{item['建议']}")
    else:
        lines.append("- 暂无反复失败动作。")

    lines.extend([
        "",
        "## 五、下一步观察",
        "",
    ])
    for item in report["下一步观察"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 六、关键文件",
        "",
    ])
    for name, state in report["关键文件"].items():
        status = "存在" if state["存在"] else "缺失"
        lines.append(f"- {name}：{status}；{state['路径']}")
    lines.extend([
        "",
        "## 七、安全边界",
        "",
        "- 本面板只读取历史执行记录并生成观察结果。",
        "- 不重启服务，不触发n8n，不发送企业微信，不调用券商接口，不自动交易。",
        "- 不更新施工接续包、接续卡片或桌面压缩包。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    manager = manager_root()
    loop_dir = manager / "03数据" / "四系统小闭环"
    now = datetime.now()
    records = [build_record(path) for path in execution_files(loop_dir)]
    main_acceptance_path = loop_dir / "股票四系统主闭环完成总验收_最新.json"
    completion_observation_path = loop_dir / "股票四系统闭环完成观察记录_最新.json"
    completion_observation_verify_path = manager / "04日志" / "四系统小闭环" / "stock-four-system-closed-loop-completion-observation-verify-最新.json"
    fusion_panel_path = loop_dir / "股票四系统融合闭环状态面板_最新.json"
    quickcheck_path = loop_dir / "四系统小闭环开工快检_最新.json"
    main_acceptance = load_json(main_acceptance_path, {})
    completion_observation = load_json(completion_observation_path, {})
    completion_verify = load_json(completion_observation_verify_path, {})
    recent = records[-12:]
    success = [item for item in records if item["失败数量"] == 0 and "成功" in item["执行结论"]]
    failed = [item for item in records if item not in success]

    failed_counter: dict[str, int] = {}
    for record in records:
        for action in record.get("失败动作", []):
            name = str(action.get("名称") or "未知动作")
            failed_counter[name] = failed_counter.get(name, 0) + 1
    suggestions = {
        "查看股票公网回调状态.ps1": "优先检查19302本地桥接、SSH反向隧道和公网502。",
        "生成四系统股票小闭环状态面板.py": "查看状态面板中的失败检查项，通常是服务或验收口径断点。",
        "验证四系统股票小闭环.py": "先修状态面板失败项，再重跑验收。",
        "验证股票企微前台交互回归.py": "检查前台输出标准和企微路由是否改动。",
    }
    failed_stats = [
        {"动作": name, "次数": count, "建议": suggestions.get(name, "查看该动作stdout/stderr和最新报告。")}
        for name, count in sorted(failed_counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    last = records[-1] if records else {}
    public_not_ready = [
        item for item in records
        if item.get("公网回调动作") and item["公网回调动作"].get("公网状态") not in {"", "ready"}
    ]
    observations = [
        "当前主闭环处于完成观察态；观察期按24小时或一次完整业务周期复核。",
        "每次开工和收工优先看本历史面板，确认是否存在重复失败动作。",
        "融合链路动作数应随主入口升级保持在4项以上：开工快检、快检验证、融合面板、融合验证。",
        "文稿质检支线只看旁路观察和样本复盘是否稳定存在，不以是否进入正式推送为目标。",
        "公网回调是手机企业微信可用性的关键，不得只看本地19302。",
        "企微前台回归用例数量会增长，验收口径应看失败数是否为0，而不是写死旧数量。",
    ]
    if public_not_ready:
        observations.insert(0, f"历史中出现过 {len(public_not_ready)} 次公网回调未ready，应重点观察SSH反向隧道稳定性。")

    report = {
        "名称": "四系统股票小闭环历史观察面板",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成四系统股票小闭环历史观察面板.py",
        "历史结论": "主闭环已进入完成观察态；历史中存在可复盘断点" if failed else "主闭环已进入完成观察态；当前历史均成功",
        "覆盖执行次数": len(records),
        "成功次数": len(success),
        "失败次数": len(failed),
        "最近一次结论": last.get("执行结论", "暂无记录"),
        "主闭环总验收": main_acceptance,
        "完成观察记录": completion_observation,
        "完成观察记录验证": completion_verify,
        "关键文件": {
            "主闭环完成总验收": file_state(main_acceptance_path),
            "完成观察记录": file_state(completion_observation_path),
            "完成观察记录验证日志": file_state(completion_observation_verify_path),
            "融合闭环状态面板": file_state(fusion_panel_path),
            "四系统开工快检": file_state(quickcheck_path),
        },
        "最近记录": list(reversed(recent)),
        "失败动作统计": failed_stats,
        "下一步观察": observations,
        "安全边界": {
            "是否重启服务": False,
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否更新施工接续包": False,
        },
    }

    latest_json = loop_dir / "四系统股票小闭环历史观察面板_最新.json"
    latest_md = loop_dir / "四系统股票小闭环历史观察面板_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "覆盖执行次数": len(records),
        "成功次数": len(success),
        "失败次数": len(failed),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
