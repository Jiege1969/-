# VIDEO_AGENT_REDLINE_BLOCK_REPLY_TEMPLATE_001 红线阻断回执模板

> 业务线：视频制作业务影子底座
> 层级：W1/R0
> 状态：影子回执模板，不是真实企业微信回复
> 日期：2026-05-08

## 目的

当输入命中真实生成、真实发布、真实外发、真实企业微信、n8n、服务、凭据或正式库写入等红线时，使用本模板生成边界清晰的影子阻断回执。

## 回执模板

```text
【影子阻断回执】
输入编号：{input_id}
命中类别：{redline_category}
阻断原因：{block_reason}
允许替代动作：{allowed_shadow_alternative}
待补事项：{missing_or_review_items}

说明：本回执仅来自视频制作业务影子底座。当前不执行真实生成、渲染、发布、上传、外发、企业微信真实发送、n8n 或正式库写入。
```

## 字段

- `input_id`
- `redline_category`
- `matched_terms`
- `block_reason`
- `allowed_shadow_alternative`
- `missing_or_review_items`
- `requires_manager_decision`
- `boundary_statement`

## 边界

本模板不真实发送企业微信，不调用服务，不触发 n8n，不写正式库。
