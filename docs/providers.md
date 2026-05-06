# Providers

## FakeProvider

`FakeProvider` 位于 `src/rqdata_tick_data/testing.py`。它生成确定性的离线 tick 数据，用于测试、CLI smoke 和文档示例。

离线命令使用：

```bash
rqdata-tick download ... --fake-provider
rqdata-tick quota --fake-provider --pretty
```

## RQData Provider

真实 provider 由 `RQDataClient` 封装。安装 live 依赖：

```bash
uv sync --extra rqdata --group dev
```

认证信息来自本地 `rqdatac` 配置或环境变量。线上下载前先运行：

```bash
rqdata-tick quota --pretty
```

真实 provider 下载默认使用 RQData 港股交易日历，只对交易日发请求。
