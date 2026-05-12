# ============================================================
# Name: 查询最新异常事件.py
# System: 00杰哥系统总管 / 02脚本
# Purpose: 扫描血脉分钟级监测的异常事件目录，提取最新事件摘要；用于总管响应“未处理报警”“最近有什么异常”等查询。
# Trigger: python 查询最新异常事件.py；可由报警查询API或统一入口间接调用。
# Dependencies: 04日志\血脉分钟级监测\异常事件\EVT-*.md
# Output: 控制台输出异常事件统计及最近事件结论摘要。
# Safety: 只读扫描本地异常事件文件；不触发n8n，不发送企业微信，不调用券商接口，不自动交易。
# ChangeLog: 2026-05-10 created for alert query integration.
# ============================================================

import os
import glob
from datetime import datetime

EVT_DIR = r"D:\杰哥智能化系统\00杰哥系统总管\04日志\血脉分钟级监测\异常事件"

def get_latest_events(n=10):
    files = glob.glob(os.path.join(EVT_DIR, "EVT-*.md"))
    if not files:
        return "当前没有任何异常事件记录。系统运行正常。"
    
    files.sort(key=os.path.getmtime, reverse=True)
    recent = files[:n]
    
    today = datetime.now().strftime("%Y%m%d")
    today_events = [f for f in recent if today in os.path.basename(f)]
    
    lines = []
    lines.append("## 异常事件查询结果")
    lines.append(f"- 历史累计事件总数：{len(files)}")
    lines.append(f"- 今日({datetime.now().strftime('%m月%d日')})事件数：{len(today_events)}")
    lines.append("")
    
    if today_events:
        lines.append("### 今日事件：")
        for f in today_events:
            name = os.path.basename(f)
            with open(f, 'r', encoding='utf-8') as fh:
                content = fh.read()
                for line in content.split('\n'):
                    if '结论' in line:
                        lines.append(f"- {name}: {line.strip()}")
                        break
                else:
                    lines.append(f"- {name}: 详见事件文件")
    elif recent:
        lines.append("### 最近事件：")
        for f in recent[:5]:
            name = os.path.basename(f)
            date_str = name[4:12] if len(name) > 12 else name
            with open(f, 'r', encoding='utf-8') as fh:
                content = fh.read()
                for line in content.split('\n'):
                    if '结论' in line:
                        lines.append(f"- {name}: {line.strip()}")
                        break
                else:
                    lines.append(f"- {name}: 详见事件文件")
    
    return '\n'.join(lines)

if __name__ == "__main__":
    print(get_latest_events())
