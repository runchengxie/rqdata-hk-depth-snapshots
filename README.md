# RQData 港股十档 Tick 数据工具

本项目用于探查、下载、校验、对账、聚合和输出 RQData 港股历史 tick-depth 快照数据。

支持范围：

- 处理历史 tick-depth 快照。
- 校验 raw tick 数据质量。
- 聚合日频研究特征。
- 对账外部日频 reference asset。
- 输出可发布或交付的 asset 目录和本地备份分包。

订单簿重建、逐笔订单事件、逐笔成交明细、队列位置模拟和实盘交易执行需要其他数据源或系统。

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

安装 live 依赖后，使用本地 `rqdatac` 配置，或在本机 shell / `.env` 中设置
`RQDATA_USERNAME`、兼容变量 `RQDATA_USER`、`RQDATA_PASSWORD` 和 `RQDATA_URI`。
`RQDataClient` 会通过 `python-dotenv` 自动读取本地 `.env`。

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

评估冷归档压缩率时，可用 `compact-raw --grouping symbol-quarter --row-group-days 60`
从 `symbol-date` cache 派生按标的合并的 compact parquet，并通过 metadata 比较输入
和输出字节数。命令默认拒绝重复日期-标的输入；对于包含 retry/refetch 重叠副本的
归档 cache，可显式用 `--duplicate-policy prefer-nonempty-identical`，仅在非空副本
内容一致时保留非空版本，否则失败。默认 raw cache 继续服务 resume、health 和聚合流程。

冷存储备份可先用 `recompress-raw --compression zstd --compression-level 12` 生成高压缩
raw 副本，再用 `package-assets --archive-format tar --raw-dedupe symbol-date --progress`
打包该副本，减少重复 raw part，并避免对已压缩 parquet 再执行耗时的外层压缩。
`tar.gz` 和 `tar.zst` 可用于显式压缩 archive 容器，其压缩等级只作用于外层 archive。
Release 上传前保持单个 archive 小于 2GiB；默认分包上限为 `1900000000` bytes。

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
point-in-time 控制。raw tick parquet 是带累计成交字段的十档盘口快照，主要用于审计、
质量门禁、样本校准和重新聚合。逐笔订单、逐笔成交和订单簿重建需要其他数据源。
