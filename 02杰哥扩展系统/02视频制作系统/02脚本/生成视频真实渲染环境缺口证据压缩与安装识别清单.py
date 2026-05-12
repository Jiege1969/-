# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
OUT_DIR = VIDEO_ROOT / "03数据" / "真实渲染环境缺口证据压缩与安装识别清单"

DISABLED_GATE = VIDEO_ROOT / "03数据" / "08本地整理门禁" / "视频真实渲染禁用态检查_最新.json"
RENDER_PRECHECK = VIDEO_ROOT / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "视频生成桥梁预检" / "视频生成桥梁预检_最新.json"
PUBLISH_PRECHECK = VIDEO_ROOT / "03数据" / "18轮次012视频工厂总控层" / "测试与审核" / "发布桥梁预检" / "发布桥梁预检_最新.json"
PATH_GAP_VERIFY = VIDEO_ROOT / "04日志" / "真实渲染环境候选路径矩阵与安装缺口清单验收" / "video-render-env-candidate-path-gap-verify-最新.json"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_missing": True, "_path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.write_text("# " + title + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def moneyprinter_summary(render: dict) -> dict:
    check = render.get("MoneyPrinterTurbo检查", {})
    candidates = check.get("候选检查", [])
    compressed = []
    for item in candidates:
        entries = item.get("入口候选", [])
        existing_entries = [entry for entry in entries if entry.get("存在") is True]
        compressed.append(
            {
                "候选根目录": item.get("路径", ""),
                "根目录存在": item.get("存在", False),
                "识别说明": item.get("识别说明", ""),
                "入口候选数": len(entries),
                "已存在入口数": len(existing_entries),
                "可识别": item.get("可识别", False),
            }
        )
    return {
        "当前可识别": check.get("可识别", False),
        "当前可用": check.get("可用", False),
        "识别结论": check.get("识别结论", "未识别"),
        "可调用入口路径": check.get("可调用入口路径", ""),
        "候选压缩": compressed,
        "缺口": [
            "提供真实 MoneyPrinterTurbo 根目录",
            "确认 start.bat、app\\main.py 或 webui\\Main.py 其中一个入口存在",
            "确认 Python/虚拟环境、项目依赖、模型与素材配置",
            "通过真实渲染最终启用门禁前仍不得调用",
        ],
    }


def imagemagick_summary(render: dict) -> dict:
    check = render.get("ImageMagick检查", {})
    which_magick = shutil.which("magick")
    return {
        "当前可识别": check.get("可识别", False),
        "当前可用": check.get("可用", False),
        "既有记录路径": check.get("路径", ""),
        "PATH只读识别结果": which_magick or "",
        "检查方式": "仅使用 shutil.which 做 PATH 识别，不执行 magick 或 magick -version",
        "错误": check.get("错误", ""),
        "缺口": [
            "安装 ImageMagick",
            "确保 magick 命令进入 PATH",
            "人工确认版本后再进入后续门禁",
            "本包不执行 magick，不写系统环境变量",
        ],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    disabled = read_json(DISABLED_GATE)
    render = read_json(RENDER_PRECHECK)
    publish = read_json(PUBLISH_PRECHECK)
    gap_verify = read_json(PATH_GAP_VERIFY)

    money = moneyprinter_summary(render)
    image = imagemagick_summary(render)

    status = "blocked"
    install_ready = bool(money["当前可识别"] and image["当前可识别"])
    evidence = {
        "名称": "视频真实渲染环境缺口证据压缩与安装识别清单",
        "生成时间": now_text(),
        "状态": status,
        "安装识别是否已满足": install_ready,
        "结论": "真实渲染环境仍不可用；MoneyPrinterTurbo 与 ImageMagick 仍需人工补齐或确认。",
        "来源文件": {
            "禁用态检查": str(DISABLED_GATE),
            "渲染预检": str(RENDER_PRECHECK),
            "发布预检": str(PUBLISH_PRECHECK),
            "候选路径缺口验收": str(PATH_GAP_VERIFY),
        },
        "当前门禁摘要": {
            "真实渲染禁用态": disabled.get("执行器状态", ""),
            "是否调用剪辑软件": disabled.get("是否调用剪辑软件", None),
            "是否生成真实媒体": disabled.get("是否生成真实媒体", None),
            "渲染总体状态": render.get("总体状态", ""),
            "环境状态": render.get("环境状态", ""),
            "可进入真实渲染": render.get("可进入真实渲染", None),
            "真实渲染启用": render.get("真实渲染启用", None),
            "发布总体状态": publish.get("总体状态", ""),
            "可进入真实发布": publish.get("可进入真实发布", None),
            "真实发布启用": publish.get("真实发布启用", None),
        },
        "MoneyPrinterTurbo压缩证据": money,
        "ImageMagick压缩证据": image,
        "Chrome与发布桥梁": {
            "Chrome可用": render.get("Chrome检查", {}).get("可用", False),
            "发布桥梁命令可用": publish.get("命令检查", {}).get("可用", False),
            "浏览器运行时可用": publish.get("浏览器运行时检查", {}).get("可用", False),
            "说明": "Chrome、发布桥梁或浏览器运行时可用不等于真实渲染/真实发布放行。",
        },
        "阻断项压缩": [
            *render.get("阻断项", []),
            *publish.get("阻断项", []),
        ],
        "下一步人工补齐清单": [
            "确认或放置 MoneyPrinterTurbo 根目录。",
            "确认 MoneyPrinterTurbo 可调用入口文件存在。",
            "安装 ImageMagick 并让 magick 进入 PATH。",
            "补齐真实渲染白名单材料与人工签收。",
            "重新运行只读识别和预检，仍不得直接真实渲染。",
        ],
        "既有候选路径缺口验收摘要": {
            "验收结论": gap_verify.get("验收结论", ""),
            "通过数": gap_verify.get("通过数", None),
            "错误数": gap_verify.get("错误数", None),
        },
        "安全边界": {
            "调用MoneyPrinterTurbo": False,
            "执行ImageMagick": False,
            "执行magick": False,
            "执行magick_version": False,
            "真实渲染": False,
            "生成真实视频": False,
            "上传发布": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "修改企业微信公共配置": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载19310": False,
            "重载19302": False,
            "安装软件": False,
            "写系统环境变量": False,
        },
    }

    outputs = {
        "总包JSON": OUT_DIR / "视频真实渲染环境缺口证据压缩与安装识别清单_最新.json",
        "总包Markdown": OUT_DIR / "视频真实渲染环境缺口证据压缩与安装识别清单_最新.md",
        "安装识别清单": OUT_DIR / "视频真实渲染安装识别清单_最新.md",
        "阻断证据压缩表": OUT_DIR / "视频真实渲染阻断证据压缩表_最新.md",
        "人工补齐清单": OUT_DIR / "视频真实渲染人工补齐清单_最新.md",
    }
    evidence["输出文件"] = {k: str(v) for k, v in outputs.items()}
    write_json(outputs["总包JSON"], evidence)

    summary_lines = [
        f"- 生成时间：{evidence['生成时间']}",
        f"- 状态：{evidence['状态']}",
        f"- 结论：{evidence['结论']}",
        f"- MoneyPrinterTurbo 可识别：{money['当前可识别']}",
        f"- ImageMagick 可识别：{image['当前可识别']}",
        f"- 可进入真实渲染：{evidence['当前门禁摘要']['可进入真实渲染']}",
        f"- 可进入真实发布：{evidence['当前门禁摘要']['可进入真实发布']}",
        "",
        "## 输出文件",
        "",
        *[f"- {name}：{path}" for name, path in evidence["输出文件"].items()],
    ]
    write_md(outputs["总包Markdown"], "视频真实渲染环境缺口证据压缩与安装识别清单", summary_lines)

    identify_lines = [
        "| 项目 | 当前识别 | 当前可用 | 缺口 |",
        "| --- | --- | --- | --- |",
        f"| MoneyPrinterTurbo | {money['当前可识别']} | {money['当前可用']} | {'；'.join(money['缺口'])} |",
        f"| ImageMagick/magick | {image['当前可识别']} | {image['当前可用']} | {'；'.join(image['缺口'])} |",
    ]
    write_md(outputs["安装识别清单"], "视频真实渲染安装识别清单", identify_lines)

    block_lines = ["| 阻断项 |", "| --- |"]
    for item in evidence["阻断项压缩"]:
        block_lines.append(f"| {item} |")
    write_md(outputs["阻断证据压缩表"], "视频真实渲染阻断证据压缩表", block_lines)

    todo_lines = [f"{idx}. {item}" for idx, item in enumerate(evidence["下一步人工补齐清单"], 1)]
    write_md(outputs["人工补齐清单"], "视频真实渲染人工补齐清单", todo_lines)
    print(json.dumps({"status": evidence["状态"], "output": str(outputs["总包JSON"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
