# Testing

安装开发依赖：

```bash
uv sync --group dev
```

运行离线测试：

```bash
uv run pytest
```

运行 lint：

```bash
uv run ruff check .
```

离线测试使用 `FakeProvider`，不需要 RQData 账号。

可选 live smoke 需要显式开启并安装 RQData extra：

```bash
uv sync --extra rqdata --group dev
RQDATA_TICK_LIVE_TESTS=1 uv run pytest -m rqdata_live
```

live smoke 只做最小 quota 或 probe 检查，不启动大规模下载。
