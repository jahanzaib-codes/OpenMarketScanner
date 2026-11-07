#!/usr/bin/env python3
"""
==============================================================================
OpenMarketScanner CLI — High-Throughput US Equities Scanner
==============================================================================
"""

import asyncio
import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.pipeline.engine import scanning_engine
from config.settings import settings

console = Console()


async def run_cli(args):
    console.print(Panel.fit(
        "[bold cyan]🔍 OpenMarketScanner — 5,000+ US Equities Screening Engine[/bold cyan]\n"
        "[dim]Premarket Gappers • Relative Volume (RVOL) • Consolidation Breakouts • Momentum Ranking[/dim]",
        border_style="cyan"
    ))

    preset = args.preset.upper()
    console.print(f"[bold yellow]⚡ Scanning {settings.universe_size:,} US stocks with preset: {preset}...[/bold yellow]")

    result = await scanning_engine.scan_universe(
        min_price=args.min_price,
        max_price=args.max_price,
        min_rvol=args.min_rvol,
        min_gap_pct=args.min_gap,
        limit=args.limit,
        preset=preset
    )

    table = Table(title=f"🎯 Top {result['returned_count']} Screened Candidates ({preset})", header_style="bold magenta")
    table.add_column("Symbol", style="bold cyan", justify="left")
    table.add_column("Price", justify="right")
    table.add_column("Gap %", justify="right")
    table.add_column("RVOL", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("Score", justify="right", style="bold green")
    table.add_column("Trigger", justify="left")
    table.add_column("Quality", justify="left")
    table.add_column("Sector", justify="left", style="dim")

    for item in result["results"]:
        gap_val = item["gap_pct"]
        gap_style = "bold green" if gap_val >= 0 else "bold red"
        gap_str = f"[{gap_style}]{'+' if gap_val >= 0 else ''}{gap_val:.2f}%[/{gap_style}]"

        rvol_val = item["rvol"]
        rvol_style = "bold yellow" if rvol_val >= 3.0 else ("bold green" if rvol_val >= 2.0 else "white")
        rvol_str = f"[{rvol_style}]{rvol_val:.1f}x[/{rvol_style}]"

        table.add_row(
            item["symbol"],
            f"${item['price']:,.2f}",
            gap_str,
            rvol_str,
            f"{item['volume']:,}",
            f"{item['momentum_score']:.1f}",
            item["trigger"],
            item["gap_quality"],
            item["sector"]
        )

    console.print(table)
    console.print(
        f"[dim]Screened: [bold]{result['total_screened']:,}[/bold] equities | "
        f"Matches: [bold]{result['matched_count']}[/bold] | "
        f"Time: [bold]{result['execution_time_sec']:.3f}s[/bold] | "
        f"Throughput: [bold]{result['throughput_tickers_per_sec']:,.0f} tickers/sec[/bold][/dim]\n"
    )


def main():
    parser = argparse.ArgumentParser(description="OpenMarketScanner Quantitative Terminal CLI")
    parser.add_argument("--preset", type=str, default="ALL", choices=["ALL", "PREMARKET_GAPPERS", "UNUSUAL_RVOL", "MOMENTUM_BREAKOUT"], help="Screening preset")
    parser.add_argument("--min-price", type=float, default=None, help="Minimum stock price in USD")
    parser.add_argument("--max-price", type=float, default=None, help="Maximum stock price in USD")
    parser.add_argument("--min-rvol", type=float, default=None, help="Minimum RVOL threshold (e.g. 2.0)")
    parser.add_argument("--min-gap", type=float, default=None, help="Minimum Gap % (e.g. 3.0)")
    parser.add_argument("--limit", type=int, default=15, help="Number of results to display")

    args = parser.parse_args()
    asyncio.run(run_cli(args))


if __name__ == "__main__":
    main()
