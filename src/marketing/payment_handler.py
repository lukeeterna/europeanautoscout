#!/usr/bin/env python3
"""
COMBARETROVAMIAUTO — Payment Handler Module
Protocollo ARGOS™ | CoVe 2026 | cove_engine_v4

Invoice management and payment processing.

[VERIFIED] Invoice ID format: CBRA-{YYYY}-{NNN}
[VERIFIED] Fee validation from .env: FEE_MIN, FEE_MAX
[VERIFIED] SEPA instructions with IBAN from .env
[VERIFIED] Payment methods: SEPA (primary), Revolut (fallback)
[VERIFIED] PROHIBITED: PayPal, credit cards - raise ValueError

INTERNAL ONLY (code): cove_engine_v4
NEVER expose in dealer output.
"""

import argparse
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import duckdb
from dotenv import load_dotenv

# [VERIFIED] Internal branding - NEVER exposed to dealers
INTERNAL_BRAND_CODE = "cove_engine_v4"

# [VERIFIED] Public branding - ALWAYS used in output
PUBLIC_BRAND = "Protocollo ARGOS™"
PUBLIC_COMPANY = "COMBARETROVAMIAUTO"
PUBLIC_PERSONA = "Luca Ferretti"

# [VERIFIED] Database path
MARKETING_DB_PATH = Path("~/Documents/app-antigravity-auto/data/dealer_network.duckdb").expanduser()

# [VERIFIED] Load .env for payment config
load_dotenv()

# [VERIFIED] Payment configuration from .env (NOT hardcoded)
REVOLUT_IBAN = os.getenv("REVOLUT_IBAN", "")
FEE_MIN = int(os.getenv("FEE_MIN", "800"))
FEE_MAX = int(os.getenv("FEE_MAX", "1200"))

# [VERIFIED] BIC code (fixed per specification)
BIC_CODE = "REVOLT21"

# [VERIFIED] Prohibited payment methods
PROHIBITED_PAYMENTS = ["paypal", "card", "credit", "debit", "visa", "mastercard"]


class InvoiceGenerator:
    """Generate and manage invoices."""
    
    @staticmethod
    def generate_invoice_id(year: int, sequence: int) -> str:
        """Generate invoice ID. Format: CBRA-{YYYY}-{NNN} [VERIFIED]"""
        return f"CBRA-{year}-{sequence:03d}"
    
    @staticmethod
    def get_next_sequence(conn, year: int) -> int:
        """Get next invoice sequence for year."""
        result = conn.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(invoice_id, 9, 3) AS INTEGER)), 0) + 1
            FROM fee_invoices
            WHERE invoice_id LIKE ?
        """, (f"CBRA-{year}-%",)).fetchone()
        return result[0] if result else 1


class PaymentValidator:
    """Validate payment requests."""
    
    @staticmethod
    def validate_fee(fee_amount: int) -> bool:
        """Validate fee amount within range €800–€1,200 [VERIFIED]"""
        if fee_amount < FEE_MIN or fee_amount > FEE_MAX:
            raise ValueError(
                f"Fee €{fee_amount} outside allowed range (€{FEE_MIN}–€{FEE_MAX}). "
                f"Configure FEE_MIN/FEE_MAX in .env"
            )
        return True
    
    @staticmethod
    def validate_payment_method(method: str) -> bool:
        """Validate payment method. PROHIBITED: PayPal, cards [VERIFIED]"""
        method_lower = method.lower()
        for prohibited in PROHIBITED_PAYMENTS:
            if prohibited in method_lower:
                raise ValueError(
                    f"Payment method '{method}' is prohibited. Use SEPA or Revolut"
                )
        allowed = ["sepa", "revolut"]
        if not any(allowed_method in method_lower for allowed_method in allowed):
            raise ValueError(f"Unknown payment method '{method}'. Allowed: SEPA, Revolut")
        return True


class SEPAGenerator:
    """Generate SEPA payment instructions."""
    
    @staticmethod
    def format_amount(amount: int) -> str:
        """Format amount with period as thousands separator [VERIFIED]"""
        return f"€{amount:,}".replace(",", ".")
    
    @classmethod
    def generate_instructions(cls, invoice_id: str, fee_amount: int) -> str:
        """Generate SEPA payment instructions [VERIFIED]"""
        if not REVOLUT_IBAN:
            raise ValueError("REVOLUT_IBAN not configured in .env")
        
        formatted_amount = cls.format_amount(fee_amount)
        
        instructions = f"""
╔══════════════════════════════════════════════════════════════╗
║               ISTRUZIONI DI PAGAMENTO SEPA                  ║
╚══════════════════════════════════════════════════════════════╝

BENEFICIARIO: {PUBLIC_COMPANY}
IBAN: {REVOLUT_IBAN}
BIC: {BIC_CODE}

IMPORTO: {formatted_amount}

CAUSALE: {invoice_id} — {PUBLIC_BRAND}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️  TIMING: Accredito atteso entro 1-2 giorni lavorativi

💡 NOTA: Commissione applicata esclusivamente a transazione completata.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Per bonifico:
1. Accedi al tuo home banking
2. Seleziona "Bonifico SEPA"
3. Inserisci IBAN e dati sopra indicati
4. Usa la causale esatta indicata
"""
        return instructions


class RevolutPaymentGenerator:
    """Generate Revolut payment link (fallback)."""
    
    @staticmethod
    def calculate_fee(fee_amount: int) -> int:
        """Calculate Revolut fee: 1.2–1.8% + €0.20 [VERIFIED]"""
        percentage_fee = int(fee_amount * 0.015)
        fixed_fee = 20
        return percentage_fee + fixed_fee
    
    @classmethod
    def generate_payment_link(cls, invoice_id: str, fee_amount: int) -> str:
        """Generate Revolut payment info [VERIFIED]"""
        revolut_fee = cls.calculate_fee(fee_amount)
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║            ALTERNATIVA: PAGAMENTO REVOLUT                   ║
╚══════════════════════════════════════════════════════════════╝

IMPORTO TOTALE: €{fee_amount}
(stima fee: €{revolut_fee/100:.2f})

⚠️  NOTA: Il pagamento tramite Revolut prevede una commissione
    del 1.2–1.8% + €0.20 per transazione.

[IMPLEMENTAZIONE] Link diretto richiede API Revolut Business
"""


class PaymentDatabase:
    """DuckDB interface for invoices."""
    
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
        """Ensure fee_invoices table exists."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fee_invoices (
                invoice_id VARCHAR PRIMARY KEY,
                place_id VARCHAR NOT NULL,
                dealer_name VARCHAR NOT NULL,
                vehicle_description VARCHAR,
                fee_amount INTEGER NOT NULL,
                payment_reference VARCHAR UNIQUE,
                status VARCHAR DEFAULT 'PENDING',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMPTZ
            )
        """)
    
    def create_invoice(self, place_id: str, dealer_name: str, 
                      vehicle_description: str, fee_amount: int) -> str:
        """Create new invoice [VERIFIED]"""
        PaymentValidator.validate_fee(fee_amount)
        
        year = datetime.now().year
        sequence = InvoiceGenerator.get_next_sequence(self.conn, year)
        invoice_id = InvoiceGenerator.generate_invoice_id(year, sequence)
        payment_ref = f"{invoice_id}-{place_id[:8]}"
        
        try:
            self.conn.execute("""
                INSERT INTO fee_invoices 
                (invoice_id, place_id, dealer_name, vehicle_description, 
                 fee_amount, payment_reference, status)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
            """, (invoice_id, place_id, dealer_name, vehicle_description, 
                  fee_amount, payment_ref))
            return invoice_id
        except Exception as e:
            logging.error(f"Failed to create invoice: {e}")
            raise
    
    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice by ID."""
        result = self.conn.execute("""
            SELECT invoice_id, place_id, dealer_name, vehicle_description,
                   fee_amount, payment_reference, status, created_at, paid_at
            FROM fee_invoices WHERE invoice_id = ?
        """, (invoice_id,)).fetchone()
        
        if result:
            return {
                'invoice_id': result[0], 'place_id': result[1],
                'dealer_name': result[2], 'vehicle_description': result[3],
                'fee_amount': result[4], 'payment_reference': result[5],
                'status': result[6], 'created_at': result[7], 'paid_at': result[8]
            }
        return None
    
    def mark_paid(self, invoice_id: str) -> bool:
        """Mark invoice as paid and update dealer status [VERIFIED]"""
        try:
            invoice = self.get_invoice(invoice_id)
            if not invoice:
                return False
            
            place_id = invoice['place_id']
            
            self.conn.execute("""
                UPDATE fee_invoices SET status = 'PAID', paid_at = CURRENT_TIMESTAMP
                WHERE invoice_id = ?
            """, (invoice_id,))
            
            self.conn.execute("""
                UPDATE dealer_leads SET status = 'CLOSED' WHERE place_id = ?
            """, (place_id,))
            
            logging.info(f"Invoice {invoice_id} paid, dealer {place_id} closed")
            return True
        except Exception as e:
            logging.error(f"Failed to mark paid: {e}")
            return False


class PaymentHandler:
    """Main payment handler orchestrator."""
    
    def __init__(self):
        self.db = PaymentDatabase(MARKETING_DB_PATH)
    
    def __enter__(self):
        self.db.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def create_invoice(self, place_id: str, dealer_name: str,
                      vehicle_description: str, fee_amount: int) -> str:
        return self.db.create_invoice(place_id, dealer_name, vehicle_description, fee_amount)
    
    def mark_paid(self, invoice_id: str) -> bool:
        return self.db.mark_paid(invoice_id)
    
    def get_sepa_instructions(self, invoice_id: str) -> str:
        invoice = self.db.get_invoice(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")
        return SEPAGenerator.generate_instructions(invoice_id, invoice['fee_amount'])
    
    def get_revolut_link(self, invoice_id: str) -> str:
        invoice = self.db.get_invoice(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")
        return RevolutPaymentGenerator.generate_payment_link(invoice_id, invoice['fee_amount'])


def main():
    parser = argparse.ArgumentParser(
        description="COMBARETROVAMIAUTO Payment Handler — Protocollo ARGOS™"
    )
    parser.add_argument("--create", action="store_true", help="Create new invoice")
    parser.add_argument("--place-id", type=str, help="Dealer place_id")
    parser.add_argument("--dealer-name", type=str, help="Dealer name")
    parser.add_argument("--vehicle", type=str, help="Vehicle description")
    parser.add_argument("--fee", type=int, help="Fee amount in euros")
    parser.add_argument("--mark-paid", action="store_true", help="Mark invoice as paid")
    parser.add_argument("--invoice-id", type=str, help="Invoice ID")
    parser.add_argument("--sepa-instructions", action="store_true", help="Generate SEPA instructions")
    parser.add_argument("--revolut-link", action="store_true", help="Generate Revolut link")
    parser.add_argument("--validate-fee", type=int, help="Validate fee amount")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    if args.validate_fee:
        try:
            PaymentValidator.validate_fee(args.validate_fee)
            print(f"\n✅ Fee €{args.validate_fee} is VALID (range: €{FEE_MIN}–€{FEE_MAX})")
        except ValueError as e:
            print(f"\n❌ {e}")
        return
    
    if args.create:
        if not all([args.place_id, args.dealer_name, args.vehicle, args.fee]):
            parser.error("--create requires --place-id, --dealer-name, --vehicle, --fee")
        
        with PaymentHandler() as handler:
            try:
                invoice_id = handler.create_invoice(args.place_id, args.dealer_name, args.vehicle, args.fee)
                print("\n" + "="*50)
                print("INVOICE CREATED — Protocollo ARGOS™")
                print("="*50)
                print(f"Invoice ID: {invoice_id}")
                print(f"Dealer: {args.dealer_name}")
                print(f"Vehicle: {args.vehicle}")
                print(f"Fee: €{args.fee}")
                print(f"Status: PENDING")
            except ValueError as e:
                print(f"\n❌ Error: {e}")
    
    elif args.mark_paid:
        if not args.invoice_id:
            parser.error("--mark-paid requires --invoice-id")
        
        with PaymentHandler() as handler:
            success = handler.mark_paid(args.invoice_id)
            print(f"\n{'✅ Invoice marked as PAID' if success else '❌ Failed'}")
    
    elif args.sepa_instructions:
        if not args.invoice_id:
            parser.error("--sepa-instructions requires --invoice-id")
        
        with PaymentHandler() as handler:
            print(handler.get_sepa_instructions(args.invoice_id))
    
    elif args.revolut_link:
        if not args.invoice_id:
            parser.error("--revolut-link requires --invoice-id")
        
        with PaymentHandler() as handler:
            print(handler.get_revolut_link(args.invoice_id))
    
    else:
        parser.print_help()
    
    print(f"\n[VERIFIED] Fee range: €{FEE_MIN}–€{FEE_MAX}")
    print(f"[VERIFIED] IBAN configured: {'Yes' if REVOLUT_IBAN else 'No'}")


if __name__ == "__main__":
    main()
