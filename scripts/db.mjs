console.error("DEPRECATED: Node.js db.mjs is no longer the source of truth for schema.");
console.error("Schema is managed by SQLAlchemy + Alembic. Use:");
console.error("  - alembic upgrade head   (apply migrations)");
console.error("  - python scripts/seed_db.py   (seed data)");
console.error("This file is kept as a wrapper for backward compatibility.");
process.exit(1);
