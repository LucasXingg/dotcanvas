# DotCanvas / 点画布

DotCanvas is a lightweight tool for authoring visual "canvases" backed by Python.
A FastAPI server exposes endpoints for reading, creating, updating, and rendering
canvases, while a web UI lets you edit canvas metadata, view builder functions,
and preview the generated image in real time.

DotCanvas 是一个轻量级的可视化画布编辑工具，后端由 Python 驱动。FastAPI 服务
提供读取、创建、更新和渲染画布的接口，配套的 Web 界面允许你直接在浏览器中
编辑画布元数据、视图构建函数代码，并实时预览生成的图片。

## Features / 功能特性

- Edit existing canvases entirely from the browser, including view builder code and friendly names.
- Create brand new canvases from a template with one click.
- Change a canvas ID safely; the server rewrites the canvas module and cleans up the old file.
- Preview canvases instantly through Pillow-powered rendering.

- 在浏览器内完成现有画布的所有编辑，包括视图函数代码和展示名称。
- 通过模板一键创建全新的画布文件。
- 安全地修改画布 ID：服务端会重写画布模块并删除旧文件。
- 借助 Pillow 即时渲染，快速查看画布预览。

## Requirements / 环境要求

- Python 3.12+
- pip (or another dependency manager compatible with `pyproject.toml`)

- Python 3.12 及以上版本
- pip（或兼容 `pyproject.toml` 的其他依赖管理工具）

## Setup / 环境配置

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Running the server / 启动服务

```bash
uvicorn server:app --reload
```

Then open the UI at <http://localhost:8000/ui/>. The FastAPI docs are available at
<http://localhost:8000/docs> for interactive exploration of each endpoint.

运行以上命令后，打开 <http://localhost:8000/ui/> 访问前端界面。FastAPI 提供的
互动式接口文档位于 <http://localhost:8000/docs>，便于调试各个端点。

## Working with canvases / 画布文件说明

- Canvas modules live in `canvas/*.py`. Each module defines a `Canvas` class and a `CONFIG` dictionary describing available views.
- The `canvas/canvas_manager` package handles all create/read/update operations and ensures canvas files stay in sync with the editor UI.
- Generated previews rely on Pillow. The preview image endpoint renders on demand using the updated module, so remember to save changes before refreshing.

- 画布模块存放在 `canvas/*.py`，每个模块包含 `Canvas` 类和描述视图的 `CONFIG` 字典。
- `canvas/canvas_manager` 负责画布的创建、读取与保存，确保磁盘文件与前端编辑保持同步。
- 预览图片依赖 Pillow。预览接口会实时加载最新模块，因此修改后请先保存再刷新预览。

## API overview / 接口总览

| Method | Path                            | Description                          |
| ------ | -------------------------------- | ------------------------------------ |
| GET    | `/canvases`                     | List all canvases                    |
| GET    | `/canvases/{canvas_id}`         | Fetch canvas metadata and view code  |
| POST   | `/canvases`                     | Create a new canvas from the template|
| PUT    | `/canvases/{canvas_id}`         | Update name, views, and optionally ID|
| GET    | `/canvases/{canvas_id}/preview` | Render and stream the latest preview |
| GET    | `/views`                        | List available view builder classes  |

| 方法 | 路径                               | 说明                                   |
| ---- | ---------------------------------- | -------------------------------------- |
| GET  | `/canvases`                        | 列出所有画布                           |
| GET  | `/canvases/{canvas_id}`            | 获取画布元数据与视图代码               |
| POST | `/canvases`                        | 基于模板创建新画布                     |
| PUT  | `/canvases/{canvas_id}`            | 更新名称、视图，并可修改画布 ID        |
| GET  | `/canvases/{canvas_id}/preview`    | 渲染并返回最新预览图像                 |
| GET  | `/views`                           | 列出可用的视图构建类                   |

## Development notes / 开发提示

- The project currently has no automated test suite. Consider adding `pytest` tests for the canvas manager when extending functionality.
- Changes to canvas modules are immediately written to disk; use version control to keep track of generated canvases and revert when necessary.
- The front-end lives in `pages/index.html` and communicates with the FastAPI backend via fetch calls.

- 项目目前尚未包含自动化测试，后续扩展功能时建议添加基于 `pytest` 的测试。
- 画布模块保存后会立即写入磁盘，建议配合版本控制管理生成的文件，便于回滚。
- 前端位于 `pages/index.html`，通过 Fetch API 与 FastAPI 后端通信。

