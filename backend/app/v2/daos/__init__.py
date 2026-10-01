"""DAO interfaces: how services reach the database.

These are a starting point, not a spec: add, rename or remove methods as your service
needs, then implement them in `daos/sql/`. Services depend on these interfaces only,
so tests can mock them.

Rules:
- A DAO only reads/writes data. Business rules belong in the service.
- `add` / `update` / `delete` flush but never commit (the request commits for you).
"""
