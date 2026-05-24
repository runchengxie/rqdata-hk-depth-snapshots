# 执行记录

本目录保存会随账号、quota、provider 行为或下载覆盖变化的 dated record。稳定规则放在
`docs/workflow.md`、`docs/data-contracts.md`、`docs/quality-gates.md`、
`docs/providers-rqdata.md` 和 `docs/development.md`。

## 当前摘要

当前状态见
[2026-05-25 current coverage](2026-05-25-hk-depth-current-coverage.md)。
截至 `2026-05-25`，provider 历史窗口内当前账号可访问的 HK CS 标的历史覆盖已补齐；
最新已确认可取交易日为 `2026-05-22`。ETF 权限拒绝和 provider 全空返回数据集已在
当前状态记录中单列。

后续维护按新增可取交易日执行增量下载、health、日频聚合和必要对账。逐日下载记录
保留审计用途，常规运行从当前状态记录和稳定工作流开始。

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
| [2026-05-24 compact benchmark](2026-05-24-hk-tick-compact-benchmark.md) | Core400 zstd12 冷归档合并压缩和 health 对照结果 |
| [2026-05-25 current coverage](2026-05-25-hk-depth-current-coverage.md) | 当前覆盖边界、冷归档验收和后续增量维护入口 |

旧逐日流水保留为上面的 dated records。需要逐 run 审计时，以对应原始快照缓存下的
`meta/download_*.json`、`audit/download_*.csv` 和 `artifacts/reports/*.json` 为准。

不要在记录中写入 secrets、token、私有账号凭据或完整本地 credential 路径。
