# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
BASE = ROOT / "03杰哥进化系统" / "04系统复盘"
OUT_DIR = BASE / "03数据"
LOG_DIR = BASE / "04日志"
RULE_PATH = BASE / "01配置" / "各业务输出质量周报规则.json"


SUBSYSTEMS = [
    {
        "name": "总管系统",
        "paths": [ROOT / "00杰哥系统总管" / "03数据", ROOT / "00杰哥系统总管" / "04日志"],
    },
    {
        "name": "企业微信公共接入层",
        "paths": [ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置"],
    },
    {
        "name": "股票研究系统",
        "paths": [ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据", ROOT / "02杰哥扩展系统" / "01股票研究系统" / "04日志"],
    },
    {
        "name": "税收业务系统",
        "paths": [ROOT / "02杰哥扩展系统" / "05税收业务系统" / "03数据", ROOT / "02杰哥扩展系统" / "05税收业务系统" / "04日志"],
    },
    {
        "name": "视频制作系统",
        "paths": [ROOT / "02杰哥扩展系统" / "02视频制作系统" / "03数据", ROOT / "02杰哥扩展系统" / "02视频制作系统" / "04日志"],
    },
    {
        "name": "本职工作系统",
        "paths": [ROOT / "02杰哥扩展系统" / "03本职工作系统"],
    },
    {
        "name": "内容处理系统",
        "paths": [ROOT / "02杰哥扩展系统" / "04内容处理系统"],
    },
    {
        "name": "知识库系统",
        "paths": [ROOT / "02杰哥扩展系统" / "07知识库系统", ROOT / "02杰哥扩展系统" / "07知识库可追溯问答框"],
    },
    {
        "name": "进化系统",
        "paths": [ROOT / "03杰哥进化系统" / "03数据", ROOT / "03杰哥进化系统" / "04日志"],
    },
]


def load_rule() -> dict:
    return json.loads(RULE_PATH.read_text(encoding="utf-8"))


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def default_week(today: datetime) -> tuple[datetime, datetime]:
    # 上周一到上周日。
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(days=7)
    end = this_monday - timedelta(seconds=1)
    return start.replace(hour=0, minute=0, second=0, microsecond=0), end


def iter_recent_files(paths: list[Path], start: datetime, end: datetime):
    for base in paths:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".jsonl", ".log", ".txt"}:
                continue
            modified = datetime.fromtimestamp(path.stat().st_mtime)
            if start <= modified <= end:
                yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def contains_any(text: str, keywords: list[str]) -> list[str]:
    return [k for k in keywords if k in text]


def short_excerpt(text: str, keywords: list[str]) -> str:
    for keyword in keywords:
        idx = text.find(keyword)
        if idx >= 0:
            start = max(0, idx - 36)
            end = min(len(text), idx + 80)
            return text[start:end].replace("\n", " ").strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="YYYY-MM-DD，默认上周一")
    parser.add_argument("--end", help="YYYY-MM-DD，默认上周日")
    args = parser.parse_args()

    now = datetime.now()
    if args.start and args.end:
        start = parse_date(args.start)
        end = parse_date(args.end).replace(hour=23, minute=59, second=59)
    else:
        start, end = default_week(now)

    rule = load_rule()
    positive_keywords = rule["反馈识别口径"]["正向关键词"]
    negative_keywords = rule["反馈识别口径"]["负向关键词"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    for subsystem in SUBSYSTEMS:
        files = list(iter_recent_files(subsystem["paths"], start, end))
        trigger_count = len(files)
        positive = 0
        negative = 0
        negative_excerpts = []
        for path in files:
            text = read_text(path)
            # 验收类 pass 容易造成虚高，第一版只把用户语义正向词作为轻量线索。
            if contains_any(text, positive_keywords) and ("用户" in text or "反馈" in text or "回传" in text):
                positive += 1
            neg_hits = contains_any(text, negative_keywords)
            if neg_hits:
                negative += 1
                if len(negative_excerpts) < 3:
                    negative_excerpts.append(short_excerpt(text, neg_hits))
        rows.append(
            {
                "子系统": subsystem["name"],
                "触发次数": trigger_count,
                "用户正向反馈次数": positive,
                "用户纠正负向反馈次数": negative,
                "主要负向反馈摘录": negative_excerpts,
            }
        )

    focus = max(rows, key=lambda x: (x["用户纠正负向反馈次数"], x["触发次数"]))
    suggestion = f"本周优先改进建议：优先复核「{focus['子系统']}」的输出质量和反馈闭环。"
    if focus["用户纠正负向反馈次数"] == 0:
        suggestion = "本周优先改进建议：当前负向反馈线索不足，优先补齐企业微信真实反馈入账口径，避免只看验收 pass。"

    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "统计窗口": {"开始": start.strftime("%Y-%m-%d %H:%M:%S"), "结束": end.strftime("%Y-%m-%d %H:%M:%S")},
        "口径": "只读扫描本地数据和日志的文本线索；不等同于真实用户行为全量统计。",
        "结果": rows,
        "本周建议": suggestion,
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否写正式规则": False,
            "是否重载服务": False,
        },
    }

    stamp = now.strftime("%Y%m%d_%H%M%S")
    json_latest = OUT_DIR / "各业务输出质量周报_最新.json"
    md_latest = OUT_DIR / "各业务输出质量周报_最新.md"
    json_stamp = OUT_DIR / f"各业务输出质量周报_{stamp}.json"
    md_stamp = OUT_DIR / f"各业务输出质量周报_{stamp}.md"
    log_path = LOG_DIR / f"各业务输出质量周报生成日志_{stamp}.json"

    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    json_latest.write_text(json_text, encoding="utf-8")
    json_stamp.write_text(json_text, encoding="utf-8")

    lines = [
        "# 杰哥智能系统各业务输出质量周报",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 统计窗口：{report['统计窗口']['开始']} 至 {report['统计窗口']['结束']}",
        "- 统计口径：只读扫描本地数据和日志的文本线索；不等同于真实用户行为全量统计。",
        "",
        "| 子系统 | 触发次数 | 用户正向反馈次数 | 用户纠正/负向反馈次数 | 主要负向反馈摘录 |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        excerpts = "<br>".join(row["主要负向反馈摘录"]) if row["主要负向反馈摘录"] else "无"
        lines.append(
            f"| {row['子系统']} | {row['触发次数']} | {row['用户正向反馈次数']} | {row['用户纠正负向反馈次数']} | {excerpts} |"
        )
    lines.extend(
        [
            "",
            f"**{suggestion}**",
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未真实发送企业微信。",
            "- 未写正式规则。",
            "- 未重载 19310/19302。",
        ]
    )
    md_text = "\n".join(lines) + "\n"
    md_latest.write_text(md_text, encoding="utf-8")
    md_stamp.write_text(md_text, encoding="utf-8")
    log_path.write_text(json.dumps({"status": "pass", "json": str(json_latest), "md": str(md_latest)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(md_latest))
    print(str(json_latest))


if __name__ == "__main__":
    main()
