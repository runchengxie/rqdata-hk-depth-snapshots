# RQData 港股十档盘口快照工具

本项目用于探查、下载、校验、对账、聚合和打包 RQData 港股历史十档盘口快照数据。
数据来自 RQData `frequency="tick"` 的港股接口，包含十档买卖盘、快照时点行情和
累计成交字段。

## 适用范围

- 下载和维护历史十档盘口快照原始缓存。
- 校验原始快照质量，并与外部日频基准数据对账。
- 聚合日频研究特征和质量标记。
- 输出可交付的数据目录和本地归档分包。

数据范围不含逐笔成交明细、逐笔委托事件、订单优先级和严格订单簿重建所需事件流。
队列位置模拟和实盘交易执行需要其他数据源或系统。

## 五分钟离线试跑

安装开发依赖：

```bash
uv sync --group dev
```

使用内置 `FakeProvider` 下载一个交易日的样本并运行质量检查，无需 RQData 账号：

```bash
rqdata-hk-depth download \
  --symbols 00001.XHKG,00700.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider

rqdata-hk-depth health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --out-units artifacts/reports/tick_health_units.csv

rqdata-hk-depth aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet
```

运行完成后，`artifacts/cache/rqdata/hk_tick_depth/demo` 是原始快照缓存，
`artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet` 是日频研究产物。

## 典型工作流

```text
probe/download -> 原始快照缓存 -> health -> aggregate-daily -> reconcile-daily -> emit-asset -> package-assets
```

| 目标 | 入口 | 详细说明 |
| --- | --- | --- |
| 验证 provider 和字段 | `probe` | [RQData Provider](docs/providers-rqdata.md) |
| 批量下载或恢复下载 | `download --resume` | [工作流](docs/workflow.md) |
| 检查原始快照质量 | `health` | [质量门禁](docs/quality-gates.md) |
| 生成日频研究特征 | `aggregate-daily` | [十档盘口快照数据说明](docs/depth-snapshot-data.md) |
| 与日频基准对账 | `reconcile-daily` | [质量门禁](docs/quality-gates.md) |
| 输出和归档资产 | `emit-asset`、`package-assets` | [工作流](docs/workflow.md) |

## 原始数据布局

新下载默认以一个标的、一个交易日为操作单元：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

这个 `symbol-date` 布局用于 resume、健康检查、聚合和低内存扫描。历史
`raw_layout=batch` 数据继续支持读取；新 batch 下载已废弃，并会在 metadata 中记录提示。

parquet 压缩、metadata/audit 格式、`recompress-raw`、`compact-raw` 和交付目录格式见
[数据契约](docs/data-contracts.md)。冷归档与 release 分包流程见
[工作流](docs/workflow.md)。

## 接入真实 RQData

安装 live provider 依赖：

```bash
uv sync --extra rqdata --group dev
```

线上下载前先查询 quota：

```bash
rqdata-hk-depth quota --pretty
```

认证变量、本地 `.env` 读取方式、quota guard 和 live smoke 测试入口见
[RQData Provider](docs/providers-rqdata.md)。全周期任务应使用 `--resume`、
`--continue-on-error` 和 audit/metadata checkpoint 保留进度。

主命令为 `rqdata-hk-depth`。历史命令 `rqdata-tick` 保留为兼容入口；Python 包名、
既有数据目录和 schema ID 继续保持兼容。

## 开发检查

```bash
uv run pytest
uv run ruff check .
uv run pyright
```

仓库当前未配置 CI workflow 或 commit hook；本地代码修改不会自动触发这些命令。
当前静态检查范围和后续扩展计划见 [开发与维护](docs/development.md) 和
[维护债清单](docs/internal/maintenance-debt-inventory.md)。

## 文档地图

详细文档从 [docs/README.md](docs/README.md) 开始：

| 主题 | 文档 |
| --- | --- |
| 运行顺序、归档和发布操作 | [工作流](docs/workflow.md) |
| 命令与参数 | [CLI 参考](docs/cli.md) |
| 字段语义和研究边界 | [十档盘口快照数据说明](docs/depth-snapshot-data.md) |
| 数据布局、metadata 和 audit | [数据契约](docs/data-contracts.md) |
| 健康检查和对账 policy | [质量门禁](docs/quality-gates.md) |
| 认证、quota 和 live provider | [RQData Provider](docs/providers-rqdata.md) |
| 测试和维护约束 | [开发与维护](docs/development.md) |
| 带日期的执行事实 | [执行记录](docs/records/) |

## 当前覆盖状态

已确认覆盖范围、权限排除项和增量维护方式见
[当前覆盖状态](docs/records/2026-05-25-hk-depth-current-coverage.md)。
低频量化研究优先使用 `aggregate-daily` 产物，并对同日聚合特征做 lag 或严格
point-in-time 控制。原始快照 parquet 主要用于审计、质量门禁、样本校准和重新聚合。
