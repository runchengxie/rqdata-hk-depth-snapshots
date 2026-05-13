# 工作流

本项目的稳定业务链路：

```text
probe/download -> raw cache -> health -> aggregate-daily -> reconcile-daily -> emit-asset -> package-assets
```

## 1. Probe

`probe` 用于单标的单日探查，适合验证 provider 认证、字段可用性、权限范围和返回结构。

```bash
rqdata-tick probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

离线调试可加 `--fake-provider`。

## 2. Download

`download` 批量写出 raw tick parquet。新下载默认使用 `symbol-date` raw layout 和
`zstd` level 3 parquet 压缩：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

线上下载建议：

- 先运行 `rqdata-tick quota --pretty`。
- 使用 `--resume` 保留已完成单元。
- 使用 `--continue-on-error` 保留失败单元记录。
- 保留 metadata 和 audit 作为进度记录。
- 保留 raw tick；日常研究读取 `aggregate-daily` 输出，raw 用于审计、质量门禁和重算。
- 优先下载核心活跃池；长期 empty remote、退市或无研究用途标的不进入正式池。
- 对 live provider 分批运行，单批 estimated quota 控制在 `300MB-700MB` 附近。

示例：

```bash
rqdata-tick download \
  --symbols-file symbols_core.txt \
  --start-date 20250401 \
  --end-date 20260506 \
  --out artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --batch-size 5 \
  --retry-max-attempts 3 \
  --retry-backoff-seconds 2 \
  --quota-stop-ratio 0.95 \
  --quota-safety-multiplier 1.2 \
  --resume \
  --continue-on-error
```

## 3. Raw Cache

raw cache 是后续 health、aggregation、reconciliation 和 asset emission 的共同输入。
`symbol-date` 也是 resume、诊断和低内存扫描的最小操作单元。

每次下载会写：

```text
meta/download_<timestamp>.json
audit/download_<timestamp>_<run>.csv
```

已有 `snappy` raw cache 可用 `recompress-raw` 迁移到 `zstd` 新目录：

```bash
rqdata-tick recompress-raw \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506_zstd3
```

迁移后先对新目录跑 `health` 和 `aggregate-daily`，确认通过后再归档或替换旧目录。

完整字段见 [数据契约](data-contracts.md)。

## 4. Health

`health` 检查 raw tick 自身质量。常用输出包括 JSON summary 和 symbol-date 级 CSV。

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --out-json artifacts/reports/tick_health_core.json \
  --out-units artifacts/reports/tick_health_core_units.csv \
  --fail-on-severity warning
```

检查内容和 severity 解释见 [质量门禁](quality-gates.md)。

## 5. Aggregate Daily

`aggregate-daily` 从 raw tick 生成日频研究特征和质量标记。

```bash
rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/data.parquet \
  --meta-output artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/meta.json
```

低频研究默认消费日频聚合产物。使用同日聚合特征时，需要做 lag 或严格 point-in-time 控制。

## 6. Reconcile Daily

下载验收优先使用同报价口径的 raw daily reference：

```bash
rqdata-tick reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_raw/hk_tick_gate_20250401_20260506 \
  --out artifacts/reports/tick_daily_reconcile_raw_gate.json \
  --reference-policy raw-daily \
  --fail-on-severity warning
```

与研究清洗底座做覆盖检查时使用 `cross-clean`：

```bash
rqdata-tick reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_clean/example \
  --out artifacts/reports/tick_daily_reconcile_cross_clean.json \
  --reference-policy cross-clean \
  --fail-on-severity warning
```

policy 选择见 [质量门禁](quality-gates.md)。

## 7. Emit Asset

`emit-asset` 输出可发布或交付的 asset 目录。

```bash
rqdata-tick emit-asset \
  --kind raw \
  --source artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/assets/rqdata/hk/tick_depth/core_20250401_20260506
```

```bash
rqdata-tick emit-asset \
  --kind daily \
  --source artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/data.parquet \
  --output artifacts/assets/rqdata/hk/tick_depth_daily/core_20250401_20260506
```

asset 目录契约见 [数据契约](data-contracts.md)。

## 8. Package Assets

`package-assets` 把本地 raw cache、日频聚合、报告、配置和记录打成本地 archive
分包。默认推荐先保留本地 tarball；上传 GitHub Release 时再显式运行 `release-assets`。

```bash
rqdata-tick package-assets \
  --preset current-cache \
  --name hk_tick_depth_current \
  --as-of 20260509 \
  --tar-dir artifacts/releases/hk_tick_depth_current_20260509_tarballs \
  --overwrite
```

只归档正式 asset 目录时，显式传入 `--raw-source` 和 `--daily-source`：

```bash
rqdata-tick package-assets \
  --name hk_tick_depth_core \
  --as-of 20260509 \
  --raw-source artifacts/assets/rqdata/hk/tick_depth/core \
  --daily-source artifacts/assets/rqdata/hk/tick_depth_daily/core \
  --metadata-source docs/records \
  --config-source path/to/universe_config
```

冷存储可以把 raw cache 先无损重编码到更高等级 parquet zstd，再用 `.tar.zst` 打包：

```bash
rqdata-tick recompress-raw \
  --input artifacts/cache/rqdata/hk_tick_depth \
  --output artifacts/cache/rqdata/hk_tick_depth_cold_zstd12 \
  --compression zstd \
  --compression-level 12 \
  --resume \
  --continue-on-error

rqdata-tick package-assets \
  --name hk_tick_depth_cold \
  --as-of 20260509 \
  --tar-dir artifacts/releases/hk_tick_depth_cold_20260509_tarballs \
  --raw-source artifacts/cache/rqdata/hk_tick_depth_cold_zstd12 \
  --daily-source artifacts/cache/rqdata/hk_tick_depth_daily \
  --metadata-source docs/records \
  --report-source artifacts/reports \
  --config-source path/to/universe_config \
  --archive-format tar.zst \
  --archive-compression-level 12 \
  --raw-dedupe symbol-date \
  --overwrite
```

生成的 `manifest.yml` 记录每个 tarball 的 `sha256`、字节数、part 和样例 entry。
公开或跨账号分发 provider 数据前，先确认账号和数据供应商条款。

## 9. 研究和审计使用

raw tick parquet 主要用于审计、质量门禁、样本校准和重新聚合。研究模型通常使用
`aggregate-daily` 产物，并按研究口径筛选 `is_usable_for_research` 或相关质量标记。
