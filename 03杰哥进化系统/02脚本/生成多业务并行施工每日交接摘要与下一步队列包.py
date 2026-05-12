# -*- coding: utf-8 -*-
"""生成多业务并行施工每日交接摘要与下一步队列包。

本包只汇总现有只读巡检、阶段包和阻断项，生成本地交接摘要与下一步队列；
不触发企业微信、n8n、券商、税局、财税软件、视频渲染/发布，不写正式规则。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EVOLUTION_ROOT.parent
VIDEO_ROOT = PROJECT_ROOT / "02杰哥扩展系统" / "02视频制作系统"

DATA_DIR = EVOLUTION_ROOT / "03数据" / "120多业务并行施工每日交接摘要与下一步队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "多业务并行施工每日交接摘要与下一步队列包验收"

PATROL_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
REGRESSION_JSON = EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"
VIDEO_ENV_JSON = VIDEO_ROOT / "03数据" / "真实渲染环境缺口证据压缩与安装识别清单" / "视频真实渲染环境缺口证据压缩与安装识别清单_最新.json"
TAX_RECOVERY_JSON = EVOLUTION_ROOT / "03数据" / "115税收业务对话框恢复接续包" / "税收业务对话框恢复接续包_最新.json"
GUARD_JSON = EVOLUTION_ROOT / "03数据" / "114并行自主施工分片护栏与抢占处理包" / "并行自主施工分片护栏与抢占处理包_最新.json"
REDLINE_REVIEW_JSON = EVOLUTION_ROOT / "03数据" / "113红线词命中语义复核包" / "红线词命中语义复核包_最新.json"

PACKAGE_JSON = DATA_DIR / "多业务并行施工每日交接摘要与下一步队列包_最新.json"
PACKAGE_MD = DATA_DIR / "多业务并行施工每日交接摘要与下一步队列包_最新.md"
STATUS_MD = DATA_DIR / "当前状态摘要_最新.md"
BOUNDARY_MD = DATA_DIR / "阻断项与红线边界_最新.md"
QUEUE_MD = DATA_DIR / "下一步自主施工队列_最新.md"
INDEX_MD = DATA_DIR / "最近阶段包索引_最新.md"
GENERATE_LOG = LOG_DIR / "multi-business-parallel-daily-handoff-next-queue-generate-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - defensive evidence capture
        return {"读取失败": str(exc), "路径": str(path)}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safety_flags() -> dict[str, Any]:
    return {
        "readonly_or_candidate_only": True,
        "local_file_only": True,
        "handoff_summary_only": True,
        "next_queue_only": True,
        "real_wecom_send": False,
        "connect_n8n": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "formal_tax_conclusion": False,
        "video_real_render": False,
        "video_real_publish": False,
        "write_formal_rule": False,
        "auto_promote_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_19310": False,
        "reload_19302": False,
        "external_network_call": False,
    }


def latest_dirs(root: Path, limit: int = 12) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    dirs = sorted(
        [p for p in root.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "名称": path.name,
            "路径": str(path),
            "最后修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for path in dirs[:limit]
    ]


def build_status(patrol: dict[str, Any], regression: dict[str, Any]) -> dict[str, Any]:
    summary = patrol.get("汇总", {})
    regression_passed = regression.get("通过")
    if regression_passed is None:
        regression_passed = regression.get("passed")
    return {
        "日常可用版": "已交付可用，持续只读巡检",
        "稳定交付版": "已完成基础稳定包，持续观察和交接",
        "完全交付使用版": "推进中，主要受真实渲染/发布、正式规则、外部系统接入红线约束",
        "真正自主运行版": "推进中，仍受企业微信真实发送、n8n、正式规则自动生效等红线约束",
        "最新自主巡检": {
            "路径": str(PATROL_JSON),
            "存在": PATROL_JSON.exists(),
            "总体状态": patrol.get("总体状态"),
            "总数": summary.get("总数"),
            "通过": summary.get("通过"),
            "失败": summary.get("失败"),
            "阻断检查总数": summary.get("阻断检查总数"),
            "阻断检查通过": summary.get("阻断检查通过"),
            "生成时间": patrol.get("生成时间"),
        },
        "一键只读总回归": {
            "路径": str(REGRESSION_JSON),
            "存在": REGRESSION_JSON.exists(),
            "通过": regression_passed,
            "错误数": regression.get("错误数", regression.get("error_count")),
        },
    }


def build_blockers(video_env: dict[str, Any]) -> list[dict[str, Any]]:
    video_text = json.dumps(video_env, ensure_ascii=False)
    return [
        {
            "编号": "BLOCK-VIDEO-RENDER-001",
            "业务线": "视频业务",
            "阻断项": "MoneyPrinterTurbo 本地可调用入口仍未识别",
            "当前状态": "blocked",
            "证据来源": str(VIDEO_ENV_JSON),
            "需总管确认": False,
            "允许自主继续": "仅允许继续做只读识别、证据压缩、安装清单和放行前检查。",
            "证据命中": "MoneyPrinterTurbo" in video_text,
        },
        {
            "编号": "BLOCK-VIDEO-RENDER-002",
            "业务线": "视频业务",
            "阻断项": "ImageMagick magick 未识别为可用",
            "当前状态": "blocked",
            "证据来源": str(VIDEO_ENV_JSON),
            "需总管确认": False,
            "允许自主继续": "仅允许继续做 PATH/候选路径只读识别，不执行真实渲染。",
            "证据命中": "ImageMagick" in video_text or "magick" in video_text,
        },
        {
            "编号": "BLOCK-RULE-001",
            "业务线": "智能进化闭环",
            "阻断项": "进化经验只能形成候选，不能自动转正式规则",
            "当前状态": "人工确认前 blocked",
            "证据来源": "全局红线",
            "需总管确认": True,
            "允许自主继续": "允许继续候选生成、只读验收、冲突扫描和签收草案。",
            "证据命中": True,
        },
        {
            "编号": "BLOCK-WECOM-N8N-001",
            "业务线": "企业微信公共接入层",
            "阻断项": "企业微信真实发送和 n8n 真实触发仍关闭",
            "当前状态": "人工确认前 blocked",
            "证据来源": "全局红线与巡检快照",
            "需总管确认": True,
            "允许自主继续": "允许继续本地预演、只读巡检、离线编排草案。",
            "证据命中": True,
        },
    ]


def build_queue() -> list[dict[str, Any]]:
    return [
        {
            "优先级": "P1",
            "任务": "企业微信公共接入层日常只读巡检持续化",
            "动作": "复跑只读巡检并把失败项登记为候选，不真实发送，不重载服务。",
            "写入范围": "企业微信公共接入层数据/日志或进化候选数据目录",
            "可自主执行": True,
        },
        {
            "优先级": "P1",
            "任务": "股票前台展示口径定期扫雷",
            "动作": "只读扫描推荐/交易化残留词，必要时仅修前台展示产物，不改引擎。",
            "写入范围": "股票研究系统前台展示层数据/验收日志",
            "可自主执行": True,
        },
        {
            "优先级": "P1",
            "任务": "视频真实渲染环境缺口继续压缩",
            "动作": "继续只读识别 MoneyPrinterTurbo/ImageMagick 候选路径，生成安装补齐清单，不渲染。",
            "写入范围": "视频制作系统数据/日志",
            "可自主执行": True,
        },
        {
            "优先级": "P2",
            "任务": "税收业务对话框恢复后只读回归",
            "动作": "待税收对话框恢复后复跑三条税收输入和公共路由确认，保持待复核草案口径。",
            "写入范围": "税收业务系统或进化系统候选数据目录",
            "可自主执行": True,
        },
        {
            "优先级": "P2",
            "任务": "进化候选包一致性与重复项复核",
            "动作": "只读核验候选包是否重复、是否触碰正式规则，输出签收/回滚草案。",
            "写入范围": "03杰哥进化系统",
            "可自主执行": True,
        },
        {
            "优先级": "P3",
            "任务": "多对话框并行施工冲突扫描复跑",
            "动作": "复核端口、写入范围、红线词语义误报，登记抢占风险。",
            "写入范围": "03杰哥进化系统",
            "可自主执行": True,
        },
        {
            "优先级": "P6",
            "任务": "总巡检聚合与交付快照更新",
            "动作": "只读聚合各业务验收结果，生成快照；不得改总管面板/一键接续包。",
            "写入范围": "03杰哥进化系统",
            "可自主执行": True,
        },
    ]


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return lines


def main() -> int:
    generated_at = now()
    patrol = read_json(PATROL_JSON, {})
    regression = read_json(REGRESSION_JSON, {})
    video_env = read_json(VIDEO_ENV_JSON, {})
    tax_recovery = read_json(TAX_RECOVERY_JSON, {})
    guard = read_json(GUARD_JSON, {})
    redline_review = read_json(REDLINE_REVIEW_JSON, {})

    status = build_status(patrol, regression)
    blockers = build_blockers(video_env)
    queue = build_queue()
    recent_evolution = latest_dirs(EVOLUTION_ROOT / "03数据", 16)
    recent_video = latest_dirs(VIDEO_ROOT / "03数据", 8)

    package = {
        "名称": "多业务并行施工每日交接摘要与下一步队列包",
        "生成时间": generated_at,
        "状态": "multi_business_parallel_daily_handoff_next_queue_ready",
        "数据目录": str(DATA_DIR),
        "日志目录": str(LOG_DIR),
        "当前状态摘要": status,
        "阻断项": blockers,
        "下一步自主施工队列": queue,
        "最近进化阶段包": recent_evolution,
        "最近视频阶段包": recent_video,
        "参考输入": {
            "日常巡检快照": str(PATROL_JSON),
            "一键只读总回归": str(REGRESSION_JSON),
            "视频环境缺口清单": str(VIDEO_ENV_JSON),
            "税收对话框恢复接续包": str(TAX_RECOVERY_JSON),
            "并行施工分片护栏": str(GUARD_JSON),
            "红线语义复核": str(REDLINE_REVIEW_JSON),
        },
        "参考输入存在": {
            "日常巡检快照": PATROL_JSON.exists(),
            "一键只读总回归": REGRESSION_JSON.exists(),
            "视频环境缺口清单": VIDEO_ENV_JSON.exists(),
            "税收对话框恢复接续包": TAX_RECOVERY_JSON.exists(),
            "并行施工分片护栏": GUARD_JSON.exists(),
            "红线语义复核": REDLINE_REVIEW_JSON.exists(),
        },
        "税收恢复摘要": {
            "存在": TAX_RECOVERY_JSON.exists(),
            "名称": tax_recovery.get("名称") or tax_recovery.get("name"),
        },
        "并行护栏摘要": {
            "存在": GUARD_JSON.exists(),
            "名称": guard.get("名称") or guard.get("name"),
        },
        "红线语义复核摘要": {
            "存在": REDLINE_REVIEW_JSON.exists(),
            "名称": redline_review.get("名称") or redline_review.get("name"),
        },
        **safety_flags(),
    }

    write_json(PACKAGE_JSON, package)

    status_lines = [
        "# 当前状态摘要",
        "",
        f"- 生成时间：{generated_at}",
        f"- 日常可用版：{status['日常可用版']}",
        f"- 稳定交付版：{status['稳定交付版']}",
        f"- 最新自主巡检：{status['最新自主巡检']['总体状态']}，{status['最新自主巡检']['通过']}/{status['最新自主巡检']['总数']} 通过，失败 {status['最新自主巡检']['失败']}",
        f"- 一键只读总回归：通过={status['一键只读总回归']['通过']}，错误数={status['一键只读总回归']['错误数']}",
        "",
        "## 交付判断",
        "",
        "- 日常可用版和稳定交付版继续维持可用状态；下一步重点是运行期观察、证据留存、视频真实渲染环境补齐和正式规则人工签收前置材料。",
        "- 完全交付和真正自主运行仍被真实外发、n8n、正式规则、视频真实渲染/发布等红线压住，不能用候选材料冒充已放行能力。",
        "",
    ]
    boundary_lines = [
        "# 阻断项与红线边界",
        "",
        f"- 生成时间：{generated_at}",
        "- 本包不解除任何红线，不登记服务重载，不写正式规则。",
        "",
        *md_table(blockers, ["编号", "业务线", "阻断项", "当前状态", "需总管确认"]),
        "",
        "## 红线确认",
        "",
        "- real_wecom_send=false",
        "- connect_n8n=false",
        "- trigger_n8n=false",
        "- broker_connection=false",
        "- trade_order=false",
        "- tax_bureau_login=false",
        "- finance_tax_software_connection=false",
        "- video_real_render=false",
        "- video_real_publish=false",
        "- write_formal_rule=false",
        "- reload_19310=false",
        "- reload_19302=false",
        "",
    ]
    queue_lines = [
        "# 下一步自主施工队列",
        "",
        f"- 生成时间：{generated_at}",
        "- 执行原则：优先 P1/P2，只做低风险、只读、候选、验收脚本和状态包。",
        "",
        *md_table(queue, ["优先级", "任务", "动作", "可自主执行"]),
        "",
    ]
    index_lines = [
        "# 最近阶段包索引",
        "",
        f"- 生成时间：{generated_at}",
        "",
        "## 进化系统最近阶段包",
        "",
        *md_table(recent_evolution, ["名称", "最后修改时间", "路径"]),
        "",
        "## 视频系统最近阶段包",
        "",
        *md_table(recent_video, ["名称", "最后修改时间", "路径"]),
        "",
    ]
    package_lines = [
        "# 多业务并行施工每日交接摘要与下一步队列包",
        "",
        f"- 生成时间：{generated_at}",
        "- 状态：multi_business_parallel_daily_handoff_next_queue_ready",
        f"- 数据目录：{DATA_DIR}",
        "- 结论：只读交接摘要与下一步队列已生成，未触发任何真实外部动作。",
        "",
        "## 产物",
        "",
        f"- 当前状态摘要：{STATUS_MD}",
        f"- 阻断项与红线边界：{BOUNDARY_MD}",
        f"- 下一步自主施工队列：{QUEUE_MD}",
        f"- 最近阶段包索引：{INDEX_MD}",
        "",
    ]

    write_text(STATUS_MD, "\n".join(status_lines))
    write_text(BOUNDARY_MD, "\n".join(boundary_lines))
    write_text(QUEUE_MD, "\n".join(queue_lines))
    write_text(INDEX_MD, "\n".join(index_lines))
    write_text(PACKAGE_MD, "\n".join(package_lines))

    package["产物"] = {
        "package_json": str(PACKAGE_JSON),
        "package_md": str(PACKAGE_MD),
        "status_md": str(STATUS_MD),
        "boundary_md": str(BOUNDARY_MD),
        "queue_md": str(QUEUE_MD),
        "index_md": str(INDEX_MD),
    }
    package["产物哈希"] = {name: sha256_file(Path(path)) for name, path in package["产物"].items()}
    write_json(PACKAGE_JSON, package)

    log = {
        "名称": "多业务并行施工每日交接摘要与下一步队列包生成日志",
        "生成时间": generated_at,
        "通过": True,
        "数据目录": str(DATA_DIR),
        "产物数量": len(package["产物"]),
        "队列数量": len(queue),
        "阻断项数量": len(blockers),
        **safety_flags(),
    }
    write_json(GENERATE_LOG, log)
    print(json.dumps({"通过": True, "数据目录": str(DATA_DIR), "队列数量": len(queue)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
