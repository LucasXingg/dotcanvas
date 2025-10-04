# LucideIconView

## 简介
`LucideIconView` 会根据指定的 Lucide 图标名称，从官方仓库下载 SVG 并渲染为位图。适合快速复用 Lucide 提供的丰富线性图标。

**注：** 此视图从GitHub仓库下载 lucide 图标文件，所以效果可能随网络环境变化。

## 参数说明
| 参数键 | 说明 | 默认值 | 备注 |
| --- | --- | --- | --- |
| `location_x` | 视图左上角的 X 坐标 | 无 | 基础参数，必填 |
| `location_y` | 视图左上角的 Y 坐标 | 无 | 基础参数，必填 |
| `width` | 图标宽度 | `24` | 小于 1 时自动设置为 1 |
| `height` | 图标高度 | `24` | |
| `icon` | Lucide 图标名称，例如 `sun`、`cloud` | `sun` | 对应 `lucide` 仓库中的文件名 |

## 渲染逻辑
- 通过 `https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{icon}.svg` 下载 SVG，结果缓存到内存（最多 128 个）。
- 使用 `cairosvg` 将 SVG 转换为 PNG，再交由 Pillow 粘贴到画布。
- 下载、转换或解析失败时，会记录日志并跳过绘制。
- 需要网络访问；在离线环境下请提前缓存或改用 `ImageView`。

## 示例配置
```json
{
  "type": "LucideIconView",
  "location_x": 16,
  "location_y": 16,
  "width": 48,
  "height": 48,
  "icon": "cloud-sun"
}
```
## 相关链接
- [lucide 官方网站](https://lucide.dev/icons/)