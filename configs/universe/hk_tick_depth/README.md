# 港股十档盘口快照标的配置

本目录保存港股十档盘口快照下载使用的规范标的列表。目录名 `hk_tick_depth` 作为历史
路径标识保持兼容。

| 目录 | 用途 |
| --- | --- |
| `current/` | 当前核心标的列表及生成列表所用的选择 CSV |
| `slices/` | 下载执行切片 |
| `experimental/` | 核心港股通集合外的 live 扩展列表 |
| `probes/` | 小规模用量或覆盖探查列表 |
| `archive/` | 仅供审计的历史启动和增量列表 |

标的列表文件每行只包含一个 RQData `order_book_id`。选择规则、日期和用途记录在
`manifest.yml`。

历史记录可能引用原有 `configs/universe/*.txt` 平铺路径。新命令使用本目录内的路径。
