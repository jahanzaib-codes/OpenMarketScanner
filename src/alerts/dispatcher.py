import logging
import time
from typing import Dict, Any, Optional
import httpx
from config.settings import settings

logger = logging.getLogger("OpenMarketScanner.Alerts")


class AlertDispatcher:
    """Dispatches high-conviction screening triggers to Telegram and Discord."""

    def __init__(self, cfg=settings):
        self.cfg = cfg
        self._cooldown_cache: Dict[str, float] = {}
        self.cooldown_seconds: float = 900.0  # 15-minute alert cooldown per symbol

    def _should_suppress(self, symbol: str) -> bool:
        now = time.time()
        last_sent = self._cooldown_cache.get(symbol, 0.0)
        if (now - last_sent) < self.cooldown_seconds:
            return True
        self._cooldown_cache[symbol] = now
        return False

    def format_telegram_card(self, alert: Dict[str, Any]) -> str:
        sym = alert.get("symbol", "UNKNOWN")
        price = alert.get("price", 0.0)
        gap = alert.get("gap_pct", 0.0)
        rvol = alert.get("rvol", 1.0)
        score = alert.get("momentum_score", 0.0)
        trigger = alert.get("trigger", "SCAN_HIT")
        urgency = alert.get("urgency", "NORMAL")

        gap_sign = "+" if gap >= 0 else ""
        icon = "🚀" if gap >= 0 else "🔻"

        card = (
            f"{icon} <b>OpenMarketScanner Alert: {sym}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Trigger:</b> <code>{trigger}</code>\n"
            f"<b>Price:</b> ${price:,.2f} ({gap_sign}{gap:.2f}% Gap)\n"
            f"<b>RVOL:</b> <b>{rvol:.1f}x</b> ({urgency})\n"
            f"<b>Momentum Score:</b> {score:.1f}/100\n"
            f"<b>Sector:</b> {alert.get('sector', 'N/A')}\n"
            f"<b>Volume:</b> {alert.get('volume', 0):,}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <a href='https://tradingview.com/chart/?symbol={sym}'>Open TradingView Chart</a>"
        )
        return card

    async def dispatch(self, alert: Dict[str, Any]) -> bool:
        symbol = alert.get("symbol", "")
        if self._should_suppress(symbol):
            logger.debug(f"Alert for {symbol} suppressed due to active cooldown.")
            return False

        message = self.format_telegram_card(alert)
        sent = False

        # 1. Telegram Dispatch
        if self.cfg.enable_telegram and self.cfg.telegram_bot_token and self.cfg.telegram_chat_id:
            tg_url = f"https://api.telegram.org/bot{self.cfg.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.cfg.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(tg_url, json=payload)
                    if resp.status_code == 200:
                        sent = True
                        logger.info(f"Telegram alert sent for {symbol}")
            except Exception as e:
                logger.error(f"Telegram alert dispatch failed for {symbol}: {e}")

        # 2. Discord Dispatch
        if self.cfg.enable_discord and self.cfg.discord_webhook_url:
            discord_payload = {
                "content": f"🚨 **OpenMarketScanner Alert: {symbol}** | Price: ${alert.get('price'):.2f} | Gap: {alert.get('gap_pct'):.2f}% | RVOL: {alert.get('rvol'):.1f}x"
            }
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(self.cfg.discord_webhook_url, json=discord_payload)
                    if resp.status_code in (200, 204):
                        sent = True
                        logger.info(f"Discord alert sent for {symbol}")
            except Exception as e:
                logger.error(f"Discord alert dispatch failed for {symbol}: {e}")

        return sent


alert_dispatcher = AlertDispatcher()
