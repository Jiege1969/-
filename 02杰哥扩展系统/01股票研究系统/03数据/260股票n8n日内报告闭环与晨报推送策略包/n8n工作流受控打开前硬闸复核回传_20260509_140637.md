# n8n工作流受控打开前硬闸复核回传

- 生成时间：2026-05-09 14:06:37
- 施工范围：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统
- 目标工作流：股票主动研究闭环_文件桥接未激活
- 目标ID：ZkzsB6MdxlC3VMxY
- 本轮动作：只读复核 current JSON、当前导出快照、CLI list 状态和既有确认包；不启用、不触发、不发送、不交易。

## 只读复核来源

- 当前CLI导出快照：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\stock-n8n-pre-active-hard-gate-export-最新.json
- 142最新工件：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\03数据\142n8n未激活导入工件\股票主动研究闭环_n8n未激活导入_最新.json
- 导入后核验：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\stock-n8n-inactive-import-post-verify-最新.json
- 执行记录只读抽查：D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\04日志\n8n未激活导入\n8n-target-execution-readonly-after-import-最新.json
- 38/65/66/67/68/69确认包：复用为历史门禁和禁止事项依据。

## 当前CLI状态

- docker状态：jiege_v3_n8n 正在运行，端口 127.0.0.1:28679->5678/tcp。
- inactive列表：目标 `ZkzsB6MdxlC3VMxY|股票主动研究闭环_文件桥接未激活` 存在。
- active列表：未列出任何工作流；目标不在active列表。
- 当前导出：成功导出5个工作流；目标匹配数量=1；active=false。
- 执行记录抽查：目标active=0，triggerCount=0，webhook_count=0，2026-05-09执行记录=0；历史CLI执行记录2条，不属于本轮。

## 当前工作流结构复核

- 节点数量：4。
- 节点类型：manualTrigger、executeCommand、set、stickyNote。
- 自动触发节点：未发现 webhook、scheduleTrigger、cron、interval、IMAP、form/chat 等自动触发节点。
- webhook：未发现。
- schedule/cron：未发现。
- credentials字段：0。
- HTTP请求/企业微信真实发送节点：未发现。
- 券商/交易节点：未发现。
- 企业微信/券商/交易字样命中说明：仅出现在 set/stickyNote 的安全声明文本里，用于说明“无真实发送节点、无券商接口、无自动交易”，未出现在可执行发送/交易节点中。

## 142工件与当前live导出差异

- 名称、active状态、节点数量、节点类型、连接结构：一致。
- executeCommand参数存在差异：
  - 当前live导出写入触发文件字段：task=stock_active_research，mode=manual，created_at=执行时生成。
  - 142最新工件写入触发文件字段：task=stock_active_research，mode=inactive_intraday_loop，stage=manual_test_or_schedule，created_at=执行时生成。
- 差异判定：不构成 active=true 自动触发风险；但说明 live 工作流不等同于142最新日内策略增强工件。若要求启用的是142最新工件内容，需另行走“未激活导入/覆盖前复核”，本轮不导入、不覆盖。

## 技术判断

- 可以确认：仅从当前live工作流结构看，active=true 不会因 webhook/schedule/cron 自动触发。
- 可以确认：当前live工作流不含企业微信真实发送节点、不含HTTP发送节点、不含credentials、不含券商/交易节点。
- 仍需注意：工作流一旦被人工执行，会运行 executeCommand，写入 `/home/node/.n8n/jiege_bridge/stock_active_research_trigger.json`；该动作可能被宿主机受控脚本消费，因此“启用 active=true”和“人工执行”必须分开管理。
- 当前状态：技术结构具备进入受控启用准备的条件；管理/人工硬闸尚未放行，本轮不得启用。

## active=true前硬闸清单

- 目标工作流ID、名称、当前导出快照必须二次确认一致，目标匹配数量必须等于1。
- active必须在启用前仍为false；active列表中不得已有目标。
- 当前导出必须无webhook、无scheduleTrigger、无cron、无interval、无其他自动触发节点。
- 当前导出必须无credentials字段、无HTTP请求节点、无企业微信真实发送节点。
- 当前导出必须无券商/交易/下单节点。
- 执行记录只读抽查必须确认当天未新增执行记录。
- 65人工确认材料必须升级为“允许受控打开active=true但不允许手动执行、不允许发送”的明确确认文本；旧的未激活导入确认不得替代本确认。
- 66/67/68必须完成当前容器运行态复核更新；早期“启动前不具备条件”的历史材料不得直接作为当前放行依据。
- 必须确认 active=true 只是打开工作流，不点击 Execute workflow，不调用 n8n execute，不触发手动节点。
- 必须确认打开后立即复查 active列表，确认只有目标按授权变更，其它工作流状态不变。
- 必须确认如需回退，只执行 `active=false` 回退，不重载19310/19302。

## 一票否决项

- 目标匹配数量不是1。
- 当前导出中出现webhook、scheduleTrigger、cron、interval或其他自动触发节点。
- 当前导出中出现credentials、HTTP请求、企业微信真实发送、群发、券商、交易、下单节点。
- active=true会导致立即执行或已有自动触发登记无法排除。
- 当前日期存在未授权执行记录，或启用前后执行记录增加。
- 65未形成“受控打开active=true”专项人工确认。
- 总管要求继续保持未激活或未授权打开。
- 需要导入/覆盖工作流、重载19310/19302、修改总管面板或修改一键接续包才可继续。

## 下一步可执行的受控启用步骤

以下步骤是“下一步可执行方案”，本轮未执行：

1. 人工确认：使用65材料另行填写专项确认，确认内容限定为“允许把 `ZkzsB6MdxlC3VMxY` 打开为 active=true；不允许手动执行；不允许真实发送企业微信；不允许群发；不允许接券商/交易”。
2. 启用前二次只读快照：重新执行 `docker exec jiege_v3_n8n n8n list:workflow --active=false`、`docker exec jiege_v3_n8n n8n list:workflow --active=true`、`docker exec jiege_v3_n8n n8n export:workflow --all --output <只读快照路径>`。
3. 二次结构扫描：确认目标仍是4个节点，且只有 manualTrigger、executeCommand、set、stickyNote，无webhook/schedule/cron/credentials/HTTP/发送/交易节点。
4. 受控启用：仅在人工确认后执行 `docker exec jiege_v3_n8n n8n update:workflow --id ZkzsB6MdxlC3VMxY --active=true`。
5. 启用后只读复查：立即执行 active/inactive 列表和目标导出；确认目标 active=true，未产生执行记录，未新增webhook登记，未发送企业微信。
6. 回传登记：写入受控启用回传，记录命令、时间、前后快照、执行记录计数和安全边界。
7. 回退条件：若任何一票否决项出现，立即执行 `docker exec jiege_v3_n8n n8n update:workflow --id ZkzsB6MdxlC3VMxY --active=false`，并只写失败回传，不重试、不发送。

## 本轮禁止动作确认

- 启用active=true：false。
- 触发n8n：false。
- n8n execute：false。
- 手动执行工作流：false。
- 企业微信真实发送：false。
- 群发：false。
- 接券商：false。
- 交易：false。
- 重载19310/19302：false。
- 修改总管面板：false。
- 修改一键接续包：false。

## 结论

从当前live导出与CLI状态看，目标工作流具备“受控打开 active=true 不会自动触发”的技术前提，也未发现真实发送、凭据或交易节点。本轮输出受控打开前硬闸清单和下一步启用步骤草案；由于专项人工/总管确认尚未完成，本轮不启用，状态保持 active=false。
