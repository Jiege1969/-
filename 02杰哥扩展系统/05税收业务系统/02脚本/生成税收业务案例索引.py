"""
名称：生成税收业务案例索引.py
作用：扫描税收业务系统本地业务案例目录，生成案例索引、字段完整性检查和人工复核提示。
触发方式：python 生成税收业务案例索引.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只读取本模块业务案例目录，只写入本模块分类索引；不读取真实涉税资料、不形成正式税务处理结论。
创建/修改记录：2026-04-26 创建税收业务案例入库索引脚本。
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


def read_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def is_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip() != "待填写"
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def parse_case(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        data = load_json(path)
        data["_解析方式"] = "json"
        return data
    text = read_text_with_fallback(path)
    return {
        "案例编号": path.stem,
        "案例标题": path.stem,
        "案例性质": "文本案例",
        "事实描述": text[:1200],
        "_解析方式": "text",
    }


def build_case_index() -> dict[str, Any]:
    root = module_root()
    template = load_json(root / "01配置" / "税收业务案例模板.json")
    case_dir = root / "03数据" / "03业务案例"
    index_dir = root / "03数据" / "02分类索引"
    case_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    required_fields = [
        "案例编号",
        "案例标题",
        "税种",
        "业务场景",
        "事实描述",
        "政策依据",
        "风险点",
        "待核实事项",
        "人工复核结论",
        "是否替代人工判断",
    ]
    allowed_ext = {".json", ".md", ".txt"}
    cases = []
    tax_counter: dict[str, int] = {}

    for path in sorted(case_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed_ext:
            continue
        try:
            data = parse_case(path)
            parse_status = "正常"
            parse_error = ""
        except Exception as exc:
            data = {"案例编号": path.stem, "案例标题": path.name}
            parse_status = "异常"
            parse_error = str(exc)

        missing = [field for field in required_fields if not is_filled(data.get(field))]
        tax_items = data.get("税种", [])
        if isinstance(tax_items, str):
            tax_items = [tax_items]
        for tax_name in tax_items:
            tax_counter[str(tax_name)] = tax_counter.get(str(tax_name), 0) + 1

        policy_links = []
        for policy in data.get("政策依据", []) if isinstance(data.get("政策依据"), list) else []:
            if isinstance(policy, dict):
                policy_links.append(
                    {
                        "标题": policy.get("标题", ""),
                        "文号": policy.get("文号", ""),
                        "来源链接": policy.get("来源链接", ""),
                        "有效状态": policy.get("有效状态", "待核实"),
                    }
                )

        cases.append(
            {
                "案例编号": data.get("案例编号", path.stem),
                "案例标题": data.get("案例标题", path.name),
                "案例性质": data.get("案例性质", "未标注"),
                "路径": str(path),
                "解析状态": parse_status,
                "解析错误": parse_error,
                "税种": tax_items,
                "业务场景": data.get("业务场景", ""),
                "字段缺失": missing,
                "政策依据": policy_links,
                "风险点": data.get("风险点", []),
                "待核实事项": data.get("待核实事项", []),
                "人工复核结论": data.get("人工复核结论", "待人工复核"),
                "是否替代人工判断": bool(data.get("是否替代人工判断", False)),
                "可进入分析预处理": parse_status == "正常" and len(missing) == 0 and not bool(data.get("是否替代人工判断", False)),
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "案例目录": str(case_dir),
        "案例数量": len(cases),
        "统计": {
            "税种分布": tax_counter,
            "字段完整案例数量": sum(1 for item in cases if not item["字段缺失"]),
            "需补充案例数量": sum(1 for item in cases if item["字段缺失"]),
            "可进入分析预处理数量": sum(1 for item in cases if item["可进入分析预处理"]),
        },
        "模板字段来源": template.get("说明", ""),
        "案例": cases,
        "安全说明": "业务案例索引只用于检索和复盘，所有涉税结论必须经过正式政策依据过滤和人工复核。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = index_dir / f"税收业务案例索引_{timestamp}.json"
    latest = index_dir / "税收业务案例索引_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"case_count": len(cases), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_case_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
