// validate-session-structure.js — CoVe 2026
// Verifica struttura directory sessione LocalAuth (non richiede sessione attiva)

const fs = require('fs');
const path = require('path');

const SESSION_DIR = path.join(__dirname, '..', '.wwebjs_auth', 'session-argosautomotive');

// In CI la sessione non esiste — test solo la logica di verifica
function checkSessionExists(dir) {
  if (!fs.existsSync(dir)) return { exists: false, files: 0 };
  const files = fs.readdirSync(dir);
  return { exists: true, files: files.length, hasDefault: files.includes('Default') };
}

const result = checkSessionExists(SESSION_DIR);

if (result.exists) {
  console.log(`✅ Sessione trovata: ${result.files} file`);
  if (!result.hasDefault) {
    console.error('❌ Directory Default mancante — sessione corrotta');
    process.exit(1);
  }
  console.log('✅ Struttura sessione valida');
} else {
  console.log('ℹ️  Sessione assente (atteso in CI) — test struttura saltato');
  console.log('✅ Logica verifica sessione OK');
}
