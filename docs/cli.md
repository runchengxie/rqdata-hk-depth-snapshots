# CLI 参考

入口命令：

```bash
rqdata-tick <command> [options]
```

查看帮助：

```bash
rqdata-tick download --help
rqdata-tick health --help
rqdata-tick reconcile-daily --help
```

## 命令总览

| 命令 | 用途 |
| --- | --- |
| `probe` | 单标的单日 provider 探查 |
| `download` | 批量下载 raw tick parquet |
| `health` | 检查 raw tick 自身质量 |
| `aggregate-daily` | 从 raw tick 聚合日频特征 |
| `emit-asset` | 输出 asset 目录 |
| `quota` | 查看 RQData quota |
| `reconcile-daily` | 对账 tick 聚合结果与外部日频 reference asset |

## `probe`

单标的单日探查，适合 live provider 接入前验证字段、权限和返回结构。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--symbol` | 必填 | 标的代码，支持 `700`、`00700.HK`、`00700.XHKG` |
| `--date` | 必填 | 交易日，格式 `YYYYMMDD` |
| `--fields` | 默认字段集 | 空格分隔字段列表 |
| `--adjust-type` | `none` | 传给 provider 的复权参数 |
| `--time-slice` | 空 | 传给 provider 的时间切片参数 |
| `--out` | `artifacts/cache/rqdata/hk_tick_depth/probe` | 输出目录 |
| `--fake-provider` | `false` | 使用离线 `FakeProvider` |

示例：

```bash
rqdata-tick probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

## `download`

批量下载 raw tick parquet。新下载默认使用 `symbol-date` raw layout。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--symbols` | 空 | 逗号分隔标的列表 |
| `--symbols-file` | 空 | TXT、CSV 或 Parquet 标的文件 |
| `--start-date` | 必填 | 起始日期，格式 `YYYYMMDD` |
| `--end-date` | 必填 | 结束日期，格式 `YYYYMMDD` |
| `--fields` | 默认字段集 | 空格分隔字段列表 |
| `--adjust-type` | `none` | 传给 provider 的复权参数 |
| `--time-slice` | 空 | 传给 provider 的时间切片参数 |
| `--out` | 必填 | raw cache 输出目录 |
| `--batch-size` | `5` | 每次 provider 请求的标的数量 |
| `--raw-layout` | `symbol-date` | `symbol-date` 或历史兼容 `batch` |
| `--calendar` | `provider` | `provider` 使用 RQData 港股交易日历；`calendar` 使用本地日历推断 |
| `--parquet-engine` | `pyarrow` | 写 parquet 的 engine |
| `--compression` | `snappy` | parquet 压缩算法 |
| `--compression-level` | 空 | parquet 压缩等级 |
| `--resume` | `true` | 跳过已通过本地校验的 symbol-date 单元 |
| `--no-resume` | `false` | 强制重新请求并覆盖本次命中的单元 |
| `--continue-on-error` | `false` | 单元失败后继续后续单元 |
| `--dry-run` | `false` | 只生成计划和 metadata，不请求 live provider |
| `--fake-provider` | `false` | 使用离线 `FakeProvider` |
| `--retry-max-attempts` | `1` | provider 请求最大尝试次数 |
| `--retry-backoff-seconds` | `0.0` | 重试初始等待秒数 |
| `--retry-max-backoff-seconds` | `60.0` | 重试最大等待秒数 |
| `--quota-guard` | `true` | 请求前检查 quota 预算 |
| `--no-quota-guard` | `false` | 关闭 quota guard |
| `--quota-stop-ratio` | `0.95` | quota 使用率达到该比例时停止新请求 |
| `--quota-safety-multiplier` | `1.2` | 估算请求量的安全倍数 |
| `--audit-output` | 空 | 指定 audit CSV 输出路径 |

离线示例：

```bash
rqdata-tick download \
  --symbols 00001.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider
```

live provider 下载建议使用 `--resume`、`--continue-on-error`、quota guard 和 audit 输出作为进度记录。

## `health`

按 parquet 分片扫描 raw cache，输出数据集级 summary 和 symbol-date 级诊断。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | raw cache 目录 |
| `--out-json` | 空 | 写出 JSON 报告 |
| `--out-units` | 空 | 写出 symbol-date 级 CSV 诊断 |
| `--fail-on-severity` | `error` | `none`、`info`、`warning`、`error`；达到阈值时返回非零退出码 |

示例：

```bash
rqdata-tick health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --out-json artifacts/reports/tick_health_demo.json \
  --out-units artifacts/reports/tick_health_demo_units.csv \
  --fail-on-severity warning
```

## `aggregate-daily`

从 raw tick 聚合日频研究特征和质量标记。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | raw cache 目录 |
| `--output` | 必填 | 日频 parquet 输出路径 |
| `--meta-output` | 空 | 聚合 metadata JSON 输出路径 |

示例：

```bash
rqdata-tick aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet \
  --meta-output artifacts/cache/rqdata/hk_tick_depth_daily/demo/meta.json
```

## `emit-asset`

输出 asset-compatible 目录。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--kind` | 必填 | `raw` 或 `daily` |
| `--source` | 必填 | raw cache 目录或 daily parquet |
| `--output` | 必填 | asset 输出目录 |

示例：

```bash
rqdata-tick emit-asset \
  --kind raw \
  --source artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/assets/rqdata/hk/tick_depth/demo
```

## `quota`

查询 provider quota。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--pretty` | `false` | 格式化输出 quota payload |
| `--fake-provider` | `false` | 使用离线 quota payload |

示例：

```bash
rqdata-tick quota --pretty
rqdata-tick quota --fake-provider --pretty
```

## `reconcile-daily`

将 raw tick 聚合出的 OHLCV 与外部日频 reference asset 对账。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--tick-input` | 必填 | raw cache 目录 |
| `--daily-asset-dir` | 必填 | 外部日频 reference asset 目录 |
| `--out` | 必填 | JSON 对账报告输出路径 |
| `--reference-policy` | `raw-daily` | `raw-daily` 或 `cross-clean` |
| `--fail-on-severity` | `error` | `none`、`info`、`warning`、`error`；达到阈值时返回非零退出码 |
| `--price-rtol` | `1e-4` | 价格相对容忍度 |
| `--price-atol` | `1e-4` | 价格绝对容忍度 |
| `--volume-rtol` | `1e-4` | 成交量相对容忍度 |
| `--volume-atol` | `1.0` | 成交量绝对容忍度 |
| `--turnover-rtol` | `1e-4` | 成交额相对容忍度 |
| `--turnover-atol` | `1.0` | 成交额绝对容忍度 |
| `--session-start` | `09:00` | 对账宽 session 起点 |
| `--session-end` | `16:30` | 对账宽 session 终点 |
| `--sample-limit` | `20` | 每类检查保留样例数量 |

示例：

```bash
rqdata-tick reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/demo \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_raw/demo \
  --out artifacts/reports/tick_daily_reconcile_demo.json \
  --reference-policy raw-daily \
  --fail-on-severity warning
```

`raw-daily` 用于同报价口径下载门禁。`cross-clean` 用于研究清洗底座覆盖检查，价格、成交量和成交额口径差异记录为 `info`。
