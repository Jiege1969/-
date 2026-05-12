path = r"D:\杰哥智能化系统\02杰哥扩展系统\00公共组件\企业微信接入设置\02脚本\企业微信统一指令本地服务入口.py"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # 替换意图归因API的静态值
    if '"意图归因API_5801":' in line:
        line = line.replace('false', 'tcp_ready(5801)')
        line = line.replace('true', 'tcp_ready(5801)')
    # 替换报警查询API的静态值
    if '"报警查询API_5802":' in line:
        line = line.replace('false', 'tcp_ready(5802)')
        line = line.replace('true', 'tcp_ready(5802)')
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# 验证替换效果
with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        if '5801' in line and 'tcp_ready' in line:
            print("替换确认:", line.strip())
        if '5802' in line and 'tcp_ready' in line:
            print("替换确认:", line.strip())
