# serviceraj 与旧计划任务核实判定

生成时间：2026-05-06 06:52:44 +08:00  
核实方式：只读扫描、计划任务读取、任务 XML 静态分析、引用路径存在性核验、进程命令行只读检索、并行窗口复核。  
安全边界：未执行可疑命令，未触发 n8n，未发送企业微信，未调用券商接口，未自动交易，未移动或删除正式数据。后续已按证据链删除无依赖旧任务和 `serviceraj`。

## 零、后续处置更新

更新时间：2026-05-06 06:55:29 +08:00

根据用户确认，“引用脚本不存在、最近失败、无当前依赖”的旧计划任务不再仅列为禁用候选，而是按“证据导出后删除”执行。

已删除旧计划任务：

- `AI_AutoEvolve`
- `AI_Backup`
- `AI_HealthCheck`
- `AI_WeeklyCleanup`
- `DailyWorkPlan`
- `WSL_AutoStart`

证据目录：`第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。`

删除前已导出：

- 6 个任务 XML：`AI_AutoEvolve.xml`、`AI_Backup.xml`、`AI_HealthCheck.xml`、`AI_WeeklyCleanup.xml`、`DailyWorkPlan.xml`、`WSL_AutoStart.xml`
- 删除前清单：`删除前清单.json`
- 删除后验收：`删除后验收.json`

删除后验收：

- 上述 6 个旧任务均不存在。
- `杰哥智能化系统_*` 新命名计划任务仍存在，状态为 `Ready`。
- `serviceraj` 当时未在旧任务批次中处理，随后已单独导出证据并删除。

二次更新时间：2026-05-06 06:58:43 +08:00

根据“不为旧债又添新债”的原则，`serviceraj` 已从“导出证据后禁用/观察”改为“导出证据后删除”。

`serviceraj` 删除证据目录：

`第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。`

删除后验收：

- `serviceraj` 不存在。
- 6 个旧计划任务仍不存在。
- 8 个 `杰哥智能化系统_*` 新命名计划任务仍存在。
- 血脉分钟级探针最新状态：`ready=true`，`failed_count=0`。

## 一、总判断

本轮不再把这些暗角交给用户凭感觉确认，而是按证据链给出技术判定：

| 对象 | 当前判定 | 建议处置 | 理由 |
|---|---|---|---|
| `serviceraj` | 非杰哥系统依赖，P0 安全风险 | 已导出证据并删除 | 混淆命令、32 位 PowerShell、编码脚本、证书校验绕过、外部下载并 `IEX` 执行，且无业务命名、无作者、无系统文档依赖 |
| `AI_AutoEvolve` | 旧任务残留，当前无依赖 | 已导出证据并删除 | 引用 `D:\杰哥智能系统\脚本工具\AutoEvolve.ps1`，脚本不存在 |
| `AI_HealthCheck` | 旧任务残留，当前无依赖 | 已导出证据并删除 | 引用 `D:\杰哥智能系统\03_脚本工具\System-Health-Check.ps1`，脚本不存在 |
| `WSL_AutoStart` | 旧任务残留，当前无依赖 | 已导出证据并删除 | 引用 `Ubuntu` 和 `/mnt/d/00杰哥系统总管/...`，本机当前 WSL 发行版为 `Ubuntu-24.04`，脚本不存在 |
| `AI_Backup` | 旧任务残留，失败态 | 已导出证据并删除 | 引用脚本不存在，最近结果失败，当前备份体系应以新依赖清单和 F 盘备份规则为准 |
| `AI_WeeklyCleanup` | 旧任务残留，失败态 | 已导出证据并删除 | 引用脚本不存在，最近结果失败；清理类任务需纳入受控窗口，不能靠旧脚本自动跑 |
| `DailyWorkPlan` | 旧任务残留，失败态 | 已导出证据并删除 | 引用 `D:\AI_System\Scripts\runworkplan.bat`，脚本不存在，最近结果失败 |
| WSL `.bashrc` 旧 Ollama 路径 | 配置残留 | 写治理预案，后续人工确认后修正 | 存在 `/mnt/d/01杰哥智能系统/...`，与当前正式 `D:\杰哥智能化系统` 不一致；但不是 Windows 主线服务当前依赖 |

## 二、`serviceraj` 证据链

计划任务读取：

- 任务名：`serviceraj`
- 状态：`Ready`
- 启用：`true`
- 隐藏：`false`
- 运行用户：`Administrator`
- 触发器：一次性时间触发，`2026-04-26T10:33:46` 到 `2026-04-26T10:33:55`
- 下一次运行：空
- 任务文件：`C:\Windows\System32\Tasks\serviceraj`
- 任务文件 SHA256：`BF5D8264C0C7492BDFCA6FA131E56A8C4702B4FAFF6EB7EB0B3CD626D3D646CF`

动作特征：

- 通过 `cmd /v:on` 拼接 `powershell`
- 调用 `%windir%\SysWOW64\WindowsPowerShell\v1.0\powershell`
- 使用 `-E` 编码脚本
- 静态解码后发现：
  - 对 `COMPUTERNAME + USERNAME` 计算 MD5 派生标识
  - 设置 `ServerCertificateValidationCallback={$true}`，绕过证书校验
  - 使用 `Net.WebClient.DownloadString(...)`
  - 请求外部地址形态：`https://ip$npl.macarona.autos/Dog-...`
  - 使用 `IEX $Filter` 执行下载内容
- 解码脚本 SHA256：`6EB6B52A9543A7E0D0BAEA2E7FC627595ED81C010A6FB65B44B326FB7E8F058B`

依赖核实：

- 在正式系统关键目录内未发现 `macarona.autos` 业务依赖命中。
- `serviceraj` 的命中只来自本轮暗角扫描报告、当前施工面板、接续包和路线图，不来自正式业务脚本。
- 当前进程命令行检索未发现 `serviceraj`、`macarona.autos`、`Dog-911542` 对应活动进程；命中的只是本轮扫描 PowerShell 自身。

结论：

`serviceraj` 不具备保留理由。它不是“用户需要确认业务价值”的项目，而是技术证据已经足够清楚的异常计划任务。已导出任务 XML、任务文件副本、哈希和删除前清单，并删除该计划任务。

## 三、旧计划任务归属判定

| 任务 | 当前状态 | 最近结果 | 下一次运行 | 动作 | 引用脚本是否存在 | 判定 |
|---|---:|---:|---:|---|---:|---|
| `AI_AutoEvolve` | Disabled | `267011` | 有 | `powershell.exe -File "D:\杰哥智能系统\脚本工具\AutoEvolve.ps1"` | 否 | 旧进化任务残留 |
| `AI_Backup` | Ready | `4294770688` | 有 | `powershell.exe -File "D:\杰哥智能系统\03_脚本工具\backup.ps1"` | 否 | 旧备份任务残留 |
| `AI_HealthCheck` | Disabled | `0` | 有 | `powershell.exe -File "D:\杰哥智能系统\03_脚本工具\System-Health-Check.ps1"` | 否 | 旧健康检查残留 |
| `AI_WeeklyCleanup` | Ready | `2147946720` | 有 | `powershell.exe -File "D:\杰哥智能系统\03_脚本工具\weekly_cleanup.ps1"` | 否 | 旧清理任务残留 |
| `DailyWorkPlan` | Ready | `1` | 有 | `D:\AI_System\Scripts\runworkplan.bat` | 否 | 旧工作计划残留 |
| `WSL_AutoStart` | Disabled | `4294967295` | 无 | `wsl.exe -d Ubuntu bash /mnt/d/00杰哥系统总管/02脚本/守护/boot_self_check.sh` | 否 | 旧 WSL 启动残留 |

辅助核实：

- `D:\杰哥智能系统\...` 相关脚本路径全部不存在。
- `D:\AI_System\Scripts\runworkplan.bat` 不存在。
- `/mnt/d/00杰哥系统总管/02脚本/守护/boot_self_check.sh` 对应 Windows 路径 `D:\00杰哥系统总管\02脚本\守护\boot_self_check.sh` 不存在。
- 当前正式目录为 `D:\杰哥智能化系统`，并行复核未发现 `D:\01杰哥智能系统` 旧根目录复发。
- 本机 WSL 发行版为 `docker-desktop` 与 `Ubuntu-24.04`，`WSL_AutoStart` 使用的 `Ubuntu` 名称不匹配。

结论：

这些任务不是当前正式系统的可靠依赖，已全部导出证据并删除。清理类、备份类、自启动类任务不能继续靠旧脚本自动运行，也不再留下“待禁用/待观察”尾巴。

## 四、WSL 旧 Ollama 路径

在 `Ubuntu-24.04` 的 `/home/jiege/.bashrc` 中发现：

- `OLLAMA_MODELS=/mnt/d/01杰哥智能系统/.../ollama`
- `OLLAMA_MODELS=/mnt/d/01杰哥智能系统/.../ollama/models`
- `alias ollama='docker exec ollama ollama'`
- 另有 Docker 命令保护函数，拦截部分 `volume rm.*ollama` 和 `system prune.*-a`

判定：

- 这是旧路径配置残留，不是当前 Windows 主线 Docker/Ollama 运行依赖。
- 当前 Windows 环境变量 `OLLAMA_MODELS` 指向 `D:\杰哥智能化系统\01杰哥智能系统\03数据\ollama\models`，路径正确。
- 当前主线 Ollama 容器为 `jiege_v3_ollama`，WSL alias 指向 `ollama` 容器名，存在失配风险。

建议：

后续建立“WSL 环境治理预案”：先备份 `.bashrc`，再把旧 `OLLAMA_MODELS` 和旧 alias 改成正式路径或显式注释废弃。这个动作会改变交互 shell 环境，不在本轮自动执行。

## 五、下一步处置顺序

1. 已完成：导出并删除 `serviceraj`。
2. 已完成：导出并删除 `AI_AutoEvolve`、`AI_Backup`、`AI_HealthCheck`、`AI_WeeklyCleanup`、`DailyWorkPlan`、`WSL_AutoStart`。
3. 下一步：为 WSL `.bashrc` 写修正预案，不直接改。
4. 下一步：继续推进数据资产台账和提示词版本化。

## 六、给总管的规则增补

- 凡是计划任务引用脚本不存在，且最近运行失败，且无当前文档/配置依赖，应标为“旧任务残留”，不得默认保留。
- 凡是计划任务包含 `-EncodedCommand`、外部下载、`IEX`、证书校验绕过、混淆执行链，且无系统归属文档，应标为 P0 安全风险。
- 对 P0 安全风险，证据充分且无当前依赖时，应导出证据后直接移除持久化入口，不长期留下“待处理”债务。
- 对清理、备份、自启动类旧任务，若引用脚本不存在且无当前依赖，应导出证据后删除；只有依赖不明时才进入观察。

## 第30轮原始证据清债说明

- 第30轮原始暗角证据目录已清债删除；判断结论、删除对象、验收结果和安全边界已固化在对应_latest收口报告。

