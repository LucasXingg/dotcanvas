# TextView

## 简介
`TextView` 用于渲染单行文本，依托 `FontManager` 自动挑选合适字体，方便显示多语言内容。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 文本左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 文本左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 占位宽度 | 无 | 目前仅用于布局参考，可自行控制 |
| `height` | 占位高度 | 无 | |
| `text` | 需展示的文本内容 | `"Hello"` | 支持多语言 |
| `fill` | 文本颜色 | `#111827` | |
| `font_size` | 字号（pt） | `18` | |
| `font_name` | 指定字体名称 | 无 | 留空则由 `FontManager` 自动挑选 |
| `font_weight` | 字重，如 `bold` | 无 | 支持字体包中存在的字重 |

## 渲染逻辑
- 使用 `FontManager.get_font` 根据字号、字体名及字重返回 Pillow 字体对象。
- 调用 `draw.text` 在配置的坐标直接绘制，无自动换行，需要自行确保内容适配区域。

## 示例配置
```json
{
  "type": "TextView",
  "location_x": 32,
  "location_y": 48,
  "width": 280,
  "height": 40,
  "text": "欢迎使用 dotcanvas",
  "fill": "#0F172A",
  "font_size": 24,
  "font_name": "Noto Sans CJK",
  "font_weight": "bold"
}
```
