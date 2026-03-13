#!/usr/bin/env python3.11
"""
OBJECTION HANDLER — ARGOS Automotive CoVe 2026
================================================
Gestione strutturata obiezioni dealer. 5 archetipi codificati OBJ-1/5.
Responses adattate per personalità dealer (IMPRENDITORE/TRADIZIONALE/LAUREATO/STRATEGICO).

Usage:
    from src.marketing.objection_handler import ObjectionHandler
    handler = ObjectionHandler()
    response = handler.handle("OBJ-2", dealer_personality="IMPRENDITORE")
"""

from typing import Dict, Optional

# OBJ codes
OBJ_PRICE       = "OBJ-1"   # "Troppo caro / fee alta"
OBJ_DELAY       = "OBJ-2"   # "Ci penso / non ora"
OBJ_COMPETITION = "OBJ-3"   # "Ho già fornitori EU"
OBJ_NO_IMPORT   = "OBJ-4"   # "Non faccio import"
OBJ_INFO_STALL  = "OBJ-5"   # "Mandami materiale / brochure"


class ObjectionHandler:
    """
    Gestione obiezioni dealer per personalità.
    Ogni OBJ ha risposta base + varianti per personality type.
    """

    def __init__(self):
        self._responses = self._build_response_matrix()

    def handle(
        self,
        obj_code: str,
        dealer_personality: str = "TRADIZIONALE",
        dealer_name: str = "",
        vehicle_info: str = "",
    ) -> Dict:
        """
        Restituisce risposta strutturata per codice obiezione.

        Returns:
            dict con keys: message, follow_up_delay_hours, escalate
        """
        obj_code = obj_code.upper()
        personality = dealer_personality.upper()

        if obj_code not in self._responses:
            raise ValueError(f"OBJ code sconosciuto: {obj_code}. Validi: OBJ-1..OBJ-5")

        obj_data = self._responses[obj_code]
        name_tag = f" {dealer_name}" if dealer_name else ""

        # Personality override se disponibile, altrimenti base
        if personality in obj_data.get("variants", {}):
            msg_template = obj_data["variants"][personality]
        else:
            msg_template = obj_data["base"]

        message = msg_template.format(
            name=name_tag,
            vehicle=vehicle_info or "il veicolo selezionato",
        )

        return {
            "obj_code": obj_code,
            "message": message,
            "follow_up_delay_hours": obj_data["follow_up_hours"],
            "escalate": obj_data["escalate"],
        }

    def list_objections(self) -> Dict[str, str]:
        """Elenco codici + descrizione."""
        return {k: v["label"] for k, v in self._responses.items()}

    # ─────────────────────────────────────────────────────────────────
    # RESPONSE MATRIX — OBJ-1/5
    # ─────────────────────────────────────────────────────────────────
    def _build_response_matrix(self) -> Dict:
        return {

            # ── OBJ-1: Prezzo / fee troppo alta ──────────────────────
            OBJ_PRICE: {
                "label": "Fee troppo alta / prezzo veicolo non conveniente",
                "follow_up_hours": 48,
                "escalate": False,
                "base": (
                    "Ciao{name}! La fee €800 è success-only — zero rischio upfront.\n"
                    "Su {vehicle} il margine dealer stimato è €2.500-4.000.\n"
                    "Lavoriamo solo se conviene anche a te. Possiamo procedere?"
                ),
                "variants": {
                    "IMPRENDITORE": (
                        "Ciao{name}! Fee €800 success-only = zero rischio.\n"
                        "Margine netto su {vehicle}: €2.500-4.000 dopo fee.\n"
                        "ROI immediato. Procediamo o preferisci alternativa?"
                    ),
                    "TRADIZIONALE": (
                        "Buongiorno{name}.\n"
                        "La fee €800 è a successo — paghi solo se acquisti.\n"
                        "Su {vehicle} il risparmio rispetto al mercato IT è confermato.\n"
                        "Possiamo parlarne con calma?"
                    ),
                    "STRATEGICO": (
                        "Buongiorno{name}.\n"
                        "Fee struttura: €800 success-only, zero upfront.\n"
                        "Unit economics su {vehicle}: costo fee ~3% del margine atteso.\n"
                        "Happy to share full breakdown. Quando sei disponibile?"
                    ),
                },
            },

            # ── OBJ-2: Ci penso / rinvio ─────────────────────────────
            OBJ_DELAY: {
                "label": "Ci penso / non è il momento / rimando",
                "follow_up_hours": 24,
                "escalate": False,
                "base": (
                    "Ciao{name}! Capito, nessun problema.\n"
                    "Ti segnalo che {vehicle} ha alta richiesta in questo periodo.\n"
                    "Posso tenerlo in stand-by 48h — poi si libera. Come preferisci?"
                ),
                "variants": {
                    "IMPRENDITORE": (
                        "Ciao{name}! Ok, capito.\n"
                        "{vehicle} — window 48h poi rilascio ad altro dealer.\n"
                        "Dimmi sì/no, gestisco io il resto."
                    ),
                    "TRADIZIONALE": (
                        "Buongiorno{name}, nessun problema.\n"
                        "Quando sei pronto risentiti pure.\n"
                        "Ti tengo {vehicle} in evidenza per 48h. Ci sentiamo."
                    ),
                    "LAUREATO": (
                        "Ciao{name}! Perfetto, prenditi il tempo.\n"
                        "FYI: {vehicle} ha 3 richieste attive questa settimana.\n"
                        "Se vuoi blocco prioritario basta un messaggio. 👍"
                    ),
                },
            },

            # ── OBJ-3: Ho già fornitori EU ────────────────────────────
            OBJ_COMPETITION: {
                "label": "Ho già fornitori EU / non ho bisogno",
                "follow_up_hours": 72,
                "escalate": False,
                "base": (
                    "Ciao{name}! Ottimo, significa che conosci il mercato.\n"
                    "ARGOS™ si differenzia su qualità documentale + VIN verification.\n"
                    "Possiamo fare una prova su {vehicle} senza impegno?"
                ),
                "variants": {
                    "IMPRENDITORE": (
                        "Ciao{name}! Rispetto, ci mancherebbe.\n"
                        "ARGOS™ opera su DE/BE/NL/AT/FR/SE/CZ — forse mercati che il tuo fornitore non copre.\n"
                        "Un confronto su {vehicle}? Zero impegno."
                    ),
                    "STRATEGICO": (
                        "Buongiorno{name}.\n"
                        "Interessante — su quali mercati opera il tuo fornitore attuale?\n"
                        "ARGOS™ copre 7 paesi EU con Protocollo ARGOS™ CERTIFICATO.\n"
                        "Happy to benchmark su {vehicle}."
                    ),
                },
            },

            # ── OBJ-4: Non faccio import ──────────────────────────────
            OBJ_NO_IMPORT: {
                "label": "Non faccio import / non è il mio settore",
                "follow_up_hours": 168,  # 1 week
                "escalate": True,        # segnala cambio strategia
                "base": (
                    "Capito{name}, nessun problema.\n"
                    "ARGOS™ gestisce tutta la parte operativa — a te arriva il veicolo chiavi in mano.\n"
                    "Molti dealer hanno iniziato così. Quando vuoi saperne di più, siamo qui."
                ),
                "variants": {
                    "TRADIZIONALE": (
                        "Buongiorno{name}.\n"
                        "Capisco, l'import può sembrare complicato.\n"
                        "Con ARGOS™ Tier 3 non devi gestire nulla — veicolo consegnato in concessionario.\n"
                        "Se cambia la situazione, sappi che siamo a disposizione."
                    ),
                },
            },

            # ── OBJ-5: Mandami materiale / brochure ───────────────────
            OBJ_INFO_STALL: {
                "label": "Mandami materiale / brochure / info via mail",
                "follow_up_hours": 24,
                "escalate": False,
                "base": (
                    "Ciao{name}! Certo, mando scheda tecnica {vehicle} entro oggi.\n"
                    "Nel frattempo: fee €800 success-only, zero upfront, consegna IT gestita.\n"
                    "Preferisci scheda via WhatsApp o email?"
                ),
                "variants": {
                    "IMPRENDITORE": (
                        "Ciao{name}! Mando scheda {vehicle} subito.\n"
                        "Key info: €27.800 | 45.200 km | fee €800 success-only.\n"
                        "WhatsApp o email?"
                    ),
                    "LAUREATO": (
                        "Ciao{name}! Perfetto, mando scheda completa {vehicle}.\n"
                        "Include: VIN check, history, valutazione mercato IT.\n"
                        "WhatsApp o email? Arrivo entro un'ora."
                    ),
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────
# CLI quick-test
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    handler = ObjectionHandler()

    if len(sys.argv) > 1:
        code = sys.argv[1].upper()
        personality = sys.argv[2].upper() if len(sys.argv) > 2 else "TRADIZIONALE"
        result = handler.handle(code, dealer_personality=personality, dealer_name="Mario")
        print(f"\n[{result['obj_code']}] → follow-up in {result['follow_up_delay_hours']}h | escalate={result['escalate']}")
        print("-" * 60)
        print(result["message"])
    else:
        print("Obiezioni disponibili:")
        for code, label in handler.list_objections().items():
            print(f"  {code}: {label}")
        print("\nUsage: python3.11 objection_handler.py OBJ-2 IMPRENDITORE")
