# 执行记录

本目录保存会随账号、quota、provider 行为或下载覆盖变化的 dated record。稳定规则放在
`docs/workflow.md`、`docs/data-contracts.md`、`docs/quality-gates.md`、
`docs/providers-rqdata.md` 和 `docs/development.md`。

## 当前摘要

截至记录日期 `2026-05-24`：

- 基于 `2026-05-21` live active 港股通选择快照的 897 只标的已覆盖到最新已确认
  可取交易日 `2026-05-22`。
- 非港股通 active ranks 1..1849 已完整覆盖 `2025-04-01..2026-05-22`；本轮补齐
  rank1301..1400 并新增 tail rank1401..1849。
- 全窗口 `CS` 并集复核为 `2,810` 只，本轮补入 historical delisted 63 只和
  `2026-05-22` 临时新增 IPO 1 只；应有上市日期单元 `753,751` 个，本地缺失 `0`。
- 新增非空 root 的 health / daily aggregate 已完成；historical zero36 的 provider
  返回全空，health 以 `empty_dataset` 失败记录覆盖事实，不输出 daily asset。
- 今日 quota 已确认刷新；最后成功查询值为 `164.28 MB / 1.00 GB`（`16.04%`）。
  ETF tick 被 provider 权限拒绝，继续到 `99.5%` 只能重复现有 CS 覆盖。

详细 metadata、audit、health 和 daily aggregate 路径见
[2026-05-24 download progress](2026-05-24-hk-tick-download-progress.md)。

## 索引

| 记录 | 内容 |
| --- | --- |
| [2026-05-06 RQData provider baseline](2026-05-06-hk-rqdata-provider-baseline.md) | 权限窗口、quota、样本估算和下载策略 |
| [2026-05-11 universe and coverage](2026-05-11-hk-tick-universe-and-coverage.md) | Core universe、配置文件组织和覆盖状态 |
| [2026-05-11 download summary](2026-05-11-hk-tick-download-summary.md) | 2026-05-06 到 2026-05-11 的下载、质量和聚合摘要 |
| [2026-05-13 download progress](2026-05-13-hk-tick-download-progress.md) | Core200 rank102..125 历史补齐、质量和 quota 摘要 |
| [2026-05-14 download progress](2026-05-14-hk-tick-download-progress.md) | Core128 最新日 refetch、Core200 rank128 补齐和 rank129..140 推进 |
| [2026-05-15 download progress](2026-05-15-hk-tick-download-progress.md) | Core200 rank166..200 补齐、Core300 rank201..230 partial 和 95% quota guard 摘要 |
| [2026-05-16 download progress](2026-05-16-hk-tick-download-progress.md) | Core200 最新增量、Core300 rank201..260 补齐和 rank261..300 partial 摘要 |
| [2026-05-17 download progress](2026-05-17-hk-tick-download-progress.md) | Core300 rank261..300 补齐、Core400 candidate rank301..340 partial 和 95% quota guard 摘要 |
| [2026-05-18 download progress](2026-05-18-hk-tick-download-progress.md) | Core400 candidate rank301..400 补齐、Core500 candidate rank401..420 partial 和 99.5% quota guard 摘要 |
| [2026-05-19 download progress](2026-05-19-hk-tick-download-progress.md) | Core500 candidate rank401..460 补齐、rank461..500 partial 和 95% quota guard 摘要 |
| [2026-05-20 download progress](2026-05-20-hk-tick-download-progress.md) | Core500 最新日增量、Core600/Core640 candidate rank501..620 补齐和 rank621..660 partial 摘要 |
| [2026-05-21 download progress](2026-05-21-hk-tick-download-progress.md) | Core500 最新日增量、rank621..660 补齐、rank661..780 完整覆盖和 Codex live 命令额度截停摘要 |
| [2026-05-22 download progress](2026-05-22-hk-tick-download-progress.md) | Core820..894 补齐、894 只港股通最新日增量、live 港股通 897 差异补齐和非港股通 top100 partial 95% quota guard 摘要 |
| [2026-05-23 download progress](2026-05-23-hk-tick-download-progress.md) | 港股通 897 最新日增量、non-connect top100 补齐和 top300 扩展覆盖摘要 |
| [2026-05-24 download progress](2026-05-24-hk-tick-download-progress.md) | 全窗口 HK CS 新覆盖补齐、ETF entitlement 阻断与 quota 截停摘要 |

旧逐日流水已压缩成上面的 dated records。需要逐 run 审计时，以对应 raw cache 下的
`meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json` 为准。

不要在记录中写入 secrets、token、私有账号凭据或完整本地 credential 路径。
