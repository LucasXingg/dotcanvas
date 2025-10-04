# DotCanvas


DotCanvas 是一个轻量级的可视化Dot编辑工具.
提供读取、创建、更新和渲染画布的接口，配套的 Web 界面允许你直接在浏览器中
编辑画布元数据、视图构建函数代码，并实时预览生成的图片。

## 功能特性

- 在浏览器内完成所有操作，包括编辑画布，设定推送任务。
- 所有元素都可以通过python脚本自由动态的生成内容。
- 实时预览你的作品！

# 快速开始

## 环境要求

- Python 3.12 及以上版本
- 推荐使用uv（或兼容 `pyproject.toml` 的其他依赖管理工具）
- cairo pango gdk-pixbuf libffi （用于执行svg2png转换）

## 安装

```bash
git clone https://github.com/LucasXingg/dotcanvas.git
cd dotcanvas

# 安装环境
uv venv
uv sync

# 创建配置文件
cp configs/config-example.yaml configs/config.yaml
```

## 启动服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动服务器
uvicorn server:app --reload
```
运行以上命令后，打开 <http://localhost:8000/> 访问管理界面。

## Docker 部署

如果你希望在容器中运行 DotCanvas，可以使用项目内置的 Dockerfile 构建镜像。
部署步骤与本地启动流程保持一致：先准备配置文件，再启动服务。

```bash
# 复制配置文件（仅首次需要，可按需修改内容）
cp configs/config-example.yaml configs/config.yaml

# 构建镜像
docker build -t dotcanvas .

# 运行容器，映射端口并挂载配置目录
docker run \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  dotcanvas
```

容器启动后，同样通过 <http://localhost:8000/> 访问管理界面。
当你需要更新配置时，直接编辑宿主机 `configs/config.yaml` 并重启容器即可。

# 自定义你的 Dot.

## 画布编辑
- 画布初始 ID 与画布名称保持一致，可修改。
- 对于视图构造函数，所有变量都需要包含在返回字典中，除非另行声明。
- 实时预览只会在保存修改后（点击`保存更改`按钮或使用快捷键`command + s`）更新。
- [视图文档](docs/views/index.md)

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
