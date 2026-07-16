import Database from "better-sqlite3";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "..", "data", "vinguard.db");

let db;
try {
  db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");
} catch (e) {
  console.error(`❌ No se pudo abrir la DB en: ${DB_PATH}`);
  console.error(`   ${e.message}`);
  console.error("\n👉 Ejecutá primero: cd scripts && npm run seed\n");
  process.exit(1);
}

console.log("\n╔══════════════════════════════════════════╗");
console.log("║     VineGuard AI — Debug DB              ║");
console.log("╚══════════════════════════════════════════╝");
console.log(`   DB Path: ${DB_PATH}\n`);

const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").all();

for (const t of tables) {
  const name = t.name;
  const count = db.prepare(`SELECT COUNT(*) as c FROM "${name}"`).get().c;
  console.log(` 📋 Tabla: ${name} (${count} registros)`);

  if (count > 0) {
    const cols = db.prepare(`PRAGMA table_info("${name}")`).all();
    const colNames = cols.map((c) => c.name).join(", ");
    const rows = db.prepare(`SELECT * FROM "${name}" ORDER BY id DESC LIMIT 3`).all();
    for (const row of rows) {
      console.log(`    └── ${JSON.stringify(row)}`);
    }
  }
  console.log("");
}

const totalDiags = db.prepare("SELECT COUNT(*) as c FROM diagnostics").get().c;
const healthyCount = db.prepare("SELECT COUNT(*) as c FROM diagnostics WHERE result = 'Healthy'").get().c;
const diseasedCount = totalDiags - healthyCount;
const todayCount = db.prepare("SELECT COUNT(*) as c FROM diagnostics WHERE date(timestamp) = date('now')").get().c;

console.log(" 📊 Resumen:");
console.log(`    ├── Total diagnósticos: ${totalDiags}`);
console.log(`    ├── Sanos: ${healthyCount} (${totalDiags ? ((healthyCount/totalDiags)*100).toFixed(1) : 0}%)`);
console.log(`    ├── Enfermos: ${diseasedCount} (${totalDiags ? ((diseasedCount/totalDiags)*100).toFixed(1) : 0}%)`);
console.log(`    ├── Hoy: ${todayCount}`);
console.log(`    └── Mejor modelo: CNN+SVM (H1) — 96.7%`);

const diagSample = db.prepare("SELECT d.id, u.name as usuario, d.result, d.confidence, d.model_used, d.timestamp FROM diagnostics d JOIN users u ON d.user_id = u.id ORDER BY d.timestamp DESC LIMIT 5").all();
if (diagSample.length > 0) {
  console.log("\n 🕐 Últimos 5 diagnósticos:");
  for (const d of diagSample) {
    console.log(`    ${d.id}. ${d.usuario} — ${d.result} (${(d.confidence*100).toFixed(1)}%) — ${d.model_used} — ${d.timestamp}`);
  }
}

db.close();
console.log("\n ✅ DB verificada correctamente\n");
