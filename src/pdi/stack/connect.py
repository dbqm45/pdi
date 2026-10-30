"""Połączenie ShipScope ↔ pdi bez przeglądarki: skrypt `node -e` w `server/` ShipScope (plan L4 §5).

Woła ten sam kod co przycisk Connect (`lib/pdi-connection.connectPdi`) dla pierwszego admina pierwszej przestrzeni.
Dane wejściowe (adresy baz, klucz) bierze ze środowiska, wynik wypisuje jedną linią `SDLC_ENV <json>`.
Kody wyjścia: 0 połączono, 3 brak przestrzeni z adminem, 4 przestrzeń już połączona, 1 inny błąd.
"""

MARKER = "SDLC_ENV "
NO_WORKSPACE = 3
ALREADY_CONNECTED = 4

CONNECT_JS = """
const { createPool } = require('./lib/db');
const { loadEncryptionKey } = require('./lib/config');
const { connectPdi, PdiConnectionConflictError } = require('./lib/pdi-connection');
(async () => {
  // memberships ma FORCE RLS: admina szukamy na koncie właściciela bazy, połączenie zakłada pula aplikacji.
  const admin = createPool({ DATABASE_URL: process.env.SDLC_ADMIN_DATABASE_URL, DATABASE_SSL: 'false' });
  const pool = createPool(process.env);
  try {
    const { rows } = await admin.query(
      "SELECT tenant_id, user_id FROM memberships WHERE role = 'admin' ORDER BY created_at LIMIT 1");
    if (!rows.length) { process.exitCode = 3; return; }
    const result = await connectPdi(pool, {
      tenantId: rows[0].tenant_id,
      actorUserId: rows[0].user_id,
      receiverUrl: process.env.SDLC_RECEIVER_URL,
      publicBaseUrl: process.env.PUBLIC_BASE_URL,
      encryptionKey: loadEncryptionKey(process.env),
      localMode: true,
    });
    process.stdout.write('SDLC_ENV ' + JSON.stringify(result.env) + '\\n');
  } catch (e) {
    if (e instanceof PdiConnectionConflictError) process.exitCode = 4;
    else { console.error(e && e.message ? e.message : String(e)); process.exitCode = 1; }
  } finally {
    await admin.end();
    await pool.end();
  }
})();
"""
