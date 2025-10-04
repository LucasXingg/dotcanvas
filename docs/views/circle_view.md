# CircleView

## 简介
`CircleView` 用于绘制一个椭圆或圆形，可配置填充色与描边色，适合表现徽标、指示点等简单图形。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 绘制区域宽度 | 无 | 与 `height` 决定椭圆的水平半径 |
| `height` | 绘制区域高度 | 无 | 与 `width` 决定椭圆的垂直半径 |
| `fill` | 填充颜色 | `#FDE68A` | 可为空表示透明 |
| `outline` | 描边颜色 | `#92400E` | 线宽固定为 2 |

## 渲染逻辑
- 使用 Pillow 的 `ellipse` 方法绘制包围盒 `[x1, y1, x2, y2]` 内的图形。
- 当 `width == height` 时即为正圆；否则为椭圆。

## 示例配置
```json
{
  "type": "CircleView",
  "location_x": 120,
  "location_y": 80,
  "width": 100,
  "height": 100,
  "fill": "#60A5FA",
  "outline": "#1E3A8A"
}
```
