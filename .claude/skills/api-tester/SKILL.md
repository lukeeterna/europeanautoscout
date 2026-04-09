---
name: api-tester
description: >
  Standard enterprise per testing API. Invocare per: writing test API,
  debug integrazione API, validare comportamento API terze parti,
  generare test suite, documentare API contract.
  Un'API non testata è una promessa, non un contratto.
---

## Copertura obbligatoria (ogni endpoint)

```
1. Happy path:      input valido → output atteso
2. Auth:            token invalido/mancante → 401/403 (testare entrambi)
3. Validazione:     campi required mancanti → 400 con messaggio utile
4. Validazione:     tipi invalidi → 400 con messaggio utile
5. Edge cases:      stringhe vuote, null, 0, numeri negativi, max length
6. Rate limiting:   verificare che esista e ritorni 429
7. Idempotency:     PUT/PATCH chiamato 2 volte = stesso risultato
```

## Struttura test (pytest)

```python
class TestEndpointName:
    def test_happy_path(self, client, auth_headers):
        # Arrange → Act → Assert
        response = client.post("/endpoint", json=payload, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["field"] == expected_value

    def test_unauthorized(self, client):
        response = client.post("/endpoint", json={})
        assert response.status_code == 401

    def test_missing_required_field(self, client, auth_headers):
        response = client.post("/endpoint", json={}, headers=auth_headers)
        assert response.status_code == 400
        assert "field_name" in response.json()["detail"]
```

## Testing API di terze parti

- Test con API reale in staging (mock per unit, reale per integration)
- Testare cosa succede quando l'API è down (simulare con mock)
- Testare formato risposta inatteso
- Documentare rate limits e testare l'implementazione di backoff
- Loggare tutte le risposte API nei test per debugging
