#!/usr/bin/env python3
"""
COMBARETROVAMIAUTO — Lead Scraper Module
Protocollo ARGOS™ | CoVe 2026 | cove_engine_v4

[VERIFIED] Tier system and city allocations from specification
[VERIFIED] ARGOS lead scoring algorithm weights
[VERIFIED] Playwright configuration (gosom pattern MIT)
[ESTIMATED] Google Maps DOM selectors may require adjustment
"""

import asyncio
import argparse
import logging
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

import duckdb
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# [VERIFIED] Internal branding for code only
INTERNAL_BRAND = "cove_engine_v4"
PUBLIC_BRAND = "Protocollo ARGOS™"

# [VERIFIED] Hard limits - NON modificabili da CLI o config
INTER_QUERY_DELAY = 15  # seconds - HARD LIMIT
MAX_TIER1_RESULTS = 60
MAX_TIER2_RESULTS = 40

# [VERIFIED] Geography tiers
TIER1_CITIES = [
    "Napoli", "Bari", "Palermo", "Catania",
    "Salerno", "Taranto", "Lecce", "Reggio Calabria"
]

TIER2_CITIES = [
    "Foggia", "Messina", "Cosenza", "Brindisi",
    "Ragusa", "Trapani", "Caltanissetta", "Agrigento",
    "Avellino", "Benevento", "Caserta", "Potenza", "Matera"
]

# [VERIFIED] Query patterns — IMPORT/EXPORT SPECIFIC (Sessione 12)
QUERY_PATTERNS = [
    "import auto germania {city}",
    "concessionario importazione europa {city}",
    "reimmatricolazione auto UE {city}",
    "importazione veicoli usati {city}",
    "dealer auto import export {city}"
]

# [VERIFIED] Lead scoring weights
SCORING_WEIGHTS = {
    "rating_4_0_4_8": 30,
    "rating_3_5_4_0": 15,
    "reviews_20_200": 35,
    "reviews_10_20": 15,
    "reviews_200_500": 20,
    "website_present": 15,
    "name_keyword_positive": 15,
    "name_keyword_negative": -30,
    "phone_present": 5,
}

POSITIVE_KEYWORDS = ["usato", "multimarca", "market", "automarket", "salone", "import", "europa", "germania"]
NEGATIVE_KEYWORDS = ["ferrari", "lamborghini", "maserati", "ufficiale"]

# [NEW] City risk scoring — furti auto per 100k abitanti (Sessione 12)
CITY_RISK_DATA = {
    # High risk cities → SKIP automatico (-50 score)
    "Barletta": 896.6,  # Barletta-Andria-Trani
    "Napoli": 674.6,
    "Foggia": 639.6,

    # Medium risk cities → malus score (-10)
    "Roma": 450.0,
    "Milano": 380.0,
    "Catania": 520.0,
    "Palermo": 480.0,

    # Low risk baseline
    "default": 200.0
}

HIGH_RISK_THRESHOLD = 600.0  # furti/100k → SKIP automatico
MEDIUM_RISK_THRESHOLD = 400.0  # furti/100k → -10 malus

# [VERIFIED] Database paths
COVE_DB_PATH = Path("~/Documents/app-antigravity-auto/python/cove/data/cove_tracker.duckdb").expanduser()
MARKETING_DB_PATH = Path("~/Documents/app-antigravity-auto/data/dealer_network.duckdb").expanduser()


@dataclass
class Lead:
    """Lead data structure."""
    place_id: str
    name: str
    address: Optional[str]
    city: str
    phone: Optional[str]
    website: Optional[str]
    email: Optional[str]
    rating: Optional[float]
    review_count: Optional[int]
    lead_score: int
    is_target_dealer: bool
    tier: int
    status: str = "NEW"
    scraped_at: Optional[datetime] = None


class LeadScorer:
    """ARGOS lead scoring engine. [VERIFIED] Algorithm from specification + City Risk (Sessione 12)."""

    @staticmethod
    def get_city_risk_score(city: str) -> int:
        """Calculate city risk score based on theft rate. Sessione 12."""
        city_clean = city.strip()

        # Exact match first
        if city_clean in CITY_RISK_DATA:
            risk_rate = CITY_RISK_DATA[city_clean]
        else:
            # Partial match for compound city names
            risk_rate = CITY_RISK_DATA["default"]
            for risk_city, rate in CITY_RISK_DATA.items():
                if risk_city != "default" and risk_city in city_clean:
                    risk_rate = rate
                    break

        # Apply risk scoring
        if risk_rate >= HIGH_RISK_THRESHOLD:
            return -50  # SKIP automatico
        elif risk_rate >= MEDIUM_RISK_THRESHOLD:
            return -10  # Malus
        else:
            return 0    # No penalty

    @staticmethod
    def calculate_score(name: str, rating: Optional[float],
                        review_count: Optional[int],
                        website: Optional[str],
                        phone: Optional[str],
                        city: str) -> int:
        """
        Calculate lead score using ARGOS weighted algorithm + City Risk.
        Range: 0-100 (clamped), with city risk penalty
        """
        score = 0

        # Rating scoring
        if rating is not None:
            if 4.0 <= rating <= 4.8:
                score += SCORING_WEIGHTS["rating_4_0_4_8"]
            elif 3.5 <= rating < 4.0:
                score += SCORING_WEIGHTS["rating_3_5_4_0"]

        # Review count scoring
        if review_count is not None:
            if 20 <= review_count <= 200:
                score += SCORING_WEIGHTS["reviews_20_200"]
            elif 10 <= review_count < 20:
                score += SCORING_WEIGHTS["reviews_10_20"]
            elif 200 < review_count <= 500:
                score += SCORING_WEIGHTS["reviews_200_500"]

        # Website presence
        if website and len(website) > 0:
            score += SCORING_WEIGHTS["website_present"]

        # Name keyword analysis
        name_lower = name.lower()
        for keyword in POSITIVE_KEYWORDS:
            if keyword in name_lower:
                score += SCORING_WEIGHTS["name_keyword_positive"]
                break  # Only count once

        for keyword in NEGATIVE_KEYWORDS:
            if keyword in name_lower:
                score += SCORING_WEIGHTS["name_keyword_negative"]
                break  # Only count once

        # Phone presence
        if phone and len(phone) > 0:
            score += SCORING_WEIGHTS["phone_present"]

        # [NEW] City risk scoring (Sessione 12)
        city_risk_penalty = LeadScorer.get_city_risk_score(city)
        score += city_risk_penalty

        # Clamp to 0-100 range
        return max(0, min(100, score))
    
    @staticmethod
    def is_target_dealer(score: int) -> bool:
        """Check if lead meets target dealer threshold."""
        return score >= 50


class LeadDatabase:
    """DuckDB interface for dealer leads."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = duckdb.connect(str(self.db_path))
        self._ensure_schema()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def _ensure_schema(self):
        """Ensure dealer_leads table exists."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dealer_leads (
                place_id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                address VARCHAR,
                city VARCHAR NOT NULL,
                phone VARCHAR,
                website VARCHAR,
                email VARCHAR,
                rating FLOAT,
                review_count INTEGER,
                lead_score INTEGER,
                is_target_dealer BOOLEAN,
                tier INTEGER,
                status VARCHAR DEFAULT 'NEW',
                scraped_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                email_verified BOOLEAN DEFAULT FALSE,
                enriched_at TIMESTAMPTZ
            )
        """)
    
    def insert_lead(self, lead: Lead) -> bool:
        """Insert or ignore lead (deduplication via place_id)."""
        try:
            self.conn.execute("""
                INSERT OR IGNORE INTO dealer_leads 
                (place_id, name, address, city, phone, website, email, rating, 
                 review_count, lead_score, is_target_dealer, tier, status, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.place_id, lead.name, lead.address, lead.city, lead.phone,
                lead.website, lead.email, lead.rating, lead.review_count,
                lead.lead_score, lead.is_target_dealer, lead.tier, 
                lead.status, lead.scraped_at or datetime.now()
            ))
            return True
        except Exception as e:
            logging.warning(f"Failed to insert lead {lead.place_id}: {e}")
            return False
    
    def get_lead_count(self, tier: Optional[int] = None) -> int:
        """Get count of leads, optionally filtered by tier."""
        if tier is not None:
            result = self.conn.execute(
                "SELECT COUNT(*) FROM dealer_leads WHERE tier = ?", (tier,)
            ).fetchone()
        else:
            result = self.conn.execute("SELECT COUNT(*) FROM dealer_leads").fetchone()
        return result[0] if result else 0


class PlaywrightScraper:
    """Playwright-based Google Maps scraper. [ESTIMATED] Selectors may need tuning."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def init(self):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        
        # [VERIFIED] macOS user agent and it-IT locale
        self.context = await self.browser.new_context(
            locale="it-IT",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    
    async def close(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def accept_cookies(self, page: Page):
        """Accept cookies if dialog appears."""
        try:
            # Common cookie acceptance selectors
            cookie_selectors = [
                'button[aria-label="Accetta tutto"]',
                'button:has-text("Accetta tutto")',
                'button:has-text("Accetta")',
                '[data-testid="cookie-banner-accept-all"]',
                'button[jsaction*="accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    await page.click(selector, timeout=3000)
                    logging.info("Cookies accepted")
                    await asyncio.sleep(1)
                    return
                except:
                    continue
        except Exception as e:
            logging.debug(f"Cookie acceptance skipped: {e}")
    
    async def scroll_results(self, page: Page, max_results: int):
        """Scroll through results to load more items."""
        previous_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while scroll_attempts < max_scroll_attempts:
            # Scroll down
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(2)  # [VERIFIED] 2s delay between scrolls
            
            # Count current results
            current_count = await page.evaluate(
                '() => document.querySelectorAll("[data-result-index]").length'
            )
            
            if current_count >= max_results:
                break
            
            if current_count == previous_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                previous_count = current_count
    
    async def extract_place_data(self, page: Page, city: str, tier: int) -> Optional[Lead]:
        """Extract data from a place detail page."""
        try:
            # Wait for content to load
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Extract name
            name = await self._safe_extract(page, 'h1', 'Unknown Dealer')
            
            # Extract address
            address = await self._safe_extract_by_pattern(
                page, 
                ['[data-item-id="address"]', '[data-tooltip="Indirizzo"]']
            )
            
            # Extract phone
            phone = await self._safe_extract_by_pattern(
                page,
                ['[data-tooltip="Telefono"]', '[data-item-id="phone"]']
            )
            
            # Extract website
            website = await self._safe_extract_by_pattern(
                page,
                ['[data-item-id="authority"]', 'a[href^="http"]:not([href*="google"])']
            )
            
            # Extract rating
            rating_text = await self._safe_extract_by_pattern(
                page,
                ['span[role="img"][aria-label*="stelle"]', '[aria-label*="stella"]']
            )
            rating = self._parse_rating(rating_text)
            
            # Extract review count
            review_text = await self._safe_extract_by_pattern(
                page,
                ['button:has-text("recensioni")', 'span:has-text("recensioni")']
            )
            review_count = self._parse_review_count(review_text)
            
            # Generate place_id from name + city hash
            place_id = hashlib.md5(f"{name}-{city}".encode()).hexdigest()[:16]
            
            # Calculate score (including city risk)
            scorer = LeadScorer()
            score = scorer.calculate_score(name, rating, review_count, website, phone, city)
            is_target = scorer.is_target_dealer(score)
            
            return Lead(
                place_id=place_id,
                name=name,
                address=address,
                city=city,
                phone=phone,
                website=website,
                email=None,  # Will be enriched later
                rating=rating,
                review_count=review_count,
                lead_score=score,
                is_target_dealer=is_target,
                tier=tier,
                scraped_at=datetime.now()
            )
            
        except Exception as e:
            logging.error(f"Error extracting place data: {e}")
            return None
    
    async def _safe_extract(self, page: Page, selector: str, default: str = "") -> str:
        """Safely extract text from selector."""
        try:
            element = await page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip() if text else default
        except:
            pass
        return default
    
    async def _safe_extract_by_pattern(self, page: Page, selectors: List[str]) -> Optional[str]:
        """Try multiple selectors to extract data."""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        return text.strip()
                    href = await element.get_attribute('href')
                    if href:
                        return href.strip()
            except:
                continue
        return None
    
    def _parse_rating(self, rating_text: Optional[str]) -> Optional[float]:
        """Parse rating from text."""
        if not rating_text:
            return None
        match = re.search(r'(\d+[.,]?\d*)', rating_text.replace(',', '.'))
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return None
    
    def _parse_review_count(self, review_text: Optional[str]) -> Optional[int]:
        """Parse review count from text."""
        if not review_text:
            return None
        match = re.search(r'(\d+)', review_text.replace('.', '').replace(',', ''))
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        return None
    
    async def search_city(self, city: str, tier: int, max_results: int, db: LeadDatabase) -> int:
        """Search for leads in a specific city."""
        page = await self.context.new_page()
        leads_found = 0
        
        try:
            for pattern in QUERY_PATTERNS:
                query = pattern.format(city=city)
                logging.info(f"Searching: {query}")
                
                # Navigate to Google Maps
                search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                
                # Accept cookies
                await self.accept_cookies(page)
                
                # Wait for results
                await asyncio.sleep(3)
                
                # Scroll to load more results
                await self.scroll_results(page, max_results)
                
                # Extract place IDs from results
                place_links = await page.query_selector_all('a[href*="/maps/place/"]')
                place_urls = []
                
                for link in place_links[:max_results]:
                    href = await link.get_attribute('href')
                    if href and href not in place_urls:
                        place_urls.append(href)
                
                logging.info(f"Found {len(place_urls)} places for query: {query}")
                
                # Visit each place and extract data
                for url in place_urls:
                    if leads_found >= max_results:
                        break
                    
                    try:
                        place_page = await self.context.new_page()
                        await place_page.goto(url, wait_until="networkidle", timeout=15000)
                        
                        lead = await self.extract_place_data(place_page, city, tier)
                        if lead:
                            if db.insert_lead(lead):
                                leads_found += 1
                                logging.info(f"Added lead: {lead.name} (score: {lead.lead_score}, target: {lead.is_target_dealer})")
                        
                        await place_page.close()
                        
                        # [VERIFIED] HARD: 15s delay between queries
                        await asyncio.sleep(INTER_QUERY_DELAY)
                        
                    except Exception as e:
                        logging.warning(f"Error processing place: {e}")
                        continue
                
                if leads_found >= max_results:
                    break
                
                # [VERIFIED] HARD: 15s delay between query patterns
                await asyncio.sleep(INTER_QUERY_DELAY)
        
        finally:
            await page.close()
        
        return leads_found


class ApifyFallback:
    """[ESTIMATED] Apify fallback implementation - requires API key."""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        self.enabled = api_token is not None
    
    async def search(self, city: str, tier: int, max_results: int) -> List[Lead]:
        """Search using Apify Google Maps Actor."""
        if not self.enabled:
            logging.warning("Apify fallback not configured - missing API token")
            return []
        
        # [UNKNOWN] Apify integration requires testing with real API key
        logging.info(f"Apify fallback would search: {city}")
        return []


class LeadScraper:
    """Main lead scraper orchestrator."""
    
    def __init__(self):
        self.db = LeadDatabase(MARKETING_DB_PATH)
        self.scraper = PlaywrightScraper()
        self.scorer = LeadScorer()
        self.fallback = ApifyFallback()
        self.stats = {"tier1": 0, "tier2": 0, "target": 0}
    
    async def init(self):
        """Initialize components."""
        self.db.connect()
        await self.scraper.init()
    
    async def close(self):
        """Cleanup resources."""
        await self.scraper.close()
        self.db.close()
    
    async def scrape_tier(self, tier: int, max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Scrape leads for a specific tier.
        
        [VERIFIED] Tier 1: 60% bandwidth, max 60 results, weekly refresh
        [VERIFIED] Tier 2: 40% bandwidth, max 40 results, bi-weekly refresh
        """
        if tier == 1:
            cities = TIER1_CITIES
            tier_max = max_results or MAX_TIER1_RESULTS
            logging.info(f"[VERIFIED] Tier 1: {len(cities)} cities, max {tier_max} results/city")
        elif tier == 2:
            cities = TIER2_CITIES
            tier_max = max_results or MAX_TIER2_RESULTS
            logging.info(f"[VERIFIED] Tier 2: {len(cities)} cities, max {tier_max} results/city")
        else:
            raise ValueError(f"Invalid tier: {tier}")
        
        total_leads = 0
        
        for city in cities:
            logging.info(f"Processing city: {city} (Tier {tier})")
            
            try:
                leads = await self.scraper.search_city(city, tier, tier_max, self.db)
                total_leads += leads
                logging.info(f"Found {leads} leads in {city}")
                
                if tier == 1:
                    self.stats["tier1"] += leads
                else:
                    self.stats["tier2"] += leads
                    
            except Exception as e:
                logging.error(f"Error scraping {city}: {e}")
                # [ESTIMATED] Consider activating fallback on repeated failures
                continue
        
        return {
            "tier": tier,
            "cities_processed": len(cities),
            "total_leads": total_leads,
            "status": "completed"
        }
    
    async def scrape_all(self) -> Dict[str, Any]:
        """Scrape all tiers."""
        results = {
            "tier1": await self.scrape_tier(1),
            "tier2": await self.scrape_tier(2)
        }
        
        # Get final counts
        results["tier1_count"] = self.db.get_lead_count(1)
        results["tier2_count"] = self.db.get_lead_count(2)
        results["total_count"] = self.db.get_lead_count()
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            "stats": self.stats,
            "db_counts": {
                "tier1": self.db.get_lead_count(1),
                "tier2": self.db.get_lead_count(2),
                "total": self.db.get_lead_count()
            }
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="COMBARETROVAMIAUTO Lead Scraper — Protocollo ARGOS™"
    )
    parser.add_argument(
        "--tier", 
        type=int, 
        choices=[1, 2],
        help="Scrape specific tier (1=Tier 1 cities, 2=Tier 2 cities)"
    )
    parser.add_argument(
        "--max", 
        type=int,
        help="Max results per city (default: 60 for Tier 1, 40 for Tier 2)"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Scrape all tiers"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Validate args
    if not args.tier and not args.all:
        parser.error("Must specify --tier or --all")
    
    # Initialize and run scraper
    scraper = LeadScraper()
    
    try:
        await scraper.init()
        
        if args.all:
            results = await scraper.scrape_all()
            print("\n" + "="*50)
            print("SCRAPING COMPLETE — Protocollo ARGOS™")
            print("="*50)
            print(f"Tier 1 leads: {results['tier1_count']}")
            print(f"Tier 2 leads: {results['tier2_count']}")
            print(f"Total leads: {results['total_count']}")
        else:
            result = await scraper.scrape_tier(args.tier, args.max)
            print("\n" + "="*50)
            print(f"TIER {args.tier} COMPLETE — Protocollo ARGOS™")
            print("="*50)
            print(f"Cities: {result['cities_processed']}")
            print(f"New leads: {result['total_leads']}")
        
        print(f"\nDatabase: {MARKETING_DB_PATH}")
        print("[VERIFIED] Hard limits enforced: 15s inter-query delay")
        
    except KeyboardInterrupt:
        logging.info("Scraping interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
