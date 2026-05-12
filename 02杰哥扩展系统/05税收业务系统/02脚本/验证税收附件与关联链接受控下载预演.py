# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "15关联附件下载预演"
RAW_DIR = OUT_DIR / "原始下载区"
TEXT_DIR = OUT_DIR / "解析文本区"
META_DIR = OUT_DIR / "元数据区"
ERROR_DIR = OUT_DIR / "异常待核验区"
REPORT_DIR = OUT_DIR / "运行报告"
RUN_JSON = REPORT_DIR / "税收附件与关联链接受控下载预演_最新.json"
RUN_MD = REPORT_DIR / "税收附件与关联链接受控下载预演_最新.md"
REPORT_JSON = REPORT_DIR / "税收附件与关联链接受控下载预演验收_最新.json"
REPORT_MD = REPORT_DIR / "税收附件与关联链接受控下载预演验收_最新.md"


REQUIRED_METADATA_FIELDS = [
    "资料ID",
    "标题",
    "原关系ID",
    "原关系类型",
    "来源名称",
    "来源链接",
    "最终链接",
    "资料类别",
    "文件类型",
    "文件时效",
    "下载时间",
    "原文哈希",
    "本地原文路径",
    "是否可作当前适用依据",
    "阻断原因",
    "人工复核状态",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check(name: str, ok: bool, detail):
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    for folder in [RAW_DIR, TEXT_DIR, META_DIR, ERROR_DIR, REPORT_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    run = load_json(RUN_JSON) if RUN_JSON.exists() else {}
    results = run.get("下载结果", [])
    errors = run.get("失败结果", [])
    safety = run.get("安全边界", {})

    checks = []
    checks.append(check("运行JSON存在", RUN_JSON.exists(), str(RUN_JSON)))
    checks.append(check("运行Markdown存在", RUN_MD.exists(), str(RUN_MD)))
    checks.append(check("分层目录存在", all(path.exists() for path in [RAW_DIR, TEXT_DIR, META_DIR, ERROR_DIR, REPORT_DIR]), str(OUT_DIR)))
    checks.append(check("候选数量大于0", run.get("候选数量", 0) > 0, run.get("候选数量", 0)))
    checks.append(check("至少成功下载1项", run.get("成功数量", 0) > 0, {"成功": run.get("成功数量"), "失败": run.get("失败数量")}))
    checks.append(check("至少覆盖附件或网页正文", run.get("附件数量", 0) + run.get("网页正文数量", 0) > 0, {"附件": run.get("附件数量"), "网页": run.get("网页正文数量")}))

    missing_fields = []
    missing_files = []
    for item in results:
        miss = [field for field in REQUIRED_METADATA_FIELDS if field not in item]
        if miss:
            missing_fields.append({"资料ID": item.get("资料ID"), "缺字段": miss})
        raw_path = Path(item.get("本地原文路径", ""))
        if not raw_path.is_file():
            missing_files.append({"资料ID": item.get("资料ID"), "本地原文路径": item.get("本地原文路径")})
        if item.get("文件类型") == "网页正文":
            text_path = Path(item.get("本地解析文本路径", ""))
            if not text_path.is_file():
                missing_files.append({"资料ID": item.get("资料ID"), "本地解析文本路径": item.get("本地解析文本路径")})

    checks.append(check("元数据字段齐备", not missing_fields, missing_fields[:5]))
    checks.append(check("本地文件路径可读", not missing_files, missing_files[:5]))

    bad_formal = [
        item for item in results
        if item.get("是否可作当前适用依据") is True and not (
            item.get("文件类型") == "网页正文"
            and item.get("文件时效") == "全文有效"
            and item.get("原关系类型") == "关联"
        )
    ]
    checks.append(check("可作依据项边界正确", not bad_formal, bad_formal[:5]))

    attachment_support = [
        item for item in results
        if item.get("文件类型") == "附件" and item.get("是否可作当前适用依据") is True
    ]
    checks.append(check("附件不得直接作为当前适用依据", not attachment_support, attachment_support[:5]))

    official_domain_bad = [
        item for item in results
        if "fgk.chinatax.gov.cn" not in item.get("最终链接", "")
    ]
    checks.append(check("下载来源均为国家税务总局政策法规库域名", not official_domain_bad, official_domain_bad[:5]))

    required_false = [
        "是否触发n8n",
        "是否企业微信真实发送",
        "是否写向量库",
        "是否调用模型推理",
        "是否生成正式税务结论",
        "是否新增端口",
        "是否重启服务",
        "是否影响股票系统",
    ]
    checks.append(check("高风险动作全部关闭", all(safety.get(key) is False for key in required_false), safety))

    passed = sum(1 for item in checks if item["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收附件与关联链接受控下载预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "统计": {
            "候选数量": run.get("候选数量", 0),
            "成功数量": run.get("成功数量", 0),
            "失败数量": run.get("失败数量", 0),
            "跳过数量": run.get("跳过数量", 0),
            "网页正文数量": run.get("网页正文数量", 0),
            "附件数量": run.get("附件数量", 0),
            "可作当前适用依据数量": run.get("可作当前适用依据数量", 0),
        },
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收附件与关联链接受控下载预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 统计",
        "",
    ]
    for key, value in report["统计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 检查结果", ""])
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}。{item['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
