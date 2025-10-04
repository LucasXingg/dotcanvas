# ProgressBarView

## 简介
`ProgressBarView` 用于绘制水平进度条，支持背景色、填充色、描边以及圆角配置，可展示任务进度或加载状态。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 进度条宽度 | 无 | 决定最大填充长度 |
| `height` | 进度条高度 | 无 | |
| `progress` | 进度值，可为 0-1 或 0-100 | `0` | 超出范围自动裁剪 |
| `background_fill` | 底色 | `#E5E7EB` | 绘制轨道区域 |
| `progress_fill` | 前景色 | `#10B981` | 绘制已完成部分 |
| `outline` | 描边颜色 | `#374151` | 线宽固定为 2 |
| `corner_radius` | 圆角半径 | `0` | 自动限制在宽高一半以内 |

## 渲染逻辑
- 先绘制带描边的完整轨道，再根据 `progress` 比例填充前景。
- 当启用圆角时，轨道与前景均使用 `rounded_rectangle`，确保圆角一致。
- 进度值会在 0-1 范围内裁剪；当提供 0-100 区间数值时自动换算。

## 示例配置
```json
{
  "type": "ProgressBarView",
  "location_x": 40,
  "location_y": 200,
  "width": 220,
  "height": 24,
  "progress": 68,
  "background_fill": "#111827",
  "progress_fill": "#22D3EE",
  "outline": "#0EA5E9",
  "corner_radius": 8
}
```
