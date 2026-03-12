#!/usr/bin/env python3
"""
Versione temporanea lead_enricher SENZA PROXY per test sessione 13
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Import originale ma modifica init per no proxy
from marketing.lead_enricher import LeadEnricher, LeadDatabase, WebsiteScraper
import aiohttp
import logging

class WebsiteScraperNoProxy(WebsiteScraper):
    """WebsiteScraper senza proxy Tailscale"""

    async def init(self):
        """Initialize aiohttp session SENZA proxy"""
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # NO PROXY - connessione diretta
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )

class LeadEnricherNoProxy(LeadEnricher):
    """LeadEnricher senza proxy"""

    def __init__(self):
        self.db = LeadDatabase(Path("~/Documents/app-antigravity-auto/data/dealer_network.duckdb").expanduser())
        self.scraper = WebsiteScraperNoProxy()  # Use no-proxy version
        self.stats = {
            'processed': 0,
            'enriched': 0,
            'failed': 0
        }

async def test_no_proxy():
    enricher = LeadEnricherNoProxy()

    try:
        await enricher.init()

        print("="*50)
        print("TEST ENRICHMENT SENZA PROXY")
        print("="*50)

        # Test su 2 lead
        results = await enricher.enrich_all(2)

        print(f"Processed: {results['processed']}")
        print(f"Enriched: {results['enriched']}")
        print(f"Success rate: {results['success_rate']:.1f}%")

        if results['enriched'] > 0:
            print("✅ Enrichment funziona senza proxy")
        else:
            print("❌ Enrichment fallisce anche senza proxy")

    finally:
        await enricher.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_no_proxy())
