# ImageView

## 简介
`ImageView` 用于加载远程或 Base64 图片并绘制到画布上，支持按比例缩放、背景填充与透明度处理。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 目标宽度 | 图片原始宽度 | 小于 1 时自动提升为 1 |
| `height` | 目标高度 | 图片原始高度 | 小于 1 时自动提升为 1 |
| `source_type` | 图像来源类型，`url` 或 `base64` | `url` | 大小写不敏感 |
| `url` | 图片地址 | 无 | 仅在 `source_type=url` 时使用 |
| `base64` | Base64 编码图像数据 | 无 | 支持 data URI 形式 |
| `maintain_aspect_ratio` | 是否保持宽高比 | `True` | 为真时居中缩放 |
| `background_fill` | 背景填充色 | 无 | 指定时先绘制底色，可用于透明图片 |

## 渲染逻辑
- 根据 `source_type` 选择加载方式：
  - `base64`：解析数据；若包含 `data:` 前缀会自动截取。
  - `url`：发送带 UA 的 HTTP 请求，超时 5 秒。
- 加载失败（网络错误、解码失败等）时直接返回，不绘制内容。
- 在保持比例模式下，图像会等比缩放并在目标区域内居中；否则拉伸填满整个区域。
- 如果原图带透明像素，会尝试保留透明度；提供 `background_fill` 时先绘制背景色。

## 示例配置
```json
{
  "type": "ImageView",
  "location_x": 0,
  "location_y": 0,
  "width": 300,
  "height": 200,
  "source_type": "url",
  "url": "https://example.com/banner.png",
  "maintain_aspect_ratio": true,
  "background_fill": "#FFFFFF"
}
```
