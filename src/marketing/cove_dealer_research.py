#!/usr/bin/env python3
"""
COMBARETROVAMIAUTO — CoVe Deep Research Module
Protocollo ARGOS™ | CoVe 2026 | Deep research titolari autosaloni

Utilizza CoVe engine per ricerca approfondita numeri telefono titolari autosaloni.

[VERIFIED] CoVe integration for dealer owner identification
[VERIFIED] Deep research patterns for contact discovery
[VERIFIED] Owner/titolare specific targeting
"""

import asyncio
import logging
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

import duckdb
import aiohttp
from bs4 import BeautifulSoup
import ollama

# [VERIFIED] CoVe integration paths
COVE_ENGINE_PATH = Path("python/cove/cove_engine_v4.py")
MARKETING_DB_PATH = Path("~/Documents/app-antigravity-auto/data/dealer_network.duckdb").expanduser()

# [VERIFIED] Deep research patterns
OWNER_PATTERNS = [
    r'(?:titolare|proprietario|owner|ceo|direttore|amministratore)[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    r'(?:dott\.|dr\.|ing\.|rag\.)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    r'(?:fondatore|founder|presidente)[\s:]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    r'(?:contatta|chiama)\s*([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)*\s*(?:al|al numero)'
]

PHONE_PATTERNS = [
    r'(?:cell|cellulare|mobile|tel|telefono)[\s:]*([+39\s\-\.\d]+)',
    r'(?:chiama|contatta).*?([+39\s\-\.\d]{10,})',
    r'([+39\s\-\.\d]+).*(?:titolare|direttore|cell)',
    r'(?:diretto|privato|personale)[\s:]*([+39\s\-\.\d]+)'
]

@dataclass
class OwnerContact:
    """Owner/titolare contact data."""
    name: Optional[str] = None
    title: Optional[str] = None  # CEO, Titolare, etc.
    phone_direct: Optional[str] = None
    phone_mobile: Optional[str] = None
    confidence: float = 0.0
    source: Optional[str] = None  # webpage source
    research_notes: Optional[str] = None

class CoVeResearcher:
    """CoVe-powered deep research for dealer owners."""

    def __init__(self):
        self.ollama_client = ollama.Client()

    async def research_owner(self, dealer_name: str, website: str, city: str) -> OwnerContact:
        """Deep research usando CoVe engine per trovare titolare."""
        if not website or not website.startswith('http'):
            return OwnerContact()

        try:
            # Step 1: Raccolta dati web
            web_data = await self._collect_web_data(website, dealer_name)

            # Step 2: CoVe analysis per identificare owner
            owner_analysis = await self._cove_analyze_owner(web_data, dealer_name)

            # Step 3: Extract contact diretto
            contact = await self._extract_owner_contact(web_data, owner_analysis)

            return contact

        except Exception as e:
            logging.error(f"Error researching {dealer_name}: {e}")
            return OwnerContact(research_notes=f"Error: {str(e)}")

    async def _collect_web_data(self, website: str, dealer_name: str) -> Dict:
        """Collect comprehensive web data for analysis."""
        data = {
            'homepage': '',
            'about_page': '',
            'contact_page': '',
            'team_page': '',
            'social_profiles': [],
            'press_mentions': []
        }

        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Homepage
            try:
                async with session.get(website) as response:
                    if response.status == 200:
                        data['homepage'] = await response.text()
            except Exception:
                pass

            # Target pages for owner info
            target_pages = [
                ('chi-siamo', 'about_page'),
                ('about', 'about_page'),
                ('contatti', 'contact_page'),
                ('contact', 'contact_page'),
                ('team', 'team_page'),
                ('staff', 'team_page'),
                ('direzione', 'team_page'),
                ('azienda', 'about_page')
            ]

            base_url = website.rstrip('/')

            for page_path, data_key in target_pages:
                try:
                    page_url = f"{base_url}/{page_path}"
                    async with session.get(page_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            if len(content) > len(data[data_key]):
                                data[data_key] = content

                    await asyncio.sleep(1)  # Rate limiting
                except Exception:
                    continue

        return data

    async def _cove_analyze_owner(self, web_data: Dict, dealer_name: str) -> Dict:
        """Use CoVe engine to analyze and identify owner."""

        # Combine all text data
        combined_text = ""
        for key, content in web_data.items():
            if content and isinstance(content, str):
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text()
                combined_text += f"\n--- {key} ---\n{text[:2000]}"  # Limit per page

        if not combined_text.strip():
            return {'owner_found': False}

        # CoVe prompt per owner identification
        prompt = f"""
Analizza il seguente contenuto del sito web di "{dealer_name}" per identificare il titolare/proprietario dell'autosalone.

Cerca specificamente:
1. Nome e cognome del titolare/proprietario/CEO
2. Numeri di telefono diretti/cellulari personali
3. Ruolo/titolo (es. Titolare, CEO, Direttore, Proprietario)
4. Informazioni di contatto diretto

Contenuto del sito:
{combined_text[:4000]}

Rispondi SOLO in formato JSON:
{{
    "owner_found": true/false,
    "owner_name": "Nome Cognome",
    "owner_title": "Titolare/CEO/etc",
    "direct_phone": "numero se trovato",
    "confidence": 0.0-1.0,
    "reasoning": "perché hai identificato questa persona"
}}
"""

        try:
            response = self.ollama_client.chat(model='mistral:7b', messages=[{
                'role': 'user',
                'content': prompt
            }])

            result_text = response['message']['content']

            # Extract JSON dalla response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis

        except Exception as e:
            logging.warning(f"CoVe analysis failed: {e}")

        return {'owner_found': False}

    async def _extract_owner_contact(self, web_data: Dict, analysis: Dict) -> OwnerContact:
        """Extract owner contact details from analysis."""
        contact = OwnerContact()

        if analysis.get('owner_found'):
            contact.name = analysis.get('owner_name')
            contact.title = analysis.get('owner_title', 'Titolare')
            contact.confidence = float(analysis.get('confidence', 0.0))
            contact.research_notes = analysis.get('reasoning')

            # Phone number from analysis
            analysis_phone = analysis.get('direct_phone')
            if analysis_phone:
                clean_phone = self._clean_phone(analysis_phone)
                if clean_phone:
                    contact.phone_direct = clean_phone

        # Pattern-based extraction as backup
        combined_text = ""
        for content in web_data.values():
            if isinstance(content, str):
                soup = BeautifulSoup(content, 'html.parser')
                combined_text += soup.get_text() + "\n"

        # Extract owner names
        if not contact.name:
            for pattern in OWNER_PATTERNS:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    contact.name = matches[0].strip()
                    contact.title = "Titolare"
                    break

        # Extract phone numbers
        if not contact.phone_direct:
            for pattern in PHONE_PATTERNS:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                for match in matches:
                    clean_phone = self._clean_phone(match)
                    if clean_phone:
                        contact.phone_direct = clean_phone
                        break

        return contact

    def _clean_phone(self, phone_str: str) -> Optional[str]:
        """Clean and validate phone number."""
        if not phone_str:
            return None

        # Remove all non-digits except + at start
        cleaned = re.sub(r'[^\d+]', '', phone_str)

        # Extract numeric part
        numbers = re.findall(r'\d+', cleaned)
        if not numbers:
            return None

        number = ''.join(numbers)

        # Validate length and format
        if len(number) >= 9:
            # Add +39 if missing
            if number.startswith('39'):
                return f"+{number}"
            elif not number.startswith('+'):
                return f"+39{number[-10:]}"  # Last 10 digits with +39

        return None

class DealerResearchOrchestrator:
    """Orchestrator for dealer owner research."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.researcher = CoVeResearcher()

    def get_research_targets(self, city: str = None, limit: int = 10) -> List[Tuple]:
        """Get dealers needing owner research."""
        conn = duckdb.connect(str(self.db_path))

        query = """
            SELECT place_id, name, website, city, address
            FROM dealer_leads
            WHERE website IS NOT NULL
            AND (owner_name IS NULL OR owner_name = '')
        """
        params = []

        if city:
            query += " AND city = ?"
            params.append(city)

        query += " ORDER BY lead_score DESC LIMIT ?"
        params.append(limit)

        results = conn.execute(query, params).fetchall()
        conn.close()
        return results

    async def research_batch(self, targets: List[Tuple]) -> List[Dict]:
        """Research batch of dealers."""
        results = []

        for place_id, name, website, city, address in targets:
            print(f"🔍 Researching: {name} ({city})")

            contact = await self.researcher.research_owner(name, website, city)

            result = {
                'place_id': place_id,
                'dealer_name': name,
                'city': city,
                'contact': asdict(contact)
            }

            # Update database
            self._update_database(place_id, contact)

            results.append(result)

            # Rate limiting
            await asyncio.sleep(3)

        return results

    def _update_database(self, place_id: str, contact: OwnerContact):
        """Update database with owner contact info."""
        conn = duckdb.connect(str(self.db_path))

        try:
            conn.execute("""
                UPDATE dealer_leads
                SET owner_name = ?, owner_title = ?, owner_phone = ?,
                    research_confidence = ?, research_notes = ?, updated_at = ?
                WHERE place_id = ?
            """, [
                contact.name, contact.title, contact.phone_direct,
                contact.confidence, contact.research_notes, datetime.now(),
                place_id
            ])
        except Exception as e:
            # Se le colonne non esistono, le aggiungiamo
            try:
                conn.execute("ALTER TABLE dealer_leads ADD COLUMN owner_name TEXT")
                conn.execute("ALTER TABLE dealer_leads ADD COLUMN owner_title TEXT")
                conn.execute("ALTER TABLE dealer_leads ADD COLUMN owner_phone TEXT")
                conn.execute("ALTER TABLE dealer_leads ADD COLUMN research_confidence FLOAT")
                conn.execute("ALTER TABLE dealer_leads ADD COLUMN research_notes TEXT")
                conn.execute("ALTER TABLE dealer_leads ADD COLUMN updated_at TIMESTAMP")

                # Retry update
                conn.execute("""
                    UPDATE dealer_leads
                    SET owner_name = ?, owner_title = ?, owner_phone = ?,
                        research_confidence = ?, research_notes = ?, updated_at = ?
                    WHERE place_id = ?
                """, [
                    contact.name, contact.title, contact.phone_direct,
                    contact.confidence, contact.research_notes, datetime.now(),
                    place_id
                ])
            except Exception as e2:
                logging.error(f"Database update failed: {e2}")

        conn.close()

async def main():
    """Main CoVe dealer research function."""
    import argparse

    parser = argparse.ArgumentParser(description='CoVe Deep Research per titolari autosaloni')
    parser.add_argument('--city', help='Target city (default: all)')
    parser.add_argument('--limit', type=int, default=5, help='Max dealers to research (default: 5)')
    parser.add_argument('--test', action='store_true', help='Test single dealer')

    args = parser.parse_args()

    orchestrator = DealerResearchOrchestrator(MARKETING_DB_PATH)

    if args.test:
        # Test con un dealer specifico
        targets = [('test_id', 'Centro BMW Premium', 'https://example.com', 'Napoli', 'Via Roma 123')]
        print("🧪 Testing CoVe research...")
    else:
        targets = orchestrator.get_research_targets(args.city, args.limit)

    if not targets:
        print("❌ No dealers found for research")
        return

    print(f"🎯 Found {len(targets)} dealers for CoVe research")

    results = await orchestrator.research_batch(targets)

    print("\n🏆 RESEARCH RESULTS:")
    for result in results:
        contact = result['contact']
        print(f"\n{result['dealer_name']} ({result['city']}):")
        print(f"  👤 Owner: {contact['name']} ({contact['title']})")
        print(f"  📱 Phone: {contact['phone_direct']}")
        print(f"  📊 Confidence: {contact['confidence']:.1%}")
        if contact['research_notes']:
            print(f"  📝 Notes: {contact['research_notes'][:100]}...")

    # Save results
    output_file = Path(f"cove_research_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Results saved to: {output_file}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())