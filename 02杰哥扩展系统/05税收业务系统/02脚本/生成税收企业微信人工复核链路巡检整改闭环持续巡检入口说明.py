# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENTRY_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = ENTRY_DIR / "人工复核链路巡检整改闭环持续巡检入口说明"
OUT_JSON = OUT_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明.json"
OUT_MD = OUT_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明.md"
LATEST_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明_最新.json"
LATEST_MD = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明_最新.md"

TRANSFER_JSON = ENTRY_DIR / "税收企业微信人工复核链路巡检整改闭环阶段总回传记录_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def copy_latest(src: Path, dst: Path) -> None:
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    transfer = load_json(TRANSFER_JSON)

    manual_commands = [
        "python 02脚本\\验证税收企业微信人工复核链路持续巡检规则.py",
        "python 02脚本\\验证税收企业微信人工复核链路持续巡检样例演练.py",
        "python 02脚本\\验证税收企业微信人工复核链路巡检失败整改模板.py",
        "python 02脚本\\验证税收企业微信人工复核链路巡检整改后再校验清单.py",
        "python 02脚本\\验证税收企业微信人工复核链路巡检整改闭环阶段收口索引.py",
        "python 02脚本\\验证税收企业微信人工复核链路巡检整改闭环阶段总回传记录.py",
        "python 02脚本\\生成税收系统当前阶段收口验收与下一步队列.py",
        "python 02脚本\\验证税收系统当前阶段收口验收与下一步队列.py",
    ]
    explanation = {
        "名称": "税收企业微信人工复核链路巡检整改闭环持续巡检入口说明",
        "生成时间": now,
        "资产身份": "税务线本地入口说明，不创建自动化任务，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座 / 待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "引用阶段总回传": str(TRANSFER_JSON),
        "阶段总回传是否存在": bool(transfer),
        "入口类型": [
            {
                "类型": "本线手动入口",
                "说明": "由税务线施工人员在税务系统目录内手动运行本地验证脚本。",
                "是否自动创建任务": False,
                "是否启动服务": False,
            },
            {
                "类型": "总管只读调度入口",
                "说明": "总管如需整合，只能只读吸收本说明和回传记录；是否配置调度由总管线另行判断。",
                "是否自动修改总管文件": False,
                "是否允许本线实施": False,
            },
        ],
        "建议本地巡检命令顺序": manual_commands,
        "触发前检查": [
            "确认当前目录为税收业务系统目录。",
            "确认不读取企业微信凭据，不接真实账号。",
            "确认不启动或重启任何服务，不新增或修改端口。",
            "确认本次只运行本地生成/验证脚本和总收口脚本。",
        ],
        "通过标准": [
            "所有巡检整改闭环相关验收脚本返回失败数量为0。",
            "当前阶段总收口缺失数量为0、失败数量为0。",
            "安全边界全部保持False。",
            "输出继续标注政策证据底座 / 待复核分析草案，不是正式税务意见。",
        ],
        "下一步建议": [
            "生成税收企业微信人工复核链路巡检整改闭环一键本地预检脚本，按入口说明顺序串联本地验证脚本。",
        ],
        "安全边界": {
            "是否创建自动化任务": False,
            "是否启动或重启服务": False,
            "是否新增或修改端口": False,
            "是否触发n8n": False,
            "是否读取或保存企业微信凭据": False,
            "是否企业微信真实发送": False,
            "是否修改公共企业微信配置": False,
            "是否修改总管文件": False,
            "是否写正式库": False,
            "是否生成正式税务结论": False,
            "是否删除或移动旧资产": False,
        },
    }

    OUT_JSON.write_text(json.dumps(explanation, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核链路巡检整改闭环持续巡检入口说明",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：税务线本地入口说明，不创建自动化任务，不启动服务，不真实发送企业微信，不写正式库，不是正式税务结论。",
        "",
        "## 入口类型",
        "",
    ]
    for item in explanation["入口类型"]:
        lines.append(f"### {item['类型']}")
        lines.append(f"- 说明：{item['说明']}")
        lines.append(f"- 是否自动创建任务：{item.get('是否自动创建任务', False)}")
        lines.append(f"- 是否启动服务：{item.get('是否启动服务', False)}")
        lines.append(f"- 是否自动修改总管文件：{item.get('是否自动修改总管文件', False)}")
        lines.append("")
    lines.extend(["## 建议本地巡检命令顺序", ""])
    for item in manual_commands:
        lines.append(f"- `{item}`")
    lines.extend(["", "## 触发前检查", ""])
    for item in explanation["触发前检查"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 通过标准", ""])
    for item in explanation["通过标准"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in explanation["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步建议", ""])
    for item in explanation["下一步建议"]:
        lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    copy_latest(OUT_JSON, LATEST_JSON)
    copy_latest(OUT_MD, LATEST_MD)
    print(json.dumps({"状态": "完成", "输出": str(LATEST_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
