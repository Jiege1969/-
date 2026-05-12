# 00总管 Redis低风险正式队列前评估回收报告

施工批次：并行小任务E  
施工时间：2026-05-05 14:10:00 +08:00  
负责范围：仅在 `D:\杰哥智能化系统\00杰哥系统总管` 下新增Redis Streams低风险正式队列前评估包、只读验证脚本和固定回收报告。未修改其他worker文件，未回退已有修改。

## 产物路径

- 评估包 JSON：`D:\杰哥智能化系统\00杰哥系统总管\03数据\任务契约\RedisStreams低风险正式队列前评估包_最新.json`
- 评估包 Markdown：`D:\杰哥智能化系统\00杰哥系统总管\03数据\任务契约\RedisStreams低风险正式队列前评估包_最新.md`
- 只读验证脚本：`D:\杰哥智能化系统\00杰哥系统总管\02脚本\验证Redis低风险正式队列前评估包.py`
- 回收报告 JSON：`D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\00总管_Redis低风险正式队列前评估回收报告_最新.json`
- 回收报告 Markdown：`D:\杰哥智能化系统\00杰哥系统总管\03数据\并行回收\00总管_Redis低风险正式队列前评估回收报告_最新.md`

## 覆盖项

- stream字段：必填/可选字段、risk_level限制、payload_json和safety_flags_json规则已覆盖。
- 消费组：候选stream、consumer group、consumer命名、创建门槛、读取策略已覆盖。
- ACK/PENDING：ACK前置条件、禁止提前ACK、pending检查与接管阈值已覆盖。
- 重试/死信：三次重试、退避策略、可重试/不可重试错误、dead-letter payload和人工回收路径已覆盖。
- 幂等：idempotency_key生成与去重规则已覆盖。
- SQLite落账：候选台账表、必需列、状态流转、事务边界已覆盖。
- 失败回收：worker崩溃、SQLite busy、禁止动作、partial output和Redis不可用场景已覆盖。
- GPU排队：默认不占GPU、低优先级本地推理、pending上限、显存阈值和CPU fallback已覆盖。
- 资源占用评估：consumer数量、CPU/内存/磁盘/SQLite/GPU/PENDING阈值与观测指标已覆盖。
- 正式升级门槛：静态契约、零副作用、shadow replay、pending/dead-letter演练、SQLite审计、资源预算、人工变更单已覆盖。

## 验收命令

```powershell
python "D:\杰哥智能化系统\00杰哥系统总管\02脚本\验证Redis低风险正式队列前评估包.py"
```

验收模式：`read_only_local_parse`  
验收结果：通过，28/28，失败0。  
外部服务触碰：否。

## 安全边界

本轮不连接真实Redis，不启动服务，不触发n8n，不发送企业微信，不写正式库，不调用券商接口，不自动交易，不发起外部网络请求。

## 阻断/风险状态

- 交付阻断项：无。
- 安全阻断项：无新增未处理阻断；正式启用仍被门槛阻断。
- 并行冲突风险：低。写入范围限定在00总管新增文件与固定回收报告。
- 正式启用结论：不得直接启用。必须先完成本地shadow replay、pending/dead-letter演练、SQLite审计、资源观测和人工变更单。
