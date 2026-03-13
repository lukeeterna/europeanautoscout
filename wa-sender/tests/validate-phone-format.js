// validate-phone-format.js — CoVe 2026
// Testa la conversione numero IT → formato WhatsApp @c.us
// Eseguibile in CI senza sessione attiva

const assert = require('assert');

function toWAFormat(numero) {
  const clean = numero.replace(/[^0-9]/g, '');
  if (!clean.startsWith('39')) throw new Error(`Numero non italiano: ${clean}`);
  if (clean.length !== 12) throw new Error(`Lunghezza errata: ${clean.length} (atteso 12)`);
  return `${clean}@c.us`;
}

const tests = [
  { input: '+393336142544',  expected: '393336142544@c.us' },
  { input: '393336142544',   expected: '393336142544@c.us' },
  { input: '3336142544',     shouldThrow: true },
  { input: '+39333614254',   shouldThrow: true }, // 11 cifre
];

let passed = 0;
for (const t of tests) {
  try {
    const result = toWAFormat(t.input);
    if (t.shouldThrow) {
      console.error(`❌ FAIL [${t.input}]: doveva lanciare errore`);
      process.exit(1);
    }
    assert.strictEqual(result, t.expected);
    console.log(`✅ OK [${t.input}] → ${result}`);
    passed++;
  } catch (e) {
    if (t.shouldThrow) {
      console.log(`✅ OK [${t.input}] → errore atteso: ${e.message}`);
      passed++;
    } else {
      console.error(`❌ FAIL [${t.input}]: ${e.message}`);
      process.exit(1);
    }
  }
}

console.log(`\n${passed}/${tests.length} test passati`);
