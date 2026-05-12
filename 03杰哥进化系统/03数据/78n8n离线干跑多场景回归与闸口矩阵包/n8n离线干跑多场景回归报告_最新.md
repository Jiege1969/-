# n8n 离线干跑多场景回归报告

- 执行时间：2026-05-08 18:03:30
- 状态：pass
- 场景数：5
- 节点结果数：16
- error_count：0
- 模式：offline/dry_run
- 真实触发：false
- webhook_enabled：false

| 场景 | 最终状态 | 阻断闸口 | dry_run 节点结果 |
| --- | --- | --- | --- |
| S01 税收消息转候选 | blocked_waiting_supervisor | G04、G05、G08 | S01-N01=ready:生成标准化税收消息对象；S01-N02=ready:输出税收候选分类；S01-N03=ready:候选草稿停留在本地；S01-N04=blocked:阻断在总管确认闸口 |
| S02 股票展示巡检 | inspection_ready_blocked_before_trade | G03、G06、G08 | S02-N01=ready:得到展示字段清单；S02-N02=ready:输出展示巡检结论；S02-N03=ready:修复建议停留在本地 |
| S03 视频渲染阻断 | blocked_video_real_render | G03、G07、G08 | S03-N01=ready:得到视频任务候选；S03-N02=blocked:命中视频真实渲染发布阻断；S03-N03=blocked:形成阻断说明 |
| S04 总管确认闸口 | blocked_waiting_supervisor | G08、G10 | S04-N01=ready:形成待确认列表；S04-N02=blocked:命中总管确认闸口；S04-N03=blocked:禁止自动放行 |
| S05 异常失败分级 | blocked_failure_level_l4 | G01、G02、G03、G08、G09 | S05-N01=ready:得到异常候选；S05-N02=ready:分级结果为 L4 红线风险；S05-N03=blocked:停止自动处置并等待确认 |
