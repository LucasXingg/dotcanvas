# DotCanvas


DotCanvas 是一个轻量级的可视化Dot.编辑工具。

提供读取、创建、更新和渲染画布的接口，配套的 Web 界面允许你直接在浏览器中编辑画布元数据、视图构建函数代码，并实时预览生成的图片。

## 功能特性

- 在浏览器内完成所有操作，包括编辑画布，设定推送任务。
- 所有元素都可以通过python脚本自由动态的生成内容。
- 实时预览你的作品！

# 快速开始

## Docker 部署

我们已在 GitHub Container Registry 发布预构建镜像 `ghcr.io/lucasxingg/dotcanvas`，可以直接拉取并运行。`main` 分支推送发布 `:latest`，`dev` 分支推送发布 `:beta`。

```bash
# 拉取稳定镜像
docker pull ghcr.io/lucasxingg/dotcanvas:latest

# 或拉取开发分支 beta 镜像
# docker pull ghcr.io/lucasxingg/dotcanvas:beta

# 运行容器（映射端口；建议同时挂载 configs 与 canvas，见下方「持久化」章节）
docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

容器启动后，通过 <http://localhost:8000/> 访问管理界面。
当你需要更新配置时，直接编辑宿主机 `configs/config.yaml` 并重启容器即可。

> 若不挂载卷，画布与配置只存在于容器可写层中；拉取新镜像并重建容器后会全部丢失。请务必按下一节挂载数据卷。

## 持久化画布与配置（镜像更新后不丢失）

目录职责：

- **`canvas/`**：只存放你的画布文件（`*.py`）。框架代码（基类、视图、模板、管理器）在镜像内的 `src/canvas_runtime/`，**不会**被卷挂载覆盖。
- **`configs/`**：服务配置与 API 令牌（如 `config.yaml`、`tokens.json`）。空目录也可以挂载；启动时会自动生成 `config.yaml` / `config-example.yaml`。
- **`user_site/`**：视图里调用 `install_package(...)` 时安装的 Python 包。

若不挂载卷，这些数据只在容器可写层中；拉取新镜像并重建容器后会丢失。

### 推荐启动方式（挂载数据目录）

从本仓库部署时，直接挂载仓库里的 `configs/` 与 `canvas/`：

```bash
# 可选：预先准备配置（不复制也没关系，容器会自动生成默认 config.yaml）
cp -n configs/config-example.yaml configs/config.yaml

docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

只有预构建镜像、本地还没有数据目录时：

```bash
mkdir -p configs canvas

docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

此后在 UI 中新建的画布都会写到宿主机的 `canvas/`。空的挂载目录也可以：服务启动时会自动补全 `canvas/__init__.py`、两个示例画布（`countdown_canvas.py`、`calendar_canvas.py`），以及 `configs/config.yaml`（可再在配置页填入真实 API Key / 设备 ID）。

可选：若视图使用了 `install_package()`，可再挂载 `-v $(pwd)/user_site:/app/user_site`，避免重建容器后重新下载依赖。

### 更新镜像时保留自己的画布

```bash
# 1. 拉取新镜像
docker pull ghcr.io/lucasxingg/dotcanvas:latest

# 2. 用相同的卷挂载重建容器
docker stop dotcanvas && docker rm dotcanvas
docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

只要 `-v .../canvas:/app/canvas` 指向同一宿主机目录，你的 `*.py` 画布会原样保留；新镜像里的框架更新（视图、基类等）会自动生效，无需再从镜像回拷框架文件。

### 注意事项

- `canvas/` 下每个画布对应一个 `*.py` 文件（例如 `hello_world.py`）。仓库自带的 demo（如 `countdown_canvas.py`、`calendar_canvas.py`）也在此目录；请勿把框架代码放回该目录。
- 若你仍保留着旧版镜像导出的 `canvas/`（内含 `_base_canvas.py`、`views/` 等），可以删掉这些遗留框架文件，只留下自己的画布 `*.py`；运行时一律使用镜像内的 `src/canvas_runtime/`。
- `configs/` 含 API key 与令牌，请妥善保管挂载目录的权限。

## 手动构建 Docker 镜像部署

如果你希望自行构建镜像，可以使用项目内置的 Dockerfile。
部署步骤与本地启动流程保持一致：先准备配置文件，再启动服务。

```bash
# 复制配置文件（仅首次需要，可按需修改内容）
cp configs/config-example.yaml configs/config.yaml

# 构建镜像
docker build -t dotcanvas .

# 运行容器，映射端口并挂载配置与画布目录（更新镜像后数据仍保留）
docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  dotcanvas
```

容器启动后，同样通过 <http://localhost:8000/> 访问管理界面。
当你需要更新配置时，直接编辑宿主机 `configs/config.yaml` 并重启容器即可。画布持久化与镜像更新步骤见上一节。

## 本地部署

### 环境要求

- Python 3.12 及以上版本
- 推荐使用uv（或兼容 `pyproject.toml` 的其他依赖管理工具）
- cairo pango gdk-pixbuf libffi （用于执行svg2png转换）

### 安装

```bash
git clone https://github.com/LucasXingg/dotcanvas.git
cd dotcanvas

# 安装环境
uv venv
uv sync

# 创建配置文件
cp configs/config-example.yaml configs/config.yaml
```

### 构建前端资源

全新的 Web 界面基于 Vite + React 实现，默认监听在 `/ui` 路径下。**访问管理界面前**需要先安装前端依赖并生成静态资源：

```bash
cd frontend
npm install
npm run build
```

### 启动服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动服务器（需已完成上一节的前端构建，否则 /ui 会返回 503）
uvicorn server:app --reload
```
运行以上命令后，打开 <http://localhost:8000/> 访问管理界面（会重定向至 `/ui/daemon`）。

开发时可以使用 Vite 开发服务器获得热更新体验：

```bash
cd frontend
npm run dev
# 默认端口为 5173，可通过 http://localhost:5173/ui 访问
```

> 提示：仓库内的 `frontend/dist/index.html` 仅用于占位，实际运行请执行 `npm run build` 生成生产环境资源。Docker 镜像构建流程也会在镜像内执行上述命令。

# 自定义你的 Dot.

## 什么是画布与视图？

在DotCanvas中，每一幅画面都是一个独立的画布，而视图则是组成画布内容的元素（例如文字，图标，形状）。一个视图的所有参数全部由**视图构造函数**的返回结果决定，您可以自由的编写函数来动态的生成内容。

## 画布编辑
- 画布初始 ID 与画布名称保持一致，可修改。
- 对于视图构造函数，所有变量都需要包含在返回字典中，除非另行声明。
- 实时预览只会在保存修改后（点击`保存更改`按钮或使用快捷键`command + s`）更新。
- [视图文档](docs/views/index.md)
- 如果需要使用额外的包，可以使用`install_package()`方法来安装一个或多个包，例如`install_package("numpy", "pandas")`。包会装到 `user_site/`；优先选择提供 Python 3.12 预编译 wheel 的包。Docker 镜像已包含编译工具，必要时可从源码构建 C 扩展。
- 更完整的说明见文档目录：[界面说明](docs/ui-overview.md)、[视图脚本进阶](docs/view-scripts.md)（也可在 Web 控制台 **文档** 页浏览）。

## 配置管理
- API密钥：在 Dot. APP 中生成
- 设备
    - 设备名称：昵称。
    - 设备ID：在 Dot. APP 中查看（[查看方法](https://dot.mindreset.tech/docs/service/studio/api/get_device_id)）。
- 任务
    - 任务名称：随意。
    - 画布ID：要推送的画布的 画布ID。
    - Cron表达式：推送定时（[Cron 表达式生成器](https://www.uptimia.com/cron-expression-generator)）。
    - 参数：JSON 对象，渲染画布时传入视图构建函数（见 [视图脚本进阶](docs/view-scripts.md)）。
- 修改配置后需要在进程控制页面重启守护进程。

# 故障排除

## `install_package()` 构建失败（例如缺少 gcc / Failed building wheel）

常见原因：依赖只有源码包（sdist）、没有当前 Python 的预编译 wheel，需要本地编译；或包本身与 Python 3.12 不兼容。Docker 镜像已包含 `build-essential`；本地开发请自行安装编译器（如 `build-essential` / Xcode CLT）。

## 在 macOS 下出现与 Cairo 相关报错
尝试安装对应库
```bash
brew update
brew install cairo pango gdk-pixbuf libffi

# 配置环境变量
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:/opt/homebrew/opt/libffi/lib/pkgconfig"
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/cairo/lib:$DYLD_LIBRARY_PATH"

```

# 开发

请参考[开发指南](CONTRIBUTING.md)
