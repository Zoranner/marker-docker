# marker-docker

`marker-docker` 构建和发布通用的 `marker-service` 镜像。该镜像把 Marker 封装为稳定的 HTTP 服务，不绑定任何业务系统或 Docker Compose 配置。

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
ghcr.io/<owner>/marker-service:<marker-version>-r1
```

例如，基于 Marker `1.10.2` 的首个适配器发布标签为 `1.10.2-r1`。部署方应固定使用精确标签或 digest，不使用 `latest`。本仓库不提供 Compose 文件，也不包含任何业务应用配置。

本地构建：

```text
docker build --build-arg MARKER_PDF_VERSION=1.10.2 --tag marker-service:1.10.2-r1 .
```

## 发布工作流

`Check Marker upstream` 每天查询 `datalab-to/marker` 的稳定 Release，并选取最新受支持主版本。只有尚未发布的版本才会调用发布工作流。发布工作流会：

1. 构建对应版本的镜像。
2. 启动容器，检查 `/health` 与空文件的 `/marker` 契约。
3. 推送 `ghcr.io/<owner>/marker-service:<marker-version>-r1`。
4. 创建同名 Git tag 和 GitHub Release。

主版本升级不会自动发布，因为 Marker 的 Python API 和解析行为可能存在不兼容变更。此类升级需要先修改适配器并补充实际文档的契约验收，再将工作流中的受支持主版本改为新版本。

手动触发两个工作流时，输入不带 `v` 前缀的 Marker 发布版本，例如 `1.10.2`。

## 开发验证

安装测试依赖后执行：

```text
python -m pytest tests -q
python -m compileall marker_api
```

本机需要 Docker 才能验证完整镜像构建和容器 HTTP 契约。Marker 首次处理真实文档可能需要下载模型；这不由健康检查或空文件契约检查覆盖。
