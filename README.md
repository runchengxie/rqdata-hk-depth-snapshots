# RQData 港股十档 Tick 数据工具

本项目用于探查、下载、校验、对账、聚合和输出 RQData 港股历史 tick-depth 快照数据。

项目边界：

- 处理历史 tick-depth 快照。
- 排除订单簿重建。
- 排除逐笔订单事件处理。
- 排除队列位置模拟。
- 排除实盘交易执行。

核心流程：

```text
probe/download -> raw cache -> health -> aggregate-daily -> reconcile-daily -> emit-asset -> package-assets
```

## 安装

离线开发依赖：

```bash
uv sync --group dev
```

离线测试和 lint：

```bash
uv run pytest
uv run ruff check .
```

真实 RQData provider 依赖：

```bash
uv sync --extra rqdata --group dev
```

离线测试和文档 smoke 使用 `FakeProvider`，不需要 RQData 账号。

## 离线 Smoke

```bash
rqdata-tick download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider
```

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --out-units artifacts/reports/tick_health_units.csv
```

```bash
rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet
```

## 真实 RQData

安装 live 依赖后，使用本地 `rqdatac` 配置，或复制环境变量样例：

```bash
cp .env.example .env
```

`.env` 可配置 `RQDATA_USERNAME`、兼容变量 `RQDATA_USER`、`RQDATA_PASSWORD` 和
`RQDATA_URI`。`RQDataClient` 会通过 `python-dotenv` 自动读取。

线上下载前先检查 quota：

```bash
rqdata-tick quota --pretty
```

新下载默认 raw layout 是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

新下载默认使用 `zstd` level 3 写 parquet，在保留 raw tick 精度的前提下降低磁盘占用。
需要更快写入时可显式传 `--compression snappy`。历史 `raw_layout=batch` 数据仍可读取；
新 batch 下载已废弃，并会写入 metadata。

已有 raw cache 可用 `rqdata-tick recompress-raw --input OLD --output NEW` 无损迁移到新的
parquet codec。迁移命令写新目录和 audit，不修改输入目录。

## 文档

详细文档从 [docs/README.md](docs/README.md) 开始：

- [CLI 参考](docs/cli.md)
- [工作流](docs/workflow.md)
- [Tick-depth 数据说明](docs/tick-depth-data.md)
- [数据契约](docs/data-contracts.md)
- [质量门禁](docs/quality-gates.md)
- [RQData Provider](docs/providers-rqdata.md)
- [开发与维护](docs/development.md)
- [术语表](docs/terminology.md)
- [执行记录](docs/records/)
- [RQData API 使用摘要与快照](docs/vendor/)

低频量化研究建议使用 `aggregate-daily` 产物，并对同日聚合特征做 lag 或严格
point-in-time 控制。raw tick parquet 是带累计成交字段的十档盘口快照，不是逐笔订单
或逐笔成交数据；主要用于审计、质量门禁、样本校准和重新聚合。
