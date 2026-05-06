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
from rqdata_tick_data.quota import augment_quota_payload, format_quota_pretty
from rqdata_tick_data.reconcile import ReconcileConfig, write_reconciliation_report
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
    probe.add_argument("--adjust-type", default="none")
    probe.add_argument("--time-slice")
    probe.add_argument("--out", default="artifacts/cache/rqdata/hk_tick_depth/probe")
    probe.add_argument("--fake-provider", action="store_true")

    download = subparsers.add_parser("download", help="Download HK tick-depth parquet parts.")
    download.add_argument("--symbols")
    download.add_argument("--symbols-file")
    download.add_argument("--start-date", required=True)
    download.add_argument("--end-date", required=True)
    download.add_argument("--fields")
    download.add_argument("--adjust-type", default="none")
    download.add_argument("--time-slice")
    download.add_argument("--out", required=True)
    download.add_argument("--batch-size", type=int, default=5)
    download.add_argument("--raw-layout", choices=["symbol-date", "batch"], default="symbol-date")
    download.add_argument("--calendar", choices=["provider", "calendar"], default="provider")
    download.add_argument("--parquet-engine", default="pyarrow")
    download.add_argument("--compression", dest="parquet_compression", default="snappy")
    download.add_argument("--compression-level", dest="parquet_compression_level", type=int)
    download.add_argument("--resume", dest="resume", action="store_true", default=True)
    download.add_argument("--no-resume", dest="resume", action="store_false")
    download.add_argument("--continue-on-error", action="store_true")
    download.add_argument("--dry-run", action="store_true")
    download.add_argument("--fake-provider", action="store_true")
    download.add_argument("--retry-max-attempts", type=int, default=1)
    download.add_argument("--retry-backoff-seconds", type=float, default=0.0)
    download.add_argument("--retry-max-backoff-seconds", type=float, default=60.0)
    download.add_argument("--quota-guard", dest="quota_guard", action="store_true", default=True)
    download.add_argument("--no-quota-guard", dest="quota_guard", action="store_false")
    download.add_argument("--quota-stop-ratio", type=float, default=0.95)
    download.add_argument("--quota-safety-multiplier", type=float, default=1.2)
    download.add_argument("--audit-output")

    health = subparsers.add_parser("health", help="Inspect raw parquet cache health.")
    health.add_argument("--input", required=True)
    health.add_argument("--out-json")
    health.add_argument(
        "--fail-on-severity",
        choices=["none", "info", "warning", "error"],
        default="error",
    )

    aggregate = subparsers.add_parser("aggregate-daily", help="Aggregate raw ticks to daily data.")
    aggregate.add_argument("--input", required=True)
    aggregate.add_argument("--output", required=True)
    aggregate.add_argument("--meta-output")

    asset = subparsers.add_parser("emit-asset", help="Emit an asset-compatible directory.")
    asset.add_argument("--kind", required=True, choices=["raw", "daily"])
    asset.add_argument("--source", required=True)
    asset.add_argument("--output", required=True)

    quota = subparsers.add_parser("quota", help="Show RQData quota usage.")
    quota.add_argument("--pretty", action="store_true")
    quota.add_argument("--fake-provider", action="store_true")

    reconcile = subparsers.add_parser(
        "reconcile-daily",
        help="Reconcile raw ticks with an external daily clean asset.",
    )
    reconcile.add_argument("--tick-input", required=True)
    reconcile.add_argument("--daily-asset-dir", required=True)
    reconcile.add_argument("--out", required=True)
    reconcile.add_argument(
        "--fail-on-severity",
        choices=["none", "info", "warning", "error"],
        default="error",
    )
    reconcile.add_argument("--price-rtol", type=float, default=1e-4)
    reconcile.add_argument("--price-atol", type=float, default=1e-4)
    reconcile.add_argument("--volume-rtol", type=float, default=1e-4)
    reconcile.add_argument("--volume-atol", type=float, default=1.0)
    reconcile.add_argument("--turnover-rtol", type=float, default=1e-4)
    reconcile.add_argument("--turnover-atol", type=float, default=1.0)
    reconcile.add_argument("--session-start", default="09:00")
    reconcile.add_argument("--session-end", default="16:30")
    reconcile.add_argument("--sample-limit", type=int, default=20)

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
                adjust_type=args.adjust_type,
                time_slice=args.time_slice,
            )
            _print_json(result)
            return 0

        if args.command == "download":
            symbols = parse_symbols(args.symbols, args.symbols_file)
            selected_provider = None
            if not args.dry_run or args.fake_provider:
                selected_provider = provider or _provider(args.fake_provider)
            result = download_tick_depth(
                provider=selected_provider,
                symbols=symbols,
                start_date=args.start_date,
                end_date=args.end_date,
                output_root=Path(args.out),
                fields=parse_fields(args.fields),
                batch_size=args.batch_size,
                adjust_type=args.adjust_type,
                time_slice=args.time_slice,
                calendar=args.calendar,
                resume=args.resume,
                continue_on_error=args.continue_on_error,
                dry_run=args.dry_run,
                raw_layout=args.raw_layout,
                parquet_engine=args.parquet_engine,
                parquet_compression=args.parquet_compression,
                parquet_compression_level=args.parquet_compression_level,
                retry_max_attempts=args.retry_max_attempts,
                retry_backoff_seconds=args.retry_backoff_seconds,
                retry_max_backoff_seconds=args.retry_max_backoff_seconds,
                quota_guard=args.quota_guard,
                quota_stop_ratio=args.quota_stop_ratio,
                quota_safety_multiplier=args.quota_safety_multiplier,
                audit_output=args.audit_output,
            )
            _print_json(result)
            return 0

        if args.command == "health":
            report = write_health_report(
                args.input,
                args.out_json,
                fail_on_severity=args.fail_on_severity,
            )
            print(format_health_summary(report))
            print(f"report_path={report['report_path']}")
            verdict = report.get("quality_verdict")
            if isinstance(verdict, dict) and verdict.get("gate_triggered"):
                return 2
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

        if args.command == "quota":
            selected_provider = provider or _provider(args.fake_provider)
            payload = augment_quota_payload(selected_provider.quota_snapshot())
            if args.pretty:
                print(format_quota_pretty(payload))
            else:
                print(json.dumps(payload, indent=2, sort_keys=True, default=str))
            return 0

        if args.command == "reconcile-daily":
            config = ReconcileConfig(
                price_rtol=args.price_rtol,
                price_atol=args.price_atol,
                volume_rtol=args.volume_rtol,
                volume_atol=args.volume_atol,
                turnover_rtol=args.turnover_rtol,
                turnover_atol=args.turnover_atol,
                session_start=args.session_start,
                session_end=args.session_end,
                sample_limit=args.sample_limit,
                fail_on_severity=args.fail_on_severity,
            )
            report = write_reconciliation_report(
                args.tick_input,
                args.daily_asset_dir,
                args.out,
                config=config,
            )
            _print_json(
                {
                    "report_path": report["report_path"],
                    "summary": report["summary"],
                    "quality_verdict": report["quality_verdict"],
                    "status": report["status"],
                }
            )
            verdict = report.get("quality_verdict")
            if isinstance(verdict, dict) and verdict.get("gate_triggered"):
                return 2
            return 0 if report["status"] == "pass" else 1

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
