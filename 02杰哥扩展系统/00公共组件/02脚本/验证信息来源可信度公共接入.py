from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE = Path("D:/杰哥智能化系统/02杰哥扩展系统")
PUBLIC_RULE = "00公共组件/01配置/信息来源可信度分层规则.json"
PUBLIC_SCRIPT = "00公共组件/02脚本/信息来源智能鉴别器.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "详情": detail}


def contains_all(text: str, parts: list[str]) -> bool:
    return all(part in text for part in parts)


def main() -> int:
    targets = {
        "公共组件README": BASE / "00公共组件/README.md",
        "总README": BASE / "README.md",
        "知识库系统README": BASE / "07知识库系统/README.md",
        "知识库问答框规则": BASE / "07知识库系统/08可追溯问答框/01配置/知识库可追溯问答框交付规则.json",
        "知识库问答框生成脚本": BASE / "07知识库系统/08可追溯问答框/02脚本/生成知识库可追溯问答框交付包.py",
        "知识库问答框验证脚本": BASE / "07知识库系统/08可追溯问答框/02脚本/验证知识库可追溯问答框交付包.py",
        "本职工作证据卡说明": BASE / "03本职工作系统/07文档/本职工作证据卡模板说明_20260505_小任务H.md",
        "股票系统README": BASE / "01股票研究系统/README.md",
        "股票数据源注册表": BASE / "01股票研究系统/01配置/股票数据源注册表.json",
        "股票标准报告来源清单": BASE / "01股票研究系统/07文档/股票标准报告v2_数据字段与来源清单.md",
        "税收证据图谱规则": BASE / "05税收业务系统/01配置/税收证据节点与关系图谱规则.json",
    }
    required_fields = ["可信度等级", "来源类型", "来源用途边界", "是否需要反向追溯", "是否可作正式依据候选"]
    checks: list[dict[str, Any]] = []

    checks.append(check("公共规则文件存在", (BASE / PUBLIC_RULE).exists(), PUBLIC_RULE))
    checks.append(check("公共鉴别脚本存在", (BASE / PUBLIC_SCRIPT).exists(), PUBLIC_SCRIPT))

    for name, path in targets.items():
        exists = path.exists()
        checks.append(check(f"{name}存在", exists, str(path)))
        if not exists:
            continue
        text = read_text(path)
        checks.append(check(f"{name}引用公共规则", "信息来源可信度分层规则.json" in text, str(path)))
        if name in {"知识库问答框规则", "知识库问答框生成脚本", "知识库问答框验证脚本", "本职工作证据卡说明", "股票数据源注册表", "股票标准报告来源清单"}:
            checks.append(check(f"{name}包含公共来源字段", contains_all(text, required_fields), required_fields))

    pass_count = sum(1 for item in checks if item["通过"])
    fail_count = len(checks) - pass_count
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "source-trust-public-adoption-verify",
        "状态": "通过" if fail_count == 0 else "失败",
        "通过数量": pass_count,
        "失败数量": fail_count,
        "检查项": checks,
        "安全边界": "只读检查公共规则接入情况；不联网、不下载、不写正式库、不触发n8n、不生成业务结论。",
    }
    log_dir = BASE / "00公共组件/04日志/信息来源可信度"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(log_dir / f"source-trust-public-adoption-verify-{stamp}.json", result)
    write_json(log_dir / "source-trust-public-adoption-verify-最新.json", result)
    print(json.dumps({"状态": result["状态"], "通过数量": pass_count, "失败数量": fail_count}, ensure_ascii=False))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
