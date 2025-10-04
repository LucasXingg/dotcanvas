# TriangleView

## 简介
`TriangleView` 绘制等腰三角形，可通过方向参数快速生成向上、向下、向左或向右的指示箭头样式。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 三角形基底宽度 | 无 | |
| `height` | 三角形高度 | 无 | |
| `direction` | 三角形朝向：`up`、`down`、`left`、`right` | `up` | 区分大小写，内部统一转小写 |
| `fill` | 填充颜色 | `#F59E0B` | |
| `outline` | 描边颜色 | `#92400E` | |

## 渲染逻辑
- 根据方向计算三角形三个顶点坐标：
  - `up`：顶点在上方，其余两个点在底边。
  - `down`：顶点在下方。
  - `left` / `right`：顶点位于左/右侧，其他两个点位于对侧垂直方向。
- 使用 `draw.polygon` 绘制填充与描边。

## 示例配置
```json
{
  "type": "TriangleView",
  "location_x": 200,
  "location_y": 120,
  "width": 80,
  "height": 60,
  "direction": "right",
  "fill": "#34D399",
  "outline": "#047857"
}
```
