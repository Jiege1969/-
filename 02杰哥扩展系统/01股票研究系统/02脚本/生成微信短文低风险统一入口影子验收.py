# -*- coding: utf-8 -*-
"""
名称：生成微信短文低风险统一入口影子验收.py
作用：基于224小样本对照包和正式入口源码快照，生成微信短文低风险统一入口影子验收包。
安全边界：只读本地对照包和入口源码；只写 03数据/225低风险统一入口影子验收；不执行正式生成器、不改入口、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "225低风险统一入口影子验收"
SAMPLE_224_JSON = DATA / "224微信短文小样本对照包" / "微信短文小样本对照包_最新.json"
SAMPLE_224_VERIFY = DATA / "224微信短文小样本对照包" / "微信短文小样本对照包验收_最新.json"
FORMAL_GENERATOR = ROOT / "02脚本" / "生成企业微信单股短回复.py"
BRIDGE_ENTRY = ROOT / "02脚本" / "股票企业微信桥接入口.py"
ASSISTANT_ENTRY = ROOT / "02脚本" / "股票助手入口.py"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"路径": str(path), "存在": False, "sha256": ""}
    stat = path.stat()
    return {
        "路径": str(path),
        "存在": True,
        "大小": stat.st_size,
        "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "sha256": sha256(path),
    }


def source_scan(path: Path) -> dict[str, Any]:
    text = read_text(path)
    return {
        "路径": str(path),
        "存在": path.exists(),
        "包含dry_run": "dry_run" in text or "dry-run" in text,
        "包含不发送边界": "不发送企业微信" in text or "发送企业微信" in text and "False" in text,
        "包含不触发n8n边界": "不触发n8n" in text or "触发n8n" in text and "False" in text,
        "包含不自动交易边界": "不自动交易" in text or "自动交易" in text and "False" in text,
        "写入目录命中": sorted(set(re.findall(r"03数据\\?[\\/][^\"']+|04日志\\?[\\/][^\"']+", text)))[:20],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 微信短文低风险统一入口影子验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、上游门禁",
        "",
    ]
    for key, value in report["上游门禁"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 二、入口源码扫描", ""])
    for item in report["入口源码扫描"]:
        lines.append(f"- `{item['路径']}`：存在={item['存在']}；dry_run={item['包含dry_run']}；不发送={item['包含不发送边界']}；不触发n8n={item['包含不触发n8n边界']}；不自动交易={item['包含不自动交易边界']}")
    lines.extend(["", "## 三、影子接入方案", ""])
    for item in report["低风险影子接入方案"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、阻断项", ""])
    for item in report["阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、入口快照", ""])
    for item in report["入口快照"]:
        lines.append(f"- `{item['路径']}`：sha256={item.get('sha256', '')[:12]}；大小={item.get('大小', 0)}")
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 七、下一步计划", "", report["下一步计划"], ""])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    sample_224 = load_json(SAMPLE_224_JSON)
    sample_224_verify = load_json(SAMPLE_224_VERIFY)
    gates = sample_224.get("准入门禁", {})
    allow_switch = gates.get("允许设计正式可控开关") is True
    shadow_only_allowed = (
        sample_224_verify.get("结论") == "通过"
        and gates.get("v21短文结构通过") is True
        and gates.get("v21禁用交易动作词通过") is True
    )
    report = {
        "名称": "微信短文低风险统一入口影子验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": (
            "统一入口可进入 dry_run 影子双写设计，但正式替换开关因历史成交额未正式化继续阻断。"
            if shadow_only_allowed and not allow_switch
            else "统一入口门禁已具备正式开关设计条件。"
        ),
        "读取文件": {
            "224小样本对照包": str(SAMPLE_224_JSON),
            "224验收": str(SAMPLE_224_VERIFY),
            "正式短回复生成器": str(FORMAL_GENERATOR),
            "股票企业微信桥接入口": str(BRIDGE_ENTRY),
            "股票助手入口": str(ASSISTANT_ENTRY),
        },
        "上游门禁": {
            "224验收通过": sample_224_verify.get("结论") == "通过",
            "v21短文结构通过": gates.get("v21短文结构通过") is True,
            "v21禁用交易动作词通过": gates.get("v21禁用交易动作词通过") is True,
            "历史成交额可解除估算降级": gates.get("历史成交额可解除估算降级") is True,
            "允许正式可控开关": allow_switch,
            "允许dry_run影子双写方案设计": shadow_only_allowed,
        },
        "入口源码扫描": [source_scan(FORMAL_GENERATOR), source_scan(BRIDGE_ENTRY), source_scan(ASSISTANT_ENTRY)],
        "低风险影子接入方案": [
            "`生成企业微信单股短回复.py` 默认行为保持不变，继续写 `03数据/24企业微信短回复` 和 `04日志/企业微信短回复`。",
            "未来只新增显式参数 `--shadow-v21-dry-run`，且默认关闭；开启后只额外读取 224 对照包并写出 shadow_v21 对照副本。",
            "桥接入口 `股票企业微信桥接入口.py` 和网页/API入口 `股票助手入口.py` 不直接引入 v21 模板，避免真实请求路径变化。",
            "当 223 的历史成交额正式回补未通过时，`--shadow-v21-dry-run` 只允许写影子对照，不允许替换 `短回复` 字段。",
            "正式发送、n8n、response_url、券商接口和服务重启不属于本入口影子验收范围。",
        ],
        "阻断项": [
            "历史成交额尚未正式化，不能解除估算降级。",
            "正式短回复模板替换继续阻断。",
            "企业微信真实发送和 n8n 接入继续阻断。",
            "入口脚本本轮只做哈希快照和方案验收，不修改源码。",
        ],
        "入口快照": [snapshot(FORMAL_GENERATOR), snapshot(BRIDGE_ENTRY), snapshot(ASSISTANT_ENTRY)],
        "安全边界": {
            "执行正式短回复生成器": False,
            "修改正式短回复生成器": False,
            "修改股票企业微信桥接入口": False,
            "修改股票助手入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "下一步计划": "先补历史K线东方财富成交额稳定回补；若仍要推进入口层，只能新增默认关闭的 dry_run 影子双写参数，并继续保持真实发送阻断。",
    }
    latest_json = OUT_DIR / "微信短文低风险统一入口影子验收_最新.json"
    latest_md = OUT_DIR / "微信短文低风险统一入口影子验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "允许dry_run影子双写方案设计": shadow_only_allowed,
        "允许正式可控开关": allow_switch,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
