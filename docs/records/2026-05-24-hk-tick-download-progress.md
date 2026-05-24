# 港股 Tick 下载进展：2026-05-24

状态：今日 quota 已刷新；在 provider 允许的历史窗口内完成全部可访问 HK CS
标的的新增覆盖。用户指定的 `99.5%` 流量目标未达到，原因是剩余可枚举新类型
`ETF` 的 tick 权限被 provider 拒绝，而继续消耗额度只能重复已覆盖 CS 数据。

记录日期：2026-05-24（Asia/Shanghai）。本日为周末，最新已确认可取交易日仍为
`2026-05-22`。

## 摘要

- 开工时真实 quota 已刷新：`371.14 KB / 1.00 GB`（`0.04%`），TRIAL 剩余
  `2` 天。
- 补齐 non-connect active CS `rank1301..1849`，其中
  `rank1401..1753` 为正成交尾段，`rank1754..1849` 为选择窗口零成交尾段。
- 以全交易日 `CS` 并集补入不在 `2026-05-21` active 快照中的历史退市标的
  `63` 只，以及 `2026-05-22` 首次出现的 `06872.XHKG`。
- 对 `2025-04-01..2026-05-22` 的 `280` 个交易日复核：
  `CS` 并集为 `2,810` 只，配置集合精确匹配；本地应有的上市日期单元
  `753,751` 个，缺失 `0`。
- 最后一次真实 quota 快照：`164.28 MB / 1.00 GB`（`16.04%`），剩余
  `859.72 MB`。所有本轮下载均使用 `--quota-stop-ratio 0.995`。
- provider 在 `2026-05-22` 可枚举 `366` 只 `ETF`，但 ETF 日频成交额查询无权限，进一步对
  `02800.XHKG` 以五档字段探测 tick 也返回明确 entitlement 拒绝并写出 `0` 行；
  因此没有可据此继续下载的新增 HK tick 数据。

## Universe 变更

新增并登记到 `configs/universe/hk_tick_depth/manifest.yml`：

| 文件 | 说明 |
| --- | --- |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_rank1401_1753_positive_20260521.txt` | Active non-stock-connect CS ranks 1401..1753；选择窗口成交额为正的 353 只尾段 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_non_connect_rank1754_1849_zero_turnover_20260521.txt` | Active non-stock-connect CS ranks 1754..1849；选择窗口成交额为零的 96 只尾段 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_historical_delisted_selection_20250401_20260521.csv` | 全交易日回溯发现的 63 只历史 CS 标的及成交额分组依据 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_historical_delisted_positive27_20250401.txt` | 历史标的中窗口日频成交额为正的 27 只 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_historical_delisted_zero36_20250401.txt` | 历史标的中窗口日频成交额为零的 36 只 |
| `configs/universe/hk_tick_depth/experimental/hk_tick_depth_cs_transient_ipo_20260522.txt` | 仅在最新交易日新增出现的 `06872.XHKG` |

## 下载结果

| 数据集 | 请求覆盖 | raw 行 / part | 审计结果 |
| --- | --- | ---: | --- |
| Non-connect rank1301..1400 full | `2025-04-01..2026-05-22` | 243,676 / 28,000 | 前序缺口已补齐 |
| Non-connect rank1401..1753 positive full | `2025-04-01..2026-05-22` | 480,406 / 98,840 | full cache 完整 |
| Non-connect rank1754..1849 zero-turnover full | `2025-04-01..2026-05-22` | 410,665 / 26,880 | written 6,917；empty 19,963 |
| Historical delisted positive27 | `2025-04-01..2026-05-22` | 1,562,944 / 7,560 | written 3,311；empty 4,249 |
| Historical delisted zero36 | `2025-04-01..2026-05-22` | 0 / 10,080 | written 0；empty 10,080 |
| CS transient IPO `06872.XHKG` | `2026-05-22` | 5,082 / 1 | written 1 |

主要 metadata / audit：

| 数据集 | metadata / audit |
| --- | --- |
| Rank1301..1400 completion | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1301_1400_20250401_20260522/meta/download_20260524_035328.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1301_1400_20250401_20260522/audit/download_20260524_035155_3dcaf8ae.csv` |
| Rank1401..1753 boundary completion | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1401_1753_positive_20250401_20260522/meta/download_20260524_060929.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1401_1753_positive_20250401_20260522/audit/download_20260524_060929_a4490698.csv` |
| Rank1754..1849 full | `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1754_1849_zero_turnover_20250401_20260522/meta/download_20260524_075858.json` / `artifacts/cache/rqdata/hk_tick_depth/non_connect_rank1754_1849_zero_turnover_20250401_20260522/audit/download_20260524_075858_7e43b3b2.csv` |
| Historical positive27 | `artifacts/cache/rqdata/hk_tick_depth/historical_delisted_positive27_20250401_20260522/meta/download_20260524_080534.json` / `artifacts/cache/rqdata/hk_tick_depth/historical_delisted_positive27_20250401_20260522/audit/download_20260524_080534_4503f375.csv` |
| Historical zero36 | `artifacts/cache/rqdata/hk_tick_depth/historical_delisted_zero36_20250401_20260522/meta/download_20260524_081125.json` / `artifacts/cache/rqdata/hk_tick_depth/historical_delisted_zero36_20250401_20260522/audit/download_20260524_081125_25beb4de.csv` |
| CS transient IPO | `artifacts/cache/rqdata/hk_tick_depth/cs_transient_ipo_20260522/meta/download_20260524_081712.json` / `artifacts/cache/rqdata/hk_tick_depth/cs_transient_ipo_20260522/audit/download_20260524_081712_146b6a72.csv` |

`rank1401..1753` 下载期间因已有 part 下 `--resume` 缺口规划较慢，最终根据已写覆盖
边界从首个不完整交易日 `2025-08-04` 使用同一 raw root 继续；最终覆盖和行数以
full-cache health 报告为准，不将重写 run 相加。

## Health 与聚合

| 数据集 | health / daily aggregate | 结果 |
| --- | --- | --- |
| Non-connect rank1301..1400 full | `artifacts/reports/tick_health_non_connect_rank1301_1400_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank1301_1400_20250401_20260522/data.parquet` | pass；243,676 raw rows；18,926 daily rows |
| Non-connect rank1401..1753 positive full | `artifacts/reports/tick_health_non_connect_rank1401_1753_positive_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank1401_1753_positive_20250401_20260522/data.parquet` | pass with warning；480,406 raw rows；53,232 daily rows |
| Non-connect rank1754..1849 zero-turnover full | `artifacts/reports/tick_health_non_connect_rank1754_1849_zero_turnover_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/non_connect_rank1754_1849_zero_turnover_20250401_20260522/data.parquet` | pass with warning；410,665 raw rows；6,917 daily rows |
| Historical delisted positive27 | `artifacts/reports/tick_health_historical_delisted_positive27_20250401_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/historical_delisted_positive27_20250401_20260522/data.parquet` | pass with warnings；1,562,944 raw rows；3,311 daily rows |
| Historical delisted zero36 | `artifacts/reports/tick_health_historical_delisted_zero36_20250401_20260522.json` / 不生成 daily asset | fail；所有 provider 返回均为空，`empty_dataset` |
| CS transient IPO | `artifacts/reports/tick_health_cs_transient_ipo_20260522.json` / `artifacts/cache/rqdata/hk_tick_depth_daily/cs_transient_ipo_20260522/data.parquet` | pass；5,082 raw rows；1 daily row |

非空集合的 warning 均未触发 error gate：

- `rank1401..1753`：`turnover_decrease_count=3`。
- `rank1754..1849`：`turnover_decrease_count=10`。
- Historical positive27：`best_spread_cross_count` 和 `quote_ladder_invalid_count`。

Historical zero36 的 health failure 用于记录 provider 空覆盖结果；其没有 raw 行，不作为
可发布 daily 研究资产。

## 截停结论

- 本轮已补齐 provider 历史窗口内可访问 HK `CS` 的新覆盖；既有 root 无需重复请求
  消耗 quota。
- `ETF` 是同市场剩余可见类型，但账户无法访问其日频排序依据或历史 tick；探测结果在
  `artifacts/cache/rqdata/hk_tick_depth/probes/probe_etf_02800_20260522_depth5/`
  下保留为 entitlement 证据。
- 当前账户权限和新增覆盖原则下，可下载的有效数据范围已覆盖完成；本轮在
  `16.04%` 终止，未通过重复请求填充额度。
