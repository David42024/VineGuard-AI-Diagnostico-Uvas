import { execSync } from "child_process";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pyScript = join(__dirname, "seed_db.py");

console.log("[DEPRECATED] seed.mjs delegates to Python seed_db.py");
try {
  execSync(`python "${pyScript}"`, { stdio: "inherit", cwd: join(__dirname, "..") });
} catch {
  process.exit(1);
}
