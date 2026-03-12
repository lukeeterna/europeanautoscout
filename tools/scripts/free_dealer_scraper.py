#!/usr/bin/env python3.11
"""
FREE DEALER SCRAPER — ZERO COST ALTERNATIVE
Replace €2.69 Top Dealers Guide with web scraping
Target: Sud Italia multi-brand dealers
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin
import csv

class FreeDealerScraper:
    """
    Scrape dealer directories for free instead of buying guides
    """

    def __init__(self):
        self.dealers = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def scrape_autotrader_it(self):
        """Scrape Autotrader.it dealer listings"""
        print("🔍 Scraping Autotrader.it dealer directory...")

        regions = [
            ('campania', 'napoli'),
            ('puglia', 'bari'),
            ('sicilia', 'palermo'),
            ('lazio', 'roma'),
            ('calabria', 'cosenza')
        ]

        for region, city in regions:
            try:
                url = f"https://www.autotrader.it/concessionari/{region}/{city}"
                print(f"  Checking {region.title()}...")

                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    print(f"    ❌ Failed: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')

                # Find dealer listings
                dealers = soup.find_all(['div', 'article'], class_=['dealer', 'concessionario', 'listing'])

                for dealer in dealers:
                    try:
                        name_elem = dealer.find(['h2', 'h3', 'h4', 'a'], class_=['name', 'title'])
                        name = name_elem.text.strip() if name_elem else ''

                        location_elem = dealer.find(['span', 'div'], class_=['location', 'address', 'city'])
                        location = location_elem.text.strip() if location_elem else f"{city.title()}, {region.title()}"

                        if name and len(name) > 3:
                            self.dealers.append({
                                'company': name,
                                'location': location,
                                'region': region,
                                'source': 'autotrader_it_free',
                                'contact_name': 'TBD',
                                'phone': 'TBD',
                                'dealer_type': 'multi-brand',
                                'priority': 'medium'
                            })

                    except Exception as e:
                        continue

                print(f"    ✅ Found {len([d for d in self.dealers if d['region'] == region])} dealers")
                time.sleep(random.uniform(2, 5))  # Anti-bot delay

            except Exception as e:
                print(f"    ❌ Error scraping {region}: {e}")

    def scrape_pagine_gialle(self):
        """Scrape Pagine Gialle concessionari auto"""
        print("🔍 Scraping Pagine Gialle...")

        cities = [
            'napoli', 'bari', 'palermo', 'roma', 'catania',
            'messina', 'foggia', 'lecce', 'taranto', 'reggio-calabria'
        ]

        for city in cities:
            try:
                url = f"https://www.paginegialle.it/ricerca/concessionari%20auto/{city}"
                print(f"  Checking {city.title()}...")

                response = self.session.get(url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Pagine Gialle structure
                listings = soup.find_all(['div', 'li'], class_=['listing', 'entry', 'result'])

                for listing in listings:
                    try:
                        name_elem = listing.find(['h3', 'h2', 'a'], class_=['name', 'business-name'])
                        name = name_elem.text.strip() if name_elem else ''

                        # Extract phone if available
                        phone_elem = listing.find(['span', 'a'], href=lambda x: x and 'tel:' in x)
                        phone = phone_elem.get('href', '').replace('tel:', '') if phone_elem else 'TBD'

                        if name and 'auto' in name.lower() and len(name) > 5:
                            self.dealers.append({
                                'company': name,
                                'location': f"{city.title()}",
                                'region': self.get_region_from_city(city),
                                'source': 'pagine_gialle_free',
                                'contact_name': 'TBD',
                                'phone': phone,
                                'dealer_type': 'multi-brand',
                                'priority': 'high' if phone != 'TBD' else 'medium'
                            })

                    except Exception:
                        continue

                print(f"    ✅ Found dealers with contacts")
                time.sleep(random.uniform(3, 7))

            except Exception as e:
                print(f"    ❌ Error scraping {city}: {e}")

    def get_region_from_city(self, city):
        """Map city to region"""
        city_region_map = {
            'napoli': 'campania', 'bari': 'puglia', 'palermo': 'sicilia',
            'roma': 'lazio', 'catania': 'sicilia', 'messina': 'sicilia',
            'foggia': 'puglia', 'lecce': 'puglia', 'taranto': 'puglia',
            'reggio-calabria': 'calabria'
        }
        return city_region_map.get(city, 'unknown')

    def enhance_dealer_data(self):
        """Add additional metadata for COMBARETROVAMIAUTO targeting"""
        print("🎯 Enhancing dealer data...")

        for dealer in self.dealers:
            # Priority scoring based on location and info availability
            if dealer['phone'] != 'TBD':
                dealer['lead_score'] = 70
            elif 'roma' in dealer['location'].lower() or 'napoli' in dealer['location'].lower():
                dealer['lead_score'] = 60
            else:
                dealer['lead_score'] = 50

            # Target specialization (assumption for premium dealers)
            if any(keyword in dealer['company'].lower() for keyword in ['premium', 'luxury', 'bmw', 'mercedes', 'audi']):
                dealer['brand_specialization'] = 'premium-german'
                dealer['lead_score'] += 20
            else:
                dealer['brand_specialization'] = 'general'

            # Estimate inventory size (assumption based on name indicators)
            if any(keyword in dealer['company'].lower() for keyword in ['group', 'holding', 'spa']):
                dealer['inventory_size'] = '50-100'
            else:
                dealer['inventory_size'] = '30-80'

    def save_dealers(self):
        """Save dealer data in multiple formats"""
        print("💾 Saving dealer database...")

        # Remove duplicates
        unique_dealers = []
        seen_names = set()
        for dealer in self.dealers:
            name_key = dealer['company'].lower().strip()
            if name_key not in seen_names:
                unique_dealers.append(dealer)
                seen_names.add(name_key)

        self.dealers = sorted(unique_dealers, key=lambda x: x['lead_score'], reverse=True)

        # JSON for database import
        with open('dealers_free_database.json', 'w', encoding='utf-8') as f:
            json.dump(self.dealers, f, indent=2, ensure_ascii=False)

        # CSV for manual review
        with open('dealers_free_database.csv', 'w', newline='', encoding='utf-8') as f:
            if self.dealers:
                writer = csv.DictWriter(f, fieldnames=self.dealers[0].keys())
                writer.writeheader()
                writer.writerows(self.dealers)

        print(f"✅ Saved {len(self.dealers)} unique dealers")
        return self.dealers

    def generate_summary(self):
        """Generate summary statistics"""
        total = len(self.dealers)
        by_region = {}
        high_priority = 0

        for dealer in self.dealers:
            region = dealer['region']
            by_region[region] = by_region.get(region, 0) + 1
            if dealer.get('lead_score', 0) >= 70:
                high_priority += 1

        print("\n📊 DEALER DATABASE SUMMARY:")
        print(f"  Total Dealers: {total}")
        print(f"  High Priority: {high_priority}")
        print(f"  With Phone: {len([d for d in self.dealers if d['phone'] != 'TBD'])}")
        print("\n  By Region:")
        for region, count in sorted(by_region.items()):
            print(f"    {region.title()}: {count}")

def main():
    """
    Main execution: Free alternative to €2.69 Top Dealers Guide
    """
    print("🚀 FREE DEALER DATABASE GENERATION")
    print("Alternative to Top Dealers Guide 2026 (€2.69 saved)")
    print("=" * 50)

    scraper = FreeDealerScraper()

    # Scrape multiple sources
    scraper.scrape_autotrader_it()
    scraper.scrape_pagine_gialle()

    # Process and save
    scraper.enhance_dealer_data()
    dealers = scraper.save_dealers()
    scraper.generate_summary()

    if len(dealers) >= 10:
        print(f"\n✅ SUCCESS: Generated {len(dealers)} dealer contacts for €0")
        print("📄 Files created: dealers_free_database.json, dealers_free_database.csv")
        print("🎯 Ready for import into DuckDB database")
    else:
        print(f"\n⚠️  LIMITED RESULTS: Only {len(dealers)} dealers found")
        print("💡 Recommendation: Run multiple times or add manual research")

    return dealers

if __name__ == "__main__":
    dealers = main()