// validate-message-payload.js — CoVe 2026
// Verifica struttura e contenuto del messaggio Mario (dati LOCKED)

const assert = require('assert');

const PAYLOAD = {
  numero: '393336142544@c.us',
  km: 45200,         // IMMUTABILE
  prezzo_de: 27800,  // IMMUTABILE
  margine: 3100,
  msg: `Buongiorno Mario, sono Luca Ferretti.\nHo individuato una BMW 330i G20 con km verificati 45.200 a €27.800 franco DE — margine potenziale per Lei €3.100.\nPosso mandarle una scheda tecnica?`,
};

// Test 1: formato numero
assert.match(PAYLOAD.numero, /^39\d{10}@c\.us$/, 'Numero non in formato @c.us');
console.log('✅ Formato numero OK');

// Test 2: km LOCKED
assert.strictEqual(PAYLOAD.km, 45200, `km deve essere 45200, trovato ${PAYLOAD.km}`);
console.log('✅ km=45200 LOCKED OK');

// Test 3: km nel messaggio = km LOCKED
assert.ok(PAYLOAD.msg.includes('45.200'), 'km nel messaggio non corrisponde');
console.log('✅ km nel messaggio OK');

// Test 4: prezzo nel messaggio
assert.ok(PAYLOAD.msg.includes('27.800'), 'prezzo DE non nel messaggio');
console.log('✅ prezzo DE nel messaggio OK');

// Test 5: lunghezza messaggio (max 6 righe regola CoVe)
const righe = PAYLOAD.msg.split('\n').length;
assert.ok(righe <= 6, `Messaggio troppo lungo: ${righe} righe (max 6)`);
console.log(`✅ Lunghezza messaggio OK (${righe} righe)`);

// Test 6: nessuna parola vietata
const parole_vietate = ['CoVe', 'Claude', 'Anthropic', 'embedding', 'algoritmo', 'AI'];
for (const p of parole_vietate) {
  assert.ok(!PAYLOAD.msg.includes(p), `Parola vietata trovata: "${p}"`);
}
console.log('✅ Nessuna parola vietata OK');

console.log('\n✅ Tutti i test payload passati');
