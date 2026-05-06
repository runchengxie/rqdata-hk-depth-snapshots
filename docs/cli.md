# CLI Reference

入口命令：

```bash
rqdata-tick <command> [options]
```

常用命令：

| 命令 | 用途 |
| --- | --- |
| `quota` | 查看 RQData quota，用 `--fake-provider` 可离线演示 |
| `probe` | 单标的单日探查 |
| `download` | 批量下载 raw tick parquet |
| `health` | 检查 raw tick 自身质量 |
| `aggregate-daily` | 从 raw tick 聚合日频特征 |
| `emit-asset` | 输出 asset 目录 |
| `reconcile-daily` | 对账 tick 聚合结果与外部日频 reference |

查看帮助：

```bash
rqdata-tick download --help
rqdata-tick health --help
rqdata-tick reconcile-daily --help
```

离线下载演示：

```bash
rqdata-tick download \
  --symbols 00001.XHKG \
  --start-date 20250303 \
  --end-date 20250303 \
  --out artifacts/cache/rqdata/hk_tick_depth/demo \
  --fields "last volume total_turnover a1 a1_v b1 b1_v" \
  --fake-provider
```

线上 RQData 下载需要先安装 `rqdata` extra，并配置本地 `rqdatac` 认证或环境变量。
