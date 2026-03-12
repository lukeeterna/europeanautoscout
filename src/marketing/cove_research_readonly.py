#!/usr/bin/env python3
"""
COMBARETROVAMIAUTO — CoVe Research Read-Only Mode
Protocollo ARGOS™ | CoVe 2026 | Deep research senza database lock

Quick research per titolari autosaloni, output JSON (no database write).
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Import core classes from main module
import sys
sys.path.append(str(Path(__file__).parent))

from cove_dealer_research import CoVeResearcher, OwnerContact

# Test dealers data (manually extracted)
NAPOLI_DEALERS = [
    {
        'name': 'Mariauto Srl Concessionario Auto',
        'website': 'https://www.mariauto.it',
        'city': 'Napoli'
    },
    {
        'name': 'Centro Automobili Premium',
        'website': 'https://www.centroautomobilipremium.it',
        'city': 'Napoli'
    },
    {
        'name': 'Autouno Peugeot Napoli',
        'website': 'https://www.autouno.it',
        'city': 'Casoria'
    }
]

async def research_dealers_readonly(dealers_list: list, max_dealers: int = 3):
    """Research dealers without database operations."""

    researcher = CoVeResearcher()
    results = []

    print(f"🔍 CoVe Research per {min(len(dealers_list), max_dealers)} dealer...")
    print("📊 Read-only mode (no database writes)")
    print()

    for i, dealer in enumerate(dealers_list[:max_dealers]):
        dealer_name = dealer['name']
        website = dealer['website']
        city = dealer['city']

        print(f"🎯 Researching {i+1}/{max_dealers}: {dealer_name}")

        try:
            contact = await researcher.research_owner(dealer_name, website, city)

            result = {
                'dealer': dealer_name,
                'city': city,
                'website': website,
                'owner_name': contact.name,
                'owner_title': contact.title,
                'phone_direct': contact.phone_direct,
                'confidence': contact.confidence,
                'research_notes': contact.research_notes,
                'timestamp': datetime.now().isoformat()
            }

            results.append(result)

            # Display result
            if contact.name:
                print(f"  👤 Owner: {contact.name} ({contact.title or 'Titolare'})")
                if contact.phone_direct:
                    print(f"  📱 Phone: {contact.phone_direct}")
                print(f"  📊 Confidence: {contact.confidence:.1%}")
                if contact.research_notes:
                    print(f"  📝 Notes: {contact.research_notes[:80]}...")
            else:
                print(f"  ❌ No owner info found")

            print()

            # Rate limiting
            await asyncio.sleep(2)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                'dealer': dealer_name,
                'city': city,
                'website': website,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

    return results

async def main():
    """Main function for read-only CoVe research."""

    print("🏆 CoVe Deep Research - Read-Only Mode")
    print("Protocollo ARGOS™ | Numeri diretti titolari autosaloni")
    print("=" * 60)

    # Run research
    results = await research_dealers_readonly(NAPOLI_DEALERS, max_dealers=3)

    print("🏆 RESEARCH COMPLETED")
    print(f"✅ Processed: {len(results)} dealer")

    # Summary
    successful = [r for r in results if 'owner_name' in r and r['owner_name']]
    with_phone = [r for r in successful if r.get('phone_direct')]

    print(f"📊 Owner info found: {len(successful)}/{len(results)}")
    print(f"📱 Direct phones: {len(with_phone)}/{len(results)}")

    if with_phone:
        print("\n🎯 DIRECT CONTACTS FOUND:")
        for r in with_phone:
            print(f"  {r['dealer'][:35]} | {r['owner_name']} | {r['phone_direct']}")

    # Save results
    output_file = f"cove_research_readonly_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Results saved: {output_file}")
    print("✅ Ready for WhatsApp outreach!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())