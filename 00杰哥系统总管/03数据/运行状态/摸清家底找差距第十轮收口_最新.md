# 摸清家底找差距第十轮收口

- 更新时间：2026-05-06 11:45:34
- 原则：清债不添新债。证实无依赖当轮删除；证实当前依赖登记为资产；误判即时纠偏。
- 并行核实：Hypatia、Chandrasekhar、Pascal 三个窗口均已回收。

## 已收口删除

- Codex scratch 临时扫描目录已迁移到 第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。，scratch 根目录复核为 0。
- WSL 旧 jiege-boot-self-check.service、broken ollama.service wants 链接已删除。
- WSL 用户级重复 openclaw-gateway.service 与 wants 链接已删除；当前只保留 openclaw.service 作为 OpenClaw gateway 入口。
- jiege 用户 crontab 中两条 /opt/jiege-net-auto/auto-proxy-switch.sh 分钟级任务已删除；/opt/jiege-net-auto 已删除。
- /home/jiege/.openclaw.backup.20260426_0755 旧整目录快照已删除；.openclaw 下 .bak/.backup/n8n_backup 配置碎片已清零。
- WSL auditd.service 已取消自启并 reset-failed；未卸载系统包。

## 证实保留

- openclaw.service：enabled + active。
- WSL 127.0.0.1:11434 Ollama：OpenClaw 当前配置依赖，保留。
- wecom-forwarder.service：enabled + active，监听 127.0.0.1:18888，未停止、未触发。
- Docker v3 主线三容器：jiege_v3_ollama、jiege_v3_redis、jiege_v3_n8n。
- 第十轮并行扫描证据：13 文件，904529 bytes。

## 验收

- n8n 200；Ollama 29134 200；Redis PONG。
- Docker named volume 0；D:\01杰哥智能系统 不存在。
- n8n 受控启用检查通过：5 个母样本，全部 inactive。
- 稳定中台只读巡检：通过 3、失败 0；闭环验证：通过 8、失败 0。
- WSL：openclaw.service enabled/active；openclaw-gateway.service not-found/inactive；jiege 无 crontab；/opt/jiege-net-auto absent；.openclaw 备份碎片 0；failed units 0。

## 安全边界

未触发 n8n workflow/webhook；未发送企业微信；未调用券商接口；未自动交易；未执行 docker prune；未删除当前运行数据目录。

## 第30轮原始证据清债说明

- 第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。


## 第31轮旧验收报告清债说明

- 第31轮旧轮次验收报告已清债删除；验收结论已固化在对应_latest收口报告、当前验收报告_最新和第31轮收口报告。

