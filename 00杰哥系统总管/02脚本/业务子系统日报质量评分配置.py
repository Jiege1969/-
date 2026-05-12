# -*- coding: utf-8 -*-

UNIVERSAL_QUALITY_RULES = [
    {
        "id": "silence_is_gold",
        "name": "沉默是金：数据缺失却强行生成结论",
        "severity": "defect",
        "penalty": 100,
        "missing_data_phrases": [
            "数据缺失",
            "缺少数据",
            "暂无数据",
            "无数据",
            "样本不足",
            "未采集",
            "无法读取",
        ],
        "forced_conclusion_phrases": [
            "结论：",
            "最终结论",
            "建议：",
            "可以认定",
            "直接执行",
            "无需复核",
        ],
    },
    {
        "id": "traceable_conclusions",
        "name": "可追溯：关键结论必须找到计算来源",
        "severity": "deduct",
        "penalty": 15,
        "conclusion_phrases": [
            "关键结论",
            "结论：",
            "最终结论",
            "建议：",
        ],
        "source_phrases": [
            "来源",
            "数据来源",
            "计算来源",
            "计算过程",
            "依据",
            "证据",
            "原始文件",
            "输入文件",
            "上游",
            "追溯",
        ],
    },
    {
        "id": "human_sovereignty",
        "name": "人的主权：进化系统不得擅自修改业务规则",
        "severity": "highest_alert",
        "penalty": 100,
        "sovereignty_phrases": [
            "擅自修改业务规则",
            "自动修改业务规则",
            "自动改写业务规则",
            "覆盖业务规则",
            "进化系统修改规则",
            "进化系统自动调整规则",
            "无需人工确认即可修改规则",
        ],
    },
]

CONFIGS = [
    {
        "system_name": "视频制作系统",
        "slug": "video-production",
        "system_dir": "02视频制作系统",
        "task_name": "杰哥智能化系统_质量评分_视频制作系统",
        "entry_scripts": [
            "生成视频制作系统状态摘要.py",
            "生成视频真实渲染环境缺口证据压缩与安装识别清单.py",
            "执行视频真实渲染启用前总闸口只读核对.py",
        ],
        "key_outputs": [
            {"name": "状态摘要", "dirs": ["03数据/09状态摘要"], "patterns": ["*状态摘要*.*", "*status-summary*.*"]},
            {"name": "视频脚本/分镜/预演", "dirs": ["03数据"], "patterns": ["*脚本*.*", "*分镜*.*", "*预演*.*"]},
        ],
        "banned_phrases": ["效果炸裂", "燃爆", "大片感拉满", "无敌", "一键爆款", "绝绝子", "随便剪"],
    },
    {
        "system_name": "本职工作系统",
        "slug": "office-work",
        "system_dir": "03本职工作系统",
        "task_name": "杰哥智能化系统_质量评分_本职工作系统",
        "entry_scripts": [
            "生成本职工作系统状态摘要.py",
            "执行R03办公材料草稿预演器.py",
            "生成办公材料计划.py",
        ],
        "key_outputs": [
            {"name": "状态摘要", "dirs": ["03数据/05状态摘要"], "patterns": ["*状态摘要*.*", "*status-summary*.*"]},
            {"name": "办公材料草稿", "dirs": ["03数据/03输出草稿", "03数据/02任务计划"], "patterns": ["*草稿*.*", "*计划*.*", "*材料*.*"]},
        ],
        "banned_phrases": ["领导一定满意", "万能模板", "照抄即可", "无需复核", "闭眼用"],
    },
    {
        "system_name": "内容处理系统",
        "slug": "content-processing",
        "system_dir": "04内容处理系统",
        "task_name": "杰哥智能化系统_质量评分_内容处理系统",
        "entry_scripts": [
            "生成内容处理系统状态摘要.py",
            "生成内容转换预演.py",
            "生成内容批处理计划.py",
        ],
        "key_outputs": [
            {"name": "状态摘要", "dirs": ["03数据/06状态摘要"], "patterns": ["*状态摘要*.*", "*status-summary*.*"]},
            {"name": "转换预演/批处理计划", "dirs": ["03数据/04转换预演", "03数据/03批处理计划"], "patterns": ["*预演*.*", "*计划*.*", "*转换*.*"]},
        ],
        "banned_phrases": ["无脑转换", "随便处理", "无需校对", "一键洗稿", "保证原创", "爆款标题"],
    },
    {
        "system_name": "税收业务系统",
        "slug": "tax-business",
        "system_dir": "05税收业务系统",
        "task_name": "杰哥智能化系统_质量评分_税收业务系统",
        "entry_scripts": [
            "生成税收企业微信正式入口消息预演.py",
            "生成税收企业微信待复核草案骨架批量预演.py",
            "生成税收系统当前阶段收口验收与下一步队列.py",
        ],
        "key_outputs": [
            {"name": "税收正式入口/草案", "dirs": ["03数据/32税收企业微信正式入口"], "patterns": ["*草案*.*", "*摘要*.*", "*预演*.*", "*入口*.*"]},
            {"name": "税收分析契约/证据", "dirs": ["03数据/29涉税业务分析契约影子样例", "03数据/31研发费用分析准备度门禁"], "patterns": ["*分析*.*", "*证据*.*", "*门禁*.*"]},
        ],
        "banned_phrases": ["无需缴税", "不用缴税", "肯定不用交税", "包过", "绝对合规", "无需申报", "百分百节税"],
    },
    {
        "system_name": "企业微信助手系统",
        "slug": "wecom-assistant",
        "system_dir": "06企业微信助手系统",
        "task_name": "杰哥智能化系统_质量评分_企业微信助手系统",
        "entry_scripts": [
            "企业微信统一指令本地服务入口.py",
            "生成企业微信助手系统状态摘要.py",
            "生成企业微信统一指令本地调用预演.py",
        ],
        "key_outputs": [
            {"name": "状态摘要", "dirs": ["03数据/07状态摘要"], "patterns": ["*状态摘要*.*", "*status-summary*.*"]},
            {"name": "统一指令预演/速查", "dirs": ["03数据/09统一指令本地调用预演", "03数据/08统一指令路由预演", "03数据/11统一指令使用速查卡"], "patterns": ["*预演*.*", "*速查*.*", "*调用*.*"]},
        ],
        "banned_phrases": ["群发所有人", "直接真实发送", "绕过确认", "无需白名单", "自动外发"],
    },
    {
        "system_name": "知识库可追溯问答框",
        "slug": "knowledge-traceable-qa",
        "system_dir": "07知识库可追溯问答框",
        "task_name": "杰哥智能化系统_质量评分_知识库可追溯问答框",
        "entry_scripts": [
            "生成知识库可追溯问答框交付包.py",
            "验证知识库可追溯问答框交付包.py",
        ],
        "key_outputs": [
            {"name": "可追溯问答交付包", "dirs": ["03数据/01交付包"], "patterns": ["*交付包*.*", "*问答*.*", "*知识库*.*"]},
        ],
        "banned_phrases": ["编一个来源", "无需出处", "随便回答", "保证正确", "不可追溯"],
    },
    {
        "system_name": "知识库系统",
        "slug": "knowledge-base",
        "system_dir": "07知识库系统",
        "task_name": "杰哥智能化系统_质量评分_知识库系统",
        "entry_scripts": [
            "执行知识库系统内生能力只读检查.py",
        ],
        "key_outputs": [
            {"name": "知识库只读检查/证据索引", "dirs": ["03数据"], "patterns": ["*只读检查*.*", "*证据*.*", "*知识库*.*", "*验收*.*"]},
        ],
        "banned_phrases": ["随便入库", "来源不重要", "无需证据", "编造引用"],
    },
]

for _config in CONFIGS:
    _config["universal_quality_rules"] = UNIVERSAL_QUALITY_RULES

WAKE_TASK_NAMES = {
    "video-production": "杰哥智能化系统_每日唤醒_视频制作系统",
    "office-work": "杰哥智能化系统_每日唤醒_本职工作系统",
    "content-processing": "杰哥智能化系统_每日唤醒_内容处理系统",
    "tax-business": "杰哥智能化系统_每日唤醒_税收业务系统",
    "wecom-assistant": "杰哥智能化系统_每日唤醒_企业微信助手系统",
    "knowledge-traceable-qa": "杰哥智能化系统_每日唤醒_知识库可追溯问答框",
}

for _config in CONFIGS:
    if _config["slug"] in WAKE_TASK_NAMES:
        _config["task_name"] = WAKE_TASK_NAMES[_config["slug"]]
