from database import get_db_connection

conn = get_db_connection()

tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("\n========== DATABASE TABLES ==========\n")

for table in tables:

    table_name = table["name"]

    print("\nTABLE:", table_name)

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    for column in columns:

        print(
            column["name"],
            "|",
            column["type"]
        )

conn.close()