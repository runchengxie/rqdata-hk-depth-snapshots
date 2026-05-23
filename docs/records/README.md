# 执行记录

本目录保存会随账号、quota、provider 行为或下载覆盖变化的 dated record。稳定规则放在
`docs/workflow.md`、`docs/data-contracts.md`、`docs/quality-gates.md`、
`docs/providers-rqdata.md` 和 `docs/development.md`。

## 当前摘要

截至记录日期 `2026-05-23`：

- 基于 `2026-05-21` live active 港股通选择快照的 897 只标的已覆盖到最新已确认
  可取交易日 `2026-05-22`。
- 非港股通 top100 历史缺口已补完并追加 `2026-05-22` 增量；rank101..300 已完整
  覆盖 `2025-04-01..2026-05-22`，形成可组合的 top300 扩展覆盖。
- 本轮新增数据 health 与 daily aggregate 已完成，health 均为 `status=pass`。
- 账户 tick quota 主动停在 48.72%，剩余 525.15 MB。

详细 metadata、audit、health 和 daily aggregate 路径见
[2026-05-23 download progress](2026-05-23-hk-tick-download-progress.md)。

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

旧逐日流水已压缩成上面的 dated records。需要逐 run 审计时，以对应 raw cache 下的
`meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json` 为准。

不要在记录中写入 secrets、token、私有账号凭据或完整本地 credential 路径。
