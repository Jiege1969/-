# -*- coding: utf-8 -*-
"""
名称：生成股票验收报告知识库问答样本.py
作用：把股票系统既有验收报告接入知识库原始文档区，重建本地全文索引，并生成四个可追溯问答样本。
触发方式：python 生成股票验收报告知识库问答样本.py
依赖：Python 标准库；生成知识库全文索引.py；股票系统既有验收报告。
所属系统：01杰哥智能系统/知识库
安全边界：只读股票系统验收报告；只写 01 智能系统知识库样本、索引、备份和日志；不修改股票脚本、不发企业微信、不触发 n8n、不调用券商接口、不自动交易。
标识：knowledge-stock-acceptance-report-qa-sample-generate
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path("D:/杰哥智能化系统")
SMART_ROOT = SYSTEM_ROOT / "01杰哥智能系统"
STOCK_ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "01股票研究系统"
KNOWLEDGE_ROOT = SMART_ROOT / "03数据" / "知识库"
RAW_DIR = KNOWLEDGE_ROOT / "01原始文档"
INDEX_PATH = KNOWLEDGE_ROOT / "03索引清单" / "知识库全文索引_最新.json"
OUTPUT_DIR = KNOWLEDGE_ROOT / "12股票验收报告问答样本"
LOG_DIR = SMART_ROOT / "04日志" / "知识库"
BACKUP_ROOT = SMART_ROOT / "05备份" / "知识库股票验收报告问答样本"
TARGET_DIR = RAW_DIR / "股票验收报告问答样本"
INDEX_SCRIPT = SMART_ROOT / "02脚本" / "知识库" / "生成知识库全文索引.py"


EVIDENCE_FILES: dict[str, Path] = {
    "220口径报告_json": STOCK_ROOT / "03数据" / "220价位成交额条件口径" / "股票价位成交额条件口径预览_最新.json",
    "220口径报告_md": STOCK_ROOT / "03数据" / "220价位成交额条件口径" / "股票价位成交额条件口径预览_最新.md",
    "220口径验收_json": STOCK_ROOT / "03数据" / "220价位成交额条件口径" / "股票价位成交额条件口径预览验收_最新.json",
    "221短文口径验收_json": STOCK_ROOT / "03数据" / "221微信短文条件口径影子预览" / "股票微信短文条件口径影子预览验收_最新.json",
    "230正式成交额对照验收_json": STOCK_ROOT / "03数据" / "230微信短文正式生成器正式成交额口径对照包" / "微信短文正式生成器正式成交额口径对照包验收_最新.json",
    "231短回复实跑验收_json": STOCK_ROOT / "03数据" / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json",
    "233历史K线刷新报告_json": STOCK_ROOT / "03数据" / "233历史K线东方财富增强受控刷新" / "重点关注池历史K线东方财富增强受控刷新执行报告_最新.json",
    "233历史K线刷新验收_json": STOCK_ROOT / "03数据" / "233历史K线东方财富增强受控刷新" / "重点关注池历史K线东方财富增强受控刷新验收_最新.json",
    "234模板准入回滚方案_json": STOCK_ROOT / "03数据" / "234企业微信短回复v21正式模板替换准入" / "企业微信短回复v21正式模板替换准入与回滚方案_最新.json",
    "234模板准入回滚验收_json": STOCK_ROOT / "03数据" / "234企业微信短回复v21正式模板替换准入" / "企业微信短回复v21正式模板替换准入与回滚方案验收_最新.json",
    "235模板dry_run验收_json": STOCK_ROOT / "03数据" / "235企业微信短回复v21模板dry_run" / "企业微信单股短回复v21模板dry_run实跑输出验收_最新.json",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(label: str, path: Path) -> str:
    clean_label = re.sub(r"[^\w\u4e00-\u9fff]+", "_", label).strip("_")
    return f"{clean_label}_{path.name}"


def backup_existing(timestamp: str) -> dict[str, Any]:
    backup_dir = BACKUP_ROOT / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "备份目录": str(backup_dir),
        "目标样本目录备份": "",
        "最新索引备份": "",
        "说明": "复制股票验收报告进入知识库前创建备份；若需要回滚，可恢复本目录中的样本目录和最新索引。",
    }
    if TARGET_DIR.exists():
        target_backup = backup_dir / "股票验收报告问答样本_刷新前备份"
        shutil.copytree(TARGET_DIR, target_backup)
        result["目标样本目录备份"] = str(target_backup)
    if INDEX_PATH.exists():
        index_backup = backup_dir / INDEX_PATH.name
        shutil.copy2(INDEX_PATH, index_backup)
        result["最新索引备份"] = str(index_backup)
    return result


def copy_evidence_files() -> dict[str, dict[str, Any]]:
    if TARGET_DIR.exists():
        resolved_target = TARGET_DIR.resolve()
        resolved_raw = RAW_DIR.resolve()
        if resolved_raw not in resolved_target.parents:
            raise RuntimeError(f"拒绝清理非知识库原始文档目录：{resolved_target}")
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    copied: dict[str, dict[str, Any]] = {}
    for label, source in EVIDENCE_FILES.items():
        target = TARGET_DIR / safe_name(label, source)
        if not source.exists():
            copied[label] = {"源文件": str(source), "存在": False, "知识库文件": str(target)}
            continue
        shutil.copy2(source, target)
        copied[label] = {
            "源文件": str(source),
            "存在": True,
            "知识库文件": str(target),
            "sha256": sha256(source),
        }
    return copied


def rebuild_index() -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(INDEX_SCRIPT)],
        cwd=str(INDEX_SCRIPT.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env=env,
    )
    index = load_json(INDEX_PATH, {})
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "索引文件": str(INDEX_PATH),
        "文档数量": index.get("文档数量"),
        "分块数量": index.get("分块数量"),
    }


def compact_excerpt(content: str, keywords: list[str], max_chars: int = 180) -> str:
    clean = re.sub(r"\s+", " ", content).strip()
    if not clean:
        return ""
    pos = -1
    for keyword in keywords:
        pos = clean.find(keyword)
        if pos >= 0:
            break
    if pos < 0:
        return clean[:max_chars]
    start = max(0, pos - 50)
    return clean[start : start + max_chars]


def find_chunk(index: dict[str, Any], kb_file: str, keywords: list[str]) -> dict[str, Any]:
    candidates = [chunk for chunk in index.get("分块", []) if str(chunk.get("路径")) == kb_file]
    if not candidates:
        return {"来源文件": kb_file, "来源文件存在": Path(kb_file).exists(), "分块序号": 0, "命中词": [], "证据摘录": ""}
    scored = []
    for chunk in candidates:
        content = str(chunk.get("内容", ""))
        hits = [keyword for keyword in keywords if keyword in content]
        scored.append((sum(len(item) for item in hits), len(hits), chunk, hits))
    _, _, best, hits = sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)[0]
    return {
        "来源文件": kb_file,
        "来源文件存在": Path(kb_file).exists(),
        "分块序号": int(best.get("分块序号", 0) or 0),
        "命中词": hits,
        "证据摘录": compact_excerpt(str(best.get("内容", "")), hits or keywords),
    }


def source_ref(
    label: str,
    copied: dict[str, dict[str, Any]],
    index: dict[str, Any],
    field: str,
    keywords: list[str],
) -> dict[str, Any]:
    info = copied[label]
    chunk = find_chunk(index, str(info["知识库文件"]), keywords)
    return {
        "来源标签": label,
        "原始股票验收报告": info["源文件"],
        "知识库来源文件": info["知识库文件"],
        "来源字段或章节": field,
        "来源文件存在": bool(info.get("存在")) and chunk.get("来源文件存在") is True,
        "分块序号": chunk["分块序号"],
        "命中词": chunk["命中词"],
        "证据摘录": chunk["证据摘录"],
    }


def build_samples(copied: dict[str, dict[str, Any]], index: dict[str, Any]) -> list[dict[str, Any]]:
    r220 = load_json(EVIDENCE_FILES["220口径报告_json"], {})
    v220 = load_json(EVIDENCE_FILES["220口径验收_json"], {})
    v230 = load_json(EVIDENCE_FILES["230正式成交额对照验收_json"], {})
    r233 = load_json(EVIDENCE_FILES["233历史K线刷新报告_json"], {})
    v233 = load_json(EVIDENCE_FILES["233历史K线刷新验收_json"], {})
    r234 = load_json(EVIDENCE_FILES["234模板准入回滚方案_json"], {})
    v234 = load_json(EVIDENCE_FILES["234模板准入回滚验收_json"], {})
    v235 = load_json(EVIDENCE_FILES["235模板dry_run验收_json"], {})
    v231 = load_json(EVIDENCE_FILES["231短回复实跑验收_json"], {})

    baseline = r220.get("基准数据", {})
    before = r233.get("刷新前统计", {})
    after = r233.get("刷新后统计", {})

    samples = [
        {
            "问题": "新易盛成交额阈值为什么这样算？",
            "回答结论": (
                "新易盛阈值按截至昨日的近5日东方财富历史K线正式成交额计算：近5日均额为"
                f"{baseline.get('截至昨日近5日均额')}，观察降级阈值取 1.2 倍为{baseline.get('截至昨日近5日均额1.2倍')}。"
                "转强条件用近5日均额，观察条件中的下跌日放大成交额用 1.2 倍阈值；220 验收和 230 对照验收均通过。"
            ),
            "来源": [
                source_ref("220口径报告_json", copied, index, "基准数据/近5日明细/条件口径", ["新易盛", "截至昨日近5日均额", "301.02亿元", "东方财富历史K线正式成交额"]),
                source_ref("220口径验收_json", copied, index, "结论/通过数量/失败数量", ["结论", "通过数量", "失败数量", "17"]),
                source_ref("230正式成交额对照验收_json", copied, index, "正式成交额口径对照验收", ["正式成交额", "通过数量", "失败数量"]),
            ],
            "验收状态": f"220 验收结论={v220.get('结论')}，通过={v220.get('通过数量')}，失败={v220.get('失败数量')}；230 验收结论={v230.get('结论')}，通过={v230.get('通过数量')}，失败={v230.get('失败数量')}。",
            "风险边界": "这是研究短文口径和复盘阈值，不是交易指令；本样本不调用券商接口、不自动交易。",
        },
        {
            "问题": "历史 K 线数据来源是什么？",
            "回答结论": (
                "历史 K 线最新快照已完成东方财富增强受控刷新。刷新前统计为"
                f"{before.get('股票数量')}只、东方财富{before.get('东方财富数量')}、腾讯{before.get('腾讯数量')}、正式成交额{before.get('含正式成交额数量')}；"
                f"刷新后为{after.get('股票数量')}只、东方财富{after.get('东方财富数量')}、腾讯{after.get('腾讯数量')}、正式成交额{after.get('含正式成交额数量')}。"
                "因此当前问答样本采用东方财富历史 K 线正式成交额口径。"
            ),
            "来源": [
                source_ref("233历史K线刷新报告_json", copied, index, "刷新前统计/刷新后统计/最新快照/备份文件", ["东方财富数量", "腾讯数量", "含正式成交额数量", "刷新后统计"]),
                source_ref("233历史K线刷新验收_json", copied, index, "结论/通过数量/失败数量", ["结论", "通过数量", "失败数量", "11"]),
            ],
            "验收状态": f"233 验收结论={v233.get('结论')}，通过={v233.get('通过数量')}，失败={v233.get('失败数量')}。",
            "风险边界": "本回答只说明已验收的数据来源；不会重新刷新历史 K 线，也不会覆盖股票系统快照。",
        },
        {
            "问题": "企业微信短回复是否会真实发送？",
            "回答结论": (
                "本批 220-235 口径、模板和 dry-run 验收链路不会真实发送企业微信。234 方案明确正式默认切换和真实发送仍需人工确认；"
                "235 dry-run 验收记录正式草稿实际动作全部为 False，包括触发 n8n、发送企业微信、写正式库、调用券商接口和自动交易。"
            ),
            "来源": [
                source_ref("234模板准入回滚方案_json", copied, index, "当前结论/切换建议/安全边界", ["真实发送仍需人工确认", "发送企业微信", "触发n8n"]),
                source_ref("235模板dry_run验收_json", copied, index, "检查结果/安全边界", ["正式草稿实际动作全部为False", "发送企业微信", "触发n8n", "自动交易"]),
                source_ref("231短回复实跑验收_json", copied, index, "shadow_v21_dry_run 实跑输出验收", ["dry_run", "发送企业微信", "触发n8n"]),
            ],
            "验收状态": f"235 验收结论={v235.get('结论')}，通过={v235.get('通过数量')}，失败={v235.get('失败数量')}；231 实跑验收结论={v231.get('结论')}。",
            "风险边界": "本样本不发企业微信真实消息，不触发 n8n；如未来进入真实灰度发送，必须另做人工确认、发送计数和回滚验收。",
        },
        {
            "问题": "失败时如何回滚？",
            "回答结论": (
                "回滚分三层：历史 K 线异常时，把 233 记录的刷新前备份复制回历史行情最新快照；模板切换异常时，关闭新增显式开关或恢复短回复生成器；"
                "数据侧保留旧的 24 企业微信短回复产物，发送侧因本阶段未真实发送，未来灰度前必须保留发送日志、response_url 指纹和人工停止开关。"
            ),
            "来源": [
                source_ref("233历史K线刷新报告_json", copied, index, "回滚方式/备份文件", ["回滚方式", "备份文件", "复制回"]),
                source_ref("234模板准入回滚方案_json", copied, index, "回滚方案", ["代码回滚", "数据回滚", "历史K线回滚", "发送回滚"]),
                source_ref("234模板准入回滚验收_json", copied, index, "回滚方案验收检查项", ["回滚", "通过数量", "失败数量"]),
            ],
            "验收状态": f"234 回滚方案验收结论={v234.get('结论')}，通过={v234.get('通过数量')}，失败={v234.get('失败数量')}；233 验收结论={v233.get('结论')}。",
            "风险边界": "本样本只给出回滚依据，不执行回滚、不删除确认令、不复制股票备份、不改正式链路。",
        },
    ]
    for sample in samples:
        sample["可追溯"] = all(
            ref.get("来源文件存在") is True and ref.get("分块序号", 0) > 0 and ref.get("证据摘录")
            for ref in sample["来源"]
        )
        sample["输出格式"] = ["回答结论", "来源文件", "分块序号", "证据摘录", "验收状态", "风险边界"]
    return samples


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票验收报告知识库问答样本",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['总体状态']}",
        f"- 问题数量：{report['汇总']['问题数量']}",
        f"- 可追溯问题数量：{report['汇总']['可追溯问题数量']}",
        f"- 知识库样本目录：{report['复制入库批次']['目标目录']}",
        f"- 备份目录：{report['备份']['备份目录']}",
        "",
        "## 四问样本",
        "",
    ]
    for sample in report["问答样本"]:
        lines.append(f"### {sample['问题']}")
        lines.append("")
        lines.append(f"- 回答结论：{sample['回答结论']}")
        lines.append(f"- 验收状态：{sample['验收状态']}")
        lines.append(f"- 风险边界：{sample['风险边界']}")
        lines.append("- 来源：")
        for ref in sample["来源"]:
            lines.append(f"  - {ref['来源标签']}：{ref['知识库来源文件']}；分块 {ref['分块序号']}")
            lines.append(f"    - 原始股票验收报告：{ref['原始股票验收报告']}")
            lines.append(f"    - 来源字段或章节：{ref['来源字段或章节']}")
            lines.append(f"    - 证据摘录：{ref['证据摘录']}")
        lines.append(f"- 是否可追溯：{sample['可追溯']}")
        lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    backup = backup_existing(timestamp)
    copied = copy_evidence_files()
    index_result = rebuild_index()
    index = load_json(INDEX_PATH, {})
    samples = build_samples(copied, index)
    traceable_count = sum(1 for item in samples if item["可追溯"])
    all_files_exist = all(info.get("存在") for info in copied.values())
    status = "通过" if all_files_exist and traceable_count == len(samples) and index_result["returncode"] == 0 else "待复核"
    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "knowledge-stock-acceptance-report-qa-sample",
        "所属系统": "01杰哥智能系统/知识库",
        "汇总": {
            "总体状态": status,
            "问题数量": len(samples),
            "可追溯问题数量": traceable_count,
            "来源文件均存在": all_files_exist,
            "索引重建成功": index_result["returncode"] == 0,
            "正式知识库样本批次已备份": bool(backup.get("备份目录")),
            "企业微信真实发送": False,
            "触发n8n": False,
            "修改股票脚本": False,
        },
        "复制入库批次": {"目标目录": str(TARGET_DIR), "文件": copied},
        "备份": backup,
        "索引重建": index_result,
        "问答样本": samples,
        "验收方式": [
            "每个回答必须给出回答结论、来源文件、分块序号、证据摘录、验收状态和风险边界。",
            "来源文件必须是 01 智能系统知识库内真实存在的复制件，同时保留原始股票验收报告路径。",
            "没有来源文件或没有分块命中的问题不得判定为通过。",
            "本样本只允许本地复制、索引和报告生成，不允许真实发送企业微信或触发 n8n。",
        ],
        "多助手分工口径": {
            "股票助手": "负责股票研究分析、数据刷新、短回复草稿和股票侧验收证据生产；不把研究内容解释成交易指令。",
            "总管助手": "负责读取阶段性交付状态和进度口径；不直接接管股票问答细节。",
            "知识库助手": "负责从已入库验收报告中检索、回答并给出来源文件、分块号和证据摘录。",
        },
        "剩余有效工时估算": {
            "知识库可追溯问答": "2-4 小时：继续扩展样本、补充路由层调用验收、整理失败拒答用例。",
            "多助手路由接入": "4-8 小时：接入企业微信本地桥接前的 dry-run 路由验收，不真实发送。",
            "01智能系统整体验收": "10-18 小时：扩容更多正式资料、补充权限门禁、形成最终验收总包。",
        },
        "阻塞项": [
            "真实企业微信入口仍需人工授权；本批只验本地知识库回答。",
            "n8n 触发仍保持关闭，需要单独授权和回滚演练。",
            "知识库样本已纳入全文索引，但向量库、正式数据库和外部发送链路未启用。",
        ],
        "安全边界": {
            "修改股票系统脚本": False,
            "修改总管进度标准文件": False,
            "修改进化系统规则固化代码": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式向量库": False,
            "写正式数据库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_json = OUTPUT_DIR / "股票验收报告知识库问答样本_最新.json"
    latest_json = OUTPUT_DIR / "股票验收报告知识库问答样本_最新.json"
    output_md = OUTPUT_DIR / "股票验收报告知识库问答样本_最新.md"
    latest_md = OUTPUT_DIR / "股票验收报告知识库问答样本_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_json(LOG_DIR / "stock-acceptance-report-qa-sample-generate-最新.json", report)
    print(json.dumps({"状态": status, "问题数量": len(samples), "可追溯": traceable_count, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
