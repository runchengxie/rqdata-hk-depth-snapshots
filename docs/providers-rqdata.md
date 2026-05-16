# RQData Provider

本项目有两个 provider 路径：离线 `FakeProvider` 和真实 `RQDataClient`。

## FakeProvider

`FakeProvider` 位于 `src/rqdata_tick_data/testing.py`。它生成确定性的离线 tick 数据，用于测试、CLI smoke 和文档示例。

离线命令：

```bash
rqdata-tick download ... --fake-provider
rqdata-tick quota --fake-provider --pretty
```

`FakeProvider` 不需要 RQData 账号。

## RQDataClient

真实 provider 由 `RQDataClient` 封装。安装 live 依赖：

```bash
uv sync --extra rqdata --group dev
```

项目直接使用的 RQData 能力：

- 港股历史 tick-depth 快照读取。
- 港股交易日历。
- quota 查询。
- 港股合约和字段语义核对。

项目实际使用的 provider 语义见 [RQData 港股 API 使用摘要](vendor/rqdata-hk-used-apis.md)。
完整外部快照只作为离线查询材料。

## 认证

`RQDataClient` 会先调用 `python-dotenv` 的 `load_dotenv()`，再读取环境变量。可以使用本地
`rqdatac` 配置，也可以把变量放在本机 shell 环境或未提交版本控制的 `.env` 中。

支持变量：

| 变量 | 用途 |
| --- | --- |
| `RQDATA_USERNAME` | RQData 用户名 |
| `RQDATA_USER` | 兼容变量 |
| `RQDATA_PASSWORD` | RQData 密码 |
| `RQDATA_URI` | RQData 服务地址 |

如果 `RQDATA_URI` 为空，初始化会使用 `rqdatac` 默认地址或本地配置。

## Quota

线上下载前先查看 quota：

```bash
rqdata-tick quota --pretty
```

`download` 默认开启 quota guard：

- `--quota-guard`
- `--quota-stop-ratio 0.95`
- `--quota-safety-multiplier 1.2`

需要探索下载计划时可使用 `--dry-run`。关闭 guard 需要显式传入 `--no-quota-guard`。

## 交易日历

`download --calendar provider` 默认使用 RQData 港股交易日历，只对交易日发请求。
`--calendar calendar` 使用本地日期推断，主要用于离线或兼容场景。

## Live Smoke

live smoke 需要显式开启：

```bash
uv sync --extra rqdata --group dev
RQDATA_TICK_LIVE_TESTS=1 uv run pytest -m rqdata_live
```

live smoke 只做最小 quota 或 provider 检查，不启动大规模下载。
