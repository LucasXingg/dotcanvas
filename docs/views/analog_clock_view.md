# AnalogClockView

## 简介
`AnalogClockView` 用于在画布上绘制一个模拟时钟。它支持自定义背景、指针与刻度颜色，并可以根据配置的时区显示当前时间。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 绘制区域宽度 | 无 | 建议为正方形以获得最佳表现 |
| `height` | 绘制区域高度 | 无 | 与 `width` 共同决定表盘尺寸 |
| `timezone` | IANA 时区字符串，例如 `UTC`、`Asia/Shanghai` | 本地系统时区 | 解析失败时退回系统时区 |
| `face_fill` | 表盘填充色 | `#F9FAFB` | |
| `outline` | 表盘边框色 | `#111827` | 线宽固定为 2 |
| `hand_color` | 时针与分针颜色 | `#111827` | |
| `second_hand_color` | 秒针颜色 | `#EF4444` | |
| `tick_color` | 小时刻度颜色 | `#4B5563` | 12 个刻度，线宽固定为 2 |

## 渲染逻辑
- 视图以 `width` 与 `height` 中较小值的一半作为半径，保持居中。
- 时针、分针、秒针根据当前时间动态旋转，秒针每秒更新。
- 当设置了 `timezone` 且解析成功时，使用指定时区；否则回退到本地时间。
- 表盘中心绘制一个小圆点，使指针视觉上更完整。

## 示例配置
```json
{
  "type": "AnalogClockView",
  "location_x": 40,
  "location_y": 40,
  "width": 200,
  "height": 200,
  "timezone": "Asia/Shanghai",
  "face_fill": "#FFFFFF",
  "outline": "#1F2937",
  "hand_color": "#1F2937",
  "second_hand_color": "#EF4444",
  "tick_color": "#9CA3AF"
}
```
