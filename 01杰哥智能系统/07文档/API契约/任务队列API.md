# 任务队列 API 契约

创建日期：2026-04-26

## 一、定位

任务队列用于管理长任务。

## 二、接口

### POST /任务/创建

请求示例：

```json
{
  "请求ID": "uuid",
  "任务类型": "视频总结",
  "优先级": "P1",
  "载荷": {
    "文件路径": "待处理文件"
  }
}
```

返回示例：

```json
{
  "任务ID": "task-id",
  "状态": "queued"
}
```

### GET /任务/{任务ID}

返回示例：

```json
{
  "任务ID": "task-id",
  "状态": "running",
  "进度": 35
}
```

## 三、状态

```text
created
queued
running
success
failed
canceled
```

