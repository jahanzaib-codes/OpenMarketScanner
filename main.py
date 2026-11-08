#!/usr/bin/env python3
"""
==============================================================================
OpenMarketScanner — Main Server & Pipeline Runner
==============================================================================
"""

import uvicorn
from config.settings import settings


def main():
    print(f"🚀 Starting OpenMarketScanner Server on {settings.api_host}:{settings.api_port}...")
    print(f"📊 Default Feed: {settings.default_provider} | Universe Size: {settings.universe_size:,}")
    print(f"🔗 Swagger Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    uvicorn.run(
        "src.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )


if __name__ == "__main__":
    main()

