# -*- coding: utf-8 -*-
"""
名称：生成旧资料归集提炼与清理报告.py
作用：汇总旧资料提炼后的清理状态，确认旧路径资料不再作为当前搭建输入。
触发方式：python 生成旧资料归集提炼与清理报告.py
安全边界：只读检查并写运行状态报告；不删除、不停止、不重启、不触发n8n、不交易。
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "旧资料归集提炼与清理_最新.json"
REPORT_MD = OUT_DIR / "旧资料归集提炼与清理_最新.md"
RULE_PATH = MANAGER / "01配置" / "旧资料归集清理规则.json"
SUMMARY_DOC = MANAGER / "07文档" / "旧资料经验提炼_20260505.md"
LEGACY_ROOT = Path("D:/01杰哥智能系统")
FORMAL_ROOT = ROOT
FORMAL_CORE = ROOT / "01杰哥智能系统"
OLD_MARKERS = ("D:\\01杰哥智能系统", "/mnt/d/01杰哥智能系统")

REMOVED_PATHS = [
    MANAGER / "07文档" / "历史经验",
    MANAGER / "07文档" / "旧系统退役",
    MANAGER / "07文档" / "D盘瘦身",
    ROOT / "01杰哥智能系统" / "07文档" / "基础设施规范化专项",
    MANAGER / "07文档" / "家底盘点报告草案.md",
    MANAGER / "02脚本" / "生成D盘瘦身前只读审计报告.py",
    MANAGER / "02脚本" / "生成D盘旧系统退役候选清单.py",
    MANAGER / "02脚本" / "生成旧系统依赖断开与备份校验报告.py",
    MANAGER / "02脚本" / "生成旧系统借鉴吸收审计包.ps1",
    ROOT / "01杰哥智能系统" / "02脚本" / "补充迁移老基础Ollama模型到新系统.ps1",
]

CURRENT_DOCS = [
    ROOT / "01杰哥智能系统" / "07文档" / "设计纲领" / "智能系统设计纲领与施工计划v3.1.md",
    MANAGER / "07文档" / "当前施工面板.md",
    MANAGER / "07文档" / "文档总索引.md",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return {"退出码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def docker_old_mount_hits() -> list[str]:
    names = command(["docker", "ps", "-a", "--format", "{{.Names}}"])
    if names["退出码"] != 0:
        return [f"Docker 查询失败：{names['标准错误']}"]
    hits: list[str] = []
    for name in names["标准输出"].splitlines():
        name = name.strip()
        if not name:
            continue
        inspect = command(["docker", "inspect", name, "--format", "{{json .Mounts}}"])
        if inspect["退出码"] != 0:
            continue
        text = inspect["标准输出"]
        if any(marker in text for marker in OLD_MARKERS):
            hits.append(f"{name}: {text}")
    return hits


def current_doc_hits() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    allowed_phrases = ("已禁用", "已清理", "不得作为", "不再使用", "残留已清理")
    for path in CURRENT_DOCS:
        text = read_text(path)
        for marker in OLD_MARKERS:
            if marker in text and not any(phrase in text for phrase in allowed_phrases):
                hits.append({"文件": str(path), "命中": marker})
    return hits


def main() -> int:
    removed_status = [{"路径": str(path), "仍存在": path.exists()} for path in REMOVED_PATHS]
    docker_hits = docker_old_mount_hits()
    doc_hits = current_doc_hits()
    summary_text = read_text(SUMMARY_DOC)
    rule_text = read_text(RULE_PATH)

    checks = [
        {"检查项": "旧资料提炼文档存在", "通过": SUMMARY_DOC.exists(), "说明": str(SUMMARY_DOC)},
        {"检查项": "旧资料清理规则存在", "通过": RULE_PATH.exists(), "说明": str(RULE_PATH)},
        {"检查项": "提炼文档声明旧路径已禁用", "通过": "已禁用" in summary_text and "不得作为运行路径" in summary_text, "说明": ""},
        {"检查项": "规则声明禁止触发外部动作", "通过": "不触发n8n" in rule_text and "不自动交易" in rule_text, "说明": ""},
        {"检查项": "旧资料源目录和旧脚本已删除", "通过": not any(item["仍存在"] for item in removed_status), "说明": ""},
        {"检查项": "D盘根目录旧路径不存在", "通过": not LEGACY_ROOT.exists(), "说明": str(LEGACY_ROOT)},
        {"检查项": "正式系统根目录仍存在", "通过": FORMAL_ROOT.exists() and FORMAL_CORE.exists(), "说明": str(FORMAL_ROOT)},
        {"检查项": "Docker 元数据无旧路径挂载", "通过": not docker_hits, "说明": "\n".join(docker_hits)},
        {"检查项": "当前设计和索引无旧路径误导口径", "通过": not doc_hits, "说明": json.dumps(doc_hits, ensure_ascii=False)},
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "旧资料归集提炼与清理报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "提炼文档": str(SUMMARY_DOC),
        "规则文件": str(RULE_PATH),
        "旧资料源状态": removed_status,
        "Docker旧挂载命中": docker_hits,
        "当前文档误导命中": doc_hits,
        "安全边界": {
            "删除正式系统目录": False,
            "停止运行中v3容器": False,
            "删除镜像": False,
            "删除Docker卷": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "检查结果": checks,
    }

    lines = [
        "# 旧资料归集提炼与清理报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        f"- 提炼文档：`{SUMMARY_DOC}`",
        f"- 规则文件：`{RULE_PATH}`",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "未停止运行中 v3 容器，未删除镜像，未删除 Docker 卷，未触发 n8n，未发送企业微信，未写正式库，未调用券商接口，未自动交易。",
    ])
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
