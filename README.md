# DotCanvas


DotCanvas 是一个轻量级的可视化Dot.编辑工具。

提供读取、创建、更新和渲染画布的接口，配套的 Web 界面允许你直接在浏览器中编辑画布元数据、视图构建函数代码，并实时预览生成的图片。

## 功能特性

- 在浏览器内完成所有操作，包括编辑画布，设定推送任务。
- 所有元素都可以通过python脚本自由动态的生成内容。
- 实时预览你的作品！

# 快速开始

## Docker 部署

我们已在 GitHub Container Registry 发布预构建镜像 `ghcr.io/lucasxingg/dotcanvas`，可以直接拉取并运行。

```bash
# 拉取镜像
docker pull ghcr.io/lucasxingg/dotcanvas:latest

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

在 DotCanvas 中：

- **自定义画布**保存为 `canvas/<画布ID>.py`（Web 界面里创建/编辑时会写回磁盘）。
- **服务配置与 API 令牌**保存在 `configs/`（如 `config.yaml`、`tokens.json`）。
- **运行时安装的 Python 包**（视图里调用 `install_package(...)`）落在 `user_site/`。

镜像只提供程序与内置 demo 画布；真正属于你的数据必须挂到宿主机，否则更新镜像后会消失。

### 推荐启动方式（挂载数据目录）

若你是从本仓库部署，可直接挂载仓库里的 `configs/` 与 `canvas/`：

```bash
# 首次准备配置（仅一次）
cp -n configs/config-example.yaml configs/config.yaml

docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

若你只有预构建镜像、本地还没有 `canvas/` 目录，可先从镜像拷出完整 `canvas`（含框架文件与 demo），再挂载：

```bash
mkdir -p configs canvas
docker create --name dotcanvas-seed ghcr.io/lucasxingg/dotcanvas:latest
docker cp dotcanvas-seed:/app/canvas/. ./canvas/
docker cp dotcanvas-seed:/app/configs/config-example.yaml ./configs/config-example.yaml
docker rm dotcanvas-seed
cp -n configs/config-example.yaml configs/config.yaml

docker run -d \
  --name dotcanvas \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

此后在 UI 中新建的画布都会写到宿主机的 `canvas/`，重启或换容器不会丢。

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

只要 `-v .../canvas:/app/canvas` 指向的是同一宿主机目录，你自定义的 `*.py` 画布文件会原样保留。

### 注意事项

- **必须挂载完整的 `canvas` 目录**，不能只挂某一个 `.py`。运行时依赖同目录下的 `_base_canvas.py`、`_canvas_template.py`、`views/`、`canvas_manager/` 等框架文件；挂载会覆盖镜像内的 `/app/canvas`。
- **你的画布**：宿主机 `canvas/` 下不以 `_` 开头的 `*.py`（例如 `hello_world.py`）。仓库自带的 demo（如 `countdown_canvas.py`、`calendar_canvas.py`）也属于此类；更新镜像时请保留它们与你自己新建的画布。请勿删除或覆盖这些文件。
- **框架文件也可能随版本更新**：若新镜像改了 `views/` 或 `_base_canvas.py` 等，而你挂载的是旧的宿主机 `canvas/`，容器会继续用旧框架。更新后如遇异常，可从新镜像把框架文件同步回来，同时**保留自己的画布文件**：

```bash
docker create --name dotcanvas-new ghcr.io/lucasxingg/dotcanvas:latest
# 备份当前挂载目录中的画布模块
mkdir -p canvas-backup && cp canvas/*.py canvas-backup/ 2>/dev/null || true
# 用新镜像中的 canvas 覆盖框架（含 views/ 等）
docker cp dotcanvas-new:/app/canvas/. ./canvas/
docker rm dotcanvas-new
# 把备份里自己的画布拷回去（跳过以下划线开头的框架/模板文件）
for f in canvas-backup/*.py; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  case "$base" in
    _*|__init__.py) ;; # 保留新镜像中的框架文件
    *) cp "$f" "canvas/$base" ;;
  esac
done
```

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
- 如果需要使用额外的包，可以使用`install_package()`方法来安装一个或多个包，例如`install_package("numpy", "pandas")`

## 配置管理
- API密钥：在 Dot. APP 中生成
- 设备
    - 设备名称：昵称。
    - 设备ID：在 Dot. APP 中查看（[查看方法](https://dot.mindreset.tech/docs/service/studio/api/get_device_id)）。
- 任务
    - 任务名称：随意。
    - 画布ID：要推送的画布的 画布ID。
    - Cron表达式：推送定时（[Cron 表达式生成器](https://www.uptimia.com/cron-expression-generator)）。
    - 参数：暂时没有用。
- 修改配置后需要在进程控制页面重启守护进程。

# 故障排除

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
