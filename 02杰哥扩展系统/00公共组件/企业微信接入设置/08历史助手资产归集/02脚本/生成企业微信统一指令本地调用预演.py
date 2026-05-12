# -*- coding: utf-8 -*-
"""
名称：生成企业微信统一指令本地调用预演.py
作用：在不真实发送、不触发n8n的前提下，把企业微信统一指令路由结果转为本机低风险调用结果和可读回复预演。
触发方式：python 生成企业微信统一指令本地调用预演.py
依赖：Python标准库；企业微信统一指令路由预演规则.json；企业微信统一指令本地调用预演规则.json；本机股票助手和各模块状态摘要。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只进行本机低风险读取和股票本地技术分析调用；不真实发送企业微信；不触发Webhook；不触发n8n；不写正式库；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令本地调用预演脚本。
标识：wecom-unified-command-local-call-preview-generate
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
import urllib.request
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def route_message(message: str, route_config: dict[str, Any]) -> dict[str, Any]:
    normalized = message.strip().lower()
    rules = sorted(route_config.get("路由规则", []), key=lambda item: int(item.get("优先级", 100)))
    for rule in rules:
        keywords = [str(item).lower() for item in rule.get("关键词", [])]
        if any(keyword and keyword in normalized for keyword in keywords):
            return {"路由": rule.get("路由"), "目标系统": rule.get("目标系统"), "能力状态": rule.get("能力状态")}
    fallback = route_config.get("兜底路由", {})
    return {"路由": fallback.get("路由", "澄清一次"), "目标系统": fallback.get("目标系统", "06企业微信助手系统"), "能力状态": fallback.get("能力状态", "可用")}


def http_get_json(url: str, timeout: int = 12) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "jiege-wecom-local-preview/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body)


def read_markdown_excerpt(path: str | Path, max_lines: int = 8) -> str:
    target = Path(path)
    if not target.exists():
        return f"未找到状态摘要：{target}"
    lines = target.read_text(encoding="utf-8-sig").splitlines()
    clean = [line for line in lines if line.strip()]
    return "\n".join(clean[:max_lines])


def latest_stock_card_link(root: Path, stock: dict[str, Any]) -> str:
    """仅在最新图形报告与当前股票一致时返回链接，避免把旧图误配给新查询。"""
    card_meta = root.parent / "01股票研究系统" / "03数据" / "86图形报告" / "股票图形报告_最新.json"
    if not card_meta.exists():
        return ""
    data = load_json(card_meta)
    card_stock = data.get("股票", {})
    current_code = str(stock.get("代码") or stock.get("code") or "").lower()
    current_name = str(stock.get("名称") or stock.get("name") or "")
    card_code = str(card_stock.get("代码") or card_stock.get("code") or "").lower()
    card_name = str(card_stock.get("名称") or card_stock.get("name") or "")
    if (current_code and current_code == card_code) or (current_name and current_name == card_name):
        return str(data.get("公网PNGURL") or data.get("本地PNGURL") or "")
    return ""


def stock_reply(message: str, call_rule: dict[str, Any]) -> dict[str, Any]:
    url = str(call_rule.get("URL模板", "")).replace("{query}", urllib.parse.quote(message, encoding="utf-8"))
    data = http_get_json(url)
    stock = data.get("股票") or {}
    quote = data.get("行情") or {}
    decision = data.get("规则判断") or {}
    signal = decision.get("研究信号") or {}
    colored_marker = signal.get("企业微信标记") or signal.get("企业微信文本标记") or signal.get("标记", "-")
    card_link = latest_stock_card_link(module_root(), stock)
    if card_link.startswith("http://43.167.210.211/"):
        card_link = ""
    lines = [
        f"{stock.get('名称', message)}（{stock.get('代码', '-') }）",
        f"研究星级：{colored_marker}（{signal.get('颜色', '不标色')}，强度{signal.get('强度', '-') }）",
        f"最新价：{quote.get('最新价', '-')}，涨跌幅：{quote.get('涨跌幅', '-')}%。",
        f"研究信号：{signal.get('方向', '')}。{signal.get('说明', '这是研究助手输出，不构成交易指令。')}",
    ]
    if card_link:
        lines.insert(2, f"图形报告PNG：{card_link}")
    reply = "\n".join(lines)
    return {"调用状态": data.get("状态"), "回复预演": reply, "来源": url, "原始摘要": {"股票": stock, "行情": quote, "研究信号": signal}}


def knowledge_qa_reply(message: str, call_rule: dict[str, Any]) -> dict[str, Any]:
    script = Path(str(call_rule.get("脚本", "")))
    result_path = Path(str(call_rule.get("结果路径", "")))
    if not script.exists():
        return {"调用状态": "异常", "回复预演": "", "来源": str(script), "调用异常": f"知识库问答预演脚本不存在：{script}"}
    result = subprocess.run([sys.executable, str(script), message], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if result.returncode != 0:
        return {"调用状态": "异常", "回复预演": "", "来源": str(script), "调用异常": result.stderr.strip() or result.stdout.strip()}
    data = load_json(result_path) if result_path.exists() else {}
    qa_items = data.get("问答结果", [])
    first = qa_items[0] if qa_items else {}
    evidence = first.get("证据", [])
    preview = first.get("回答预演", "知识库本地问答预演未返回结果。")
    if len(preview) > 420:
        preview = preview[:420].rstrip() + "..."
    reply = f"{preview}\n\n证据片段：{len(evidence)}。"
    return {"调用状态": data.get("汇总", {}).get("状态", "完成"), "回复预演": reply, "来源": str(result_path), "原始摘要": {"问题": message, "证据数量": len(evidence)}}


def run_local_script(script_value: str, timeout: int = 60) -> dict[str, Any]:
    script = Path(str(script_value))
    if not script.exists():
        return {"可用": False, "退出码": 127, "标准输出": "", "标准错误": f"脚本不存在：{script}"}
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"可用": result.returncode == 0, "退出码": result.returncode, "标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}


def content_office_reply(message: str, call_rule: dict[str, Any]) -> dict[str, Any]:
    content_run = run_local_script(str(call_rule.get("内容预演脚本", "")))
    office_run = run_local_script(str(call_rule.get("办公预演脚本", "")))
    content_path = Path(str(call_rule.get("内容预演结果", "")))
    draft_path = Path(str(call_rule.get("办公草稿结果", "")))
    content_data = load_json(content_path) if content_path.exists() else {}
    draft_data = load_json(draft_path) if draft_path.exists() else {}
    previews = content_data.get("预演", [])
    templates = draft_data.get("草稿模板", [])
    preferred_type = "汇报" if "汇报" in message else "方案" if "方案" in message else "纪要" if "纪要" in message else ""
    selected = next((item for item in templates if item.get("材料类型") == preferred_type), templates[0] if templates else {})
    chapters = selected.get("章节", [])
    content_lines = []
    if previews:
        first = previews[0]
        actions = "、".join(str(item) for item in first.get("建议动作", [])[:4])
        content_lines.append(f"素材建议：{first.get('文件名', '当前素材')} -> {first.get('任务类型', '内容整理')}；{actions}。")
    if selected:
        content_lines.append(f"材料类型：{selected.get('材料类型')}；风格：{draft_data.get('默认风格', '稳重、清晰、条理化')}。")
        content_lines.extend(f"{idx + 1}. {chapter}" for idx, chapter in enumerate(chapters))
    reply = "\n".join(content_lines) if content_lines else "内容办公预演暂未生成可读框架。"
    reply += "\n\n说明：这是内容办公本地预演，不生成正式文档、不覆盖原文件、不外发。"
    ok = content_run.get("可用") is True and office_run.get("可用") is True and bool(content_lines)
    return {
        "调用状态": "完成" if ok else "异常",
        "回复预演": reply if ok else "",
        "来源": [str(content_path), str(draft_path)],
        "原始摘要": {
            "内容预演脚本": content_run,
            "办公预演脚本": office_run,
            "内容预演数量": content_data.get("预演数量", 0),
            "草稿模板数量": len(templates),
        },
    }


def video_preview_reply(message: str, call_rule: dict[str, Any]) -> dict[str, Any]:
    script_run = run_local_script(str(call_rule.get("脚本", "")))
    draft_path = Path(str(call_rule.get("脚本草稿", "")))
    storyboard_path = Path(str(call_rule.get("分镜计划", "")))
    theme_path = Path(str(call_rule.get("主题化预演结果", "")))
    draft = load_json(draft_path) if draft_path.exists() else {}
    storyboard = load_json(storyboard_path) if storyboard_path.exists() else {}
    theme = load_json(theme_path) if theme_path.exists() else {}
    structures = draft.get("脚本结构", [])
    shots = storyboard.get("镜头", [])
    titles = theme.get("封面标题预演", [])
    subtitles = theme.get("字幕要点", [])
    lines = [
        f"视频主题：{message}",
        f"口播风格：{draft.get('默认风格', '清晰、稳重、适合口播')}",
    ]
    if structures:
        lines.append("脚本结构：" + " / ".join(str(item.get("段落", "")) for item in structures[:4]))
    if shots:
        lines.append("分镜预演：")
        for shot in shots[:3]:
            lines.append(f"{shot.get('镜头编号')}. {shot.get('画面内容')}；字幕：{shot.get('字幕要点')}；约{shot.get('时长秒')}秒")
    if titles:
        lines.append("封面标题候选：" + "；".join(str(item) for item in titles[:3]))
    if subtitles and not shots:
        lines.append("字幕要点：" + "；".join(str(item.get("字幕", "")) for item in subtitles[:3]))
    reply = "\n".join(lines) + "\n\n说明：这是视频制作本地预演，不调用剪辑软件、不生成真实媒体、不上传发布。"
    ok = script_run.get("可用") is True and bool(lines)
    return {
        "调用状态": "完成" if ok else "异常",
        "回复预演": reply if ok else "",
        "来源": [str(draft_path), str(storyboard_path), str(theme_path)],
        "原始摘要": {
            "主题化脚本": script_run,
            "脚本结构数量": len(structures),
            "分镜数量": len(shots),
            "封面标题数量": len(titles),
        },
    }


def execute_local_call(message: str, route: dict[str, Any], call_config: dict[str, Any]) -> dict[str, Any]:
    route_name = str(route.get("路由") or "澄清一次")
    call_rule = call_config.get("允许本地调用", {}).get(route_name, {})
    method = call_rule.get("方式")
    if method == "http_get":
        result = stock_reply(message, call_rule)
    elif method == "knowledge_qa_preview":
        result = knowledge_qa_reply(message, call_rule)
    elif method == "content_office_preview":
        result = content_office_reply(message, call_rule)
    elif method == "video_preview":
        result = video_preview_reply(message, call_rule)
    elif method == "read_markdown":
        result = {"调用状态": "完成", "回复预演": read_markdown_excerpt(call_rule.get("路径", "")), "来源": call_rule.get("路径", "")}
    elif method == "read_markdown_group":
        parts = [read_markdown_excerpt(path, max_lines=5) for path in call_rule.get("路径", [])]
        result = {"调用状态": "完成", "回复预演": "\n\n".join(parts), "来源": call_rule.get("路径", [])}
    elif method == "paused_response":
        result = {
            "调用状态": "已暂停",
            "回复预演": "税收业务系统按当前约定暂停搭建和真实接入。当前只保留未来闸口设计，不执行抓取、登录、申报、写库等动作。",
            "来源": "暂停规则",
        }
    else:
        result = {"调用状态": "需澄清", "回复预演": "我需要你补充一下：这是要查股票、看系统状态、查资料、处理文档，还是做视频？", "来源": "澄清一次"}
    return {**route, **result, "真实发送企业微信": False, "触发n8n": False, "写旧系统": False, "交易接口": False}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信统一指令本地调用预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['状态']}",
        f"- 样例数量：{report['汇总']['样例数量']}",
        f"- 调用成功数量：{report['汇总']['调用成功数量']}",
        f"- 真实动作数量：{report['汇总']['真实动作数量']}",
        "",
        "## 回复预演",
        "",
    ]
    for item in report.get("调用结果", []):
        preview = str(item.get("回复预演", "")).replace("\n", " / ")
        lines.append(f"- {item.get('输入')} -> {item.get('路由')}：{preview[:180]}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 不真实发送企业微信。",
        "- 不触发Webhook、不触发n8n、不写正式库、不写旧系统。",
        "- 股票输出仍为研究助手结果，不接入交易接口。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    route_config = load_json(root / "01配置" / "企业微信统一指令路由预演规则.json")
    call_config = load_json(root / "01配置" / "企业微信统一指令本地调用预演规则.json")
    results: list[dict[str, Any]] = []
    for sample in route_config.get("预演样例", []):
        message = str(sample.get("输入", ""))
        route = route_message(message, route_config)
        try:
            result = execute_local_call(message, route, call_config)
            result["调用异常"] = ""
        except Exception as exc:  # noqa: BLE001
            result = {**route, "输入": message, "调用状态": "异常", "回复预演": "", "调用异常": str(exc), "真实发送企业微信": False, "触发n8n": False, "写旧系统": False, "交易接口": False}
        result["输入"] = message
        results.append(result)
    success = [item for item in results if item.get("调用状态") in {"完成", "healthy", "已暂停", "需澄清"} and item.get("回复预演")]
    real_actions = [
        item for item in results
        if item.get("真实发送企业微信") or item.get("触发n8n") or item.get("写旧系统") or item.get("交易接口")
    ]
    safety = call_config.get("安全边界", {})
    safety_ok = all(value is False for value in safety.values())
    status = "healthy" if len(success) == len(results) and not real_actions and safety_ok else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-local-call-preview",
        "所属系统": "02杰哥扩展系统/06企业微信助手系统",
        "汇总": {
            "状态": status,
            "样例数量": len(results),
            "调用成功数量": len(success),
            "真实动作数量": len(real_actions),
            "调用模式": call_config.get("调用模式", "local_preview_only"),
        },
        "调用结果": results,
        "安全边界": safety,
    }
    output_dir = root / "03数据" / "09统一指令本地调用预演"
    latest_json = output_dir / "wecom-unified-command-local-call-preview-最新.json"
    output_json = latest_json
    latest_md = output_dir / "企业微信统一指令本地调用预演_最新.md"
    output_md = latest_md
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "样例数量": len(results), "调用成功数量": len(success), "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
