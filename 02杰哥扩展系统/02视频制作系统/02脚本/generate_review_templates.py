# -*- coding: utf-8 -*-
"""
名称：generate_review_templates.py
作用：为轮次012视频工厂生成素材授权字段模板与平台规则待确认模板。
触发方式：python generate_review_templates.py
安全边界：只做本地模板生成；不读取真实素材、不访问平台、不渲染、不发布、不发送企业微信、不连接 n8n。
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
OUTPUT_DIR = DATA_ROOT / "人工复核链" / "复核模板"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def task_value(task: dict[str, Any], key: str, default: str = "") -> str:
    value = task.get(key, default)
    return str(value) if value not in (None, "") else default


def nested_value(data: dict[str, Any], *keys: str, default: str = "") -> str:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return str(current) if current not in (None, "") else default


def build_material_template(task: dict[str, Any]) -> dict[str, Any]:
    task_id = task_value(task, "任务ID", "未知任务")
    topic = nested_value(task, "任务定义", "主题", default="待填写")
    ratios = task.get("任务定义", {}).get("目标画面比例", ["9:16", "16:9"])
    return {
        "模板名称": "素材授权字段模板",
        "模板状态": "待人工填写",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "主题": topic,
        "适用画幅": ratios,
        "安全边界": {
            "读取真实素材": False,
            "调用外部素材API": False,
            "触发真实渲染": False,
            "触发真实发布": False,
            "说明": "本模板只登记待复核字段；素材授权、肖像、隐私、平台限制未齐时，必须阻断真实渲染。",
        },
        "素材字段": [
            {
                "镜头编号": "S01",
                "画面需求": "待填写：例如雨天地铁口、通勤人群、城市空镜",
                "素材来源类型": "待填写：Pexels/本地拍摄/自制图像/授权素材/其他",
                "素材文件或链接": "待填写",
                "授权证明": "待填写：许可证、截图、购买记录、来源页",
                "可商用范围": "待确认",
                "是否含人物肖像": "待确认",
                "是否含未成年人": "待确认",
                "是否含品牌商标": "待确认",
                "是否含平台水印": "待确认",
                "是否需要二次授权": "待确认",
                "对应旁白句子": "待填写",
                "9:16适配风险": "待确认",
                "16:9适配风险": "待确认",
                "人工复核结论": "待确认",
            }
        ],
        "阻断事项": [
            "素材来源无法追溯时，阻断真实渲染",
            "授权证明缺失时，阻断真实渲染",
            "人物肖像、隐私、商标、水印风险未确认时，阻断真实渲染",
            "仅有生成放行但无素材授权复核时，阻断真实渲染",
        ],
    }


def build_platform_template(task: dict[str, Any]) -> dict[str, Any]:
    task_id = task_value(task, "任务ID", "未知任务")
    topic = nested_value(task, "任务定义", "主题", default="待填写")
    return {
        "模板名称": "平台规则待确认模板",
        "模板状态": "待人工填写",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "主题": topic,
        "安全边界": {
            "访问平台": False,
            "连接真实账号": False,
            "触发发布": False,
            "发送企业微信": False,
            "说明": "本模板只登记平台规则待确认字段；平台规则、AI标识、账号和人工确认不齐时，必须阻断发布放行。",
        },
        "平台字段": [
            {
                "平台": "抖音",
                "官方规则来源": "待填写",
                "视频比例要求": "待确认",
                "时长限制": "待确认",
                "标题限制": "待确认",
                "标签限制": "待确认",
                "AI生成内容标识要求": "待确认",
                "音乐版权要求": "待确认",
                "分区或话题要求": "待确认",
                "发布账号": "待确认",
                "人工确认人": "待确认",
                "发布放行结论": "待确认",
            },
            {
                "平台": "小红书",
                "官方规则来源": "待填写",
                "视频比例要求": "待确认",
                "时长限制": "待确认",
                "标题限制": "待确认",
                "标签限制": "待确认",
                "AI生成内容标识要求": "待确认",
                "音乐版权要求": "待确认",
                "分区或话题要求": "待确认",
                "发布账号": "待确认",
                "人工确认人": "待确认",
                "发布放行结论": "待确认",
            },
            {
                "平台": "微信视频号",
                "官方规则来源": "待填写",
                "视频比例要求": "待确认",
                "时长限制": "待确认",
                "标题限制": "待确认",
                "标签限制": "待确认",
                "AI生成内容标识要求": "待确认",
                "音乐版权要求": "待确认",
                "分区或话题要求": "待确认",
                "发布账号": "待确认",
                "人工确认人": "待确认",
                "发布放行结论": "待确认",
            },
            {
                "平台": "B站",
                "官方规则来源": "待填写",
                "视频比例要求": "待确认",
                "时长限制": "待确认",
                "标题限制": "待确认",
                "标签限制": "待确认",
                "AI生成内容标识要求": "待确认",
                "音乐版权要求": "待确认",
                "分区或话题要求": "待确认",
                "发布账号": "待确认",
                "人工确认人": "待确认",
                "发布放行结论": "待确认",
            },
        ],
        "阻断事项": [
            "平台官方规则来源缺失时，阻断发布放行",
            "AI生成内容标识要求未确认时，阻断发布放行",
            "发布账号、人工确认人或发布放行结论缺失时，阻断发布",
            "生成放行或渲染放行不得自动推导为发布放行",
        ],
    }


def render_material_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 素材授权字段模板",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 任务ID：{payload['任务ID']}",
        f"- 主题：{payload['主题']}",
        f"- 模板状态：{payload['模板状态']}",
        "- 文件属性：影子复核模板，不是正式授权结论",
        "- 真实系统触发：否",
        "",
        "## 素材字段",
        "",
        "| 镜头编号 | 画面需求 | 素材来源类型 | 素材文件或链接 | 授权证明 | 可商用范围 | 肖像/隐私/商标/水印风险 | 对应旁白句子 | 人工复核结论 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for item in payload["素材字段"]:
        risk = "；".join(
            [
                f"人物肖像：{item['是否含人物肖像']}",
                f"未成年人：{item['是否含未成年人']}",
                f"品牌商标：{item['是否含品牌商标']}",
                f"平台水印：{item['是否含平台水印']}",
            ]
        )
        lines.append(
            f"| {item['镜头编号']} | {item['画面需求']} | {item['素材来源类型']} | {item['素材文件或链接']} | "
            f"{item['授权证明']} | {item['可商用范围']} | {risk} | {item['对应旁白句子']} | {item['人工复核结论']} |"
        )
    lines.extend(["", "## 阻断事项", ""])
    for item in payload["阻断事项"]:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## 边界声明",
            "",
            "- 本模板不读取真实素材。",
            "- 本模板不调用 Pexels、MoneyPrinterTurbo、Pixelle-Video 或任何外部API。",
            "- 本模板不发送企业微信、不接 n8n、不修改服务入口。",
            "- 素材授权、肖像、隐私、商标、水印任一未确认时，只能登记阻断，不能进入真实渲染。",
            "",
        ]
    )
    return "\n".join(lines)


def render_platform_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 平台规则待确认模板",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 任务ID：{payload['任务ID']}",
        f"- 主题：{payload['主题']}",
        f"- 模板状态：{payload['模板状态']}",
        "- 文件属性：影子复核模板，不是正式发布结论",
        "- 真实系统触发：否",
        "",
        "## 平台字段",
        "",
        "| 平台 | 官方规则来源 | 比例 | 时长 | 标题 | 标签 | AI标识 | 音乐版权 | 分区/话题 | 账号 | 人工确认人 | 发布放行结论 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in payload["平台字段"]:
        lines.append(
            f"| {item['平台']} | {item['官方规则来源']} | {item['视频比例要求']} | {item['时长限制']} | "
            f"{item['标题限制']} | {item['标签限制']} | {item['AI生成内容标识要求']} | {item['音乐版权要求']} | "
            f"{item['分区或话题要求']} | {item['发布账号']} | {item['人工确认人']} | {item['发布放行结论']} |"
        )
    lines.extend(["", "## 阻断事项", ""])
    for item in payload["阻断事项"]:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## 边界声明",
            "",
            "- 本模板不访问平台、不连接真实账号、不调用发布工具。",
            "- 本模板不读取真实素材。",
            "- 本模板不发送企业微信、不接 n8n、不修改服务入口。",
            "- 平台规则、AI内容标识、账号、人工确认任一未齐时，只能登记阻断，不能发布放行。",
            "",
        ]
    )
    return "\n".join(lines)


def archive_outputs(stamp: str, task_id: str, material: dict[str, Any], platform: dict[str, Any]) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    material_md = render_material_markdown(material)
    platform_md = render_platform_markdown(platform)
    base = f"{task_id}_{stamp}"
    write_json(ARCHIVE_DIR / f"素材授权字段模板_{base}.json", material)
    write_text(ARCHIVE_DIR / f"素材授权字段模板_{base}.md", material_md)
    write_json(ARCHIVE_DIR / f"平台规则待确认模板_{base}.json", platform)
    write_text(ARCHIVE_DIR / f"平台规则待确认模板_{base}.md", platform_md)


def main() -> int:
    task = read_json(TASK_PATH)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = task_value(task, "任务ID", "未知任务")

    material = build_material_template(task)
    platform = build_platform_template(task)

    write_json(OUTPUT_DIR / "素材授权字段模板_最新.json", material)
    write_text(OUTPUT_DIR / "素材授权字段模板_最新.md", render_material_markdown(material))
    write_json(OUTPUT_DIR / "平台规则待确认模板_最新.json", platform)
    write_text(OUTPUT_DIR / "平台规则待确认模板_最新.md", render_platform_markdown(platform))
    archive_outputs(stamp, task_id, material, platform)

    print("复核模板生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
