"""
名称：检查企业微信凭据隔离.py
作用：检查企业微信接入设置配置、脚本和文档中是否出现禁止的明文凭据关键词。
触发方式：python 检查企业微信凭据隔离.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只扫描本模块01配置、02脚本、07文档；不读取真实凭据文件，不输出任何密钥内容。
创建/修改记录：2026-04-27 创建企业微信凭据隔离检查脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def scan_credentials() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "企业微信凭据隔离规则.json")
    output_dir = root / "03数据" / "01接入检查"
    output_dir.mkdir(parents=True, exist_ok=True)
    scan_dirs = [root / "01配置", root / "02脚本", root / "07文档"]
    forbidden = [str(item) for item in rules.get("禁止关键词", [])]
    allowed_ext = {".json", ".py", ".md", ".txt", ".env"}
    findings = []
    high_risk_keywords = [keyword for keyword in forbidden if "=" in keyword or "access_token" in keyword.lower()]
    scanned = 0
    for directory in scan_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in allowed_ext:
                continue
            scanned += 1
            text = read_text(path)
            for keyword in forbidden:
                if keyword and keyword in text:
                    is_rule_definition = path.name == "企业微信凭据隔离规则.json"
                    findings.append(
                        {
                            "文件": str(path),
                            "命中关键词": keyword,
                            "风险等级": "高" if keyword in high_risk_keywords and not is_rule_definition else "提示",
                            "处理建议": "人工核查该关键词是否为说明文字；禁止出现真实密钥值。",
                        }
                    )

    high_risk_count = sum(1 for item in findings if item["风险等级"] == "高")
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "扫描范围": [str(path) for path in scan_dirs],
        "扫描文件数": scanned,
        "发现数量": len(findings),
        "高风险发现数量": high_risk_count,
        "发现项": findings,
        "是否发现明文凭据风险": high_risk_count > 0,
        "安全说明": "本检查只做关键词风险筛查；真实接入前还需要人工复核凭据存放位置和权限。",
    }
    latest = output_dir / "企业微信凭据隔离检查_最新.json"
    output = latest
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"scanned": scanned, "findings": len(findings), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    scan_credentials()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
