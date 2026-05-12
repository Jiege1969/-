# -*- coding: utf-8 -*-
"""
名称：机器人串线影子干预器.py
作用：以影子模式识别企业微信机器人串线，并生成温和引导建议。
所属系统：02杰哥扩展系统/00公共组件
边界：只读检测、只生成建议和日志材料；不修改核心路由、不真实发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：EWF-005-cross-wire-shadow-intervention
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class IntentRule:
    keywords: tuple[str, ...]
    correct_robot: str
    target_route: str
    intent_type: str


class CrossWireIntervention:
    """检测“入口机器人”和“用户意图”明显不匹配的场景。"""

    def __init__(self) -> None:
        self.block_rules: dict[str, tuple[IntentRule, ...]] = {
            "/wecom/stock": self._stock_rules(),
            "/wecom-bot/message": self._stock_rules(),
            "/wecom/video": self._video_rules(),
            "/wecom/video-assistant": self._video_rules(),
            "/wecom/work-secretary": self._work_secretary_rules(),
            "/wecom/system-manager": self._system_manager_rules(),
        }

    @staticmethod
    def _stock_rules() -> tuple[IntentRule, ...]:
        return (
            IntentRule(("视频", "剪辑", "分镜", "素材", "字幕", "配音"), "杰哥视频助理", "视频制作", "视频制作"),
            IntentRule(("税收", "增值税", "所得税", "发票", "申报", "资料准备"), "杰哥工作秘书", "税收业务待复核分析", "税收业务"),
            IntentRule(("工作汇报", "材料", "文案", "合同", "制度"), "杰哥工作秘书", "内容办公处理", "办公内容"),
        )

    @staticmethod
    def _video_rules() -> tuple[IntentRule, ...]:
        return (
            IntentRule(("股票", "行情", "K线", "个股", "持仓", "财报", "风险线", "股份"), "杰哥私人股票分析顾问", "股票研究", "股票研究"),
            IntentRule(("税收", "增值税", "所得税", "发票", "申报"), "杰哥工作秘书", "税收业务待复核分析", "税收业务"),
            IntentRule(("进度", "系统状态", "接续包", "健康检查"), "杰哥系统管家", "系统状态", "系统状态"),
        )

    @staticmethod
    def _work_secretary_rules() -> tuple[IntentRule, ...]:
        return (
            IntentRule(("股票", "行情", "K线", "个股", "持仓", "财报", "风险线", "股份"), "杰哥私人股票分析顾问", "股票研究", "股票研究"),
            IntentRule(("视频制作", "视频", "剪辑", "分镜", "素材", "字幕", "配音"), "杰哥视频助理", "视频制作", "视频制作"),
        )

    @staticmethod
    def _system_manager_rules() -> tuple[IntentRule, ...]:
        return (
            IntentRule(("股票", "行情", "K线", "个股", "持仓", "财报", "风险线", "股份"), "杰哥私人股票分析顾问", "股票研究", "股票研究"),
            IntentRule(("视频制作", "视频", "剪辑", "分镜", "素材", "字幕", "配音"), "杰哥视频助理", "视频制作", "视频制作"),
            IntentRule(("税收", "增值税", "所得税", "发票", "申报"), "杰哥工作秘书", "税收业务待复核分析", "税收业务"),
        )

    @staticmethod
    def canonical_path(route_path: str) -> str:
        path = str(route_path or "").split("?", 1)[0].strip()
        aliases = {
            "/wecom/stock": "/wecom-bot/message",
            "/wecom/video": "/wecom/video-assistant",
        }
        return aliases.get(path, path)

    def check(self, route_path: str, user_message: str) -> dict[str, Any]:
        """返回影子干预建议；不直接改变路由。"""
        path = self.canonical_path(route_path)
        message = str(user_message or "")
        for rule in self.block_rules.get(path, ()):
            for keyword in rule.keywords:
                if keyword in message:
                    return {
                        "intervention_needed": True,
                        "shadow_only": True,
                        "event": "robot_cross_wire_shadow",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "route_path": path,
                        "matched_keyword": keyword,
                        "intent_type": rule.intent_type,
                        "target_route": rule.target_route,
                        "reason": f"检测到入口 {path} 接收了包含“{keyword}”的消息，疑似机器人串线。",
                        "suggested_robot": rule.correct_robot,
                        "gentle_redirect_message": f"杰哥，这个问题更适合交给“{rule.correct_robot}”。我会先按影子模式记录这次串线风险，不改变当前路由。",
                        "user_message": message,
                        "safety_boundary": {
                            "real_send": False,
                            "trigger_webhook": False,
                            "trigger_n8n": False,
                            "change_core_route": False,
                            "broker_api": False,
                            "auto_trade": False,
                        },
                    }
        return {
            "intervention_needed": False,
            "shadow_only": True,
            "route_path": path,
            "user_message": message,
        }


if __name__ == "__main__":
    import json
    import sys

    route = sys.argv[1] if len(sys.argv) > 1 else "/wecom/work-secretary"
    text = sys.argv[2] if len(sys.argv) > 2 else "帮我分析一下沪电股份"
    print(json.dumps(CrossWireIntervention().check(route, text), ensure_ascii=False, indent=2))
