# CLI 参考

入口命令：

```bash
rqdata-hk-depth <command> [options]
```

`rqdata-tick` 保留为兼容入口，参数和行为与主命令相同。

查看帮助：

```bash
rqdata-hk-depth download --help
rqdata-hk-depth health --help
rqdata-hk-depth reconcile-daily --help
rqdata-hk-depth compact-raw --help
rqdata-hk-depth package-assets --help
```

## 命令总览

| 命令 | 用途 |
| --- | --- |
| `probe` | 单标的单日 provider 探查 |
| `download` | 批量下载原始快照 parquet |
| `health` | 检查原始快照自身质量 |
| `aggregate-daily` | 从原始快照聚合日频特征 |
| `recompress-raw` | 重编码原始快照 parquet 压缩格式 |
| `compact-raw` | 生成冷归档 compact parquet 派生物 |
| `emit-asset` | 输出交付目录 |
| `package-assets` | 生成本地备份 tarball |
| `release-assets` | 上传备份 tarball 到 GitHub Release |
| `quota` | 查看 RQData quota |
| `reconcile-daily` | 对账原始快照聚合结果与外部日频基准数据 |

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
rqdata-hk-depth probe \
  --symbol 00001.XHKG \
  --date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/probe_00001_20250303
```

## `download`

批量下载原始快照 parquet。新下载默认使用 `symbol-date` 原始快照布局，并以 `zstd`
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
| `--out` | 必填 | 原始快照缓存输出目录 |
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
rqdata-hk-depth download \
  --symbols 00001.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider
```

live provider 下载建议使用 `--resume`、`--continue-on-error`、quota guard 和 audit
输出作为进度记录。非 `dry-run` 执行会在每个 provider 批次结束后追加 audit 行。

## `health`

按 parquet 分片扫描原始快照缓存，输出数据集级 summary 和 symbol-date 级诊断。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | 原始快照缓存目录 |
| `--out-json` | 空 | 写出 JSON 报告 |
| `--out-units` | 空 | 写出完整 symbol-date 级诊断；全量扫描建议使用 `.csv` 以便流式写出 |
| `--unit-sample-limit` | `20` | JSON 报告中保留的异常 symbol-date 样例数量；完整诊断使用 `--out-units` |
| `--fail-on-severity` | `error` | `none`、`info`、`warning`、`error`；达到阈值时返回非零退出码 |

示例：

```bash
rqdata-hk-depth health \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --out-json artifacts/reports/tick_health_demo.json \
  --out-units artifacts/reports/tick_health_demo_units.csv \
  --unit-sample-limit 20 \
  --fail-on-severity warning
```

## `aggregate-daily`

从原始快照聚合日频研究特征和质量标记。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | 原始快照缓存目录 |
| `--output` | 必填 | 日频 parquet 输出路径 |
| `--meta-output` | 空 | 聚合 metadata JSON 输出路径 |

示例：

```bash
rqdata-hk-depth aggregate-daily \
  --input artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/cache/rqdata/hk_tick_depth_daily/demo/data.parquet \
  --meta-output artifacts/cache/rqdata/hk_tick_depth_daily/demo/meta.json
```

## `recompress-raw`

将原始快照 parquet 缓存无损重编码到新目录，默认写 `zstd` level 3。该命令不修改输入目录，
输出目录会保留原始 `parts/...` 相对路径，并写出 migration metadata 和 part 级 audit CSV。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | 源原始快照缓存目录 |
| `--output` | 必填 | 新原始快照缓存输出目录 |
| `--compression` | `zstd` | 目标 parquet 压缩算法 |
| `--compression-level` | `3` | 目标 parquet 压缩等级 |
| `--min-rewrite-bytes` | `0` | 小于该字节数的分片直接复制；`0` 表示全部重写 |
| `--resume` | `true` | 跳过已匹配 schema、行数和目标 codec 的输出分片 |
| `--no-resume` | `false` | 强制重写或复制所有分片 |
| `--continue-on-error` | `false` | 单分片失败后继续处理后续分片 |
| `--meta-output` | 空 | migration metadata JSON 输出路径 |
| `--out-units` | 空 | part 级 audit CSV 输出路径 |
| `--progress` | `false` | 在 stderr 显示 part/字节进度条 |

示例：

```bash
rqdata-hk-depth recompress-raw \
  --input artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20260506 \
  --output artifacts/cache/rqdata/hk_tick_depth/round1_20_20250401_20260506_zstd3 \
  --compression zstd \
  --compression-level 3 \
  --progress
```

## `compact-raw`

将 `symbol-date` 原始快照缓存合并成冷归档 parquet 派生物。输入缓存保持原样；
compact 输出按标的和时间段组织，metadata 记录输入/输出字节数和压缩比例。
`--row-group-days 1` 主要衡量小文件元数据开销；使用较大的值可评估跨日 row group
的压缩收益，峰值内存随该值增加。输出 compact part 内的空分片 `null` schema 会
与 typed schema 统一，并在 metadata 中计数。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | 必填 | `symbol-date` 原始快照缓存目录 |
| `--output` | 必填 | compact 输出目录 |
| `--grouping` | `symbol-quarter` | 输出分组：`symbol-quarter` 或 `symbol-year` |
| `--compression` | `zstd` | compact parquet 压缩算法 |
| `--compression-level` | `3` | compact parquet 压缩等级 |
| `--row-group-days` | `1` | 一个输出 row group 最多合并的源交易日 part 数 |
| `--duplicate-policy` | `error` | 重复日期-标的处理；`prefer-nonempty-identical` 仅折叠相同非空副本，并让非空 refetch 替换空 retry |
| `--resume` | `true` | 输出行数、schema、codec 和 row group 数匹配时跳过已有 compact part |
| `--no-resume` | `false` | 强制重写全部 compact part |
| `--continue-on-error` | `false` | 一个 compact part 失败后继续处理 |
| `--meta-output` | 空 | compact metadata JSON 输出路径 |
| `--out-units` | 空 | compact part 级 audit CSV 输出路径 |
| `--progress` | `false` | 在 stderr 显示输入 part/字节进度 |

示例：

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

当输入是包含 retry/refetch 副本的完整 cold cache 时，可使用保守重复处理：

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

该策略只接受字节相同副本、全部为空的副本，或空 retry 与内容一致的非空副本组合；
发现两个内容不同的非空副本时命令失败，不静默选择来源。

## `emit-asset`

输出可发布或交付的数据目录。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--kind` | 必填 | `raw` 或 `daily` |
| `--source` | 必填 | 原始快照缓存目录或日频 parquet |
| `--output` | 必填 | 交付目录 |

示例：

```bash
rqdata-hk-depth emit-asset \
  --kind raw \
  --source artifacts/cache/rqdata/hk_tick_depth/demo \
  --output artifacts/assets/rqdata/hk/tick_depth/demo
```

## `package-assets`

将本地十档盘口快照数据、聚合结果、报告、配置和记录打成可搬运的归档分包。
默认输出 `.tar`，避免对已压缩 parquet 再执行耗时的外层压缩。`tar.gz` 和
`tar.zst` 为显式 archive 容器压缩选项；调整 raw parquet 压缩率使用
`recompress-raw`。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--preset` | `explicit` | `explicit` 使用显式路径；`current-cache` 选择当前默认缓存、reports、universe configs、记录索引和当前覆盖摘要 |
| `--name` | `hk-depth-snapshots` | 分发名称，用于 manifest 和 tarball 文件名 |
| `--as-of` | 当日 UTC 日期 | 资产日期标签，格式建议 `YYYYMMDD` |
| `--tar-dir` | `artifacts/releases/<name>_<as_of>_tarballs` | tarball 输出目录 |
| `--overwrite` | `false` | 覆盖已有非空输出目录 |
| `--dry-run` | `false` | 只生成选择计划，不写 tarball |
| `--part` | 全部 part | 选择 `raw`、`daily`、`metadata`、`reports`、`configs`；可重复 |
| `--raw-source` | 空 | 额外原始快照缓存或原始快照交付目录路径；可重复 |
| `--daily-source` | 空 | 额外日频聚合或日频交付目录路径；可重复 |
| `--metadata-source` | 空 | 额外 metadata 或记录路径；可重复 |
| `--report-source` | 空 | 额外 report 路径；可重复 |
| `--config-source` | 空 | 额外 config 或 universe 路径；可重复 |
| `--max-tar-bytes` | `1900000000` | 单个 tarball 目标上限；超过上限时会按文件切分；GitHub Release 单 asset 需小于 2GiB，网络不稳时可用 `1000000000` |
| `--archive-format` | `tar` | 输出格式：`tar.gz`、`tar.zst` 或 `tar`；压缩格式仅作用于 archive 容器 |
| `--archive-compression-level` | 空 | 外层 archive 压缩等级；`tar.gz` 支持 `1-9`，`tar.zst` 支持 `1-22` |
| `--raw-dedupe` | `none` | 原始快照分片去重模式；`symbol-date` 只折叠安全可判定的重复日期-标的分片，冲突非空副本会使命令失败 |
| `--progress` | `false` | 在 stderr 显示 archive 写入进度条 |

示例：

```bash
rqdata-hk-depth package-assets \
  --preset current-cache \
  --name hk_tick_depth_current \
  --as-of 20260509 \
  --tar-dir artifacts/releases/hk_tick_depth_current_20260509_tarballs \
  --archive-format tar \
  --overwrite
```

冷存储可先用 `recompress-raw` 生成高等级 zstd parquet 副本，再显式选择冷副本打
未压缩 archive 分包：

```bash
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
  --archive-format tar \
  --raw-dedupe symbol-date \
  --progress \
  --overwrite
```

`--raw-dedupe symbol-date` 使用与 `compact-raw` 相同的安全判定：字节一致副本可
折叠，空副本可由一致非空副本替代，不同内容的非空副本会中止打包。
需要附带全部历史执行流水时，显式增加 `--metadata-source docs/records`。

交付流程要求压缩 archive 容器时，可显式选择 `--archive-format tar.zst` 和
`--archive-compression-level`。包含原始快照 parquet 时，命令会提示该等级仅压缩
外层 archive；parquet 压缩率由其生成或 `recompress-raw` 阶段决定。

显式选择已 emit 的 raw/daily asset：

```bash
rqdata-hk-depth package-assets \
  --name hk_tick_depth_core \
  --as-of 20260509 \
  --raw-source artifacts/assets/rqdata/hk/tick_depth/core \
  --daily-source artifacts/assets/rqdata/hk/tick_depth_daily/core \
  --metadata-source docs/records/2026-05-25-hk-depth-current-coverage.md \
  --config-source path/to/universe_config
```

## `release-assets`

把 `package-assets` 生成的 archive 文件上传到 GitHub Release。该命令依赖本机
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
rqdata-hk-depth release-assets \
  --tar-dir artifacts/releases/hk_tick_depth_current_20260509_tarballs \
  --tag hk-depth-snapshots-current-20260509 \
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
rqdata-hk-depth quota --pretty
rqdata-hk-depth quota --fake-provider --pretty
```

## `reconcile-daily`

将原始快照聚合出的 OHLCV 与外部日频基准数据对账。

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--tick-input` | 必填 | 原始快照缓存目录 |
| `--daily-asset-dir` | 必填 | 外部日频基准数据目录 |
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
rqdata-hk-depth reconcile-daily \
  --tick-input artifacts/cache/rqdata/hk_tick_depth/demo \
  --daily-asset-dir artifacts/assets/rqdata/hk/daily_raw/demo \
  --out artifacts/reports/tick_daily_reconcile_demo.json \
  --reference-policy raw-daily \
  --fail-on-severity warning
```

`raw-daily` 用于同报价口径下载门禁。`cross-clean` 用于研究清洗底座覆盖检查，价格、成交量和成交额口径差异记录为 `info`。
