# n8n禁用态导入草案禁用态回滚演练

- 生成时间：2026-05-08 19:00:51
- simulation_only=true
- rollback_executed=false
- network_request=false
- disabled=true
- active=false
- webhook_enabled=false
- real_trigger=false
- credential_values_present=false

| 场景 | simulation_only | rollback_executed | 目标 |
| --- | --- | --- | --- |
| 导入前备份 | True | False | 演练在允许导入之前必须存在备份清单与人工签收拦截点。 |
| 导入失败回滚 | True | False | 演练导入失败时的只读回滚剧本，不执行真实导入或回滚。 |
| 误激活回滚 | True | False | 演练误激活时的人工处置顺序，材料层保持 active=false。 |
| 凭据泄露阻断 | True | False | 演练发现凭据泄露迹象时的阻断清单，草案中不得出现真实凭据值。 |
