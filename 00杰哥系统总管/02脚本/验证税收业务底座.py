"""
名称：验证税收业务底座.py
作用：验证 v3 税收业务系统配置、税种分类、政策来源、入库规则、案例模板、处理模板、政策全文索引、业务案例索引、官方来源核验和正式依据过滤是否可用。
触发方式：python 验证税收业务底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 税收业务配置，只运行本地计划脚本；不抓取政策、不读取真实涉税资料、不替代正式判断。
创建/修改记录：2026-04-26 创建第一阶段税收业务底座验证脚本；增加政策案例索引、政策全文索引、业务案例索引、官方来源核验和正式依据过滤验收。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "05税收业务系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "税收业务验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "税收业务配置.json")
    rules = load_json(root / "01配置" / "税种分类规则.json")
    sources = load_json(root / "01配置" / "税收政策来源.json")
    official_rules = load_json(root / "01配置" / "税收官方来源核验规则.json")
    template = load_json(root / "01配置" / "税收业务处理模板.json")
    metadata = load_json(root / "01配置" / "税收政策元数据模板.json")
    intake_rules = load_json(root / "01配置" / "税收政策入库规则.json")
    case_template = load_json(root / "01配置" / "税收业务案例模板.json")
    script = root / "02脚本" / "生成税收业务分类计划.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    policy_case_script = root / "02脚本" / "生成税收政策案例索引.py"
    policy_case_result = subprocess.run(
        [sys.executable, str(policy_case_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    policy_fulltext_script = root / "02脚本" / "生成税收政策全文索引.py"
    policy_fulltext_result = subprocess.run(
        [sys.executable, str(policy_fulltext_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    business_case_script = root / "02脚本" / "生成税收业务案例索引.py"
    business_case_result = subprocess.run(
        [sys.executable, str(business_case_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    official_verify_script = root / "02脚本" / "核验税收政策官方来源.py"
    official_verify_result = subprocess.run(
        [sys.executable, str(official_verify_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    basis_filter_script = root / "02脚本" / "生成税收正式依据过滤结果.py"
    basis_filter_result = subprocess.run(
        [sys.executable, str(basis_filter_script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    latest_index = root / "03数据" / "02分类索引" / "税种分类索引_最新.json"
    latest_policy_case_index = root / "03数据" / "02分类索引" / "税收政策案例索引_最新.json"
    latest_policy_fulltext_index = root / "03数据" / "02分类索引" / "税收政策全文索引_最新.json"
    latest_business_case_index = root / "03数据" / "02分类索引" / "税收业务案例索引_最新.json"
    latest_official_verify = root / "03数据" / "06依据过滤" / "税收政策来源核验_最新.json"
    latest_basis_filter = root / "03数据" / "06依据过滤" / "税收正式依据过滤_最新.json"
    latest_plan = root / "03数据" / "04处理计划" / "税收业务处理计划_最新.json"
    index_data = load_json(latest_index) if latest_index.exists() else {}
    policy_case_index_data = load_json(latest_policy_case_index) if latest_policy_case_index.exists() else {}
    policy_fulltext_index_data = load_json(latest_policy_fulltext_index) if latest_policy_fulltext_index.exists() else {}
    business_case_index_data = load_json(latest_business_case_index) if latest_business_case_index.exists() else {}
    official_verify_data = load_json(latest_official_verify) if latest_official_verify.exists() else {}
    basis_filter_data = load_json(latest_basis_filter) if latest_basis_filter.exists() else {}
    plan_data = load_json(latest_plan) if latest_plan.exists() else {}
    tax_names = [item.get("税种") for item in rules.get("税种", [])]

    checks = [
        check("税收业务配置", "核心税种" in config and "输出原则" in config, config.get("说明")),
        check("税种分类规则", {"增值税", "企业所得税", "消费税"}.issubset(set(tax_names)), tax_names),
        check("政策来源", "官方来源" in sources and "来源规则" in sources, sources.get("说明")),
        check("官方来源核验规则", "官方域名" in official_rules and "有效状态允许值" in official_rules, official_rules.get("核验模式")),
        check("业务处理模板", "处理流程" in template and "事实采集字段" in template, template.get("说明")),
        check("政策元数据模板", "文号" in metadata and "有效状态" in metadata, metadata),
        check("政策入库规则", "入库流程" in intake_rules and "质量门槛" in intake_rules, intake_rules.get("说明")),
        check("政策全文解析策略", "全文解析策略" in intake_rules and "元数据伴随文件规则" in intake_rules, intake_rules.get("全文解析策略")),
        check("业务案例模板", "事实要素" in case_template and "处理结论" in case_template, case_template.get("说明")),
        check("分类计划脚本执行", result.returncode == 0, (result.stdout or "").strip() or (result.stderr or "").strip()),
        check(
            "政策案例索引脚本执行",
            policy_case_result.returncode == 0,
            (policy_case_result.stdout or "").strip() or (policy_case_result.stderr or "").strip(),
        ),
        check(
            "政策全文索引脚本执行",
            policy_fulltext_result.returncode == 0,
            (policy_fulltext_result.stdout or "").strip() or (policy_fulltext_result.stderr or "").strip(),
        ),
        check(
            "业务案例索引脚本执行",
            business_case_result.returncode == 0,
            (business_case_result.stdout or "").strip() or (business_case_result.stderr or "").strip(),
        ),
        check(
            "官方来源核验脚本执行",
            official_verify_result.returncode == 0,
            (official_verify_result.stdout or "").strip() or (official_verify_result.stderr or "").strip(),
        ),
        check(
            "正式依据过滤脚本执行",
            basis_filter_result.returncode == 0,
            (basis_filter_result.stdout or "").strip() or (basis_filter_result.stderr or "").strip(),
        ),
        check("最新分类索引", latest_index.exists(), str(latest_index)),
        check("分类索引结构", "税种分类" in index_data and "政策来源" in index_data, index_data.get("税种数量")),
        check("最新政策案例索引", latest_policy_case_index.exists(), str(latest_policy_case_index)),
        check(
            "政策案例索引结构",
            "政策文件" in policy_case_index_data and "业务案例" in policy_case_index_data,
            policy_case_index_data.get("统计"),
        ),
        check("最新政策全文索引", latest_policy_fulltext_index.exists(), str(latest_policy_fulltext_index)),
        check(
            "政策全文索引结构",
            "政策文件" in policy_fulltext_index_data and "分块" in policy_fulltext_index_data,
            {"政策数量": policy_fulltext_index_data.get("政策数量"), "分块数量": policy_fulltext_index_data.get("分块数量")},
        ),
        check("最新业务案例索引", latest_business_case_index.exists(), str(latest_business_case_index)),
        check(
            "业务案例索引结构",
            "案例" in business_case_index_data and "统计" in business_case_index_data,
            {"案例数量": business_case_index_data.get("案例数量"), "可预处理": business_case_index_data.get("统计", {}).get("可进入分析预处理数量")},
        ),
        check("最新官方来源核验", latest_official_verify.exists(), str(latest_official_verify)),
        check(
            "官方来源核验结构",
            "核验结果" in official_verify_data and official_verify_data.get("是否联网核验") is False,
            official_verify_data.get("统计"),
        ),
        check("最新正式依据过滤", latest_basis_filter.exists(), str(latest_basis_filter)),
        check(
            "正式依据过滤结构",
            "正式依据候选" in basis_filter_data and "阻断依据" in basis_filter_data and basis_filter_data.get("是否替代人工判断") is False,
            basis_filter_data.get("统计"),
        ),
        check("最新处理计划", latest_plan.exists(), str(latest_plan)),
        check("处理计划结构", "处理流程" in plan_data and "任务列表" in plan_data, plan_data.get("处理流程")),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "tax-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"tax-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "tax-base-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
