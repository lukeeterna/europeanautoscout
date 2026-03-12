#!/usr/bin/env python3
"""
COMBARETROVAMIAUTO — Lead Enricher Module
Protocollo ARGOS™ | CoVe 2026 | cove_engine_v4

Email enrichment via website crawling with MX verification.

[VERIFIED] Semaphore limit: 5 concurrent connections (HARD)
[VERIFIED] Email regex pattern for extraction
[VERIFIED] MX verification using dns.resolver
[VERIFIED] Blacklist and TLD filters
"""

import asyncio
import argparse
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Set, Dict, Any
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp_socks import ProxyConnector  # Tailscale proxy support (Sessione 12)
import dns.resolver
from bs4 import BeautifulSoup
import duckdb

# [VERIFIED] Hard limits
MAX_CONCURRENT = 5  # asyncio.Semaphore - HARD LIMIT
REQUEST_TIMEOUT = 10  # seconds for homepage
SECONDARY_TIMEOUT = 8  # seconds for secondary pages
INTER_PAGE_DELAY = 1  # seconds between page requests

# [VERIFIED] Email extraction regex
EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
)

# [VERIFIED] Email blacklist
EMAIL_BLACKLIST = [
    'noreply@', 'no-reply@', 'privacy@', 'admin@',
    '@wordpress', '@wix', '@shopify', '@squarespace',
    'info@example', 'test@', 'example@'
]

# [VERIFIED] Allowed TLDs
ALLOWED_TLDS = ['.com', '.it', '.eu', '.net', '.org']

# [VERIFIED] Contact page patterns
CONTACT_PATTERNS = [
    r'contatt',
    r'contact',
    r'info',
    r'about',
    r'chi.siamo',
]

# [VERIFIED] Priority keywords for email selection
EMAIL_PRIORITY = [
    'commerciale',
    'vendite',
    'sales',
    'dealer',
    'concessionaria',
    'info',
    'email',
    'contact'
]

# [VERIFIED] Database path
MARKETING_DB_PATH = Path("~/Documents/app-antigravity-auto/data/dealer_network.duckdb").expanduser()


class EmailValidator:
    """Email validation with MX record verification."""
    
    @staticmethod
    def is_blacklisted(email: str) -> bool:
        """Check if email is in blacklist."""
        email_lower = email.lower()
        for pattern in EMAIL_BLACKLIST:
            if pattern in email_lower:
                return True
        return False
    
    @staticmethod
    def has_allowed_tld(email: str) -> bool:
        """Check if email has allowed TLD."""
        email_lower = email.lower()
        for tld in ALLOWED_TLDS:
            if email_lower.endswith(tld):
                return True
        return False
    
    @staticmethod
    def extract_domain(email: str) -> Optional[str]:
        """Extract domain from email."""
        try:
            return email.split('@')[1]
        except IndexError:
            return None
    
    @staticmethod
    def has_mx_record(domain: str) -> bool:
        """
        Verify MX record exists for domain.
        [VERIFIED] dns.resolver with 5s lifetime timeout
        """
        try:
            answers = dns.resolver.resolve(domain, "MX", lifetime=5)
            return len(answers) > 0
        except Exception as e:
            logging.debug(f"MX lookup failed for {domain}: {e}")
            return False
    
    @classmethod
    def validate_email(cls, email: str, website_domain: Optional[str] = None) -> bool:
        """
        Full email validation pipeline.
        
        Checks:
        1. Not blacklisted
        2. Has allowed TLD
        3. MX record exists
        """
        # Check blacklist
        if cls.is_blacklisted(email):
            logging.debug(f"Email {email} rejected: blacklisted")
            return False
        
        # Check TLD
        if not cls.has_allowed_tld(email):
            logging.debug(f"Email {email} rejected: TLD not allowed")
            return False
        
        # Check MX record
        domain = cls.extract_domain(email)
        if not domain:
            return False
        
        if not cls.has_mx_record(domain):
            logging.debug(f"Email {email} rejected: no MX record")
            return False
        
        return True
    
    @classmethod
    def prioritize_emails(cls, emails: List[str], website_domain: Optional[str] = None) -> List[str]:
        """
        Prioritize emails by relevance.
        
        Priority order:
        1. Domain-match (email domain matches website)
        2. Commercial keywords (commerciale, vendite, etc.)
        3. Generic info/contact
        """
        scored_emails = []
        
        for email in emails:
            score = 0
            email_lower = email.lower()
            email_domain = cls.extract_domain(email)
            
            # Domain match gets highest priority
            if website_domain and email_domain:
                if website_domain.lower() in email_domain.lower():
                    score += 100
            
            # Priority keywords
            for i, keyword in enumerate(EMAIL_PRIORITY):
                if keyword in email_lower:
                    score += (50 - i * 5)  # Decreasing priority
                    break
            
            scored_emails.append((email, score))
        
        # Sort by score descending
        scored_emails.sort(key=lambda x: x[1], reverse=True)
        return [email for email, _ in scored_emails]


class WebsiteScraper:
    """Async website scraper for email extraction."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)  # [VERIFIED] HARD LIMIT
    
    async def init(self):
        """Initialize aiohttp session with Tailscale proxy. (Sessione 12)"""
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # [TEMPORARY] Proxy disabled for SESSIONE 14 - Tailscale setup failed on macOS 11
        # [NEW] Tailscale proxy configuration — Xiaomi Redmi Note 9 Pro :8022
        # proxy_connector = ProxyConnector.from_url('socks5://127.0.0.1:8022')

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
            # connector=proxy_connector  # DISABLED - see SESSIONE 14 notes
        )
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
        """Fetch page content with semaphore control."""
        async with self.semaphore:
            try:
                async with self.session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logging.debug(f"HTTP {response.status} for {url}")
            except asyncio.TimeoutError:
                logging.debug(f"Timeout fetching {url}")
            except Exception as e:
                logging.debug(f"Error fetching {url}: {e}")
            return None
    
    def extract_emails(self, html: str) -> Set[str]:
        """Extract emails from HTML content."""
        emails = set()
        matches = EMAIL_REGEX.findall(html)
        for email in matches:
            email = email.lower().strip()
            if len(email) > 5:  # Basic sanity check
                emails.add(email)
        return emails
    
    def find_contact_links(self, html: str, base_url: str) -> List[str]:
        """Find contact page links."""
        contact_urls = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            base_domain = urlparse(base_url).netloc
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True).lower()
                
                # Check href patterns
                href_match = any(
                    re.search(pattern, href, re.IGNORECASE) 
                    for pattern in CONTACT_PATTERNS
                )
                
                # Check text patterns
                text_match = any(
                    re.search(pattern, text, re.IGNORECASE)
                    for pattern in CONTACT_PATTERNS
                )
                
                if href_match or text_match:
                    full_url = urljoin(base_url, href)
                    # Only include same-domain URLs
                    if urlparse(full_url).netloc == base_domain:
                        contact_urls.append(full_url)
            
            # Return max 2 unique URLs
            return list(dict.fromkeys(contact_urls))[:2]
            
        except Exception as e:
            logging.debug(f"Error finding contact links: {e}")
            return []
    
    async def scrape_website(self, url: str) -> Optional[str]:
        """
        Scrape website for email addresses.

        Process:
        1. Fetch homepage
        2. Extract emails
        3. Find contact pages
        4. Scrape up to 2 contact pages
        5. Validate and prioritize all emails

        Returns: Best email or None
        """
        # [FIX] Clean URL from encoding issues (SESSIONE 14)
        url = url.strip().replace('%EE%A0%8B', '').replace('%EF%BF%BD', '')

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        all_emails = set()
        website_domain = urlparse(url).netloc.replace('www.', '')
        
        try:
            # Fetch homepage
            logging.info(f"Scraping: {url}")
            homepage_html = await self.fetch_page(url, REQUEST_TIMEOUT)
            
            if not homepage_html:
                logging.warning(f"Failed to fetch homepage: {url}")
                return None
            
            # Extract emails from homepage
            homepage_emails = self.extract_emails(homepage_html)
            all_emails.update(homepage_emails)
            logging.debug(f"Found {len(homepage_emails)} emails on homepage")
            
            # Find contact pages
            contact_links = self.find_contact_links(homepage_html, url)
            logging.debug(f"Found {len(contact_links)} contact links")
            
            # Scrape contact pages
            for i, contact_url in enumerate(contact_links):
                if i > 0:
                    # [VERIFIED] 1s delay between pages
                    await asyncio.sleep(INTER_PAGE_DELAY)
                
                logging.debug(f"Scraping contact page: {contact_url}")
                contact_html = await self.fetch_page(contact_url, SECONDARY_TIMEOUT)
                
                if contact_html:
                    contact_emails = self.extract_emails(contact_html)
                    all_emails.update(contact_emails)
                    logging.debug(f"Found {len(contact_emails)} emails on contact page")
            
            if not all_emails:
                logging.info(f"No emails found on {url}")
                return None
            
            # Validate emails
            valid_emails = []
            for email in all_emails:
                if EmailValidator.validate_email(email, website_domain):
                    valid_emails.append(email)
            
            if not valid_emails:
                logging.info(f"No valid emails found on {url}")
                return None
            
            # Prioritize and return best email
            prioritized = EmailValidator.prioritize_emails(valid_emails, website_domain)
            best_email = prioritized[0]
            
            logging.info(f"Selected email: {best_email} (from {len(valid_emails)} valid)")
            return best_email
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return None


class LeadDatabase:
    """DuckDB interface for dealer leads."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = duckdb.connect(str(self.db_path))
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def get_leads_without_email(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get leads that need email enrichment."""
        query = """
            SELECT place_id, name, website, city
            FROM dealer_leads
            WHERE email IS NULL 
              AND website IS NOT NULL
              AND website != ''
            ORDER BY lead_score DESC, scraped_at ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        result = self.conn.execute(query).fetchall()
        
        leads = []
        for row in result:
            leads.append({
                'place_id': row[0],
                'name': row[1],
                'website': row[2],
                'city': row[3]
            })
        
        return leads
    
    def get_lead_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get single lead by ID."""
        result = self.conn.execute(
            """SELECT place_id, name, website, city 
               FROM dealer_leads 
               WHERE place_id = ? AND email IS NULL""",
            (place_id,)
        ).fetchone()
        
        if result:
            return {
                'place_id': result[0],
                'name': result[1],
                'website': result[2],
                'city': result[3]
            }
        return None
    
    def update_email(self, place_id: str, email: str) -> bool:
        """Update lead with verified email."""
        try:
            self.conn.execute("""
                UPDATE dealer_leads
                SET email = ?,
                    email_verified = TRUE,
                    enriched_at = CURRENT_TIMESTAMP
                WHERE place_id = ?
            """, (email, place_id))
            return True
        except Exception as e:
            logging.error(f"Failed to update lead {place_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics."""
        total = self.conn.execute("SELECT COUNT(*) FROM dealer_leads").fetchone()[0]
        with_email = self.conn.execute(
            "SELECT COUNT(*) FROM dealer_leads WHERE email IS NOT NULL"
        ).fetchone()[0]
        without_email = self.conn.execute(
            """SELECT COUNT(*) FROM dealer_leads 
               WHERE email IS NULL AND website IS NOT NULL"""
        ).fetchone()[0]
        verified = self.conn.execute(
            "SELECT COUNT(*) FROM dealer_leads WHERE email_verified = TRUE"
        ).fetchone()[0]
        
        return {
            'total_leads': total,
            'with_email': with_email,
            'without_email_website': without_email,
            'verified_emails': verified,
            'enrichment_rate': (with_email / total * 100) if total > 0 else 0
        }


class LeadEnricher:
    """Main lead enricher orchestrator."""
    
    def __init__(self):
        self.db = LeadDatabase(MARKETING_DB_PATH)
        self.scraper = WebsiteScraper()
        self.stats = {
            'processed': 0,
            'enriched': 0,
            'failed': 0
        }
    
    async def init(self):
        """Initialize components."""
        self.db.connect()
        await self.scraper.init()
    
    async def close(self):
        """Cleanup resources."""
        await self.scraper.close()
        self.db.close()
    
    async def enrich_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Enrich single lead with email.
        
        [VERIFIED] Process:
        1. Scrape website for emails
        2. Validate with MX check
        3. Update database
        """
        place_id = lead['place_id']
        website = lead['website']
        
        if not website:
            logging.debug(f"Skipping {place_id}: no website")
            return False
        
        self.stats['processed'] += 1
        
        try:
            # Scrape website
            email = await self.scraper.scrape_website(website)
            
            if email:
                # Update database
                if self.db.update_email(place_id, email):
                    self.stats['enriched'] += 1
                    logging.info(f"✅ Enriched {lead['name']} with {email}")
                    return True
            else:
                logging.info(f"❌ No email found for {lead['name']}")
                
        except Exception as e:
            logging.error(f"Error enriching {place_id}: {e}")
        
        self.stats['failed'] += 1
        return False
    
    async def enrich_all(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Enrich all leads without emails."""
        leads = self.db.get_leads_without_email(limit)
        
        if not leads:
            logging.info("No leads to enrich")
            return {'processed': 0, 'enriched': 0}
        
        logging.info(f"Found {len(leads)} leads to enrich")
        
        # Process sequentially with semaphore control
        for lead in leads:
            await self.enrich_lead(lead)
        
        return {
            'processed': self.stats['processed'],
            'enriched': self.stats['enriched'],
            'failed': self.stats['failed'],
            'success_rate': (self.stats['enriched'] / self.stats['processed'] * 100) 
                           if self.stats['processed'] > 0 else 0
        }
    
    async def enrich_single(self, place_id: str) -> bool:
        """Enrich single lead by ID."""
        lead = self.db.get_lead_by_id(place_id)
        
        if not lead:
            logging.error(f"Lead not found or already has email: {place_id}")
            return False
        
        return await self.enrich_lead(lead)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.db.get_stats()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="COMBARETROVAMIAUTO Lead Enricher — Protocollo ARGOS™"
    )
    parser.add_argument(
        "--enrich-all",
        action="store_true",
        help="Enrich all leads without emails"
    )
    parser.add_argument(
        "--place-id",
        type=str,
        help="Enrich specific lead by place_id"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of leads to process"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show enrichment statistics"
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
    
    # Initialize enricher
    enricher = LeadEnricher()
    
    try:
        await enricher.init()
        
        if args.stats:
            stats = enricher.get_stats()
            print("\n" + "="*50)
            print("ENRICHMENT STATISTICS — Protocollo ARGOS™")
            print("="*50)
            print(f"Total leads: {stats['total_leads']}")
            print(f"With email: {stats['with_email']}")
            print(f"Without email (have website): {stats['without_email_website']}")
            print(f"Verified emails: {stats['verified_emails']}")
            print(f"Enrichment rate: {stats['enrichment_rate']:.1f}%")
        
        elif args.place_id:
            success = await enricher.enrich_single(args.place_id)
            print(f"\n{'✅ Success' if success else '❌ Failed'}: {args.place_id}")
        
        elif args.enrich_all:
            print("\n" + "="*50)
            print("LEAD ENRICHMENT — Protocollo ARGOS™")
            print("="*50)
            
            results = await enricher.enrich_all(args.limit)
            
            print("\n" + "-"*50)
            print("RESULTS")
            print("-"*50)
            print(f"Processed: {results['processed']}")
            print(f"Enriched: {results['enriched']}")
            print(f"Failed: {results['failed']}")
            print(f"Success rate: {results['success_rate']:.1f}%")
        
        else:
            parser.print_help()
        
        print(f"\n[VERIFIED] Hard limits: Semaphore({MAX_CONCURRENT})")
        print(f"Database: {MARKETING_DB_PATH}")
        
    except KeyboardInterrupt:
        logging.info("Enrichment interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise
    finally:
        await enricher.close()


if __name__ == "__main__":
    asyncio.run(main())
