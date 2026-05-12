# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DOWNLOAD_REPORT = ROOT / "03数据" / "15关联附件下载预演" / "运行报告" / "税收附件与关联链接受控下载预演_最新.json"
OUT_DIR = ROOT / "03数据" / "18附件正文解析预演"
TEXT_DIR = OUT_DIR / "解析文本区"
META_DIR = OUT_DIR / "元数据区"
REPORT_JSON = OUT_DIR / "税收附件正文解析预演_最新.json"
REPORT_MD = OUT_DIR / "税收附件正文解析预演_最新.md"


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


def safe_filename(value: str, limit: int = 80) -> str:
    value = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", value or "未命名附件")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].strip(" ._") or "未命名附件"


def clean_text(text: str) -> str:
    text = re.sub(r"\x00+", " ", text)
    text = re.sub(r"[\x01-\x08\x0b-\x1f]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_zip_docx(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        candidates = [name for name in names if name.endswith(".xml") and ("word/" in name or "wps/" in name)]
        chunks = []
        for name in candidates[:20]:
            raw = zf.read(name).decode("utf-8", errors="ignore")
            chunks.append(re.sub(r"<[^>]+>", " ", raw))
    text = clean_text(" ".join(chunks))
    return text, "zip_xml"


def extract_binary_strings(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    if data[:2] == b"PK":
        return extract_zip_docx(path)

    candidates = []
    for encoding, method in [("utf-8", "utf8_ignore"), ("gb18030", "gb18030_ignore"), ("utf-16le", "utf16le_ignore")]:
        try:
            decoded = data.decode(encoding, errors="ignore")
        except Exception:
            continue
        snippets = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9（）()《》、，。；：:,.%\-\s]{8,}", decoded)
        text = clean_text(" ".join(snippets))
        chinese_count = len(re.findall(r"[\u4e00-\u9fa5]", text))
        candidates.append((chinese_count, len(text), method, text))

    candidates.sort(reverse=True)
    if not candidates or candidates[0][0] < 20:
        return "", "unparsed"
    _chinese_count, _length, method, text = candidates[0]
    return text[:30000], method


def main() -> int:
    for folder in [OUT_DIR, TEXT_DIR, META_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = load_json(DOWNLOAD_REPORT)
    attachments = [item for item in report.get("下载结果", []) if item.get("文件类型") == "附件"]
    results = []

    for item in attachments:
        source_path = Path(item.get("本地原文路径", ""))
        title = item.get("标题") or item.get("原目标标题", "")
        status = "失败"
        method = ""
        text_path = ""
        blockers = []
        text = ""
        if not source_path.is_file():
            blockers.append("附件原文文件不存在。")
        else:
            text, method = extract_binary_strings(source_path)
            if text:
                status = "部分解析" if method != "zip_xml" else "完成"
                text_file = TEXT_DIR / f"{safe_filename(title)}.txt"
                text_file.write_text(text, encoding="utf-8")
                text_path = str(text_file)
                if status == "部分解析":
                    blockers.append("采用轻量字符串抽取，需后续使用正式文档解析器复核。")
            else:
                blockers.append("轻量解析未抽取到可靠正文，需后续使用 Office/WPS 或专门解析器处理。")

        metadata = {
            "资料ID": item.get("资料ID"),
            "标题": title,
            "来源链接": item.get("来源链接"),
            "最终链接": item.get("最终链接"),
            "本地附件路径": str(source_path),
            "解析状态": status,
            "解析方法": method,
            "解析文本路径": text_path,
            "解析字符数": len(text),
            "是否可作当前适用依据": False,
            "阻断原因": blockers + ["附件解析预演不能直接作为当前适用依据，需人工复核。"],
            "解析时间": now,
        }
        meta_path = META_DIR / f"{safe_filename(title)}.解析元数据.json"
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        metadata["本地解析元数据路径"] = str(meta_path)
        results.append(metadata)

    output = {
        "名称": "税收附件正文解析预演",
        "生成时间": now,
        "模式": "preview_only_no_runtime_change_lightweight_attachment_parse",
        "附件数量": len(attachments),
        "解析完成数量": sum(1 for item in results if item["解析状态"] == "完成"),
        "部分解析数量": sum(1 for item in results if item["解析状态"] == "部分解析"),
        "失败数量": sum(1 for item in results if item["解析状态"] == "失败"),
        "解析结果": results,
        "安全边界": NO_RUNTIME_CHANGE,
        "下一步建议": [
            "对部分解析和失败附件引入正式文档解析器。",
            "人工复核附件文本后再回填问题包。",
            "附件仍不得直接作为当前适用依据。",
        ],
    }
    REPORT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收附件正文解析预演",
        "",
        f"- 生成时间：{now}",
        "- 模式：preview_only_no_runtime_change_lightweight_attachment_parse",
        f"- 附件数量：{output['附件数量']}",
        f"- 解析完成数量：{output['解析完成数量']}",
        f"- 部分解析数量：{output['部分解析数量']}",
        f"- 失败数量：{output['失败数量']}",
        "",
        "## 解析结果",
        "",
    ]
    for item in results:
        lines.extend([
            f"### {item['标题']}",
            f"- 解析状态：{item['解析状态']}",
            f"- 解析方法：{item['解析方法']}",
            f"- 解析字符数：{item['解析字符数']}",
            f"- 解析文本路径：{item['解析文本路径']}",
            f"- 阻断原因：{'；'.join(item['阻断原因'])}",
            "",
        ])
    lines.extend(["## 安全边界", ""])
    for key, value in NO_RUNTIME_CHANGE.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "附件数量": len(attachments), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
