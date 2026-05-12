# -*- coding: utf-8 -*-
"""
Name: 汇总业务子系统日报质量评分到总管面板.py
System: 00杰哥系统总管 / 02脚本
Purpose: 汇总各扩展业务子系统日报质量评分，并写入总管面板数据。
Trigger: Windows Scheduled Task 杰哥智能化系统_质量评分_扩展子系统总汇.
Dependencies: 业务子系统日报质量评分公共库.py；业务子系统日报质量评分配置.py；各子系统评分输出。
Output: 总管日报质量评分汇总面板和对应运行状态文件。
Safety: 本地读取和写入质量评分结果；不触发n8n，不发送企业微信，不调用券商接口，不自动交易。
ChangeLog: 2026-05-09 created; 2026-05-10 header standardized.
"""

from __future__ import annotations

from 业务子系统日报质量评分公共库 import aggregate_quality_panel
from 业务子系统日报质量评分配置 import CONFIGS


if __name__ == "__main__":
    aggregate_quality_panel(CONFIGS)
