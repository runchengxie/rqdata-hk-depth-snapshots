# HK Tick-depth Universe Configs

This directory keeps the canonical symbol lists for HK tick-depth downloads.

| Directory | Role |
| --- | --- |
| `current/` | Current Core universe lists and the selection CSV used to derive them |
| `slices/` | Operational download slices |
| `experimental/` | Live-selected expansion lists outside the Core stock-connect universe |
| `probes/` | Small sizing or coverage probes |
| `archive/` | Historical bootstrap and add-on lists kept for audit only |

Symbol list files contain only RQData `order_book_id` values, one per line. Selection rules,
dates, and intended use live in `manifest.yml`.

Historical records may still reference the previous flat `configs/universe/*.txt` paths. New
commands should use the paths in this directory.
