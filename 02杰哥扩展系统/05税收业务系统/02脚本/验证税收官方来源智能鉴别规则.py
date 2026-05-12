# -*- coding: utf-8 -*-
"""
名称：验证税收官方来源智能鉴别规则.py
作用：离线验证税收官方来源智能鉴别规则、核验脚本和地方税务局子域识别能力。
触发方式：python 验证税收官方来源智能鉴别规则.py
安全边界：不联网、不下载、不写正式库、不写向量库、不触发n8n、不生成税务结论。
"""

from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def load_verifier(script: Path):
    spec = importlib.util.spec_from_file_location("tax_official_source_verifier", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "税收官方来源核验规则.json"
    script = root / "02脚本" / "核验税收政策官方来源.py"
    log_dir = root / "04日志" / "官方来源智能鉴别"
    config = load_json(config_path) if config_path.exists() else {}
    official_items = []

    checks: list[dict[str, Any]] = [
        check("官方来源核验规则存在", config_path.exists(), str(config_path)),
        check("核验脚本存在", script.exists(), str(script)),
        check("规则名称升级为智能鉴别", "智能鉴别" in json.dumps(config, ensure_ascii=False), config.get("说明", "")),
        check("地方官方来源规则存在", any(str(item.get("域名", "")).startswith("*.chinatax.gov.cn") for item in config.get("官方域名", [])), config.get("官方域名", [])),
        check("可信来源分层存在", all(item in json.dumps(config.get("可信来源分层", []), ensure_ascii=False) for item in ["学术权威", "中央级主流媒体", "大型商业门户"]), config.get("可信来源分层", [])),
        check("人工复核重点已重定向", all(key in config for key in ["地方官方来源识别规则", "人工复核重点", "智能鉴别结论分层", "可信来源分层"]), list(config.keys())),
    ]

    try:
        py_compile.compile(str(script), doraise=True)
        checks.append(check("核验脚本编译通过", True, ""))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("核验脚本编译通过", False, str(exc)))

    try:
        module = load_verifier(script)
        official_items = module.expanded_source_rules(config)
        central = module.classify_link("https://fgk.chinatax.gov.cn/zcfgk/c100012/c5241820/content.html", official_items)
        national = module.classify_link("https://www.chinatax.gov.cn/chinatax/n810341/index.html", official_items)
        local = module.classify_link("https://shanghai.chinatax.gov.cn/zcfw/sszc/index.html", official_items)
        academic = module.classify_link("https://www.pku.edu.cn/research/example.html", official_items)
        media = module.classify_link("https://www.people.com.cn/example.html", official_items)
        portal = module.classify_link("https://news.163.com/example.html", official_items)
        blocked = module.classify_link("https://example.com/tax-policy.html", official_items)
        checks.append(check("国家税务总局政策法规库识别为官方来源", central.get("来源核验结论") == "官方来源已核验", central))
        checks.append(check("国家税务总局官网识别为官方来源", national.get("来源核验结论") == "官方来源已核验", national))
        checks.append(check("地方税务局子域识别为地方官方来源", local.get("来源核验结论") == "地方官方来源已核验" and local.get("来源级别") == "地方官方来源", local))
        checks.append(check("学术权威来源识别为可信但非正式政策依据", academic.get("可信度等级") == "S3" and academic.get("可作为正式政策依据") is False, academic))
        checks.append(check("中央级主流媒体识别为可信线索来源", media.get("可信度等级") == "S4" and media.get("可作为正式政策依据") is False, media))
        checks.append(check("网易等商业门户识别为公共传播来源", portal.get("可信度等级") == "S5" and portal.get("可作为正式政策依据") is False, portal))
        checks.append(check("非官方来源阻断", bool(blocked.get("阻断原因")), blocked))
        checks.append(check("智能鉴别输出字段齐备", all(key in local for key in ["来源级别", "可信度等级", "智能鉴别依据", "用途边界", "仍需人工复核事项"]), local))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("样例分类执行通过", False, str(exc)))

    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    checks.append(check("现有来源核验脚本可执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "税收官方来源智能鉴别规则验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否写正式库": False,
            "是否写向量库": False,
            "是否触发n8n": False,
            "是否生成税务结论": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(log_dir / f"tax-official-source-intelligence-verify-{stamp}.json", report)
    write_json(log_dir / "tax-official-source-intelligence-verify-最新.json", report)
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
