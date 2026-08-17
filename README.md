# marker-docker

`marker-docker` 构建和发布通用的 `marker-api` 镜像。该镜像把 Marker 封装为稳定的 HTTP 服务，不绑定任何业务系统或 Docker Compose 配置。

## HTTP 契约

服务监听 `8000`，提供两个接口：

| 方法 | 路径 | 请求 | 成功响应 |
| --- | --- | --- | --- |
| `GET` | `/health` | 无 | `{"status":"ok"}` |
| `POST` | `/marker` | `multipart/form-data`，文件字段为 `file` | 含非空 `markdown` 字符串的 JSON |

`POST /marker` 会保留 Marker 输出的 JSON 结构，并在顶层加入 `markdown`。空文件返回 `400`；转换异常返回不含内部细节的 `500`。

## 镜像

工作流发布精确版本标签：

```text
ghcr.io/zoranner/marker-api:<marker-version>-r1
```

例如，基于 Marker `1.10.2` 的首个适配器发布标签为 `1.10.2-r1`。部署方应固定使用精确标签或 digest，不使用 `latest`。本仓库不提供 Compose 文件，也不包含任何业务应用配置。

本地构建：

```text
docker build --tag marker-api:1.10.2-r1 .
```

## 发布工作流

`Check Marker upstream` 每天在 `02:17 UTC` 查询 `datalab-to/marker` 的稳定 Release，并选取最新受支持主版本。GitHub 的计划工作流可能延迟执行；只有尚未发布的版本才会调用内部发布工作流。发布工作流会：

1. 使用 uv 将目标 Marker 版本写入临时锁文件后构建镜像。
2. 启动容器，检查 `/health` 与空文件的 `/marker` 契约。
3. 推送 `ghcr.io/zoranner/marker-api:<marker-version>-r1`。
4. 创建同名 Git tag 和 GitHub Release。

主版本升级不会自动发布，因为 Marker 的 Python API 和解析行为可能存在不兼容变更。此类升级需要先修改适配器并补充实际文档的契约验收，再将工作流中的受支持主版本改为新版本。

### 手动发布

发布入口只有 `Check Marker upstream`，内部 `Publish marker API image` 不提供手动触发，以避免绕过上游版本与重复发布检查。

在 GitHub 仓库的 **Actions** 页面选择 `Check Marker upstream`，点击 **Run workflow**，分支选择 `master`：

- `marker_version` 留空：选择最新受支持的稳定 `1.x` Release。
- `marker_version` 填入精确版本：例如 `1.10.2`，不带 `v` 前缀。

工作流会检查 Git tag `v<marker-version>-r1`。该 tag 已存在时，仅记录跳过原因；不存在时才构建并发布镜像。也可使用 GitHub CLI：

```text
gh workflow run "Check Marker upstream" --ref master
gh workflow run "Check Marker upstream" --ref master -f marker_version=1.10.2
```

首次执行前，仓库或所属组织的 Actions 策略必须允许工作流令牌拥有 `contents: write` 和 `packages: write`，否则 Git tag、GitHub Release 或 GHCR 推送会失败。

## 开发验证

安装测试依赖后执行：

```text
uv run --group dev pytest tests -q
uv run --no-sync python -m compileall src
```

`pyproject.toml` 和 `uv.lock` 是唯一依赖来源，不使用 requirements 文件。本机需要 Docker 才能验证完整镜像构建和容器 HTTP 契约。Marker 首次处理真实文档可能需要下载模型；这不由健康检查或空文件契约检查覆盖。
