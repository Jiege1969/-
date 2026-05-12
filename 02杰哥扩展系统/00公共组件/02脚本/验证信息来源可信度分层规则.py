# -*- coding: utf-8 -*-
"""
名称：验证信息来源可信度分层规则.py
作用：验证 00公共组件的信息来源可信度分层配置、文档和智能鉴别器。
触发方式：python 验证信息来源可信度分层规则.py
安全边界：不联网、不下载、不写正式库、不写向量库、不触发 n8n、不生成业务结论。
"""

from __future__ import annotations

import importlib.util
import json
import py_compile
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


def load_classifier(path: Path):
    spec = importlib.util.spec_from_file_location("source_trust_classifier", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "信息来源可信度分层规则.json"
    script_path = root / "02脚本" / "信息来源智能鉴别器.py"
    doc_path = root / "07文档" / "信息来源可信度判断通用规则.md"
    config = load_json(config_path) if config_path.exists() else {}
    doc = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
    checks: list[dict[str, Any]] = [
        check("公共可信度规则配置存在", config_path.exists(), str(config_path)),
        check("公共智能鉴别脚本存在", script_path.exists(), str(script_path)),
        check("公共规则文档存在", doc_path.exists(), str(doc_path)),
    ]

    layers = config.get("可信度分层", [])
    layer_text = json.dumps(layers, ensure_ascii=False)
    checks.append(check("S1-S6分层齐备", all(level in layer_text for level in ["S1", "S2", "S3", "S4", "S5", "S6"]), layers))
    checks.append(check("规则定位为公共组件", "公共来源判断机制" in config.get("定位", ""), config.get("定位", "")))
    checks.append(check("业务系统适配原则存在", all(name in config.get("业务系统适配原则", {}) for name in ["税收业务系统", "股票研究系统", "文稿系统", "知识库系统"]), config.get("业务系统适配原则", {})))
    checks.append(check("文档明确不是税务专用", "不是税务系统专用规则" in doc, "不是税务系统专用规则"))

    try:
        py_compile.compile(str(script_path), doraise=True)
        checks.append(check("智能鉴别脚本编译通过", True, ""))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("智能鉴别脚本编译通过", False, str(exc)))

    try:
        module = load_classifier(script_path)
        samples = {
            "S1国家官方": ("https://www.gov.cn/zhengce/index.htm", "S1"),
            "S1交易所": ("https://www.sse.com.cn/disclosure/listedinfo/announcement/", "S1"),
            "S3学术权威": ("https://www.pku.edu.cn/research/example.html", "S3"),
            "S4主流媒体": ("https://www.people.com.cn/example.html", "S4"),
            "S5网易门户": ("https://news.163.com/example.html", "S5"),
            "S6未知来源": ("https://example.com/example.html", "S6")
        }
        for name, (url, expected) in samples.items():
            result = module.classify_url(url, config)
            checks.append(check(f"{name}识别正确", result.get("可信度等级") == expected, result))
        portal = module.classify_url("https://news.sina.com.cn/example.html", config)
        checks.append(check("大型门户需要反向追溯", portal.get("可信度等级") == "S5" and portal.get("是否需要反向追溯") is True, portal))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("样例分类执行通过", False, str(exc)))

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "信息来源可信度分层规则验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": config.get("安全边界", {}),
    }
    output_dir = root / "04日志" / "信息来源可信度"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(output_dir / f"source-trust-classification-verify-{stamp}.json", report)
    write_json(output_dir / "source-trust-classification-verify-最新.json", report)
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
