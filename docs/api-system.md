# DotCanvas API 系统

DotCanvas 提供了一套精简的 HTTP API，方便自动化工作流。本文件介绍如何创建和管理 API 令牌，以及如何调用自动化相关端点。

## 认证

所有公开的自动化端点都需要 **Bearer 令牌**。可以通过新的网页控制台 **API Tokens** 页面（`/ui/tokens`）或调用下文记录的 `/tokens` REST 端点来管理令牌。每个令牌在创建时只会展示 **一次**，请妥善保存。当服务器运行在[无浏览器模式](./no-browser-mode.md)时，`/tokens` 端点会被禁用；此时需要按照该指南的说明，在命令行运行 `TokenStore` 辅助工具来创建或吊销令牌。

在每一次 API 调用的 `Authorization` 请求头中携带该令牌：

```http
Authorization: Bearer <token-value>
```

如果令牌缺失、格式错误或已被吊销，服务器会返回 `401 Unauthorized`，并带有 `WWW-Authenticate: Bearer` 响应头。

## 令牌管理端点

| 方法与路径          | 说明                                         |
| ------------------- | -------------------------------------------- |
| `GET /tokens`       | 列出活跃令牌（id、名称、预览、创建时间）       |
| `POST /tokens`      | 创建新令牌（令牌明文只返回 **一次**）          |
| `DELETE /tokens/{id}` | 按 id 吊销令牌                                 |

### 创建令牌

```bash
curl -X POST http://localhost:8000/tokens \
  -H 'Content-Type: application/json' \
  -d '{"name": "build pipeline"}'
```

成功响应会返回令牌明文及摘要记录：

```json
{
  "token": "uGW4R2...", 
  "record": {
    "id": "ab12cd34",
    "name": "build pipeline",
    "preview": "uGW4…8fzQ",
    "created_at": "2024-05-19T11:27:45Z"
  }
}
```

### 列出令牌

```bash
curl http://localhost:8000/tokens
```

服务器会返回每个令牌保存的元数据，令牌明文**不会**再次暴露。

### 吊销令牌

```bash
curl -X DELETE http://localhost:8000/tokens/ab12cd34
```

若令牌存在，响应为 `{ "status": "deleted" }`。尝试删除不存在的 id 会得到 `404 Not Found`。

## 自动化端点

所有自动化端点都需要有效的 Bearer 令牌。

### 按名称触发计划

```
POST /api/schedules/trigger
```

请求体：

```json
{
  "schedule_name": "morning-update",
  "params_override": {
    "date": "2024-05-19"
  }
}
```

服务器会重新加载配置，查找所有 `name` 与请求负载匹配的计划（覆盖所有设备，即便该计划被禁用），渲染关联的画布，并推送到已配置的设备。`params_override` 中的键值会在渲染前合并进已保存的计划参数。成功响应会包含每个被触发计划的一条记录，展示执行状态、耗时以及下一次计划运行时间：

```json
{
  "triggered": 2,
  "results": [
    {
      "task_name": "morning-update",
      "device_name": "Desk display",
      "device_id": "device-01",
      "canvas_id": "daily_overview",
      "triggered_at": "2024-05-19T11:42:12.345678",
      "status": "success",
      "duration": 1.82,
      "next_run": "2024-05-19T12:00:00"
    },
    { "task_name": "morning-update", "status": "error", "error": "..." }
  ]
}
```

如果没有任何计划名称匹配，API 会返回 `404`。

### 向指定设备发送画布

```
POST /api/devices/send-canvas
```

请求体：

```json
{
  "device_name": "Office frame",
  "canvas_id": "daily_overview",
  "params": {
    "refresh": true
  }
}
```

服务器会验证该设备是否存在，使用可选的 `params` 渲染所请求的画布，并将生成的图像推送给设备。该响应与计划触发端点的单次执行结果格式一致。

缺少设备名称会得到 `404 Not Found`。如果 DotCanvas 配置中没有 Dot. API key，服务器会返回 `400 Bad Request`。

## 在配置编辑器中手动触发

配置编辑器现在为每个已保存的计划提供一个 **Run now** 按钮。点击后会调用内部的 `/config/schedules/trigger` 端点（在控制台内无需 Bearer 令牌），并立即使用保存的参数运行该计划。

## 错误处理

* `400 Bad Request` – 请求体不合法、缺少 API key 或验证失败。
* `401 Unauthorized` – 缺失或无效的 Bearer 令牌。
* `404 Not Found` – 未知的令牌 id、设备或计划名称。
* `503 Service Unavailable` – 无法加载令牌存储。

错误响应会包含 `detail` 字段描述问题。
