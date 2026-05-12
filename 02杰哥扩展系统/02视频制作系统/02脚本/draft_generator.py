# -*- coding: utf-8 -*-
"""
名称：draft_generator.py
作用：读取轮次012视频工厂任务单，生成去AI感脚本草案和分镜草案。
触发方式：python draft_generator.py
依赖：Python 标准库；task_generator.compliance_check；轮次012视频工厂任务单。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只读取本地任务单并写入轮次012草案输出目录；不调用网络、不调用剪辑软件、不生成真实媒体、不发布。
创建/修改记录：2026-05-08 创建轮次012视频工厂草案生成器。
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

from task_generator import compliance_check


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
ROUND_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
TASK_PATH = ROUND_DIR / "视频工厂任务单_最新.json"
OUTPUT_DIR = ROUND_DIR / "草案输出"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
SCRIPT_DRAFT_PATH = OUTPUT_DIR / "视频脚本草案_最新.md"
STORYBOARD_DRAFT_PATH = OUTPUT_DIR / "分镜草案_最新.md"

CREATOR_CHECKLIST = """## 创作者自查清单（发布前必检）

- [ ] 是否有具体的生活场景或真人细节？
- [ ] 标题是否包含点击诱饵或绝对化词汇？
- [ ] 是否记得在发布平台勾选“内容由AI生成”？
- [ ] 文案是否无意中贩卖焦虑或引发对立？
"""

IDIOM_STORY_LIBRARY: dict[str, dict[str, Any]] = {
    "掩耳盗铃": {
        "一句话寓意": "自欺欺人不能让问题消失，只会让后果来得更快。",
        "故事情节": [
            "从前有个人看见别人家门口挂着一只漂亮的铃，心里起了贪念，想把铃偷走。",
            "他刚伸手去摘，铃一碰就响。他害怕声音惊动主人，却没有停手反省。",
            "他想出一个荒唐办法：把自己的耳朵捂住，以为自己听不见，别人也听不见。",
            "结果铃声照样传出去，主人和邻居很快发现了他，他的遮掩反而暴露了心虚。",
        ],
        "现代解读": [
            "今天的“掩耳盗铃”，不一定是偷东西，也可能是明知道方案有漏洞，却只关掉提醒；明知道关系出了问题，却假装没听见对方的不满。",
            "真正危险的不是问题发出了声音，而是我们为了舒服一点，先把自己的耳朵捂上。",
            "这个成语提醒的是：不看、不听、不回应，只能减少一秒钟的尴尬，不能减少真正的成本。",
        ],
        "口播稿": [
            "今天讲一个特别像现代人的成语，叫掩耳盗铃。",
            "故事里，有个人看见别人家门口挂着一只铃，觉得好看，就想偷偷摘走。",
            "可铃这个东西，一碰就响。他怕被人发现，按理说应该停手，可他没有。",
            "他想了个办法：把自己的耳朵捂住。心里想着，只要我听不见铃声，别人应该也听不见。",
            "你看，问题荒唐就荒唐在这里。铃声不是因为他听见才存在，也不会因为他捂住耳朵就消失。",
            "放到今天也一样。项目已经延期了，你不看进度表；身体已经报警了，你不看体检单；朋友已经不舒服了，你假装没听懂。",
            "这都不是解决问题，只是让自己短暂舒服一点。",
            "掩耳盗铃真正刺中的，是人的自欺：我们有时候不是不知道真相，而是希望真相不要发出声音。",
            "但现实不会配合这种假装。越早听见铃声，越有机会把事情拉回来。",
            "所以这句成语不是笑古人笨，而是在提醒我们：别把逃避当成安全感。",
        ],
        "分镜": [
            ("1", "0-5s", "古代院门特写：木门、铜铃、安静环境，人物从门侧探头看铃", "字幕：一只铃，照出一个人的侥幸心理"),
            ("2", "5-12s", "人物伸手去摘铃，手刚碰到铃身，铃开始晃动", "口播：他想把铃偷走，可铃一碰就响"),
            ("3", "12-20s", "人物慌张四顾，不是收手，而是抬手捂住自己的耳朵", "字幕：听不见，不等于没人听见"),
            ("4", "20-30s", "铃继续晃，门内灯亮，主人和邻居被声音吸引出来", "口播：声音照样传出去，遮掩反而暴露心虚"),
            ("5", "30-42s", "现代办公室对照：电脑弹出延期提醒，人物把提醒关闭，表情松一口气", "字幕：现代版掩耳盗铃：关掉提醒，不等于风险消失"),
            ("6", "42-53s", "现代生活对照：手机未读消息、体检单、待处理清单快速切换", "口播：不看、不听、不回应，只能减少一秒尴尬"),
            ("7", "53-60s", "人物放下手，正视镜头或桌面清单，画面停在铃声余韵上", "字幕：越早听见铃声，越有机会补救"),
        ],
    }
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"未找到任务单：{path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sentence_lines(sentences: list[str], seed_text: str) -> list[str]:
    """为约30%的句子追加人工确认点；至少保留一个标记，方便人工复核入口识别。"""
    rng = random.Random(seed_text)
    if not sentences:
        return []
    target_count = max(1, round(len(sentences) * 0.3))
    selected = set(rng.sample(range(len(sentences)), k=min(target_count, len(sentences))))
    lines: list[str] = []
    for index, sentence in enumerate(sentences):
        suffix = " [人工确认]" if index in selected else ""
        lines.append(f"{index + 1}. {sentence}{suffix}")
    return lines


def is_idiom_or_quote(task_definition: dict[str, Any]) -> bool:
    video_type = str(task_definition.get("视频类型", ""))
    return "成语故事" in video_type or "经典语录" in video_type


def is_idiom_story(task_definition: dict[str, Any]) -> bool:
    video_type = str(task_definition.get("视频类型", ""))
    topic = str(task_definition.get("主题", ""))
    return "成语故事" in video_type or any(name in topic for name in IDIOM_STORY_LIBRARY)


def detect_idiom_name(task_definition: dict[str, Any]) -> str:
    topic = str(task_definition.get("主题", ""))
    for idiom_name in IDIOM_STORY_LIBRARY:
        if idiom_name in topic:
            return idiom_name
    return topic.replace("做一个", "").replace("成语故事", "").replace("的视频脚本", "").strip(" ：:，,。")


def build_idiom_fallback(idiom_name: str) -> dict[str, Any]:
    display_name = idiom_name or "待确认成语"
    return {
        "一句话寓意": "请人工补齐准确出处、人物和情节后再进入生成放行。",
        "故事情节": [
            f"先交代“{display_name}”发生的时间、人物和冲突，不直接套用泛口播模板。",
            "再写清楚人物做了什么、为什么这么做、动作造成了什么后果。",
            "最后落到成语寓意，说明它批评或提醒的是哪一种真实行为。",
        ],
        "现代解读": [
            "把成语放回一个现代具体场景，例如职场沟通、家庭相处、朋友关系或自我管理。",
            "说明这个成语今天仍然有效的边界：它不是用来给别人贴标签，而是提醒自己识别相似行为。",
        ],
        "口播稿": [
            f"今天讲“{display_name}”。这条成语不能只讲一句解释，要先把故事讲完整。",
            "第一步，讲清楚人物遇到了什么诱惑或困难。",
            "第二步，讲清楚他采取了什么动作，以及这个动作为什么站不住脚。",
            "第三步，讲清楚结果如何暴露问题。",
            "最后再回到今天：我们在生活里什么时候也会做类似的事，又该怎样及时停下来。",
        ],
        "分镜": [
            ("1", "0-6s", "成语故事关键物件或人物动作特写，禁止城市空镜代替故事", "字幕：先进入故事，不先讲大道理"),
            ("2", "6-16s", "人物面对诱惑或冲突，表情和手部动作要清楚", "口播：交代人物为什么做出选择"),
            ("3", "16-30s", "人物执行错误动作，画面突出动作和后果之间的矛盾", "字幕：错误逻辑在这里露出来"),
            ("4", "30-42s", "结果出现，旁人反应或环境变化推动故事落点", "口播：后果不是被解释出来的，是被动作带出来的"),
            ("5", "42-54s", "现代生活对照场景，必须是具体行为，不用泛泛城市空镜", "字幕：今天的相似行为"),
            ("6", "54-60s", "人物停下动作、正视问题或做出修正", "口播：寓意收束"),
        ],
    }


def get_idiom_story_package(task_definition: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    if not is_idiom_story(task_definition):
        return None
    idiom_name = detect_idiom_name(task_definition)
    return idiom_name, IDIOM_STORY_LIBRARY.get(idiom_name, build_idiom_fallback(idiom_name))


def gate_separation_lines(task: dict[str, Any]) -> list[str]:
    generation_control = task.get("生成控制", {})
    return [
        "- 人工复核：只确认脚本、分镜、素材授权、平台规则和AI标识问题，不自动触发生成。",
        f"- 生成放行：当前任务状态为“{task.get('状态')}”，但生成放行仍不等于真实渲染放行。",
        "- 发布放行：必须等成品预览后单独确认，不能由复核通过或生成放行自动继承。",
        f"- 真实渲染开关：{generation_control.get('允许真实渲染', False)}。",
        "- 上传开关：False。",
        f"- 自动发布开关：{generation_control.get('允许自动发布', False)}。",
        "- 本地草案生成不调用n8n、不上传、不发布、不登录平台账号。",
    ]


def block_content(task: dict[str, Any], reason: str) -> tuple[str, str]:
    task_id = task.get("任务ID", "未生成")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = "\n".join([
        "# 轮次012 视频草案生成阻断",
        "",
        f"- 生成时间：{now}",
        f"- 任务ID：{task_id}",
        "",
        f"生成被合规门禁阻断，原因：{reason}",
        "",
        "当前动作只写入本地阻断说明，不进入脚本草案、分镜草案、真实渲染或发布。",
        "",
    ])
    return body, body


def build_script_draft(task: dict[str, Any], compliance: dict[str, Any]) -> str:
    task_def = task.get("任务定义", {})
    task_id = task.get("任务ID", "未生成")
    topic = task_def.get("主题", "")
    angle = task_def.get("表达角度", "")
    audience = task_def.get("受众人群", "")
    emotion = task_def.get("关键情绪", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    idiom_package = get_idiom_story_package(task_def)
    if idiom_package:
        idiom_name, story = idiom_package
        story_lines = [f"{index + 1}. {item}" for index, item in enumerate(story["故事情节"])]
        modern_lines = [f"{index + 1}. {item}" for index, item in enumerate(story["现代解读"])]
        oral_lines = sentence_lines(list(story["口播稿"]), f"{task_id}-{idiom_name}-oral")
        gate_items = compliance.get("gate_items", [])
        gate_text = "\n".join(f"- {item}" for item in gate_items) if gate_items else "- 未命中新增风险项，仍需人工复核。"
        return "\n".join([
            "# 轮次012 成语故事视频脚本草案",
            "",
            f"- 生成时间：{now}",
            f"- 任务ID：{task_id}",
            f"- 成语：{idiom_name}",
            f"- 会话来源：{task.get('会话来源', '企业微信')}",
            f"- 会话ID：{task.get('会话ID') or '未提供'}",
            f"- 当前状态：{task.get('状态')}",
            "",
            "## 1. 任务定义",
            "",
            f"- 主题：{topic}",
            f"- 表达角度：{angle}",
            f"- 受众人群：{audience}",
            f"- 视频类型：{task_def.get('视频类型', '')}",
            f"- 关键情绪：{emotion}",
            f"- 一句话寓意：{story['一句话寓意']}",
            "",
            "## 2. 故事情节稿",
            "",
            *story_lines,
            "",
            "## 3. 现代生活化解读",
            "",
            *modern_lines,
            "",
            "## 4. 可直接录制口播稿",
            "",
            *oral_lines,
            "",
            "## 5. 复核、生成放行、发布放行拆分",
            "",
            *gate_separation_lines(task),
            "",
            "## 6. 合规与去AI感提示",
            "",
            gate_text,
            f"- {task.get('生成建议', '')}",
            "",
            CREATOR_CHECKLIST,
        ])
    sentences = [
        f"开场：有些念头，不是在大场面里冒出来的，而是在一个很普通的生活缝隙里突然出现。",
        f"主题：这期想聊的是“{topic}”。",
        f"角度：我会从“{angle}”切入，不急着下结论，先把真实感受讲清楚。",
        "生活细节：比如等地铁、等雨停、等一条迟迟没有回复的消息时，人很容易看见自己的真实状态。",
        f"主体：对{audience}来说，这类问题往往不是一句道理能解决，而是需要把经验、情绪和边界放在一起看。",
        f"表达基调：保持{emotion}，不制造恐吓，也不把复杂生活说成单一答案。",
        "收束：好的内容不是替别人做决定，而是帮人把心里模糊的东西说得更清楚。",
    ]
    marked_lines = sentence_lines(sentences, f"{task_id}-script")
    gate_items = compliance.get("gate_items", [])
    gate_text = "\n".join(f"- {item}" for item in gate_items) if gate_items else "- 未命中新增风险项，仍需人工复核。"
    return "\n".join([
        "# 轮次012 视频脚本草案",
        "",
        f"- 生成时间：{now}",
        f"- 任务ID：{task_id}",
        f"- 会话来源：{task.get('会话来源', '企业微信')}",
        f"- 会话ID：{task.get('会话ID') or '未提供'}",
        f"- 当前状态：{task.get('状态')}",
        "",
        "## 1. 任务定义",
        "",
        f"- 主题：{topic}",
        f"- 表达角度：{angle}",
        f"- 受众人群：{audience}",
        f"- 视频类型：{task_def.get('视频类型', '')}",
        f"- 关键情绪：{emotion}",
        "",
        "## 2. AI初始口播草案",
        "",
        *marked_lines,
        "",
        "## 3. 合规与去AI感提示",
        "",
        gate_text,
        f"- {task.get('生成建议', '')}",
        "",
        CREATOR_CHECKLIST,
    ])


def build_storyboard_draft(task: dict[str, Any], compliance: dict[str, Any]) -> str:
    task_def = task.get("任务定义", {})
    task_id = task.get("任务ID", "未生成")
    topic = task_def.get("主题", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    idiom_package = get_idiom_story_package(task_def)
    if idiom_package:
        idiom_name, story = idiom_package
        shot_rows = "\n".join(
            f"| {number} | {duration} | {visual} | {note} | 待人工确认，不触发真实渲染 |"
            for number, duration, visual, note in story["分镜"]
        )
        gate_items = compliance.get("gate_items", [])
        gate_text = "\n".join(f"- {item}" for item in gate_items) if gate_items else "- 未命中新增风险项，仍需人工复核。"
        return "\n".join([
            "# 轮次012 成语故事分镜草案",
            "",
            f"- 生成时间：{now}",
            f"- 任务ID：{task_id}",
            f"- 成语：{idiom_name}",
            f"- 视频类型：{task_def.get('视频类型', '')}",
            "",
            "## 1. 故事动作分镜",
            "",
            "| 镜头 | 时长 | 画面需求 | 文案/字幕方向 | 素材状态 |",
            "| --- | --- | --- | --- | --- |",
            shot_rows,
            "",
            "## 2. 寓意落点",
            "",
            f"- {story['一句话寓意']}",
            "- 分镜必须服务“动作导致后果”的故事逻辑，禁止用泛泛城市空镜替代偷铃、铃响、捂耳、被发现等关键动作。",
            "- 现代对照只做生活化解释，不等于发布成片；仍需人工复核素材授权、平台规则和AI标识。",
            "",
            "## 3. 复核、生成放行、发布放行拆分",
            "",
            *gate_separation_lines(task),
            "",
            "## 4. 合规复核提示",
            "",
            gate_text,
            "",
            CREATOR_CHECKLIST,
        ])
    shots = [
        ("1", "0-5s", "生活场景开场，例如雨天路口、地铁口、楼道灯光", "用一个具体画面把观众带入真实情境"),
        ("2", "5-15s", "人物独处或慢节奏城市空镜", f"点出主题：{topic}"),
        ("3", "15-35s", "与主题相关的日常细节组合画面", "展开表达角度，避免空泛大道理"),
        ("4", "35-50s", "手写便签、聊天窗口、通勤背影等可替换素材", "加入一个生活化细节，降低AI感"),
        ("5", "50-60s", "安静收束画面，不做强刺激转场", "温和收束，保留思考空间"),
    ]
    shot_rows = "\n".join(
        f"| {number} | {duration} | {visual} | {note} | 待人工确认 |"
        for number, duration, visual, note in shots
    )
    extra_section = ""
    if is_idiom_or_quote(task_def):
        extra_section = "\n".join([
            "",
            "## 古今结合举例",
            "",
            "请用一个现代生活场景承接传统表达：例如把成语或语录放进通勤、职场沟通、家庭相处、朋友关系等具体情境里，说明它今天仍然有用的边界和新理解。该段必须加入原创解读，禁止仅翻译原文或复述常见故事。",
            "",
        ])
    gate_items = compliance.get("gate_items", [])
    gate_text = "\n".join(f"- {item}" for item in gate_items) if gate_items else "- 未命中新增风险项，仍需人工复核。"
    return "\n".join([
        "# 轮次012 分镜草案",
        "",
        f"- 生成时间：{now}",
        f"- 任务ID：{task_id}",
        f"- 视频类型：{task_def.get('视频类型', '')}",
        "",
        "## 1. 分镜预演",
        "",
        "| 镜头 | 时长 | 画面需求 | 文案/字幕方向 | 素材状态 |",
        "| --- | --- | --- | --- | --- |",
        shot_rows,
        extra_section,
        "## 2. 合规复核提示",
        "",
        gate_text,
        "",
        CREATOR_CHECKLIST,
    ])


def save_outputs(script_content: str, storyboard_content: str, task_id: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    write_text(SCRIPT_DRAFT_PATH, script_content)
    write_text(STORYBOARD_DRAFT_PATH, storyboard_content)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_text(ARCHIVE_DIR / f"视频脚本草案_{task_id}_{timestamp}.md", script_content)
    write_text(ARCHIVE_DIR / f"分镜草案_{task_id}_{timestamp}.md", storyboard_content)


def main() -> int:
    task = load_json(TASK_PATH)
    task_def = task.get("任务定义", {})
    compliance = compliance_check(str(task.get("原始输入", "")), task_def)
    task_id = str(task.get("任务ID", "VF-UNKNOWN"))
    if compliance.get("risk_level") == "高风险":
        script_content, storyboard_content = block_content(task, str(compliance.get("reason", "未知原因")))
        save_outputs(script_content, storyboard_content, task_id)
        print("草案生成完成，请人工复核")
        return 0

    script_content = build_script_draft(task, compliance)
    storyboard_content = build_storyboard_draft(task, compliance)
    save_outputs(script_content, storyboard_content, task_id)
    print("草案生成完成，请人工复核")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
