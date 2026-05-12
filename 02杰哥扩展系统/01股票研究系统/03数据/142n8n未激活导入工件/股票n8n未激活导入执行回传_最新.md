# 股票 n8n 未激活导入执行回传

- 生成时间：2026-05-09 13:58:21
- 结论：通过：目标工作流存在，id=ZkzsB6MdxlC3VMxY，active=false；未启用、未触发、未真实发送企业微信；无credentials、无webhook节点、无企业微信真实发送节点、无券商/交易节点。
- 范围：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统`

## 一、导入前

- 最终核验：16/16 pass，fail=0
- 最终核验报告：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\38n8n导入前只读审计\股票n8n未激活导入前最终核验_最新.json`
- 导入前快照：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\stock-n8n-pre-import-workflows-snapshot-最新.json`
- 导入前快照 sha256：`98e48ea4f6ab58d1ab062c9c900f82b1bb397872516cc020cf4fd42e09995935`

## 二、导入动作

- 使用 142 最新工件：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\142n8n未激活导入工件\股票主动研究闭环_n8n未激活导入_最新.json`
- 目标容器：jiege_v3_n8n
- 目标工作流：股票主动研究闭环_文件桥接未激活
- 工件 active：false
- 是否新增导入 n8n：false
- 已存在未重复导入：true
- 说明：目标工作流已存在且保持未激活，本次未重复导入。
- 执行记录：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\stock-active-research-n8n-inactive-import-最新.json`

## 三、导入后核验

- 工作流 ID：ZkzsB6MdxlC3VMxY
- 工作流名称：股票主动研究闭环_文件桥接未激活
- active 状态：false
- 节点数量：4
- 节点类型：n8n-nodes-base.manualTrigger, n8n-nodes-base.executeCommand, n8n-nodes-base.set, n8n-nodes-base.stickyNote
- 导入后快照：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\stock-n8n-post-import-workflows-snapshot-最新.json`
- 导入后快照 sha256：`98e48ea4f6ab58d1ab062c9c900f82b1bb397872516cc020cf4fd42e09995935`
- 导入后核验报告：`D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\stock-n8n-inactive-import-post-verify-最新.json`，15/15 pass，fail=0
- 当前只读复核：工作流总数=5，目标匹配数=1，webhook节点=0，credentials字段=0，企业微信真实发送节点=0，券商/交易节点=0

## 四、触发与发送

- 是否触发 n8n：false
- 是否手动触发：false
- 是否 webhook 真实触发：false
- 是否真实发送企业微信：false
- 是否群发：false
- 是否接券商/交易：false / false
- 是否重载 19310/19302：false / false

## 五、总管确认

- 是否需要总管确认：本次未激活导入回传不需要；若后续启用、触发、真实发送企业微信、群发或接券商/交易，必须另行总管/人工确认。
