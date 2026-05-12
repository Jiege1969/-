# -*- coding: utf-8 -*-
"""
名称：generate_review_examples.py
作用：为轮次012视频工厂生成素材授权与平台规则的占位填写样例。
触发方式：python generate_review_examples.py
安全边界：只生成本地占位样例；不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
所属系统：02杰哥扩展系统/02视频制作系统
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
DATA_ROOT = ROOT / "03数据" / "18轮次012视频工厂总控层"
TASK_PATH = DATA_ROOT / "视频工厂任务单_最新.json"
DRAFT_DIR = DATA_ROOT / "草案输出"
STORYBOARD_PATH = DRAFT_DIR / "分镜草案_最新.md"
OUTPUT_DIR = DATA_ROOT / "人工复核链" / "占位填写样例"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def get_value(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    return str(value) if value not in (None, "") else default


def nested_value(data: dict[str, Any], *keys: str, default: str = "") -> str:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return str(current) if current not in (None, "") else default


def build_material_example(task: dict[str, Any], storyboard_text: str) -> dict[str, Any]:
    task_id = get_value(task, "任务ID", "未知任务")
    topic = nested_value(task, "任务定义", "主题", default="待填写")
    has_storyboard = bool(storyboard_text.strip())
    return {
        "样例名称": "素材授权占位填写样例",
        "样例状态": "占位示范-待人工替换",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "主题": topic,
        "分镜草案存在": has_storyboard,
        "结论": "本样例不是授权结论，只演示字段如何填写。",
        "安全边界": {
            "读取真实素材": False,
            "调用外部素材API": False,
            "触发真实渲染": False,
            "说明": "所有素材字段均为占位示例，必须由人工替换为真实可追溯来源后才可复核。",
        },
        "占位样例": [
            {
                "镜头编号": "S01",
                "画面需求": "雨天地铁口外，一个人撑伞等待，画面不出现可识别正脸",
                "素材来源类型": "占位：待选择 Pexels / 本地拍摄 / 自制素材 / 授权素材",
                "素材文件或链接": "占位：待填写真实链接或本地文件编号",
                "授权证明": "占位：待粘贴许可证页面、购买记录或自制声明",
                "可商用范围": "待人工确认",
                "隐私与肖像风险": "示例要求：避免可识别正脸、车牌、工牌、住址、儿童影像",
                "水印与版权风险": "示例要求：不得使用带平台水印或来源不明搬运素材",
                "对应旁白句子": "今天下雨，我在地铁口等了很久，突然想明白一件事",
                "人工复核结论": "待确认",
            },
            {
                "镜头编号": "S02",
                "画面需求": "城市雨夜空镜或通勤人群背影，用来承接情绪",
                "素材来源类型": "占位：待选择 Pexels / 本地拍摄 / 自制素材 / 授权素材",
                "素材文件或链接": "占位：待填写真实链接或本地文件编号",
                "授权证明": "占位：待粘贴许可证页面、购买记录或自制声明",
                "可商用范围": "待人工确认",
                "隐私与肖像风险": "示例要求：不出现清晰可识别个人信息",
                "水印与版权风险": "示例要求：不使用影视剧、综艺、新闻搬运片段",
                "对应旁白句子": "有些念头，不是在大场面里冒出来的，而是在普通生活缝隙里出现",
                "人工复核结论": "待确认",
            },
        ],
        "必须阻断": [
            "占位字段未替换为真实来源前，阻断真实渲染",
            "授权证明未补齐前，阻断真实渲染",
            "隐私、肖像、商标、水印任一风险未确认前，阻断真实渲染",
        ],
    }


def build_platform_example(task: dict[str, Any]) -> dict[str, Any]:
    task_id = get_value(task, "任务ID", "未知任务")
    topic = nested_value(task, "任务定义", "主题", default="待填写")
    return {
        "样例名称": "平台规则占位填写样例",
        "样例状态": "占位示范-待人工替换",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "主题": topic,
        "结论": "本样例不是平台规则结论，也不是发布放行结论。",
        "安全边界": {
            "访问平台": False,
            "连接真实账号": False,
            "触发发布": False,
            "发送企业微信": False,
            "说明": "所有平台规则字段均为占位示例，必须由人工根据官方规则来源替换。",
        },
        "占位样例": [
            {
                "平台": "抖音",
                "官方规则来源": "占位：待填写官方规则链接和读取日期",
                "视频比例要求": "待人工确认，建议同时核对 9:16",
                "时长限制": "待人工确认",
                "标题限制": "待人工确认，避免绝对化和焦虑诱导",
                "标签限制": "待人工确认",
                "AI生成内容标识要求": "待人工确认，发布前必须确认是否需要勾选或声明",
                "账号": "待人工确认",
                "发布放行结论": "待确认",
            },
            {
                "平台": "小红书",
                "官方规则来源": "占位：待填写官方规则链接和读取日期",
                "视频比例要求": "待人工确认，建议同时核对 9:16",
                "时长限制": "待人工确认",
                "标题限制": "待人工确认，避免夸大承诺和标题党",
                "标签限制": "待人工确认",
                "AI生成内容标识要求": "待人工确认，发布前必须确认是否需要勾选或声明",
                "账号": "待人工确认",
                "发布放行结论": "待确认",
            },
            {
                "平台": "微信视频号",
                "官方规则来源": "占位：待填写官方规则链接和读取日期",
                "视频比例要求": "待人工确认，建议同时核对 9:16 与 16:9",
                "时长限制": "待人工确认",
                "标题限制": "待人工确认，避免诱导分享、夸大结果",
                "标签限制": "待人工确认",
                "AI生成内容标识要求": "待人工确认，发布前必须确认是否需要勾选或声明",
                "账号": "待人工确认",
                "发布放行结论": "待确认",
            },
            {
                "平台": "B站",
                "官方规则来源": "占位：待填写官方规则链接和读取日期",
                "视频比例要求": "待人工确认，建议核对 16:9",
                "时长限制": "待人工确认",
                "标题限制": "待人工确认，避免误导性标题",
                "标签限制": "待人工确认",
                "AI生成内容标识要求": "待人工确认，发布前必须确认是否需要勾选或声明",
                "账号": "待人工确认",
                "发布放行结论": "待确认",
            },
        ],
        "必须阻断": [
            "官方规则来源未填写前，阻断发布放行",
            "AI生成内容标识要求未确认前，阻断发布放行",
            "账号、人工确认人、发布放行结论任一未确认前，阻断发布",
            "生成放行和渲染放行不得自动推导为发布放行",
        ],
    }


def render_example_markdown(payload: dict[str, Any], table_kind: str) -> str:
    lines = [
        f"# 轮次012 {payload['样例名称']}",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 任务ID：{payload['任务ID']}",
        f"- 主题：{payload['主题']}",
        f"- 样例状态：{payload['样例状态']}",
        f"- 结论：{payload['结论']}",
        "- 真实系统触发：否",
        "",
        "## 占位样例",
        "",
    ]
    if table_kind == "material":
        lines.extend(
            [
                "| 镜头编号 | 画面需求 | 来源类型 | 文件或链接 | 授权证明 | 风险提示 | 对应旁白 | 复核结论 |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in payload["占位样例"]:
            risk = f"{item['隐私与肖像风险']}；{item['水印与版权风险']}"
            lines.append(
                f"| {item['镜头编号']} | {item['画面需求']} | {item['素材来源类型']} | {item['素材文件或链接']} | "
                f"{item['授权证明']} | {risk} | {item['对应旁白句子']} | {item['人工复核结论']} |"
            )
    else:
        lines.extend(
            [
                "| 平台 | 官方规则来源 | 比例 | 时长 | 标题 | 标签 | AI标识 | 账号 | 发布结论 |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for item in payload["占位样例"]:
            lines.append(
                f"| {item['平台']} | {item['官方规则来源']} | {item['视频比例要求']} | {item['时长限制']} | "
                f"{item['标题限制']} | {item['标签限制']} | {item['AI生成内容标识要求']} | {item['账号']} | {item['发布放行结论']} |"
            )
    lines.extend(["", "## 必须阻断", ""])
    for item in payload["必须阻断"]:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## 边界声明",
            "",
            "- 本样例只是字段填写演示，不是正式素材授权、平台规则结论或发布放行。",
            "- 本样例不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n。",
            "- 任一占位字段未替换并人工复核前，只能保持阻断状态。",
            "",
        ]
    )
    return "\n".join(lines)


def archive_outputs(stamp: str, task_id: str, material: dict[str, Any], platform: dict[str, Any]) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{task_id}_{stamp}"
    write_json(ARCHIVE_DIR / f"素材授权占位填写样例_{base}.json", material)
    write_text(ARCHIVE_DIR / f"素材授权占位填写样例_{base}.md", render_example_markdown(material, "material"))
    write_json(ARCHIVE_DIR / f"平台规则占位填写样例_{base}.json", platform)
    write_text(ARCHIVE_DIR / f"平台规则占位填写样例_{base}.md", render_example_markdown(platform, "platform"))


def main() -> int:
    task = read_json(TASK_PATH)
    storyboard = read_text(STORYBOARD_PATH)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = get_value(task, "任务ID", "未知任务")

    material = build_material_example(task, storyboard)
    platform = build_platform_example(task)

    write_json(OUTPUT_DIR / "素材授权占位填写样例_最新.json", material)
    write_text(OUTPUT_DIR / "素材授权占位填写样例_最新.md", render_example_markdown(material, "material"))
    write_json(OUTPUT_DIR / "平台规则占位填写样例_最新.json", platform)
    write_text(OUTPUT_DIR / "平台规则占位填写样例_最新.md", render_example_markdown(platform, "platform"))
    archive_outputs(stamp, task_id, material, platform)

    print("占位填写样例生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
