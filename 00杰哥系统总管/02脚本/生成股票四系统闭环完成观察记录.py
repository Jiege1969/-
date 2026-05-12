#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
名称：生成股票四系统闭环完成观察记录.py
作用：汇总股票系统日常可用、四系统融合面板、手机端图文详情、公网回调、开工快检和194受控同步结果，生成闭环完成观察记录。
输入：股票C+++验收、股票日常一键运行、股票四系统融合闭环状态面板、推荐点击详情与手机排版验收、公网回调状态、四系统小闭环开工快检、194模板同步执行报告。
输出：00杰哥系统总管/03数据/四系统小闭环/股票四系统闭环完成观察记录_最新.md/json。
安全边界：只读取本地验收产物并写观察记录；不触发n8n，不发送企业微信，不重启服务，不写股票业务库，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建，用于股票系统与四系统最小闭环完成态收尾；2026-05-04 纳入手机端图文详情和公网回调ready，防止只看本地闭环。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
OUT_DIR = MANAGER / "03数据" / "四系统小闭环"


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default
    return default


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def run_public_callback_status(stock: Path) -> dict[str, Any]:
    script = stock / "02脚本" / "查看股票公网回调状态.ps1"
    if not script.exists():
        return {"执行成功": False, "返回码": -1, "数据": {}, "错误": f"missing {script}"}
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        stdout = (completed.stdout or "").strip()
        return {
            "执行成功": completed.returncode == 0,
            "返回码": completed.returncode,
            "数据": json.loads(stdout) if stdout else {},
            "stderr": (completed.stderr or "").strip()[-1000:],
        }
    except Exception as exc:
        return {"执行成功": False, "返回码": -1, "数据": {}, "错误": str(exc)}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票四系统闭环完成观察记录",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总结论：{report['总结论']}",
        f"- 当前阶段：{report['当前阶段']}",
        f"- 观察期状态：{report['观察期状态']}",
        f"- 观察起点：{report['观察起点']}",
        "",
        "## 关键验收",
    ]
    for item in report["关键验收"]:
        mark = "通过" if item["通过"] else "未通过"
        lines.append(f"- {item['名称']}：{mark}；{item['摘要']}")
    lines.extend([
        "",
        "## 已完成链路",
    ])
    for item in report["已完成链路"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 后续观察事项",
    ])
    for item in report["后续观察事项"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 安全边界",
    ])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = {
        "股票C+++日常可用总验收": STOCK / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.json",
        "股票日常一键运行": STOCK / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.json",
        "股票四系统融合闭环状态面板": MANAGER / "03数据" / "四系统小闭环" / "股票四系统融合闭环状态面板_最新.json",
        "推荐点击详情与手机排版验收": STOCK / "03数据" / "196推荐点击详情与手机排版验收" / "股票推荐点击详情与手机排版验收_最新.json",
        "四系统小闭环开工快检": MANAGER / "03数据" / "四系统小闭环" / "四系统小闭环开工快检_最新.json",
        "四系统股票小闭环验收": MANAGER / "03数据" / "四系统小闭环" / "四系统股票小闭环验收_最新.json",
        "194模板同步执行报告": STOCK / "03数据" / "194单股证据核验模板同步执行" / "单股证据核验模板同步执行报告_最新.json",
    }

    c_acceptance = load_json(paths["股票C+++日常可用总验收"], {})
    daily_run = load_json(paths["股票日常一键运行"], {})
    fusion = load_json(paths["股票四系统融合闭环状态面板"], {})
    mobile_detail = load_json(paths["推荐点击详情与手机排版验收"], {})
    quickcheck = load_json(paths["四系统小闭环开工快检"], {})
    small_loop = load_json(paths["四系统股票小闭环验收"], {})
    template_sync = load_json(paths["194模板同步执行报告"], {})
    public_callback = run_public_callback_status(STOCK)

    checks = [
        {
            "名称": "股票C+++日常可用总验收",
            "通过": c_acceptance.get("失败数量") == 0 and "通过" in str(c_acceptance.get("验收结论", "")),
            "摘要": f"通过={c_acceptance.get('通过数量')}；失败={c_acceptance.get('失败数量')}",
        },
        {
            "名称": "股票日常一键运行",
            "通过": daily_run.get("失败数量") == 0,
            "摘要": f"失败={daily_run.get('失败数量')}",
        },
        {
            "名称": "股票四系统融合闭环状态面板",
            "通过": fusion.get("融合结论") == "通过：可以按融合主线继续施工" and "不影响" in str(fusion.get("是否影响股票日常使用", "")),
            "摘要": f"{fusion.get('当前进度')}；{fusion.get('剩余有效工作时间估算')}",
        },
        {
            "名称": "推荐点击详情与手机排版",
            "通过": mobile_detail.get("失败数量") == 0 and int(mobile_detail.get("链接数量") or 0) >= 5,
            "摘要": f"链接={mobile_detail.get('链接数量')}；失败={mobile_detail.get('失败数量')}",
        },
        {
            "名称": "公网回调ready",
            "通过": public_callback.get("执行成功") is True and public_callback.get("数据", {}).get("status") == "ready",
            "摘要": f"status={public_callback.get('数据', {}).get('status')}；ssh={public_callback.get('数据', {}).get('ssh_tunnel_ok')}；public={public_callback.get('数据', {}).get('public_callback_ok')}",
        },
        {
            "名称": "四系统小闭环开工快检",
            "通过": quickcheck.get("失败数量") == 0,
            "摘要": f"通过={quickcheck.get('通过数量')}；失败={quickcheck.get('失败数量')}",
        },
        {
            "名称": "四系统股票小闭环验收",
            "通过": int((small_loop.get("汇总") or {}).get("失败") or small_loop.get("失败数量") or 0) == 0 and "通过" in str(small_loop.get("验收结论", "")),
            "摘要": f"通过={(small_loop.get('汇总') or {}).get('通过') or small_loop.get('通过数量')}；失败={(small_loop.get('汇总') or {}).get('失败') or small_loop.get('失败数量')}",
        },
        {
            "名称": "194模板同步执行",
            "通过": template_sync.get("执行写入") is True and "已写入172/175/178人工模板" in str(template_sync.get("总结论", "")),
            "摘要": str(template_sync.get("总结论", "")),
        },
    ]

    ok = all(item["通过"] for item in checks)
    report = {
        "名称": "股票四系统闭环完成观察记录",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总结论": "通过：股票系统与四系统最小闭环已进入完成观察态" if ok else "待处理：闭环完成观察仍有断点",
        "当前阶段": "股票系统作为真实业务样板，已完成证据链受控同步与四系统闭环验收收尾",
        "观察期状态": "已启动观察；后续按24小时或一次完整业务周期复核",
        "观察起点": now.strftime("%Y-%m-%d %H:%M:%S"),
        "关键验收": checks,
        "关键文件": {name: file_state(path) for name, path in paths.items()},
        "公网回调状态": public_callback,
        "已完成链路": [
            "205正式确认回执已录入。",
            "208候选值与205核验字段已补入191 CSV。",
            "197已在显式授权下同步191台账。",
            "193模板同步闸口已放行。",
            "194已在显式授权下写入172/175/178人工模板。",
            "股票C+++总验收、日常一键运行、融合面板和开工快检均为零失败。",
            "推荐点击详情与手机排版、公网回调ready、四系统股票小闭环验收已纳入观察记录。",
        ],
        "后续观察事项": [
            "观察期按24小时或一次完整业务周期执行，观察期内保持现有稳定链路，不为完善而改动正式链路。",
            "观察期内若股票日常一键运行、C+++验收或企微问答出现异常，先隔离失败环节，不回滚已验证成功链路。",
            "文稿质检仍保持旁路第一阶段，继续累计样本确认，不阻断股票系统和四系统主闭环。",
            "收工或新开对话时再统一更新施工接续包、接续卡片和桌面无缝接手包。",
        ],
        "安全边界": {
            "触发n8n": False,
            "真实发送企业微信": False,
            "重启服务": False,
            "写股票业务正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "更新施工接续包": False,
        },
    }

    latest_json = OUT_DIR / "股票四系统闭环完成观察记录_最新.json"
    latest_md = OUT_DIR / "股票四系统闭环完成观察记录_最新.md"
    latest_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_md.write_text(build_markdown(report), encoding="utf-8")

    print(json.dumps({
        "状态": report["总结论"],
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
