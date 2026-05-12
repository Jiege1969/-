# -*- coding: utf-8 -*-
"""
名称：验证旧资料归集提炼与清理报告.py
作用：验收旧资料已提炼、旧源文件已删除、旧路径不会继续误导当前搭建。
触发方式：python 验证旧资料归集提炼与清理报告.py
安全边界：只读检查并写验收报告；不删除、不停止、不重启、不触发n8n、不交易。
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
VALIDATION_JSON = OUT_DIR / "旧资料归集提炼与清理验收_最新.json"
VALIDATION_MD = OUT_DIR / "旧资料归集提炼与清理验收_最新.md"
SUMMARY_DOC = MANAGER / "07文档" / "旧资料经验提炼_20260505.md"
RULE_PATH = MANAGER / "01配置" / "旧资料归集清理规则.json"
LEGACY_ROOT = Path("D:/01杰哥智能系统")
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def current_doc_bad_hits() -> list[str]:
    hits: list[str] = []
    forbidden_pairs = [
        "D:\\01杰哥智能系统\\WSL2",
        "00杰哥系统总管\\07文档\\历史经验",
    ]
    for path in CURRENT_DOCS:
        text = read_text(path)
        for token in forbidden_pairs:
            if token in text:
                hits.append(f"{path}: {token}")
    return hits


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def main() -> int:
    report = load_json(REPORT_JSON)
    report_md = read_text(REPORT_MD)
    summary = read_text(SUMMARY_DOC)
    rule = read_text(RULE_PATH)
    old_mounts = docker_old_mount_hits()
    removed_existing = [str(path) for path in REMOVED_PATHS if path.exists()]
    doc_bad_hits = current_doc_bad_hits()
    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "归集清理报告存在", str(OUT_DIR)),
        check(report.get("结论") == "通过", "归集清理报告结论通过", report.get("结论", "")),
        check(SUMMARY_DOC.exists() and "旧资料清理后的唯一学习材料" in summary, "提炼文档存在且声明唯一学习材料", str(SUMMARY_DOC)),
        check(RULE_PATH.exists() and "已禁用路径" in rule, "规则文件存在且声明已禁用路径", str(RULE_PATH)),
        check(not removed_existing, "旧资料源目录和旧脚本已删除", "\n".join(removed_existing)),
        check(not LEGACY_ROOT.exists(), "D盘根目录旧路径不存在", str(LEGACY_ROOT)),
        check(FORMAL_CORE.exists(), "正式01智能系统仍存在", str(FORMAL_CORE)),
        check(not old_mounts, "Docker 元数据无旧路径挂载", "\n".join(old_mounts)),
        check(not doc_bad_hits, "当前设计纲领/面板/索引无旧口径误导项", "\n".join(doc_bad_hits)),
        check("未停止运行中 v3 容器" in report_md or report.get("安全边界", {}).get("停止运行中v3容器") is False, "安全边界已记录", ""),
    ]
    failed = [item for item in checks if not item["通过"]]
    validation = {
        "名称": "旧资料归集提炼与清理验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
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
    }
    lines = [
        "# 旧资料归集提炼与清理验收",
        "",
        f"- 生成时间：{validation['生成时间']}",
        f"- 结论：{validation['结论']}",
        f"- 通过数量：{validation['通过数量']}",
        f"- 失败数量：{validation['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    write_json(VALIDATION_JSON, validation)
    write_text(VALIDATION_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": validation["结论"], "通过数量": validation["通过数量"], "失败数量": validation["失败数量"], "报告": str(VALIDATION_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
