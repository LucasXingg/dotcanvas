# 无浏览器模式

DotCanvas 可以在仅 API 模式下运行，此时会禁用内嵌的网页界面，仅暴露自动化相关端点。该模式适用于不需要管理界面的无头环境或云端部署。

## 启用无浏览器模式

在启动 FastAPI 应用或 Docker 容器之前，将环境变量 `DOTCANVAS_NO_BROWSER` 设置为真值。有效取值包括 `1`、`true`、`yes`、`on`（大小写不敏感）。

### 本地 uvicorn 示例

```bash
export DOTCANVAS_NO_BROWSER=1
uvicorn server:app --host 0.0.0.0 --port 8000
```

启用该环境变量后：

* 静态前端资源不会被挂载。
* `/`、`/ui` 与 `/ui/*` 路由会返回提示性的 JSON 响应或 `404`。
* 支持浏览器 UI 的所有管理端点（画布编辑、日志、守护进程控制、配置、令牌 CRUD）都会返回 `403 Forbidden`。
* OpenAPI 文档（`/docs`）与自动化端点仍然可用。
* 如果启动时不存在任何 API 令牌，服务器会自动创建一个，并在标准输出打印 `Generated API token for no-browser mode: <token>`。

### Docker 示例

```bash
docker run -d \
  -e DOTCANVAS_NO_BROWSER=1 \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

容器启动后会记录日志 `Running in no-browser mode; frontend routes are disabled.`，访问 `http://localhost:8000/` 将得到一条指向 OpenAPI 文档的简短 JSON 提示。

## 在无 UI 情况下管理令牌

由于无浏览器模式会禁用 `/tokens` 端点，请直接在服务器上创建或吊销 API 令牌。首次在没有令牌的情况下启动时，DotCanvas 会自动生成一个，并输出前述的 `Generated API token for no-browser mode: <token>` 日志——请在日志轮转前及时保存。

如果之后需要更多令牌，可在命令行运行应用使用的 `TokenStore` 工具：

```bash
uv run python - <<'PY'
from src.token_store import TokenStore

store = TokenStore()
token, record = store.create_token(name="automation")
print("Token:", token)
print("Metadata:", record)
PY
```

脚本会输出新令牌（请立即复制）及其元数据。要吊销令牌，可在类似的临时脚本中调用 `store.delete_token("token-id")`，或手动编辑 `configs/tokens.json`。

## 无头部署的安全注意事项

以无浏览器模式运行 DotCanvas 与其他 API-only 服务一样，需要保持安全警惕：

* **保护网络访问。** 通过防火墙或反向代理限制入站流量，并在对外提供 API 时使用 HTTPS。
* **保护配置卷。** `configs/` 目录包含 Dot API key 与令牌数据库，应以最小权限方式挂载。
* **及时轮换凭据。** 立即吊销不再使用的令牌，如怀疑泄露需更换 Dot API key。
* **监控日志。** 建议将 FastAPI 日志转发到云端日志服务，便于审计失败或异常请求。

## 恢复完整界面

清除该环境变量（或将其设为 `0`/`false`）并重启服务器，即可恢复基于浏览器的管理控制台。
