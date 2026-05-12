# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
ATTACH_PARSE = ROOT / "03数据" / "18附件正文解析预演" / "税收附件正文解析预演_最新.json"
OUT_DIR = ROOT / "03数据" / "20正式文档解析器接入评估"
OUT_JSON = OUT_DIR / "税收正式文档解析器接入评估_最新.json"
OUT_MD = OUT_DIR / "税收正式文档解析器接入评估_最新.md"


NO_RUNTIME_CHANGE = {
    "是否触发n8n": False,
    "是否企业微信真实发送": False,
    "是否写向量库": False,
    "是否调用模型推理": False,
    "是否生成正式税务结论": False,
    "是否新增端口": False,
    "是否重启服务": False,
    "是否影响股票系统": False,
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attach_pack = load_json(ATTACH_PARSE)
    attachments = attach_pack.get("解析结果", [])

    command_tools = {
        "soffice": shutil.which("soffice"),
        "libreoffice": shutil.which("libreoffice"),
        "antiword": shutil.which("antiword"),
        "pandoc": shutil.which("pandoc"),
    }
    python_modules = {
        "docx": module_available("docx"),
        "lxml": module_available("lxml"),
        "mammoth": module_available("mammoth"),
        "olefile": module_available("olefile"),
        "win32com": module_available("win32com"),
        "pypandoc": module_available("pypandoc"),
        "bs4": module_available("bs4"),
    }

    attachment_items = []
    for item in attachments:
        path = Path(item.get("本地附件路径", ""))
        suffix = path.suffix.lower()
        recommended = "待定"
        blocker = []
        if suffix == ".docx":
            if python_modules["docx"]:
                recommended = "python-docx可尝试正式解析"
            else:
                recommended = "需安装或接入docx解析能力"
                blocker.append("python-docx不可用")
        elif suffix == ".doc":
            if command_tools["soffice"] or command_tools["libreoffice"]:
                recommended = "LibreOffice/soffice转换为docx或txt后正式解析"
            elif command_tools["antiword"]:
                recommended = "antiword抽取doc正文后人工复核"
            elif python_modules["win32com"]:
                recommended = "Windows Office COM转换后解析"
            else:
                recommended = "当前仅可轻量抽取，需接入LibreOffice、antiword或Office COM"
                blocker.append("缺少老式doc正式解析器")
        elif suffix == ".wps":
            recommended = "需WPS/LibreOffice转换或人工下载为doc/docx"
            blocker.append("WPS格式解析器未接入")
        else:
            recommended = "按文件类型另行评估"
            blocker.append(f"未知附件后缀：{suffix}")

        attachment_items.append({
            "标题": item.get("标题"),
            "本地附件路径": item.get("本地附件路径"),
            "后缀": suffix,
            "轻量解析状态": item.get("解析状态"),
            "轻量解析字符数": item.get("解析字符数"),
            "推荐正式解析方案": recommended,
            "阻断原因": blocker or ["需正式解析后人工复核，当前不得作为正式依据。"],
        })

    install_free_plan = [
        "保留现有轻量解析文本作为预览，不替代正式解析。",
        "优先接入本机已存在能力；当前可用python-docx更适合docx，不适合老式doc。",
        "对老式doc附件，建议后续选择LibreOffice/soffice或Office COM作为转换层。",
        "正式解析器接入前，不把附件正文写入正式依据库，不进入RAG，不接企业微信。",
    ]

    result = {
        "名称": "税收正式文档解析器接入评估",
        "生成时间": now,
        "模式": "readonly_evaluation_no_runtime_change",
        "Python解释器": sys.executable,
        "命令行工具": command_tools,
        "Python模块": python_modules,
        "附件数量": len(attachment_items),
        "附件评估": attachment_items,
        "推荐路线": install_free_plan,
        "结论": "当前可保留轻量解析预演；老式doc正式解析能力不足，需后续接入LibreOffice/soffice、antiword或Office COM后再正式回填。",
        "安全边界": NO_RUNTIME_CHANGE,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收正式文档解析器接入评估",
        "",
        f"- 生成时间：{now}",
        "- 模式：readonly_evaluation_no_runtime_change",
        f"- Python解释器：{sys.executable}",
        f"- 附件数量：{len(attachment_items)}",
        "",
        "## 工具探测",
        "",
    ]
    for key, value in command_tools.items():
        lines.append(f"- {key}：{value or '不可用'}")
    lines.extend(["", "## Python模块", ""])
    for key, value in python_modules.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 附件评估", ""])
    for item in attachment_items:
        lines.extend([
            f"### {item['标题']}",
            f"- 后缀：{item['后缀']}",
            f"- 轻量解析状态：{item['轻量解析状态']}",
            f"- 轻量解析字符数：{item['轻量解析字符数']}",
            f"- 推荐正式解析方案：{item['推荐正式解析方案']}",
            f"- 阻断原因：{'；'.join(item['阻断原因'])}",
            "",
        ])
    lines.extend(["## 结论", "", result["结论"], "", "## 安全边界", ""])
    for key, value in NO_RUNTIME_CHANGE.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "附件数量": len(attachment_items), "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
