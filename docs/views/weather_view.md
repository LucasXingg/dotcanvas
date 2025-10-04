# WeatherView

## 简介
`WeatherView` 用卡片样式展示天气信息，包括地点、气温、天气状况及更新时间，适合从外部服务获取数据后渲染。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 卡片左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 卡片左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 卡片宽度 | 无 | |
| `height` | 卡片高度 | 无 | |
| `location` | 地点文字 | `"Weather"` | 显示在顶部 |
| `temperature` | 温度文本，例如 `21°C` | `"--°"` | |
| `condition` | 天气描述，例如 `Sunny` | `"Unknown"` | |
| `updated_at` | 更新时间，ISO 格式字符串 | 无 | 支持 `...Z` 结尾解析 |
| `timezone` | 用于格式化更新时间的 IANA 时区 | 本地时区 | 解析失败时回退到本地 |
| `fill` | 主文本颜色 | `#111827` | 用于温度 |
| `secondary_fill` | 次文本颜色 | `#6B7280` | 用于地点、描述、更新时间 |
| `font_size` | 主体字号（pt） | `20` | 次字体字号为 `max(10, font_size - 6)` |
| `background_fill` | 背景填充色 | `#F3F4F6` | |

## 渲染逻辑
- 先绘制背景矩形，再按顺序写入地点、温度、描述文字，垂直方向使用小间距堆叠。
- 若提供 `updated_at`，尝试解析 ISO 时间；当字符串以 `Z` 结尾时自动转为 `+00:00`。
- 如果提供 `timezone`，在可能的情况下将时间转换至对应时区，并以 `Updated HH:MM` 输出。
- 任一步骤解析失败时会静默忽略更新时间，避免报错中断渲染。

## 示例配置
```json
{
  "type": "WeatherView",
  "location_x": 12,
  "location_y": 12,
  "width": 260,
  "height": 140,
  "location": "上海",
  "temperature": "27°C",
  "condition": "多云",
  "updated_at": "2024-03-12T09:30:00Z",
  "timezone": "Asia/Shanghai",
  "fill": "#0F172A",
  "secondary_fill": "#64748B",
  "font_size": 22,
  "background_fill": "#E0F2FE"
}
```
