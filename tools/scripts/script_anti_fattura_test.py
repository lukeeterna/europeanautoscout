"""
COMBARETROVAMIAUTO — Anti-Fattura Script per Test Phase
Gestione richieste fatturazione durante fase pilota pre-P.IVA

IMPORTANTE: Questo script è per fase test. Per business operativo
consultare commercialista per compliance fiscale completa.
"""

import json
from datetime import datetime
from enum import Enum

class FatturaRequest(Enum):
    DIRECT_REQUEST = "direct_fattura_request"
    P_IVA_QUESTION = "p_iva_question"
    RECEIPT_REQUEST = "receipt_request"
    TAX_COMPLIANCE = "tax_compliance_question"
    FORMAL_INVOICE = "formal_invoice_request"

class AntiRichiestaFatturaHandler:
    """
    Handler per scoraggiare richieste fattura in fase test/pilota
    con approcci legali e trasparenti.
    """

    def __init__(self):
        self.test_phase_messaging = {
            "positioning": "test_pilot_phase",
            "legal_status": "pre_business_validation",
            "payment_method": "pilot_agreement",
            "escalation_path": "business_formalization"
        }

    # ────────────────────────────────────────────
    # RESPONSES ANTI-FATTURA (Fase Test)
    # ────────────────────────────────────────────

    def handle_fattura_request(self, request_type: FatturaRequest, dealer_name: str = "") -> dict:
        """
        Gestisce richieste fattura con approcci che scoraggiano
        mantenendo trasparenza sulla fase test.
        """

        responses = {
            FatturaRequest.DIRECT_REQUEST: self._direct_fattura_response(dealer_name),
            FatturaRequest.P_IVA_QUESTION: self._piva_deflection_response(dealer_name),
            FatturaRequest.RECEIPT_REQUEST: self._receipt_alternative_response(dealer_name),
            FatturaRequest.TAX_COMPLIANCE: self._compliance_transparency_response(dealer_name),
            FatturaRequest.FORMAL_INVOICE: self._formal_invoice_alternative(dealer_name)
        }

        return responses.get(request_type, self._default_escalation_response(dealer_name))

    def _direct_fattura_response(self, dealer_name: str) -> dict:
        """Risposta diretta a richiesta fattura - redirect a test nature"""
        return {
            "primary_response": f"""
            {dealer_name}, attualmente operiamo in modalità test pilota
            per validare il servizio con dealer selezionati.

            Per questa fase iniziale lavoriamo con accordi pilota
            sperimentali — se il servizio vi convince, formalizziamo
            tutto regolarmente per i deal successivi.

            L'importante è che proviate il valore del servizio prima
            di qualsiasi formalizzazione burocratica.
            """,

            "alternative_positioning": """
            In questa fase ci focalizziamo su validazione operativa:
            se il veicolo e la documentazione ARGOS™ vi convincono,
            strutturiamo il rapporto commerciale regolare.
            """,

            "risk_mitigation": """
            Per il pilota: pagamento solo se acquistate +
            documentazione completa fornita. Zero rischio vostro.
            """
        }

    def _piva_deflection_response(self, dealer_name: str) -> dict:
        """Deflection da P.IVA verso valore servizio"""
        return {
            "primary_response": f"""
            {dealer_name}, giusta domanda. Siamo in fase di
            validazione del servizio con dealer premium italiani.

            Per questi test pilota ci focalizziamo sulla qualità
            del servizio — se il veicolo e la due diligence ARGOS™
            vi soddisfano, strutturiamo tutto regolarmente per
            i deal futuri.
            """,

            "value_redirect": """
            L'importante è che valutiate la BMW 330i e la
            documentazione completa — tutto il resto si
            sistema facilmente una volta che vedete il valore.
            """,

            "future_formalization": """
            Per deal regolari post-pilota: fatturazione standard
            con tutte le garanzie fiscali del caso.
            """
        }

    def _receipt_alternative_response(self, dealer_name: str) -> dict:
        """Alternativa alla ricevuta fiscale per fase test"""
        return {
            "primary_response": f"""
            {dealer_name}, per la fase test possiamo fornire:

            - Documento di accordo pilota sperimentale
            - Report completo ARGOS™ del veicolo
            - Documentazione completa del processo
            - Contatti per verifiche indipendenti
            """,

            "transparency_note": """
            Tutto tracciato e documentato — ma come accordo
            pilota per validazione servizio, non transazione
            commerciale standard.
            """,

            "escalation_option": """
            Se preferite operare solo con fatturazione regolare,
            vi ricontatto quando saremo operativi standard
            (stimiamo 60-90 giorni).
            """
        }

    def _compliance_transparency_response(self, dealer_name: str) -> dict:
        """Trasparenza su compliance per dealer attenti"""
        return {
            "primary_response": f"""
            {dealer_name}, apprezzo l'attenzione ai dettagli fiscali.

            Siamo in fase test pre-commerciale: validazione
            servizio con dealer selezionati prima del lancio
            ufficiale con tutte le formalizzazioni del caso.
            """,

            "professional_positioning": """
            Approccio standard per startup automotive tech:
            test pilota → validazione mercato → struttura
            commerciale completa.
            """,

            "timeline_transparency": """
            Per operazioni standard con fatturazione regolare:
            lancio previsto Q2 2026 con tutte le garanzie
            fiscali e assicurative del settore.
            """
        }

    def _formal_invoice_alternative(self, dealer_name: str) -> dict:
        """Alternative a fattura formale per fase test"""
        return {
            "primary_response": f"""
            {dealer_name}, per questa fase offriamo:

            INVECE di fattura commerciale:
            - Accordo pilota sperimentale documentato
            - Report ARGOS™ ufficiale con timbro
            - Documentazione completa processo
            - Garanzia rimborso se dati errati
            """,

            "value_proposition": """
            Focus su sostanza: se BMW 330i e documentazione
            vi convincono, formalizziamo tutto per deal futuri.
            Meglio testare valore prima di burocrazia.
            """,

            "escalation_path": """
            Per fatturazione standard: Q2 2026 con lancio
            commerciale completo + tutte le garanzie fiscali.
            """
        }

    def _default_escalation_response(self, dealer_name: str) -> dict:
        """Response di default per escalation"""
        return {
            "primary_response": f"""
            {dealer_name}, per questioni amministrative specifiche
            vi metto in contatto con il responsabile che può
            fornire tutti i dettagli sulla strutturazione.

            Nel frattempo, volete che vi mandi la documentazione
            ARGOS™ della BMW 330i per valutare il servizio?
            """
        }

    # ────────────────────────────────────────────
    # MESSAGING STRATEGICO PREVENTIVO
    # ────────────────────────────────────────────

    def generate_preventive_messaging(self) -> dict:
        """
        Messaging preventivo per evitare richieste fattura
        posizionando naturalmente come test/pilota.
        """
        return {
            "msg1_intro_addition": """
                Lavoro su validazione servizio scouting con
                dealer premium — test pilota prima del lancio ufficiale.
            """,

            "msg2_qualification_addition": """
                Per questi test ci focalizziamo sulla qualità
                veicoli e documentazione ARGOS™ — tutto il resto
                si formalizza se vi convince il servizio.
            """,

            "msg3_pitch_addition": """
                BMW 330i come test pilota — se documentazione
                e processo vi soddisfano, strutturiamo rapporto
                commerciale regolare per deal futuri.
            """,

            "signature_line": """
                ARGOS™ Automotive - Fase Test Pilota
                Validazione Servizio con Dealer Premium IT
            """
        }

    # ────────────────────────────────────────────
    # TRACKING E ANALYTICS
    # ────────────────────────────────────────────

    def log_fattura_request(self, request_type: FatturaRequest, dealer_id: str, response_used: str):
        """Log richieste fattura per pattern analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type.value,
            "dealer_id": dealer_id,
            "response_strategy": response_used,
            "escalation_required": request_type in [
                FatturaRequest.FORMAL_INVOICE,
                FatturaRequest.TAX_COMPLIANCE
            ]
        }

        # Save to DuckDB per analysis
        return log_entry

# ────────────────────────────────────────────
# USAGE EXAMPLES
# ────────────────────────────────────────────

if __name__ == "__main__":
    handler = AntiRichiestaFatturaHandler()

    # Test scenario: Mario chiede P.IVA
    mario_piva_request = handler.handle_fattura_request(
        FatturaRequest.P_IVA_QUESTION,
        "Mario"
    )

    print("=== RESPONSE MARIO P.IVA REQUEST ===")
    print(mario_piva_request["primary_response"])
    print("\n" + mario_piva_request["value_redirect"])

    # Preventive messaging
    preventive = handler.generate_preventive_messaging()
    print("\n=== PREVENTIVE MSG3 ADDITION ===")
    print(preventive["msg3_pitch_addition"])