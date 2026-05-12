# -*- coding: utf-8 -*-
"""生成红线材料模板第一批只读填报预演包。

只生成示例填报预演，不提交、不发送、不触发、不重载、不生效。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "109红线材料模板第一批只读填报预演包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "红线材料模板第一批只读填报预演包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "红线材料缺口第一批模板": EVOLUTION_ROOT / "03数据" / "108红线材料缺口低风险补齐第一批模板包" / "红线材料缺口低风险补齐第一批模板包_最新.json",
    "红线材料一致性复核": EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线材料一致性复核与缺口补齐包" / "完全交付使用版红线材料一致性复核与缺口补齐包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "红线材料模板第一批只读填报预演包_最新.json"
PACKAGE_MD = DATA_DIR / "红线材料模板第一批只读填报预演包_最新.md"
WECOM_MD = DATA_DIR / "企业微信发送对象确认模板_只读填报预演.md"
RELOAD_MD = DATA_DIR / "服务重载操作窗口登记模板_只读填报预演.md"
N8N_MD = DATA_DIR / "n8n禁用态静态扫描二轮摘要模板_只读填报预演.md"
VIDEO_MD = DATA_DIR / "视频白名单生效前拒收口径模板_只读填报预演.md"
RULE_MD = DATA_DIR / "正式规则申请人工签收补充页模板_只读填报预演.md"
GEN_LOG = LOG_DIR / "生成红线材料模板第一批只读填报预演包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "写正式规则": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "提交申请": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def preview_items() -> list[dict[str, str]]:
    return [
        {"模板": "企业微信发送对象确认模板", "预演结论": "可填报对象、草案、范围、审计字段", "提交状态": "未提交，未发送"},
        {"模板": "服务重载操作窗口登记模板", "预演结论": "可填报端口、PID、窗口、回滚字段", "提交状态": "未提交，未重载"},
        {"模板": "n8n禁用态静态扫描二轮摘要模板", "预演结论": "可填报草案、凭据隔离、禁用态检查字段", "提交状态": "未提交，未导入未触发"},
        {"模板": "视频白名单生效前拒收口径模板", "预演结论": "可填报任务ID、白名单状态、拒收原因字段", "提交状态": "未提交，未渲染未发布"},
        {"模板": "正式规则申请人工签收补充页模板", "预演结论": "可填报规则候选、冲突扫描、回滚说明字段", "提交状态": "未提交，未写正式规则"},
    ]


def main() -> int:
    source_summary: dict[str, Any] = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("总体状态") or data.get("状态") or data.get("通过") or data.get("passed"),
            "指标": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }

    snapshot = read_json(SOURCES["日常可用版自主巡检快照"])
    regression = read_json(SOURCES["日常可用版一键只读总回归"])
    ready = (
        all(item["存在"] for item in source_summary.values())
        and snapshot.get("总体状态") == "pass"
        and snapshot.get("汇总", {}).get("失败", 0) == 0
        and regression.get("通过") is True
        and regression.get("指标", {}).get("错误数", 0) == 0
    )
    previews = preview_items()
    package = {
        "名称": "红线材料模板第一批只读填报预演包",
        "生成时间": now_text(),
        "状态": "redline_template_batch1_readonly_preview_ready" if ready else "redline_template_batch1_readonly_preview_blocked",
        "用途": "验证第一批红线材料模板可填报，但不提交、不发送、不触发、不重载、不生效。",
        "来源摘要": source_summary,
        "只读填报预演清单": previews,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "企业微信发送对象确认模板预演": str(WECOM_MD),
            "服务重载操作窗口登记模板预演": str(RELOAD_MD),
            "n8n禁用态静态扫描二轮摘要模板预演": str(N8N_MD),
            "视频白名单生效前拒收口径模板预演": str(VIDEO_MD),
            "正式规则申请人工签收补充页模板预演": str(RULE_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    preview_rows = [f"| {item['模板']} | {item['预演结论']} | {item['提交状态']} |" for item in previews]
    package_md = "\n".join([
        "# 红线材料模板第一批只读填报预演包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 用途：{package['用途']}",
        "",
        "## 来源摘要",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
        "",
        "## 只读填报预演清单",
        "| 模板 | 预演结论 | 提交状态 |",
        "| --- | --- | --- |",
        *preview_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(WECOM_MD, "\n".join(["# 企业微信发送对象确认模板只读填报预演", "", "- 确认对象：示例对象A（占位）", "- 消息草案：示例草案（占位）", "- 单次范围：仅本次预演", "- 审计记录：本地只读预演", "- 提交状态：未提交，未发送"]))
    write_text(RELOAD_MD, "\n".join(["# 服务重载操作窗口登记模板只读填报预演", "", "- 端口：19310（示例）", "- 重载前 PID：示例占位", "- 重载窗口：示例占位", "- 回滚方式：示例占位", "- 提交状态：未提交，未重载"]))
    write_text(N8N_MD, "\n".join(["# n8n禁用态静态扫描二轮摘要模板只读填报预演", "", "- 草案来源：示例草案", "- 凭据隔离：示例已隔离", "- 禁用态检查：示例通过", "- 回滚演练：示例已记录", "- 提交状态：未提交，未导入未触发"]))
    write_text(VIDEO_MD, "\n".join(["# 视频白名单生效前拒收口径模板只读填报预演", "", "- 任务ID：VF-DEMO", "- 白名单状态：未生效", "- 预检结果：示例 blocked", "- 拒收原因：白名单未生效", "- 提交状态：未提交，未渲染未发布"]))
    write_text(RULE_MD, "\n".join(["# 正式规则申请人工签收补充页模板只读填报预演", "", "- 规则候选：示例候选", "- 冲突扫描：示例待复核", "- 人工签收：示例未签收", "- 回滚说明：示例回滚说明", "- 提交状态：未提交，未写正式规则"]))
    write_json(GEN_LOG, {"名称": "生成红线材料模板第一批只读填报预演包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "预演数": len(previews), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
