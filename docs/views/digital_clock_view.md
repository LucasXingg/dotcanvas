# DigitalClockView

## 简介
`DigitalClockView` 以数字形式显示当前时间，支持自定义时间格式、时区、字体与背景色。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 绘制区域宽度 | 无 | 用于计算文本居中位置 |
| `height` | 绘制区域高度 | 无 | 用于计算文本居中位置 |
| `format` | Python `strftime` 格式字符串 | `%H:%M:%S` | 例如 `%Y-%m-%d %H:%M` |
| `timezone` | IANA 时区，例如 `Asia/Shanghai` | 本地系统时区 | 解析失败时使用本地时间 |
| `fill` | 文字颜色 | `#111827` | |
| `background_fill` | 背景色 | 无 | 留空则背景透明 |
| `font_size` | 字号（pt） | `24` | 加载 `arial.ttf`，失败时回退默认字体 |

## 渲染逻辑
- 生成当前时间，优先使用配置的时区。
- 计算文本包围盒，将文本在给定区域内水平、垂直居中。
- 若提供背景色，将在文本区域先绘制矩形背景。

## 示例配置
```json
{
  "type": "DigitalClockView",
  "location_x": 20,
  "location_y": 20,
  "width": 200,
  "height": 60,
  "format": "%Y-%m-%d %H:%M",
  "timezone": "Asia/Shanghai",
  "background_fill": "#111827",
  "fill": "#F9FAFB",
  "font_size": 28
}
```
