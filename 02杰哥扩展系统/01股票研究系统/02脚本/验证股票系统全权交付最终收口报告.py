# -*- coding: utf-8 -*-
"""
名称：验证股票系统全权交付最终收口报告.py
作用：验收 242 股票系统全权交付最终收口报告。
安全边界：只读取 242 报告与相关证据，只写 242 验收结果；不发送企业微信，不触发 n8n，不调用券商接口，不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "242股票系统全权交付最终收口"
REPORT_JSON = OUT_DIR / "股票系统全权交付最终收口报告_最新.json"


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


def check(condition: bool, name: str, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def path_exists(path_text: str) -> bool:
    return bool(path_text) and Path(path_text).exists()


def main() -> int:
    data = load_json(REPORT_JSON)
    send_result = data.get("真实灰度发送结果", {})
    safety = data.get("安全边界", {})
    checks_dict = data.get("检查项", {})
    generated_paths = data.get("生成或修改的文件路径", [])

    checks = [
        check(REPORT_JSON.exists(), "242报告存在", str(REPORT_JSON)),
        check(data.get("总结论") == "通过", "总结论通过", data.get("总结论")),
        check(all(checks_dict.values()) if checks_dict else False, "内置检查项全通过", checks_dict),
        check(len(data.get("已完成清单", [])) >= 7, "已完成清单覆盖核心任务", data.get("已完成清单", [])),
        check(len(data.get("验收结果", [])) >= 4 and all(item.get("结论") == "通过" for item in data.get("验收结果", [])), "关键验收包全部通过", data.get("验收结果", [])),
        check(send_result.get("真实发送成功") is True, "单条真实灰度发送成功", send_result),
        check(send_result.get("目标用户") == "ChenXiaoJie", "发送目标为本人白名单", send_result.get("目标用户")),
        check(bool(send_result.get("企业微信msgid")), "企业微信msgid存在", send_result.get("企业微信msgid")),
        check("3/5" in str(send_result.get("当天计数", "")), "当天计数记录为3/5", send_result.get("当天计数")),
        check(path_exists(send_result.get("发送日志", "")), "股票侧发送日志存在", send_result.get("发送日志")),
        check(path_exists(send_result.get("公共发送器日志", "")), "公共发送器日志存在", send_result.get("公共发送器日志")),
        check("拦截" in str(send_result.get("前置未确认尝试", "")), "前置未确认尝试已被拦截", send_result.get("前置未确认尝试")),
        check(safety.get("触发n8n") is False, "n8n未触发", safety),
        check(safety.get("调用券商接口") is False and safety.get("自动交易") is False and safety.get("下单") is False, "券商/交易/下单均关闭", safety),
        check(safety.get("写正式库") is False and safety.get("重启正式服务") is False, "未写正式库且未重启正式服务", safety),
        check(safety.get("群发") is False and safety.get("外部客户发送") is False, "未群发且未向外部客户发送", safety),
        check(safety.get("输出密钥") is False, "未输出密钥", safety),
        check(len(data.get("回滚证据", [])) >= 5, "回滚证据完整", data.get("回滚证据", [])),
        check(all(path_exists(path) for path in generated_paths if "00公共组件" not in path), "股票系统生成路径存在", generated_paths),
        check(data.get("是否还有阻塞") == "无本轮交付阻塞", "无本轮交付阻塞", data.get("是否还有阻塞")),
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "股票系统全权交付最终收口报告验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
    }
    write_json(OUT_DIR / "股票系统全权交付最终收口报告验收_最新.json", result)
    write_text(
        OUT_DIR / "股票系统全权交付最终收口报告验收_最新.md",
        "\n".join([
            "# 股票系统全权交付最终收口报告验收",
            "",
            f"- 结论：{result['结论']}",
            f"- 通过数量：{result['通过数量']}",
            f"- 失败数量：{result['失败数量']}",
            "",
        ]),
    )
    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"]}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
