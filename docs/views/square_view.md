# SquareView

## 简介
`SquareView` 绘制矩形或带圆角的矩形，可用于卡片、容器或基础装饰元素。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 矩形宽度 | 无 | |
| `height` | 矩形高度 | 无 | |
| `fill` | 填充颜色 | `#D1E8FF` | 可为空表示透明 |
| `outline` | 描边颜色 | `#1E3A8A` | 线宽固定为 2 |
| `corner_radius` | 圆角半径 | `0` | 大于 0 时使用圆角矩形 |

## 渲染逻辑
- 当 `corner_radius` > 0 时调用 `rounded_rectangle`，否则使用 `rectangle`。
- 描边宽度固定为 2；若不需要描边，可在配置中将 `outline` 设置为与背景相同。

## 示例配置
```json
{
  "type": "SquareView",
  "location_x": 10,
  "location_y": 10,
  "width": 180,
  "height": 120,
  "fill": "#F9FAFB",
  "outline": "#D1D5DB",
  "corner_radius": 12
}
```
