# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度回滚清单影子模板.py
作用：生成知识库问答灰度回滚清单影子模板，登记未来灰度的可回退对象和默认不执行状态。
触发方式：python 生成知识库问答灰度回滚清单影子模板.py
安全边界：只读预检报告并写回滚模板；不执行回滚、不放行灰度、不接正式入口、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
PRECHECK = OUT_DIR / "知识库问答灰度样本填写预检验收_最新.json"
REPORT_JSON = OUT_DIR / "知识库问答灰度回滚清单影子模板_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度回滚清单影子模板_最新.md"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    precheck = load_json(PRECHECK)
    precheck_ok = precheck.get("结论") == "通过" and int(precheck.get("失败数量", 0)) == 0
    rollback = {
        "名称": "知识库问答灰度回滚清单影子模板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if precheck_ok else "预检不足",
        "来源预检": str(PRECHECK),
        "默认状态": "影子模板，未执行回滚",
        "回滚对象": [
            {"对象": "影子入口配置", "当前状态": "未创建", "回滚动作": "删除影子入口配置", "是否执行": False},
            {"对象": "灰度样本清单", "当前状态": "空样本", "回滚动作": "清空灰度样本清单", "是否执行": False},
            {"对象": "企业微信助手知识库显示", "当前状态": "未放行", "回滚动作": "关闭知识库显示开关", "是否执行": False},
            {"对象": "n8n/Webhook", "当前状态": "关闭", "回滚动作": "保持关闭并验收", "是否执行": False},
            {"对象": "知识库写库", "当前状态": "禁用态", "回滚动作": "保持禁用态并验收", "是否执行": False}
        ],
        "回滚触发条件": [
            "出现真实发送开关被打开。",
            "出现 n8n/Webhook 被触发。",
            "出现写 Qdrant/PostgreSQL 行为。",
            "证据卡缺失或人工复核失败。",
            "用户要求停止灰度。"
        ],
        "回滚验收条件": [
            "企业微信真实发送为 false。",
            "Webhook 和 n8n 为 false。",
            "灰度样本数量回到 0 或全部标记为禁用。",
            "知识库写库禁用态验收通过。",
            "无干扰队列重新回到只读观察项。"
        ],
        "安全边界": {
            "执行回滚": False,
            "删除配置": False,
            "放行灰度": False,
            "接入正式入口": False,
            "调用企业微信接口": False,
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "启动问答": False,
            "写正式知识库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
        },
    }
    lines = [
        "# 知识库问答灰度回滚清单影子模板",
        "",
        f"- 生成时间：{rollback['生成时间']}",
        f"- 结论：{rollback['结论']}",
        f"- 默认状态：{rollback['默认状态']}",
        "",
        "## 回滚对象",
        "",
    ]
    for item in rollback["回滚对象"]:
        lines.append(f"- {item['对象']}：{item['当前状态']}；动作：{item['回滚动作']}；执行：{item['是否执行']}")
    lines.extend(["", "## 回滚触发条件", ""])
    for item in rollback["回滚触发条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 回滚验收条件", ""])
    for item in rollback["回滚验收条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成回滚清单影子模板，不执行回滚，不删除配置，不放行灰度，不接正式入口，不触发 n8n，不写库。")
    write_json(REPORT_JSON, rollback)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": rollback["结论"], "回滚对象数量": len(rollback["回滚对象"]), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if precheck_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
