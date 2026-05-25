# 工作流

本项目的稳定业务链路：

```text
probe/download -> 原始快照缓存 -> health -> aggregate-daily -> reconcile-daily -> emit-asset -> package-assets
```

## 1. Probe

`probe` 用于单标的单日探查，适合验证 provider 认证、字段可用性、权限范围和返回结构。

```bash
rqdata-hk-depth probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

离线调试可加 `--fake-provider`。

## 2. Download

`download` 批量写出原始快照 parquet。新下载默认使用 `symbol-date` 原始快照布局和
`zstd` level 3 parquet 压缩：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

线上下载建议：

- 先运行 `rqdata-hk-depth quota --pretty`。
- 使用 `--resume` 保留已完成单元。
- 使用 `--continue-on-error` 保留失败单元记录。
- 保留 metadata 和 audit 作为进度记录。
- 保留原始快照；日常研究读取 `aggregate-daily` 输出，原始快照用于审计、质量门禁和重算。
- 优先下载核心活跃池；长期 empty remote、退市或无研究用途标的不进入正式池。
- 对 live provider 分批运行，单批 estimated quota 控制在 `300MB-700MB` 附近。

示例：

```bash
rqdata-hk-depth download \
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

## 3. 原始快照缓存

原始快照缓存是后续 health、聚合、对账和交付目录输出的共同输入。
`symbol-date` 也是 resume、诊断和低内存扫描的最小操作单元。

每次下载会写：

```text
meta/download_<timestamp>.json
audit/download_<timestamp>_<run>.csv
```

已有 `snappy` 原始快照缓存可用 `recompress-raw` 迁移到 `zstd` 新目录：

```bash
rqdata-hk-depth recompress-raw \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506_zstd3
```

迁移后先对新目录跑 `health` 和 `aggregate-daily`，确认通过后再归档或替换旧目录。

冷归档压缩实验可从 zstd12 cache 派生 compact 输出。下面的无重叠样本季度方案
每次最多在内存中合并同一标的 60 个交易日 part：

```bash
rqdata-hk-depth compact-raw \
  --input artifacts/cache/rqdata/hk_tick_depth_cold_zstd12/core400_rank341_380_20250401_20260515 \
  --output artifacts/cache/rqdata/hk_tick_depth_compact_bench/core400_q_zstd12_rg60 \
  --grouping symbol-quarter \
  --compression zstd \
  --compression-level 12 \
  --row-group-days 60 \
  --progress
```

用 `--grouping symbol-year --row-group-days 1` 可形成仅合并文件的对照输出。
compact metadata 中的 `source_bytes`、`output_bytes` 和 `compression_ratio`
用于判断后续是否值得全量派生冷归档。

完整 cold cache 若包含 retry/refetch 重复单元，无需先复制一份新目录。可显式
启用保守去重策略：仅保留相同非空副本或用非空 refetch 替代空 retry，遇到不同的
非空副本立即失败：

```bash
rqdata-hk-depth compact-raw \
  --input artifacts/cache/rqdata/hk_tick_depth_cold_zstd12 \
  --output artifacts/cache/rqdata/hk_tick_depth_compact_zstd12_q_rg60 \
  --grouping symbol-quarter \
  --compression zstd \
  --compression-level 12 \
  --row-group-days 60 \
  --duplicate-policy prefer-nonempty-identical \
  --progress
```

完整字段见 [数据契约](data-contracts.md)。

## 4. Health

`health` 检查原始快照自身质量。JSON summary 保留异常样例和汇总统计；完整
symbol-date 明细通过 CSV 随扫描写出。全量扫描使用 CSV，避免 JSON 携带完整诊断列表。

```bash
rqdata-hk-depth health \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --out-json artifacts/reports/tick_health_core.json \
  --out-units artifacts/reports/tick_health_core_units.csv \
  --unit-sample-limit 20 \
  --fail-on-severity warning
```

检查内容和 severity 解释见 [质量门禁](quality-gates.md)。

## 5. Aggregate Daily

`aggregate-daily` 从原始快照生成日频研究特征和质量标记。

```bash
rqdata-hk-depth aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/data.parquet \
  --meta-output artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/meta.json
```

低频研究默认消费日频聚合产物。使用同日聚合特征时，需要做 lag 或严格 point-in-time 控制。

## 6. Reconcile Daily

下载验收优先使用同报价口径的日频基准数据：

```bash
rqdata-hk-depth reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_raw/hk_tick_gate_20250401_20260506 \
  --out artifacts/reports/tick_daily_reconcile_raw_gate.json \
  --reference-policy raw-daily \
  --fail-on-severity warning
```

与研究清洗底座做覆盖检查时使用 `cross-clean`：

```bash
rqdata-hk-depth reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_clean/example \
  --out artifacts/reports/tick_daily_reconcile_cross_clean.json \
  --reference-policy cross-clean \
  --fail-on-severity warning
```

policy 选择见 [质量门禁](quality-gates.md)。

## 7. 输出交付目录

`emit-asset` 输出可发布或交付的数据目录。

```bash
rqdata-hk-depth emit-asset \
  --kind raw \
  --source artifacts/cache/rqdata/hk_tick_depth/core_20250401_20260506 \
  --output artifacts/assets/rqdata/hk/tick_depth/core_20250401_20260506
```

```bash
rqdata-hk-depth emit-asset \
  --kind daily \
  --source artifacts/cache/rqdata/hk_tick_depth_daily/core_20250401_20260506/data.parquet \
  --output artifacts/assets/rqdata/hk/tick_depth_daily/core_20250401_20260506
```

交付目录契约见 [数据契约](data-contracts.md)。

## 8. Package Assets

`package-assets` 把本地原始快照缓存、日频聚合、报告、配置和记录打成本地 archive
分包。默认使用 `.tar` 避免对已压缩 parquet 再执行耗时的外层压缩；上传 GitHub
Release 时再显式运行 `release-assets`。`--preset current-cache` 只自动附带执行
记录索引和当前覆盖摘要，完整历史流水需要显式传入 `--metadata-source docs/records`。

```bash
rqdata-hk-depth package-assets \
  --preset current-cache \
  --name hk_tick_depth_current \
  --as-of 20260509 \
  --tar-dir artifacts/releases/hk_tick_depth_current_20260509_tarballs \
  --archive-format tar \
  --overwrite
```

只归档正式交付目录时，显式传入 `--raw-source` 和 `--daily-source`：

```bash
rqdata-hk-depth package-assets \
  --name hk_tick_depth_core \
  --as-of 20260509 \
  --raw-source artifacts/assets/rqdata/hk/tick_depth/core \
  --daily-source artifacts/assets/rqdata/hk/tick_depth_daily/core \
  --metadata-source docs/records/2026-05-25-hk-depth-current-coverage.md \
  --config-source path/to/universe_config
```

冷存储可以把原始快照缓存先无损重编码到更高等级 parquet zstd，再按需要生成
compact 派生物或用 `.tar` 分包：

```bash
rqdata-hk-depth recompress-raw \
  --input artifacts/cache/rqdata/hk_tick_depth \
  --output artifacts/cache/rqdata/hk_tick_depth_cold_zstd12 \
  --compression zstd \
  --compression-level 12 \
  --resume \
  --continue-on-error \
  --progress

rqdata-hk-depth package-assets \
  --name hk_tick_depth_cold \
  --as-of 20260509 \
  --tar-dir artifacts/releases/hk_tick_depth_cold_20260509_tarballs \
  --raw-source artifacts/cache/rqdata/hk_tick_depth_cold_zstd12 \
  --daily-source artifacts/cache/rqdata/hk_tick_depth_daily \
  --metadata-source docs/records/README.md \
  --metadata-source docs/records/2026-05-25-hk-depth-current-coverage.md \
  --report-source artifacts/reports \
  --config-source path/to/universe_config \
  --max-tar-bytes 1900000000 \
  --archive-format tar \
  --raw-dedupe symbol-date \
  --progress \
  --overwrite
```

若交付端要求压缩 archive 容器，可显式选择 `.tar.zst`；其压缩等级作用于外层
archive，包含原始快照 parquet 的运行会输出相应提示。`--raw-dedupe symbol-date`
只折叠可安全判定的重复分片；不同内容的非空副本会中止打包。

生成的 `manifest.yml` 记录每个 tarball 的 `sha256`、字节数、part 和样例 entry。
公开或跨账号分发 provider 数据前，先确认账号和数据供应商条款。

## 9. 研究和审计使用

原始快照 parquet 主要用于审计、质量门禁、样本校准和重新聚合。研究模型通常使用
`aggregate-daily` 产物，并按研究口径筛选 `is_usable_for_research` 或相关质量标记。
