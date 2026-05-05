"""Command line interface for RQData HK tick-depth tooling."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rqdata_tick_data.aggregate import write_daily_aggregate
from rqdata_tick_data.assets import emit_daily_asset, emit_raw_asset
from rqdata_tick_data.downloader import (
    download_tick_depth,
    probe_tick_depth,
    provider_error_to_exit,
)
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.health import format_health_summary, write_health_report
from rqdata_tick_data.rq_client import RQDataClient, TickDataProvider
from rqdata_tick_data.symbols import parse_symbols


def _provider(fake: bool) -> TickDataProvider:
    if fake:
        from rqdata_tick_data.testing import FakeProvider

        return FakeProvider()
    return RQDataClient()


def _print_json(data: dict[str, object]) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rqdata-tick")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="Run a one-symbol one-day provider probe.")
    probe.add_argument("--symbol", required=True)
    probe.add_argument("--date", required=True)
    probe.add_argument("--fields")
    probe.add_argument("--out", default="artifacts/cache/rqdata/hk_tick_depth/probe")
    probe.add_argument("--fake-provider", action="store_true")

    download = subparsers.add_parser("download", help="Download HK tick-depth parquet parts.")
    download.add_argument("--symbols")
    download.add_argument("--symbols-file")
    download.add_argument("--start-date", required=True)
    download.add_argument("--end-date", required=True)
    download.add_argument("--fields")
    download.add_argument("--out", required=True)
    download.add_argument("--batch-size", type=int, default=5)
    download.add_argument("--resume", dest="resume", action="store_true", default=True)
    download.add_argument("--no-resume", dest="resume", action="store_false")
    download.add_argument("--continue-on-error", action="store_true")
    download.add_argument("--dry-run", action="store_true")
    download.add_argument("--fake-provider", action="store_true")

    health = subparsers.add_parser("health", help="Inspect raw parquet cache health.")
    health.add_argument("--input", required=True)
    health.add_argument("--out-json")

    aggregate = subparsers.add_parser("aggregate-daily", help="Aggregate raw ticks to daily data.")
    aggregate.add_argument("--input", required=True)
    aggregate.add_argument("--output", required=True)
    aggregate.add_argument("--meta-output")

    asset = subparsers.add_parser("emit-asset", help="Emit an asset-compatible directory.")
    asset.add_argument("--kind", required=True, choices=["raw", "daily"])
    asset.add_argument("--source", required=True)
    asset.add_argument("--output", required=True)

    return parser


def main(argv: list[str] | None = None, provider: TickDataProvider | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "probe":
            selected_provider = provider or _provider(args.fake_provider)
            result = probe_tick_depth(
                provider=selected_provider,
                symbol=args.symbol,
                trade_date=args.date,
                fields=parse_fields(args.fields),
                output_root=Path(args.out),
            )
            _print_json(result)
            return 0

        if args.command == "download":
            symbols = parse_symbols(args.symbols, args.symbols_file)
            selected_provider = None if args.dry_run else provider or _provider(args.fake_provider)
            result = download_tick_depth(
                provider=selected_provider,
                symbols=symbols,
                start_date=args.start_date,
                end_date=args.end_date,
                output_root=Path(args.out),
                fields=parse_fields(args.fields),
                batch_size=args.batch_size,
                resume=args.resume,
                continue_on_error=args.continue_on_error,
                dry_run=args.dry_run,
            )
            _print_json(result)
            return 0

        if args.command == "health":
            report = write_health_report(args.input, args.out_json)
            print(format_health_summary(report))
            print(f"report_path={report['report_path']}")
            return 0 if report["status"] == "pass" else 1

        if args.command == "aggregate-daily":
            metadata = write_daily_aggregate(args.input, args.output, args.meta_output)
            _print_json(metadata)
            return 0

        if args.command == "emit-asset":
            if args.kind == "raw":
                metadata = emit_raw_asset(args.source, args.output)
            else:
                metadata = emit_daily_asset(args.source, args.output)
            _print_json(metadata)
            return 0

    except Exception as exc:
        code, message = provider_error_to_exit(exc)
        print(message, file=sys.stderr)
        return code

    parser.error(f"Unhandled command {args.command!r}")
    return 2


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
