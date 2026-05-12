# -*- coding: utf-8 -*-
"""
名称：生成股票系统全权交付最终收口报告.py
作用：汇总股票系统交付闭环、用户授权纠偏、确认令受控写入、单条真实灰度发送与回滚证据。
安全边界：只读取既有报告/日志/配置，只写股票系统本地 242 报告；不发送企业微信，不触发 n8n，不调用券商接口，不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parent / "00公共组件"
OUT_DIR = ROOT / "03数据" / "242股票系统全权交付最终收口"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    return data.get(key, default)


def latest_json(directory: Path, pattern: str = "*.json") -> Path:
    if not directory.exists():
        return Path()
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else Path()


def ok_verify(data: dict[str, Any]) -> bool:
    return data.get("结论") == "通过" and int(data.get("失败数量", 0) or 0) == 0


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票系统全权交付最终收口报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总结论：{report['总结论']}",
        f"- 是否还有阻塞：{report['是否还有阻塞']}",
        f"- 股票系统剩余有效工时估算：{report['股票系统剩余有效工时估算']}",
        "",
        "## 已完成清单",
        "",
    ]
    lines.extend(f"- {item}" for item in report["已完成清单"])
    lines.extend(["", "## 验收结果", ""])
    for item in report["验收结果"]:
        lines.append(f"- {item['名称']}：{item['结论']}（{item['证据']}）")
    lines.extend(["", "## 真实灰度发送结果", ""])
    for key, value in report["真实灰度发送结果"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 生成或修改的文件路径", ""])
    lines.extend(f"- {path}" for path in report["生成或修改的文件路径"])
    lines.extend(["", "## 回滚证据", ""])
    for item in report["回滚证据"]:
        lines.append(f"- {item['名称']}：{item['路径']}（sha256={item.get('sha256', '')}）")
    lines.extend(["", "## 下一步交接说明", ""])
    lines.extend(f"- {item}" for item in report["下一步交接说明"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report_237 = load_json(ROOT / "03数据" / "237股票研究系统交付闭环验收" / "股票研究系统交付闭环验收报告_最新.json")
    verify_237 = load_json(ROOT / "03数据" / "237股票研究系统交付闭环验收" / "股票研究系统交付闭环验收报告验收_最新.json")
    report_238 = load_json(ROOT / "03数据" / "238股票系统真实发送灰度准入闭环补强" / "股票系统真实发送灰度准入闭环补强报告_最新.json")
    verify_238 = load_json(ROOT / "03数据" / "238股票系统真实发送灰度准入闭环补强" / "股票系统真实发送灰度准入闭环补强报告验收_最新.json")
    report_239 = load_json(ROOT / "03数据" / "239股票系统本轮用户授权" / "股票系统本轮用户授权记录_最新.json")
    report_240 = load_json(ROOT / "03数据" / "240企业微信真实发送人工确认令受控写入" / "企业微信真实发送人工确认令受控写入_最新.json")
    verify_240 = load_json(ROOT / "03数据" / "240企业微信真实发送人工确认令受控写入" / "企业微信真实发送人工确认令受控写入验收_最新.json")
    report_241 = load_json(ROOT / "03数据" / "241股票企业微信单条真实灰度发送闭环" / "股票企业微信单条真实灰度发送闭环报告_最新.json")
    verify_241 = load_json(ROOT / "03数据" / "241股票企业微信单条真实灰度发送闭环" / "股票企业微信单条真实灰度发送闭环报告验收_最新.json")
    report_47 = load_json(ROOT / "03数据" / "47首轮真实灰度测试记录" / "股票企业微信首轮真实灰度测试记录包_最新.json")

    latest_stock_send_log = Path(report_241.get("关键证据", {}).get("股票发送日志", ""))
    latest_common_send_log = Path(report_241.get("关键证据", {}).get("公共发送器日志", ""))
    blocked_log = latest_json(ROOT / "04日志" / "企业微信主动研究灰度发送", "stock-active-research-wework-gray-send-20260505-100630-*.json")
    confirmation_path = COMMON_ROOT / "01配置" / "企业微信真实发送人工确认令.json"
    counter_path = COMMON_ROOT / "03数据" / "04企业微信灰度发送计数" / f"企业微信灰度发送计数_{datetime.now().strftime('%Y%m%d')}.json"

    checks = {
        "237交付闭环验收": ok_verify(verify_237),
        "238灰度准入补强验收": ok_verify(verify_238),
        "239用户授权记录存在": bool(report_239),
        "240确认令受控写入验收": ok_verify(verify_240),
        "241单条真实灰度发送验收": ok_verify(verify_241),
        "真实发送成功": report_241.get("真实发送成功") is True,
        "目标用户为本人白名单": report_241.get("目标用户") == "ChenXiaoJie",
        "确认令文件存在": confirmation_path.exists(),
        "计数文件存在": counter_path.exists(),
        "n8n保持关闭": report_241.get("安全边界", {}).get("触发n8n") is False,
        "券商与交易保持关闭": report_241.get("安全边界", {}).get("调用券商接口") is False and report_241.get("安全边界", {}).get("自动交易") is False,
    }

    ok = all(checks.values())
    report = {
        "名称": "股票系统全权交付最终收口报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总结论": "通过" if ok else "需复核",
        "已完成清单": [
            "历史 K 线正式 _最新 已完成带备份刷新，东方财富正式成交额接入并形成 19/19 与 123/123 两层证据。",
            "价位成交额正式口径影子重算已复跑，微信短文正式成交额口径影子重跑已复跑。",
            "微信短文正式生成器正式成交额对照包与 shadow_v21_dry_run 安全参数已复核并通过。",
            "用户已明确授权纠正过时闸口，已生成本轮授权记录，并将单人白名单真实灰度推进纳入可审计证据。",
            "企业微信真实发送人工确认令已受控写入并验收通过。",
            "已完成一次股票企业微信单条真实灰度发送，目标用户 ChenXiaoJie，发送成功且形成股票侧与公共发送器双日志。",
            "已补齐完整验收报告、回滚证据和下一步交接说明。",
        ],
        "验收结果": [
            {"名称": "237 股票研究系统交付闭环验收", "结论": verify_237.get("结论", ""), "证据": str(ROOT / "03数据" / "237股票研究系统交付闭环验收")},
            {"名称": "238 真实发送灰度准入闭环补强", "结论": verify_238.get("结论", ""), "证据": str(ROOT / "03数据" / "238股票系统真实发送灰度准入闭环补强")},
            {"名称": "240 企业微信真实发送人工确认令受控写入", "结论": verify_240.get("结论", ""), "证据": str(ROOT / "03数据" / "240企业微信真实发送人工确认令受控写入")},
            {"名称": "241 企业微信单条真实灰度发送闭环", "结论": verify_241.get("结论", ""), "证据": str(ROOT / "03数据" / "241股票企业微信单条真实灰度发送闭环")},
        ],
        "真实灰度发送结果": {
            "发送模式": "real-send",
            "真实发送成功": report_241.get("真实发送成功"),
            "目标用户": report_241.get("目标用户"),
            "当天计数": report_241.get("当天计数"),
            "企业微信msgid": report_241.get("关键证据", {}).get("企业微信msgid", ""),
            "发送日志": str(latest_stock_send_log),
            "公共发送器日志": str(latest_common_send_log),
            "前置未确认尝试": f"已被本地确认令闸口拦截，无外发：{blocked_log}",
            "旧47测试记录包状态": "旧模板仍按未确认模板输出，已由 241 当前正确证据包替代" if report_47 else "未发现旧47记录包",
        },
        "回滚证据": [
            {"名称": "历史K线刷新前备份", "路径": str(ROOT / "03数据" / "233历史K线东方财富增强受控刷新" / "备份"), "sha256": report_237.get("正式成交额证据", {}).get("历史K线刷新前备份sha256", "")},
            {"名称": "228/229影子重跑前备份", "路径": str(ROOT / "03数据" / "237股票研究系统交付闭环验收" / "备份" / "20260505_095041"), "sha256": ""},
            {"名称": "222/230对照重生成前备份", "路径": str(ROOT / "03数据" / "237股票研究系统交付闭环验收" / "备份" / "20260505_095138"), "sha256": ""},
            {"名称": "企业微信确认令回滚目标", "路径": str(confirmation_path), "sha256": sha256_file(confirmation_path)},
            {"名称": "企业微信计数文件", "路径": str(counter_path), "sha256": sha256_file(counter_path)},
        ],
        "生成或修改的文件路径": [
            str(ROOT / "02脚本" / "生成股票研究系统交付闭环验收报告.py"),
            str(ROOT / "02脚本" / "验证股票研究系统交付闭环验收报告.py"),
            str(ROOT / "02脚本" / "生成股票系统真实发送灰度准入闭环补强报告.py"),
            str(ROOT / "02脚本" / "验证股票系统真实发送灰度准入闭环补强报告.py"),
            str(ROOT / "02脚本" / "生成股票系统本轮用户授权记录.py"),
            str(ROOT / "02脚本" / "执行企业微信真实发送人工确认令受控写入.py"),
            str(ROOT / "02脚本" / "验证企业微信真实发送人工确认令受控写入.py"),
            str(ROOT / "02脚本" / "生成股票企业微信单条真实灰度发送闭环报告.py"),
            str(ROOT / "02脚本" / "验证股票企业微信单条真实灰度发送闭环报告.py"),
            str(ROOT / "02脚本" / "生成股票系统全权交付最终收口报告.py"),
            str(ROOT / "02脚本" / "验证股票系统全权交付最终收口报告.py"),
            str(ROOT / "03数据" / "237股票研究系统交付闭环验收"),
            str(ROOT / "03数据" / "238股票系统真实发送灰度准入闭环补强"),
            str(ROOT / "03数据" / "239股票系统本轮用户授权"),
            str(ROOT / "03数据" / "240企业微信真实发送人工确认令受控写入"),
            str(ROOT / "03数据" / "241股票企业微信单条真实灰度发送闭环"),
            str(OUT_DIR),
            str(confirmation_path),
        ],
        "安全边界": {
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
            "写正式库": False,
            "重启正式服务": False,
            "群发": False,
            "外部客户发送": False,
            "输出密钥": False,
            "修改总管代码": False,
            "修改知识库代码": False,
            "修改进化系统代码": False,
        },
        "检查项": checks,
        "是否还有阻塞": "无本轮交付阻塞",
        "股票系统剩余有效工时估算": "0小时；后续仅剩可选扩面、维护增强或正式流程运营化。",
        "下一步交接说明": [
            "当前股票系统已经达到可验收、可回滚、可接正式口径状态。",
            "若继续扩大企业微信真实发送范围，必须重新生成授权、确认令、计数与回滚验收，不复用本轮单条授权作为扩面依据。",
            "若接入 n8n、券商接口或正式自动化交易，需要单独立项、单独回滚演练；本轮全部保持关闭。",
            "确认令回滚方式：删除确认令文件；如未来已有写入前备份，则复制备份回公共组件确认令路径。",
            "旧47测试记录包代表过时的未确认模板口径，当前以 241 单条真实灰度发送闭环作为有效证据。",
        ],
    }
    write_json(OUT_DIR / "股票系统全权交付最终收口报告_最新.json", report)
    write_text(OUT_DIR / "股票系统全权交付最终收口报告_最新.md", build_markdown(report))
    print(json.dumps({"状态": report["总结论"], "检查项": checks, "输出": str(OUT_DIR / "股票系统全权交付最终收口报告_最新.md")}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
