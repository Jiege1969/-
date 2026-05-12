# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
OUT_DIR = VIDEO_ROOT / "03数据" / "真实渲染环境缺口证据压缩与安装识别清单"
LOG_DIR = VIDEO_ROOT / "04日志" / "真实渲染环境缺口证据压缩与安装识别清单验收"
SUMMARY = OUT_DIR / "视频真实渲染环境缺口证据压缩与安装识别清单_最新.json"


def add(checks: list[dict], name: str, passed: bool, detail) -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(SUMMARY.read_text(encoding="utf-8"))
    checks: list[dict] = []

    safety = data.get("安全边界", {})
    money = data.get("MoneyPrinterTurbo压缩证据", {})
    image = data.get("ImageMagick压缩证据", {})
    gate = data.get("当前门禁摘要", {})

    add(checks, "总包存在", SUMMARY.exists(), str(SUMMARY))
    add(checks, "状态仍为blocked", data.get("状态") == "blocked", data.get("状态"))
    add(checks, "未满足安装识别", data.get("安装识别是否已满足") is False, data.get("安装识别是否已满足"))
    add(checks, "MoneyPrinterTurbo未识别", money.get("当前可识别") is False, money)
    add(checks, "ImageMagick未识别", image.get("当前可识别") is False, image)
    add(checks, "真实渲染不可进入", gate.get("可进入真实渲染") is False, gate)
    add(checks, "真实发布不可进入", gate.get("可进入真实发布") is False, gate)
    add(checks, "阻断项非空", len(data.get("阻断项压缩", [])) >= 2, data.get("阻断项压缩", []))
    add(checks, "人工补齐清单非空", len(data.get("下一步人工补齐清单", [])) >= 5, data.get("下一步人工补齐清单", []))
    add(checks, "安全边界均未触发", all(value is False for value in safety.values()), safety)
    add(checks, "未执行magick版本检查", safety.get("执行magick_version") is False, safety)
    add(checks, "未调用MoneyPrinterTurbo", safety.get("调用MoneyPrinterTurbo") is False, safety)

    for name, path_text in data.get("输出文件", {}).items():
        add(checks, f"输出文件存在-{name}", Path(path_text).exists(), path_text)

    passed = all(item["通过"] for item in checks)
    log = {
        "名称": "视频真实渲染环境缺口证据压缩与安装识别清单验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "通过项": sum(1 for item in checks if item["通过"]),
        "失败项": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
    }
    latest = LOG_DIR / "video-render-env-gap-compressed-install-identify-verify-最新.json"
    latest.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "log": str(latest)}, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
