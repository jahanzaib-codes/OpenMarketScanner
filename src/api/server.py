import asyncio
import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from src.pipeline.engine import scanning_engine
from src.feed.universe import universe_manager

logger = logging.getLogger("OpenMarketScanner.API")

app = FastAPI(
    title="OpenMarketScanner API",
    description="High-Throughput 5,000+ US Equities Market Scanner API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "OpenMarketScanner",
        "version": "1.0.0",
        "status": "ONLINE",
        "universe_size": len(universe_manager.get_symbols()),
        "endpoints": {
            "health": "/api/health",
            "scan": "/api/scan",
            "presets": "/api/presets/{preset_name}",
            "universe_stats": "/api/universe/stats",
            "websocket_stream": "/ws/stream"
        }
    }


@app.get("/api/health")
def get_health():
    return {
        "status": "HEALTHY",
        "provider": settings.default_provider,
        "screened_universe": len(universe_manager.get_symbols()),
        "default_min_rvol": settings.min_rvol,
        "default_min_gap_pct": settings.min_gap_pct,
        "telegram_alerts": settings.enable_telegram,
        "discord_alerts": settings.enable_discord
    }


@app.get("/api/scan")
async def run_scan(
    min_price: Optional[float] = Query(None, description="Minimum stock price in USD"),
    max_price: Optional[float] = Query(None, description="Maximum stock price in USD"),
    min_rvol: Optional[float] = Query(None, description="Minimum Relative Volume (e.g. 2.0 = 200%)"),
    min_gap_pct: Optional[float] = Query(None, description="Minimum Gap % (e.g. 3.0)"),
    limit: int = Query(25, ge=1, le=100, description="Max results to return"),
    preset: str = Query("ALL", description="Screening preset: ALL, PREMARKET_GAPPERS, UNUSUAL_RVOL, MOMENTUM_BREAKOUT")
):
    """Executes live quantitative scan across 5,000+ US stocks."""
    result = await scanning_engine.scan_universe(
        min_price=min_price,
        max_price=max_price,
        min_rvol=min_rvol,
        min_gap_pct=min_gap_pct,
        limit=limit,
        preset=preset
    )
    return result


@app.get("/api/presets/{preset_name}")
async def run_preset(preset_name: str, limit: int = Query(25, ge=1, le=100)):
    """Runs a named preset scanner."""
    return await scanning_engine.scan_universe(preset=preset_name, limit=limit)


@app.get("/api/universe/stats")
def get_universe_stats():
    """Returns sector and market-cap breakdown of the screened equities universe."""
    all_stocks = universe_manager.get_all()
    sector_counts: Dict[str, int] = {}
    for s in all_stocks:
        sec = s.get("sector", "Other")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    return {
        "total_equities": len(all_stocks),
        "sectors": sector_counts,
        "core_benchmarks_tracked": len([s for s in all_stocks if s.get("is_core")])
    }


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """Real-time WebSocket broadcasting market alert events every 5 seconds."""
    await websocket.accept()
    logger.info("WebSocket client connected to live alert stream.")
    try:
        while True:
            scan_data = await scanning_engine.scan_universe(limit=5, preset="ALL")
            top_movers = scan_data.get("results", [])
            payload = {
                "event": "MARKET_PULSE",
                "timestamp": scan_data.get("execution_time_sec"),
                "total_screened": scan_data.get("total_screened"),
                "throughput": scan_data.get("throughput_tickers_per_sec"),
                "alerts": top_movers
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(5.0)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"WebSocket session closed: {e}")

