# 港股 Tick 下载进展：2026-05-21

状态：今日 RQData quota 重置后，先补 Core500 最新完整交易日
`2026-05-20`，再补齐 Core700 candidate rank621..660 历史 partial，随后按
成交额排序继续扩展完整历史覆盖到 rank780。原目标是继续到 95% quota guard；
本轮在 RQData quota 46.40% 时，Codex 外部 live 命令审批额度达到上限，后续
需要 live provider 的下载命令未能继续执行。

记录日期：2026-05-21。下载窗口以最新已确认完整交易日 `2026-05-20` 收口。

本轮最终 live quota：

| 项 | 值 |
| --- | ---: |
| license type | TRIAL |
| remaining days | 5 |
| bytes used | 475.15MB |
| bytes remaining | 548.85MB |
| used pct | 46.40% |

## 下载顺序

1. Probe `00700.XHKG` / `2026-05-20`，确认最新完整交易日 tick-depth 可取。
2. 下载 Core300 `2026-05-20` 增量。
3. 下载 Core500 candidate rank301..500 的 `2026-05-20` 增量。
4. Resume Core700 candidate rank621..660 历史 partial，补齐
   `2025-04-01` 到 `2026-05-19`。
5. 补 rank501..660 的 `2026-05-20` 日增量，使 rank501..660 覆盖到最新完整
   交易日。
6. 下载 rank661..700、rank701..740 和 rank741..780 的完整历史窗口
   `2025-04-01` 到 `2026-05-20`。

所有 live 下载均使用 `symbol-date` raw layout、`zstd` level 3 parquet、
provider 交易日历、`--resume`、`--continue-on-error`、`batch_size=1`、
`--quota-stop-ratio 0.95` 和 `--quota-safety-multiplier 1.2`。

## 下载结果

| 数据集 | 标的数 | 目标窗口 | written | empty remote | skipped existing | quota blocked | raw rows | health | daily rows |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Core300 increment | 300 | `2026-05-20` | 300 | 0 | 0 | 0 | 1,190,383 | pass / warning | 300 |
| Core500 rank301..500 increment | 200 | `2026-05-20` | 200 | 0 | 0 | 0 | 212,942 | pass | 200 |
| Core700 rank621..660 resume/full | 40 | `2025-04-01` 到 `2026-05-19` | 5,208 | 60 | 5,812 | 0 | 1,320,850 new / 4,147,652 total | pass | 11,020 |
| Core600 rank501..540 increment | 40 | `2026-05-20` | 40 | 0 | 0 | 0 | 24,348 | pass | 40 |
| Core600 rank541..580 increment | 40 | `2026-05-20` | 40 | 0 | 0 | 0 | 27,074 | pass | 40 |
| Core640 rank581..620 increment | 40 | `2026-05-20` | 39 | 1 | 0 | 0 | 29,877 | pass | 39 |
| Core700 rank621..660 increment | 40 | `2026-05-20` | 40 | 0 | 0 | 0 | 9,574 | pass | 40 |
| Core700 rank661..700 full | 40 | `2025-04-01` 到 `2026-05-20` | 10,987 | 133 | 0 | 0 | 3,123,534 | pass / warning | 10,987 |
| Core740 rank701..740 full | 40 | `2025-04-01` 到 `2026-05-20` | 11,116 | 4 | 0 | 0 | 3,775,722 | pass | 11,116 |
| Core780 rank741..780 full | 40 | `2025-04-01` 到 `2026-05-20` | 10,927 | 193 | 0 | 0 | 1,175,588 | pass / warning | 10,927 |

## Run Records

| 数据集 | metadata | audit |
| --- | --- | --- |
| Core300 increment | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260520/meta/download_20260521_061515.json` | `artifacts/cache/rqdata/hk_tick_depth/core300_increment_20260520/audit/download_20260521_061515_461a456d.csv` |
| Core500 rank301..500 increment | `artifacts/cache/rqdata/hk_tick_depth/core500_rank301_500_increment_20260520/meta/download_20260521_061709.json` | `artifacts/cache/rqdata/hk_tick_depth/core500_rank301_500_increment_20260520/audit/download_20260521_061708_68ac21eb.csv` |
| Core700 rank621..660 resume/full | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_20250401_20260519/meta/download_20260521_061855.json` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_20250401_20260519/audit/download_20260521_061812_fe42c5e5.csv` |
| Core600 rank501..540 increment | `artifacts/cache/rqdata/hk_tick_depth/core600_rank501_540_increment_20260520/meta/download_20260521_063700.json` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank501_540_increment_20260520/audit/download_20260521_063700_b74ed7e3.csv` |
| Core600 rank541..580 increment | `artifacts/cache/rqdata/hk_tick_depth/core600_rank541_580_increment_20260520/meta/download_20260521_063724.json` | `artifacts/cache/rqdata/hk_tick_depth/core600_rank541_580_increment_20260520/audit/download_20260521_063724_e5e96ca4.csv` |
| Core640 rank581..620 increment | `artifacts/cache/rqdata/hk_tick_depth/core640_rank581_620_increment_20260520/meta/download_20260521_063751.json` | `artifacts/cache/rqdata/hk_tick_depth/core640_rank581_620_increment_20260520/audit/download_20260521_063751_65d62962.csv` |
| Core700 rank621..660 increment | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_increment_20260520/meta/download_20260521_063816.json` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank621_660_increment_20260520/audit/download_20260521_063816_616b6f41.csv` |
| Core700 rank661..700 full | `artifacts/cache/rqdata/hk_tick_depth/core700_rank661_700_20250401_20260520/meta/download_20260521_063840.json` | `artifacts/cache/rqdata/hk_tick_depth/core700_rank661_700_20250401_20260520/audit/download_20260521_063840_0a03e097.csv` |
| Core740 rank701..740 full | `artifacts/cache/rqdata/hk_tick_depth/core740_rank701_740_20250401_20260520/meta/download_20260521_071208.json` | `artifacts/cache/rqdata/hk_tick_depth/core740_rank701_740_20250401_20260520/audit/download_20260521_071208_ba9f0e07.csv` |
| Core780 rank741..780 full | `artifacts/cache/rqdata/hk_tick_depth/core780_rank741_780_20250401_20260520/meta/download_20260521_074340.json` | `artifacts/cache/rqdata/hk_tick_depth/core780_rank741_780_20250401_20260520/audit/download_20260521_074340_0f80b1a7.csv` |

## 质量与聚合

| 数据集 | health report | daily aggregate |
| --- | --- | --- |
| Core300 increment | `artifacts/reports/tick_health_core300_increment_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core300_increment_20260520/data.parquet` |
| Core500 rank301..500 increment | `artifacts/reports/tick_health_core500_rank301_500_increment_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core500_rank301_500_increment_20260520/data.parquet` |
| Core700 rank621..660 resume/full | `artifacts/reports/tick_health_core700_rank621_660_20250401_20260519.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core700_rank621_660_20250401_20260519/data.parquet` |
| Core600 rank501..540 increment | `artifacts/reports/tick_health_core600_rank501_540_increment_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core600_rank501_540_increment_20260520/data.parquet` |
| Core600 rank541..580 increment | `artifacts/reports/tick_health_core600_rank541_580_increment_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core600_rank541_580_increment_20260520/data.parquet` |
| Core640 rank581..620 increment | `artifacts/reports/tick_health_core640_rank581_620_increment_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core640_rank581_620_increment_20260520/data.parquet` |
| Core700 rank621..660 increment | `artifacts/reports/tick_health_core700_rank621_660_increment_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core700_rank621_660_increment_20260520/data.parquet` |
| Core700 rank661..700 full | `artifacts/reports/tick_health_core700_rank661_700_20250401_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core700_rank661_700_20250401_20260520/data.parquet` |
| Core740 rank701..740 full | `artifacts/reports/tick_health_core740_rank701_740_20250401_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core740_rank701_740_20250401_20260520/data.parquet` |
| Core780 rank741..780 full | `artifacts/reports/tick_health_core780_rank741_780_20250401_20260520.json` | `artifacts/cache/rqdata/hk_tick_depth_daily/core780_rank741_780_20250401_20260520/data.parquet` |

所有本轮 health 均为 `status=pass`，无 failure。warning 级检查如下：

- Core300 `2026-05-20`：`00268.XHKG` / `20260520` timestamp 非单调 1 次、
  累计成交量回落 1 次、累计成交额回落 1 次。
- Core700 rank661..700：`00279.XHKG` / `20250818` 累计成交额回落 1 次；
  `00279.XHKG` / `20250819` 累计成交额回落 2 次。
- Core780 rank741..780：`02246.XHKG` / `20250523` 累计成交额回落 1 次；
  `02369.XHKG` / `20250624` 累计成交额回落 1 次。

## 覆盖状态

- Core500 最新完整交易日已覆盖到 `2026-05-20`。
- rank501..660 已覆盖完整历史窗口到 `2026-05-20`。
- rank661..780 已完整覆盖 `2025-04-01` 到 `2026-05-20`。
- rank781..894 的切片配置已新增，但 live 下载尚未开始；后续从
  `core820_rank781_820_20250401_20260520` 继续。
- 本轮未到 RQData 95% quota guard；停止原因是 Codex 外部 live 命令审批额度，
  不是 RQData provider quota。

## 配置更新

本轮新增以下成交额排序切片配置，并同步 `configs/universe/hk_tick_depth/manifest.yml`：

- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core740_rank701_740.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core780_rank741_780.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core820_rank781_820.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core860_rank821_860.txt`
- `configs/universe/hk_tick_depth/slices/hk_tick_depth_core894_rank861_894.txt`
