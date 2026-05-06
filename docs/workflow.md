# 工作流

本项目的稳定业务链路：

```text
probe/download -> raw cache -> health -> aggregate-daily -> reconcile-daily -> emit-asset
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

`download` 批量写出 raw tick parquet。新下载默认使用 `symbol-date` raw layout：

```text
parts/trade_date=YYYYMMDD/order_book_id=00001.XHKG.parquet
```

线上下载建议：

- 先运行 `rqdata-tick quota --pretty`。
- 使用 `--resume` 保留已完成单元。
- 使用 `--continue-on-error` 保留失败单元记录。
- 保留 metadata 和 audit 作为进度记录。
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

## 8. 研究和审计使用

raw tick parquet 主要用于审计、质量门禁、样本校准和重新聚合。研究模型通常使用
`aggregate-daily` 产物，并按研究口径筛选 `is_usable_for_research` 或相关质量标记。
