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
ghcr.io/zoranner/marker-api:<marker-version>-r<revision>
```

例如，基于 Marker `2.0.0` 的首个适配器发布标签为 `2.0.0-r1`。部署方应固定使用精确标签或 digest，不使用 `latest`。本仓库不提供 Compose 文件，也不包含任何业务应用配置。

本地构建：

```text
docker build --tag marker-api:2.0.0-r1 .
```

## 发布工作流

`Check Upstream Release` 每天在 `02:17 UTC` 查询 `datalab-to/marker` 的最新稳定 Release。GitHub 的计划工作流可能延迟执行。工作流根据同一 Marker 版本已有的 Release tag 和镜像输入文件，确定是否需要发布新的适配器修订。发布工作流会：

1. 使用 uv 将目标 Marker 版本写入临时锁文件后构建镜像。
2. 启动容器，检查 `/health`、空文件错误和真实 PDF 的 `/marker` 转换契约。
3. 在 `linux/amd64` 与 `linux/arm64` 原生 runner 构建镜像，合并为 `ghcr.io/zoranner/marker-api:<marker-version>-r<revision>`。
4. 创建 `v<marker-version>-r<revision>` Git tag 和 GitHub Release，并上传两个可用 `docker load` 导入的离线镜像归档。

同一 Marker 版本首次发布使用 `r1`。若 `src/`、`Dockerfile`、`pyproject.toml` 或 `uv.lock` 在最新同版本 Release 后发生变化，工作流自动递增修订号并发布 `r2`、`r3` 等后续版本；README、测试和工作流文案变更不会触发镜像重发。上游出现新的稳定大版本时，工作流从 `r1` 开始构建并执行真实 PDF 转换；构建或转换失败则不会推送镜像、创建 Git tag 或 GitHub Release。

### 手动发布

发布入口只有 `Check Upstream Release`，内部 `Release Marker API Image` 不提供手动触发，以避免绕过上游版本与修订号检查。

在 GitHub 仓库的 **Actions** 页面选择 `Check Upstream Release`，点击 **Run workflow**，分支选择 `master`。该工作流不接受版本输入，始终选择 Marker 最新稳定 Release。

工作流会检查同一 Marker 版本的最新 `v<marker-version>-r<revision>` tag，并比较该 tag 与当前提交的镜像输入文件。输入未变化时记录跳过原因；输入变化时递增修订号并构建发布。也可使用 GitHub CLI：

```text
gh workflow run "Check Upstream Release" --ref master
```

首次执行前，仓库或所属组织的 Actions 策略必须允许工作流令牌拥有 `contents: write` 和 `packages: write`，否则 Git tag、GitHub Release、离线镜像归档上传或 GHCR 推送会失败。

## 开发验证

安装测试依赖后执行：

```text
uv run --group dev pytest tests -q
uv run --no-sync python -m compileall src
```

`pyproject.toml` 和 `uv.lock` 是唯一依赖来源，不使用 requirements 文件。本机需要 Docker 才能验证完整镜像构建和容器 HTTP 契约。Marker 首次处理真实文档可能需要下载模型；这不由健康检查或空文件契约检查覆盖。
