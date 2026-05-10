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
rqdata-tick package-assets --help
```

## 命令总览

| 命令 | 用途 |
| --- | --- |
| `probe` | 单标的单日 provider 探查 |
| `download` | 批量下载 raw tick parquet |
| `health` | 检查 raw tick 自身质量 |
| `aggregate-daily` | 从 raw tick 聚合日频特征 |
| `emit-asset` | 输出 asset 目录 |
| `package-assets` | 生成本地备份 tarball |
| `release-assets` | 上传备份 tarball 到 GitHub Release |
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

批量下载 raw tick parquet。新下载默认使用 `symbol-date` raw layout，并以 `zstd`
level 3 写 parquet。

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
| `--compression` | `zstd` | parquet 压缩算法 |
| `--compression-level` | `3` | parquet 压缩等级；显式使用 `snappy` 时保持为空 |
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

## `recompress-raw`

将 raw parquet cache 无损重编码到新目录，默认写 `zstd` level 3。该命令不修改输入目录，
输出目录会保留原始 `parts/...` 相对路径，并写出 migration metadata 和 part 级 audit CSV。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | 源 raw cache 目录 |
| `--output` | 必填 | 新 raw cache 输出目录 |
| `--compression` | `zstd` | 目标 parquet 压缩算法 |
| `--compression-level` | `3` | 目标 parquet 压缩等级 |
| `--min-rewrite-bytes` | `0` | 小于该字节数的分片直接复制；`0` 表示全部重写 |
| `--resume` | `true` | 跳过已匹配 schema、行数和目标 codec 的输出分片 |
| `--no-resume` | `false` | 强制重写或复制所有分片 |
| `--continue-on-error` | `false` | 单分片失败后继续处理后续分片 |
| `--meta-output` | 空 | migration metadata JSON 输出路径 |
| `--out-units` | 空 | part 级 audit CSV 输出路径 |

示例：

```bash
rqdata-tick recompress-raw \
  --input artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20260506_zstd3 \
  --compression zstd \
  --compression-level 3
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

## `package-assets`

将本地 tick-depth 数据、聚合结果、报告、配置和记录打成可搬运的 `.tar.gz` 分包。
单个 tarball 默认控制在 GitHub Release asset 限制以下。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--preset` | `explicit` | `explicit` 使用显式路径；`current-cache` 选择当前默认 cache、reports、universe configs 和 dated records |
| `--name` | `tick-depth` | 分发名称，用于 manifest 和 tarball 文件名 |
| `--as-of` | 当日 UTC 日期 | 资产日期标签，格式建议 `YYYYMMDD` |
| `--tar-dir` | `artifacts/releases/<name>_<as_of>_tarballs` | tarball 输出目录 |
| `--overwrite` | `false` | 覆盖已有非空输出目录 |
| `--dry-run` | `false` | 只生成选择计划，不写 tarball |
| `--part` | 全部 part | 选择 `raw`、`daily`、`metadata`、`reports`、`configs`；可重复 |
| `--raw-source` | 空 | 额外 raw cache 或 raw asset 路径；可重复 |
| `--daily-source` | 空 | 额外 daily aggregate 或 daily asset 路径；可重复 |
| `--metadata-source` | 空 | 额外 metadata 或记录路径；可重复 |
| `--report-source` | 空 | 额外 report 路径；可重复 |
| `--config-source` | 空 | 额外 config 或 universe 路径；可重复 |
| `--max-tar-bytes` | `1900000000` | 单个 tarball 目标上限；超过上限时会按文件切分 |

示例：

```bash
rqdata-tick package-assets \
  --preset current-cache \
  --name hk_tick_depth_current \
  --as-of 20260509 \
  --tar-dir artifacts/releases/hk_tick_depth_current_20260509_tarballs \
  --overwrite
```

显式选择已 emit 的 raw/daily asset：

```bash
rqdata-tick package-assets \
  --name hk_tick_depth_core \
  --as-of 20260509 \
  --raw-source artifacts/assets/rqdata/hk/tick_depth/core \
  --daily-source artifacts/assets/rqdata/hk/tick_depth_daily/core \
  --metadata-source docs/records \
  --config-source path/to/universe_config
```

## `release-assets`

把 `package-assets` 生成的 `.tar.gz` 文件上传到 GitHub Release。该命令依赖本机
GitHub CLI `gh`，并且只处理已有 tarball 目录。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--tar-dir` | 必填 | `package-assets` 输出目录 |
| `--tag` | 必填 | GitHub Release tag |
| `--repo` | 当前 git remote | 目标仓库，格式 `owner/name` |
| `--title` | tag | Release 标题 |
| `--notes-file` | 自动选择 release notes | Release notes 文件 |
| `--draft` | `false` | 创建 draft release |
| `--prerelease` | `false` | 标记为 prerelease |
| `--latest` | `false` | 标记为 latest |
| `--clobber` | `false` | 已存在同名 asset 时覆盖 |
| `--dry-run` | `false` | 打印将执行的 `gh` 命令 |

示例：

```bash
rqdata-tick release-assets \
  --tar-dir artifacts/releases/hk_tick_depth_current_20260509_tarballs \
  --tag hk-tick-depth-current-20260509 \
  --repo owner/private-repo \
  --draft
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
