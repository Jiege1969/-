# -*- coding: utf-8 -*-
"""
名称：验证税收人工入口一键生成清单.py
作用：不联网验证网址填写模板和一键生成清单脚本可用，并确认默认不下载。
触发方式：python 验证税收人工入口一键生成清单.py
依赖：Python标准库；生成税收人工入口网址填写模板.py；税收人工入口资料清单一键生成.py。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只运行self-test，不联网、不下载、不入库、不触发n8n、不推送企微。
创建/修改记录：2026-04-30 创建税收人工入口一键生成清单验收脚本。
标识：tax-manual-url-manifest-one-click-verify
"""

from __future__ import annotations

import json
import os
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
    return {"名称": name, "通过": bool(passed), "说明": detail}


def run_script(root: Path, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(script), *args], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "税收人工入口资料下载器配置.json"
    template_script = root / "02脚本" / "生成税收人工入口网址填写模板.py"
    one_click_script = root / "02脚本" / "税收人工入口资料清单一键生成.py"
    config = load_json(config_path)
    checks: list[dict[str, Any]] = [
        check("配置存在", config_path.exists(), str(config_path)),
        check("模板脚本存在", template_script.exists(), str(template_script)),
        check("一键清单脚本存在", one_click_script.exists(), str(one_click_script)),
    ]
    gen = run_script(root, template_script)
    checks.append(check("网址填写模板生成", gen.returncode == 0, gen.stdout.strip() or gen.stderr.strip()))
    input_path = root / config["输出"]["数据目录"] / config["输出"]["入口网址填写文件"]
    checks.append(check("网址填写文件存在", input_path.exists(), str(input_path)))
    one = run_script(root, one_click_script, "--self-test")
    checks.append(check("一键脚本self-test执行", one.returncode == 0, one.stdout.strip() or one.stderr.strip()))
    manifest_json = root / config["输出"]["数据目录"] / config["输出"]["清单最新文件"]
    manifest_md = root / config["输出"]["数据目录"] / config["输出"]["清单Markdown最新文件"]
    checks.append(check("清单JSON存在", manifest_json.exists(), str(manifest_json)))
    checks.append(check("清单Markdown存在", manifest_md.exists(), str(manifest_md)))
    manifest = load_json(manifest_json) if manifest_json.exists() else {}
    checks.append(check("默认未下载", manifest.get("是否执行下载") is False, manifest.get("是否执行下载")))
    checks.append(check("候选数量正确", manifest.get("候选数量") == 3, manifest.get("候选数量")))
    text = manifest_md.read_text(encoding="utf-8-sig") if manifest_md.exists() else ""
    checks.append(check("Markdown包含候选资料和安全边界", "候选资料" in text and "安全边界" in text, str(manifest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(manifest_json)}
    output_dir = root / "04日志" / "人工入口下载器"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"tax-manual-url-manifest-one-click-verify-{stamp}.json"
    latest = output_dir / "tax-manual-url-manifest-one-click-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
