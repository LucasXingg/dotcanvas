# DotCanvas 贡献指南

感谢你对 DotCanvas 的兴趣！本文档介绍项目概况、如何开发新的视图、如何调用已有 API，以及贡献代码的推荐流程。

## 目录
- [总览](#总览)
  - [核心目录结构](#核心目录结构)
  - [开发提示](#开发提示)
- [开发新的 View](#开发新的-view)
  - [1. 复制模板](#1-复制模板)
  - [2. 重命名类与类型标识](#2-重命名类与类型标识)
  - [3. 定义配置参数](#3-定义配置参数)
  - [4. 实现 draw 方法](#4-实现-draw-方法)
  - [5. 导出视图模块](#5-导出视图模块)
  - [6. 编写配置与测试](#6-编写配置与测试)
- [使用 API](#使用-api)
- [画布文件结构](#画布文件结构)
- [贡献流程](#贡献流程)
  - [1. 准备开发环境](#1-准备开发环境)
  - [2. 创建特性分支](#2-创建特性分支)
  - [3. 编写并记录改动](#3-编写并记录改动)
  - [4. 运行质量检查](#4-运行质量检查)
  - [5. 推送并创建合并请求](#5-推送并创建合并请求)
  - [6. 响应代码审查反馈](#6-响应代码审查反馈)

---

## 总览
DotCanvas 提供一个可定制的画布渲染与管理平台，后端基于 FastAPI，前端使用静态页面与 Fetch API 通信，渲染由 Pillow 完成。

### 核心目录结构
- `canvas/`：用户画布模块（每个画布一个 `*.py`），不含框架代码。
- `src/canvas_runtime/`：画布框架（基类、模板、`views/`、`canvas_manager/`、运行时包安装）。
- `configs/`：配置文件路径。
- `assets/`：字体与其他静态资源（如 `font_manager.py`）。
- `src/`：后台服务逻辑（`api.py`、`daemon.py`、`service_config.py` 等）以及上述 `canvas_runtime`。
- `frontend/`：Vite + React 管理界面。
- `server.py`：服务启动脚本

### 开发提示
- 项目尚未包含完整的自动化测试。
- 画布模块的改动会即时写入磁盘，结合版本控制可回滚生成文件。
- 前端默认主页文件为 `pages/daemon.html`，并通过 Fetch API 与 FastAPI 后端通信。
- 画布尺寸固定为 296x152 像素，这是 Dot. 的硬件屏幕尺寸。

---

## 开发新的 View
Views 负责在画布上绘制图形、文字或其他内容。每个视图需继承 `_BaseView` 并实现静态方法 `draw`，该方法接收 `PIL.ImageDraw` 实例和配置字典。

### 1. 复制模板
从 [`src/canvas_runtime/views/_new_view_template.py`](src/canvas_runtime/views/_new_view_template.py) 开始，复制模板至同目录下的新模块。例如创建横幅视图：
```bash
cp src/canvas_runtime/views/_new_view_template.py src/canvas_runtime/views/banner.py
```

### 2. 重命名类与类型标识
在新模块中：
- 将类名改为具描述性的名称（如 `BannerView`）。
- 将 `TYPE` 常量设置为全局唯一字符串。`_BaseCanvas.find_available_views` 会扫描 `src.canvas_runtime.views` 目录以发现该标识，因此文件名与类名需与视图保持一致。

### 3. 定义配置参数
扩展 `_BaseView.DEFAULT_PARAMS`，为视图所需的额外配置键提供说明：

```python
PARAMS = {
    **_BaseView.DEFAULT_PARAMS,
    "title": "横幅内显示的文本",
    "background_color": "横幅的填充颜色",
}
```

### 4. 实现 `draw` 方法
实现 `@staticmethod draw(draw: ImageDraw.ImageDraw, config: dict) -> None`，使用传入的 `PIL.ImageDraw` 对象绘制视图内容。参考 [`CircleView.draw`](src/canvas_runtime/views/circle.py) 等示例，验证 `config` 参数并提供合理默认值。

### 5. 导出视图模块
若希望通过 `src.canvas_runtime.views` 直接导入新视图，可在 [`src/canvas_runtime/views/__init__.py`](src/canvas_runtime/views/__init__.py) 中添加：
```python
from .banner import BannerView

__all__ = ["BannerView"]
```
**注：** `Canvas` 类会自动扫描 `src.canvas_runtime.views` 下的模块，所以此步骤非必需，但能提升模块的可用性。

### 6. 编写视图文档
从 [`docs/view-doc-template.md`](docs/view-doc-template.md) 开始，复制模板至`docs/views`目录下。例如创建横幅文档：
```bash
cp docs/view-doc-template.md docs/views/banner_view.md
```
填写视图对应信息，然后在[index.md](docs/views/index.md)中添加对应的索引。

---

## 使用 API

启动服务后可通过 <http://localhost:8000/> 访问接口文档。

调用接口前，请确保通过 `uvicorn server:app --reload` 启动本地服务，并在请求中提供所需的 JSON 载荷或查询参数。

---

## 画布文件结构
- 画布文件位于 `canvas/` 目录，由程序根据用户操作自动生成或更新，无需手动创建。
- 每个画布模块定义 `Canvas` 类和匹配的 `CONFIG` 配置，用于描述视图布局与默认参数。
- 每个画布对应一个独立的文件，文件名需要与`ID`常量保持一致，此常量为全局唯一。

---

## 贡献流程

### 1. 准备开发环境
参考[README](README.md)中的**快速开始**章节

### 2. 创建特性分支
1. 确保本地 `main` 分支为最新：
   ```bash
   git checkout main
   git pull origin main
   ```
2. 基于最新代码创建描述性特性分支：
   ```bash
   git checkout -b feature/<short-description>
   ```

### 3. 编写并记录改动
- 频繁提交，提交信息需清晰描述每次改动的目的。
- 在代码变更的同时更新相关文档，提升项目可维护性。

### 4. 运行质量检查
- 在提交合并请求前，确保项目依然稳定可用。
- 如修改了渲染逻辑，请手动启动服务验证视图效果。


### 5. 推送并创建合并请求
1. 推送特性分支：
   ```bash
   git push -u origin feature/<short-description>
   ```
2. 创建合并请求

### 6. 响应代码审查反馈
- 在同一特性分支上完成审查修改。
- 对审查意见逐一回复，说明修改内容。
- 按评审要求通过 rebase 或 merge 方式保持分支与 `main` 同步。

准备就绪后，欢迎通过合并请求分享你的贡献！
