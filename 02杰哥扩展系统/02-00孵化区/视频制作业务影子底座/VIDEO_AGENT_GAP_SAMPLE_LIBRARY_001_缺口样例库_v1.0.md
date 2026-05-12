# VIDEO_AGENT_GAP_SAMPLE_LIBRARY_001 缺口样例库

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子样例库，不是真实案例库
> 日期：2026-05-08

## 目的

沉淀常见缺口样例，帮助后续影子试运行把问题准确转入澄清、复核或红线阻断，不编造用户输入或真实任务。

## 样例

| 样例编号 | 缺口类型 | 典型描述 | 进入队列 | 影子处理 |
|:---|:---|:---|:---|:---|
| GAP-SAMPLE-001 | `missing_shadow_task_id` | 用户只问“进度怎么样” | 输入澄清队列 | 请求提供影子任务编号 |
| GAP-SAMPLE-002 | `missing_platform_rule` | 未说明投放平台 | 平台规范复核队列 | 请求补平台或规则来源 |
| GAP-SAMPLE-003 | `missing_asset_authorization` | 使用素材但未说明授权 | 素材授权复核队列 | 补授权字段 |
| GAP-SAMPLE-004 | `missing_human_decision` | 草案已生成但无人复核 | 人工复核队列 | 保持待复核 |
| GAP-SAMPLE-005 | `release_gate_unclear` | 用户问“能发了吗” | 发布门禁复核队列 | 返回门禁缺口，不放行 |
| GAP-SAMPLE-006 | `real_system_request` | 用户要求直接发布或发送 | 红线阻断队列 | 登记阻断 |

## 边界

样例库只用于影子分类训练和人工复核参考，不代表真实业务发生，不读取真实素材或消息。
