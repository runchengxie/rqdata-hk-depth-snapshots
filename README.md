# RQData 港股十档盘口快照工具

本项目用于探查、下载、校验、对账、聚合和打包 RQData 港股历史十档盘口快照数据。
数据来自 RQData `frequency="tick"` 的港股接口，包含十档买卖盘、快照时点行情和
累计成交字段。

支持范围：

- 下载和维护历史十档盘口快照原始缓存。
- 校验原始快照数据质量。
- 聚合日频研究特征。
- 对账外部日频基准数据。
- 输出可发布或交付的数据目录和本地归档分包。

数据范围不含逐笔成交明细、逐笔委托事件、订单优先级和严格订单簿重建所需事件流。
队列位置模拟和实盘交易执行需要其他数据源或系统。

核心流程：

```text
probe/download -> 原始快照缓存 -> health -> aggregate-daily -> reconcile-daily -> emit-asset -> package-assets
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
uv run pyright
```

真实 RQData provider 依赖：

```bash
uv sync --extra rqdata --group dev
```

离线测试和文档 smoke 使用 `FakeProvider`，不需要 RQData 账号。

## 离线 Smoke

```bash
rqdata-hk-depth download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider
```

```bash
rqdata-hk-depth health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --out-units artifacts/reports/tick_health_units.csv
```

```bash
rqdata-hk-depth aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet
```

## 真实 RQData

安装 live 依赖后，使用本地 `rqdatac` 配置，或在本机 shell / `.env` 中设置
`RQDATA_USERNAME`、兼容变量 `RQDATA_USER`、`RQDATA_PASSWORD` 和 `RQDATA_URI`。
`RQDataClient` 会通过 `python-dotenv` 自动读取本地 `.env`。

线上下载前先检查 quota：

```bash
rqdata-hk-depth quota --pretty
```

新下载默认原始快照布局是 `symbol-date`：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

新下载默认使用 `zstd` level 3 写 parquet，在保留原始快照精度的前提下降低磁盘占用。
需要更快写入时可显式传 `--compression snappy`。历史 `raw_layout=batch` 数据仍可读取；
新 batch 下载已废弃，并会写入 metadata。

已有原始快照缓存可用 `rqdata-hk-depth recompress-raw --input OLD --output NEW` 无损迁移到新的
parquet codec。迁移命令写新目录和 audit，不修改输入目录。

评估冷归档压缩率时，可用 `compact-raw --grouping symbol-quarter --row-group-days 60`
从 `symbol-date` cache 派生按标的合并的 compact parquet，并通过 metadata 比较输入
和输出字节数。命令默认拒绝重复日期-标的输入；对于包含 retry/refetch 重叠副本的
归档缓存，可显式用 `--duplicate-policy prefer-nonempty-identical`，仅在非空副本
字节一致时保留非空版本，否则失败。默认原始快照缓存继续服务 resume、health 和聚合流程。

冷存储备份可先用 `recompress-raw --compression zstd --compression-level 12` 生成高压缩
原始快照副本，再用 `package-assets --archive-format tar --raw-dedupe symbol-date --progress`
打包该副本。该去重模式只折叠可安全判定的重复分片，遇到不同内容的非空副本会失败。
使用 `.tar` 可避免对已压缩 parquet 再执行耗时的外层压缩。
`tar.gz` 和 `tar.zst` 可用于显式压缩 archive 容器，其压缩等级只作用于外层 archive。
Release 上传前保持单个 archive 小于 2GiB；默认分包上限为 `1900000000` bytes。

主命令为 `rqdata-hk-depth`。历史命令 `rqdata-tick` 保留为兼容入口；Python 包名、
既有数据目录和 schema ID 继续保持兼容。

## 文档

详细文档从 [docs/README.md](docs/README.md) 开始：

- [CLI 参考](docs/cli.md)
- [工作流](docs/workflow.md)
- [十档盘口快照数据说明](docs/depth-snapshot-data.md)
- [数据契约](docs/data-contracts.md)
- [质量门禁](docs/quality-gates.md)
- [RQData Provider](docs/providers-rqdata.md)
- [开发与维护](docs/development.md)
- [术语表](docs/terminology.md)
- [执行记录](docs/records/)
- [RQData API 使用摘要与快照](docs/vendor/)

当前已确认覆盖范围、权限排除项和后续增量维护方式见
[当前覆盖状态](docs/records/2026-05-25-hk-depth-current-coverage.md)。
低频量化研究建议使用 `aggregate-daily` 产物，并对同日聚合特征做 lag 或严格
point-in-time 控制。原始快照 parquet 主要用于审计、质量门禁、样本校准和重新聚合。
