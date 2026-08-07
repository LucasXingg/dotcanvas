# 视图脚本进阶用法

每个画布视图由一个 **视图构建函数** 驱动：函数返回一个字典，描述视图类型与绘制参数。函数体可在画布工作台中编辑，最终写入 `canvas/<画布ID>.py`。

## 基本结构

```python
@staticmethod
def my_view(params: dict | None = None) -> dict:
    return {
        "type": "TextView",
        "location_x": 16,
        "location_y": 16,
        "width": 120,
        "height": 40,
        "text": "Hello",
        "fill": "#111827",
        "font_size": 16,
    }
```

返回字典中的 `type` 必须是已注册的视图类型（见 [视图文档索引](views/index.md)）。`location_x`、`location_y`、`width`、`height` 为通用必填项。

## 获取传入参数

计划任务、API 推送以及画布预览都可以附带一个 **参数字典**。运行时会把该字典传给每个视图构建函数。

### 函数签名

推荐始终声明 `params` 参数：

```python
@staticmethod
def head_view(params: dict | None = None) -> dict:
    params = params or {}
    start_date = params.get("start_date") or "2025-09-01"
    title = params.get("title", "Calendar")
    return {
        "type": "TextView",
        "location_x": 16,
        "location_y": 8,
        "width": 200,
        "height": 24,
        "text": f"{title} · {start_date}",
        "fill": "#111827",
        "font_size": 14,
    }
```

运行时会按函数签名注入参数：若存在名为 `params` 的形参，则以关键字传入；否则尝试把整份字典作为第一个位置参数。无参函数不会收到参数。

### 参数从哪里来？

| 来源 | 说明 |
| --- | --- |
| 配置管理 → 任务「参数 (JSON)」 | 守护进程按 Cron 推送时使用 |
| 画布工作台 →「预览参数」 | 仅影响浏览器预览与配置预览 |
| `POST /api/schedules/trigger` 的 `params_override` | 覆盖任务已保存参数后触发 |
| `POST /api/devices/send-canvas` 的 `params` | 向指定设备即时推送时使用 |

示例（任务参数）：

```json
{
  "start_date": "2025-09-01",
  "title": "School"
}
```

预览时在画布页填入相同 JSON 并点击「刷新预览」，即可本地验证参数逻辑。

## 安装外部 Python 库

内置环境已包含 Pillow、requests 等常用依赖。若视图需要额外包（如 `caldav`、`numpy`），在脚本中调用 `install_package`：

```python
from src.canvas_runtime.package_manager import install_package

@staticmethod
def event_text(params: dict | None = None) -> dict:
    install_package("caldav", "icalendar")

    from caldav import DAVClient
    from icalendar import Calendar
    # ... 使用第三方库生成视图配置
    return {
        "type": "TextView",
        # ...
    }
```

### 行为说明

- 包安装到项目下的 `user_site/`（可用环境变量 `DOTCANVAS_USER_SITE` 覆盖）。
- 已记录在本地清单中的包不会重复下载；首次安装可能较慢。
- 可一次传入多个包名：`install_package("numpy", "pandas")`。
- 在 Web 界面触发预览或保存并加载视图时，若发生了新的安装，控制台会弹出提示框告知正在安装的包名。
- Docker 部署时建议挂载 `user_site/`，避免重建容器后重新下载：

```bash
-v $(pwd)/user_site:/app/user_site
```

### 注意

- 仅安装可信来源的包；运行环境具备网络访问时才会成功。
- `install_package` 会阻塞当前渲染线程直到安装完成，请避免在热路径中反复安装大量不同包。
- 新画布模板已预置 `from src.canvas_runtime.package_manager import install_package`，可直接使用。

## 相关文档

- [主要界面说明](ui-overview.md)
- [视图文档索引](views/index.md)
- [API 系统](api-system.md)
