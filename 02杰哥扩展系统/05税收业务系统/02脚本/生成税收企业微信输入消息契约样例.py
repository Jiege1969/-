# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信输入消息契约样例.py
作用：基于输入消息契约，生成“杰哥工作秘书”输入侧本地预演样例。
安全边界：只生成本地输入样例；不接收真实企业微信回调、不读取凭据、不联网、不真实发送。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
CONTRACT = ROOT / "01配置" / "税收企业微信输入消息契约.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信输入消息契约样例_最新.json"
OUT_MD = OUT_DIR / "税收企业微信输入消息契约样例_最新.md"


RAW_QUESTION = "我们公司2025年有研发项目，想问研发费用加计扣除能不能享受？目前有立项书和部分费用辅助账，项目创新性资料还没整理。"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def mask_sensitive(text: str) -> str:
    patterns = [
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+",
        r"\b1[3-9]\d{9}\b",
        r"\b\d{17}[\dXx]\b",
        r"\b\d{12,19}\b",
        r"\b[0-9A-Z]{15,20}\b",
    ]
    masked = text
    for pattern in patterns:
        masked = re.sub(pattern, "[已脱敏]", masked)
    return masked


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    contract = load_json(CONTRACT)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    masked_question = mask_sensitive(RAW_QUESTION)
    sample = {
        "名称": "税收企业微信输入消息契约样例",
        "生成时间": now,
        "契约来源": str(CONTRACT),
        "输入样例": {
            "消息ID": "wecom-tax-input-sample-001",
            "接收时间": now,
            "机器人名称": "杰哥工作秘书",
            "提问人标识": "internal_user_masked",
            "原始问题": masked_question,
            "问题摘要": "咨询2025年研发费用加计扣除政策分析条件。",
            "业务事项": "研发费用加计扣除适用条件分析",
            "适用税种": "企业所得税",
            "所属期间": "2025年度",
            "地区": "待补充",
            "业务事实": {
                "纳税人类型": "待补充",
                "企业主体": "待补充",
                "事项类型": "研发费用加计扣除",
                "金额口径": "不测算金额",
                "资料来源": "企业微信用户输入",
                "已提供资料": ["立项书", "部分费用辅助账"],
                "尚缺资料": ["项目创新性资料", "研发费用归集明细", "所属地区口径", "企业主体和征收方式"]
            },
            "附件提示": {
                "是否提到附件": True,
                "附件名称": ["立项书", "费用辅助账"],
                "附件类型": ["项目资料", "财务资料"],
                "附件是否已入库": False,
                "附件待处理事项": ["待人工上传或登记", "待脱敏", "待证据库关联"]
            },
            "脱敏状态": "masked",
            "输入状态": "pending_evidence_match",
            "待补充字段": ["企业主体", "纳税人类型", "地区", "项目创新性资料", "费用归集明细"],
            "禁止动作": contract.get("禁止动作", []),
            "来源通道": "企业微信/杰哥工作秘书"
        },
        "安全边界": contract.get("安全边界", {})
    }
    OUT_JSON.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding="utf-8")
    item = sample["输入样例"]
    lines = [
        "# 税收企业微信输入消息契约样例",
        "",
        f"- 生成时间：{now}",
        f"- 机器人名称：{item['机器人名称']}",
        f"- 输入状态：{item['输入状态']}",
        f"- 业务事项：{item['业务事项']}",
        f"- 适用税种：{item['适用税种']}",
        f"- 所属期间：{item['所属期间']}",
        f"- 脱敏状态：{item['脱敏状态']}",
        "",
        "## 问题摘要",
        "",
        f"- {item['问题摘要']}",
        "",
        "## 待补充字段",
        "",
    ]
    for field in item["待补充字段"]:
        lines.append(f"- {field}")
    lines.extend(["", "## 禁止动作", ""])
    for action in item["禁止动作"]:
        lines.append(f"- {action}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in sample["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "输入状态": item["输入状态"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
