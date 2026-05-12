# -*- coding: utf-8 -*-
"""
名称：验证税收人工入口资料下载器.py
作用：不联网验证人工入口资料下载器的配置、脚本、自测解析、白名单和安全边界。
触发方式：python 验证税收人工入口资料下载器.py
依赖：Python标准库；税收人工入口资料下载器.py；税收人工入口资料下载器配置.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只运行self-test，不联网、不下载、不写正式政策目录、不写向量库、不触发n8n、不推送企微。
创建/修改记录：2026-04-30 创建人工入口资料下载器验收脚本。
标识：tax-manual-url-official-document-downloader-verify
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


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "税收人工入口资料下载器配置.json"
    script = root / "02脚本" / "税收人工入口资料下载器.py"
    checks: list[dict[str, Any]] = [
        check("配置存在", config_path.exists(), str(config_path)),
        check("脚本存在", script.exists(), str(script))
    ]
    config = load_json(config_path)
    checks.append(check("默认不下载", config.get("安全边界", {}).get("是否默认下载") is False, config.get("安全边界", {})))
    checks.append(check("官方域名白名单存在", "www.chinatax.gov.cn" in config.get("允许域名", []) and "fgk.chinatax.gov.cn" in config.get("允许域名", []), config.get("允许域名", [])))
    checks.append(check("地方税务局子域可由根域白名单覆盖", "chinatax.gov.cn" in config.get("允许域名", []), config.get("允许域名", [])))
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run([sys.executable, str(script), "--self-test"], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
    checks.append(check("脚本self-test执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    blocked = subprocess.run([sys.executable, str(script), "--url", "https://example.com/not-allowed.pdf"], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60)
    checks.append(check("非官方域名联网前拦截", blocked.returncode == 2 and "URL不在官方白名单域名内" in (blocked.stdout + blocked.stderr), blocked.stdout.strip() or blocked.stderr.strip()))
    manifest_path = root / config["输出"]["数据目录"] / config["输出"]["清单最新文件"]
    checks.append(check("自测清单存在", manifest_path.exists(), str(manifest_path)))
    manifest = load_json(manifest_path) if manifest_path.exists() else {}
    checks.append(check("自测候选数量正确", manifest.get("候选数量") == 3, manifest.get("候选数量")))
    checks.append(check("外部域名被排除", all("example.com" not in item.get("链接", "") for item in manifest.get("候选资料", [])), manifest.get("候选资料", [])))
    checks.append(check("未执行下载", manifest.get("是否执行下载") is False, manifest.get("是否执行下载")))
    safety = manifest.get("安全边界", {})
    checks.append(check("高风险动作关闭", all(value is False for value in safety.values()), safety))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(manifest_path)}
    output_dir = root / "04日志" / "人工入口下载器"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"tax-manual-url-official-document-downloader-verify-{stamp}.json"
    latest = output_dir / "tax-manual-url-official-document-downloader-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
