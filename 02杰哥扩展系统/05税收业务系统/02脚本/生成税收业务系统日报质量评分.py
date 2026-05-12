# -*- coding: utf-8 -*-
"""
Name: 生成税收业务系统日报质量评分.py
System: 02杰哥扩展系统 / 05税收业务系统 / 02脚本
Purpose: 生成税收业务系统的日报质量评分。
Trigger: Windows Scheduled Task 杰哥智能化系统_质量评分_税收业务系统.
Dependencies: 00总管/02脚本/业务子系统日报质量评分公共库.py；业务子系统日报质量评分配置.py。
Output: 税收业务系统日报质量评分结果。
Safety: 本地只读评分和本地结果写入；不触发n8n，不发送企业微信，不调用券商接口，不自动交易。
ChangeLog: 2026-05-09 created; 2026-05-10 header standardized.
"""

from __future__ import annotations

import sys
from pathlib import Path

manager_scripts = Path(r"D:\杰哥智能化系统\00杰哥系统总管\02脚本")
sys.path.insert(0, str(manager_scripts))

from 业务子系统日报质量评分公共库 import score_system
from 业务子系统日报质量评分配置 import CONFIGS


if __name__ == "__main__":
    score_system(CONFIGS[3])
