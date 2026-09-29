"""
Copy data from a Microsoft Access database (.accdb / .mdb) to Microsoft SQL Server.

Requirements (Windows):
    pip install pyodbc
    - Microsoft Access Database Engine (ODBC driver) matching your Python bitness (32/64-bit)
    - "ODBC Driver 17 or 18 for SQL Server"

Tables are created in the HT schema by default (created if missing).
Use --schema to override.

Authentication is SQL Server login (--user / --password). If --password is
omitted, the SQLSERVER_PASSWORD environment variable is used, otherwise you
are prompted securely.

Examples:
    python access_to_sqlserver.py --access "C:\\data\\mydb.accdb" ^
        --server localhost --database TargetDB --user myuser

    python access_to_sqlserver.py --access "C:\\data\\mydb.accdb" ^
        --server myserver --database TargetDB --user myuser --password secret ^
        --tables Customers Orders --if-exists replace
"""

import argparse
import getpass
import os
import sys

import pyodbc

BATCH_SIZE = 5000

# Access ODBC type name -> SQL Server type
TYPE_MAP = {
    "COUNTER": "INT",
    "AUTOINCREMENT": "INT",
    "INTEGER": "INT",
    "LONG": "INT",
    "SMALLINT": "SMALLINT",
    "SHORT": "SMALLINT",
    "BYTE": "TINYINT",
    "TINYINT": "TINYINT",
    "REAL": "REAL",
    "SINGLE": "REAL",
    "DOUBLE": "FLOAT",
    "FLOAT": "FLOAT",
    "CURRENCY": "MONEY",
    "DATETIME": "DATETIME2",
    "DATE": "DATETIME2",
    "BIT": "BIT",
    "YESNO": "BIT",
    "GUID": "UNIQUEIDENTIFIER",
    "LONGCHAR": "NVARCHAR(MAX)",
    "MEMO": "NVARCHAR(MAX)",
    "LONGBINARY": "VARBINARY(MAX)",
    "VARBINARY": "VARBINARY(MAX)",
    "BINARY": "VARBINARY(MAX)",
}


def q(name: str) -> str:
    """Quote an identifier for SQL Server."""
    return "[" + name.replace("]", "]]") + "]"


def installed_drivers() -> list[str]:
    return list(pyodbc.drivers())


def pick_sqlserver_driver(requested: str | None) -> str:
    """Use the requested driver if given, else the newest installed SQL Server driver."""
    drivers = installed_drivers()
    if requested:
        return requested
    versioned = sorted(
        (d for d in drivers if d.startswith("ODBC Driver") and "SQL Server" in d),
        key=lambda d: int("".join(ch for ch in d.split()[2] if ch.isdigit()) or 0),
        reverse=True,
    )
    if versioned:
        return versioned[0]
    for fallback in ("SQL Server Native Client 11.0", "SQL Server"):
        if fallback in drivers:
            return fallback
    raise RuntimeError(
        "No SQL Server ODBC driver found. Install 'ODBC Driver 18 for SQL Server' "
        "from Microsoft.\nInstalled drivers: " + (", ".join(drivers) or "(none)")
    )


def connect_access(path: str) -> pyodbc.Connection:
    drivers = installed_drivers()
    access_drivers = [d for d in drivers if "Access Driver" in d]
    if not access_drivers:
        raise RuntimeError(
            "No Microsoft Access ODBC driver found. Install the 'Microsoft Access "
            "Database Engine' (2016 Redistributable or newer) using the same "
            "bitness (32/64-bit) as your Python.\n"
            "Installed drivers: " + (", ".join(drivers) or "(none)")
        )
    conn_str = f"DRIVER={{{access_drivers[0]}}};DBQ={path};"
    return pyodbc.connect(conn_str)


def odbc_escape(value: str) -> str:
    """Wrap a value in braces so special characters (; = etc.) are safe in an ODBC string."""
    return "{" + value.replace("}", "}}") + "}"


def connect_sqlserver(args) -> pyodbc.Connection:
    driver = pick_sqlserver_driver(args.driver)
    print(f"Using SQL Server driver: {driver}")
    conn_str = (
        f"DRIVER={{{driver}}};SERVER={args.server};DATABASE={args.database};"
        f"UID={odbc_escape(args.user)};PWD={odbc_escape(args.password)};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


def get_access_tables(cur) -> list[str]:
    return [t.table_name for t in cur.tables(tableType="TABLE")]


def sql_type(col) -> str:
    """Map an Access column (from cursor.columns) to a SQL Server type."""
    tname = (col.type_name or "").upper()
    if tname in ("VARCHAR", "CHAR", "TEXT"):
        size = col.column_size or 255
        return f"NVARCHAR({size})" if size <= 4000 else "NVARCHAR(MAX)"
    if tname in ("DECIMAL", "NUMERIC"):
        return f"DECIMAL({col.column_size or 18},{col.decimal_digits or 0})"
    return TYPE_MAP.get(tname, "NVARCHAR(MAX)")


def qt(schema: str, table: str) -> str:
    """Schema-qualified, quoted table name."""
    return f"{q(schema)}.{q(table)}"


def ensure_schema(dst_cur, schema: str):
    """Create the schema if it doesn't exist yet."""
    lit = schema.replace("'", "''")
    dst_cur.execute(
        f"IF SCHEMA_ID(N'{lit}') IS NULL EXEC(N'CREATE SCHEMA {q(schema).replace(chr(39), chr(39) * 2)}')"
    )


def create_table(src_cur, dst_cur, schema: str, table: str, if_exists: str) -> list[str]:
    columns = list(src_cur.columns(table=table))
    if not columns:
        raise RuntimeError(f"No columns found for table {table!r}")

    ensure_schema(dst_cur, schema)

    exists = dst_cur.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?",
        schema,
        table,
    ).fetchone()

    if exists:
        if if_exists == "replace":
            dst_cur.execute(f"DROP TABLE {qt(schema, table)}")
        elif if_exists == "skip":
            raise FileExistsError
        # "append" -> keep the table as is

    if not exists or if_exists == "replace":
        col_defs = []
        for c in columns:
            null = "NULL" if c.nullable else "NOT NULL"
            # Identity is not preserved; COUNTER columns copy as plain INT values.
            col_defs.append(f"{q(c.column_name)} {sql_type(c)} {null}")
        dst_cur.execute(f"CREATE TABLE {qt(schema, table)} ({', '.join(col_defs)})")

    return [c.column_name for c in columns]


def copy_table(src, dst, schema: str, table: str, if_exists: str) -> int:
    src_cur = src.cursor()
    dst_cur = dst.cursor()
    dst_cur.fast_executemany = True

    try:
        col_names = create_table(src_cur, dst_cur, schema, table, if_exists)
    except FileExistsError:
        print(f"  Skipped {schema}.{table} (already exists)")
        return 0

    select_sql = f"SELECT {', '.join(q(c) for c in col_names)} FROM {q(table)}"
    # Access uses [brackets] too, so the same quoting works.
    insert_sql = (
        f"INSERT INTO {qt(schema, table)} ({', '.join(q(c) for c in col_names)}) "
        f"VALUES ({', '.join('?' * len(col_names))})"
    )

    src_cur.execute(select_sql)
    total = 0
    while True:
        rows = src_cur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        dst_cur.executemany(insert_sql, [tuple(r) for r in rows])
        total += len(rows)

    dst.commit()
    return total


def main():
    p = argparse.ArgumentParser(description="Copy Access tables to SQL Server")
    p.add_argument("--access", required=True, help="Path to .accdb/.mdb file")
    p.add_argument("--server", required=True, help="SQL Server host[\\instance][,port]")
    p.add_argument("--database", required=True, help="Target SQL Server database")
    p.add_argument("--schema", default="dbo", help="Target schema (default: dbo)")
    p.add_argument(
        "--driver",
        default=None,
        help="SQL Server ODBC driver name (default: auto-detect newest installed)",
    )
    p.add_argument("--user", required=True, help="SQL Server login name")
    p.add_argument(
        "--password",
        help="SQL Server password (if omitted, uses SQLSERVER_PASSWORD env var, "
        "or prompts securely)",
    )
    p.add_argument("--tables", nargs="*", help="Tables to copy (default: all)")
    p.add_argument(
        "--if-exists",
        choices=["append", "replace", "skip"],
        default="append",
        help="What to do if the table already exists in SQL Server",
    )
    args = p.parse_args()

    if not args.password:
        args.password = os.environ.get("SQLSERVER_PASSWORD") or getpass.getpass(
            f"Password for {args.user}: "
        )

    try:
        src = connect_access(args.access)
    except (pyodbc.Error, RuntimeError) as e:
        sys.exit(f"Could not connect to ACCESS database:\n{e}")

    try:
        dst = connect_sqlserver(args)
    except (pyodbc.Error, RuntimeError) as e:
        sys.exit(f"Could not connect to SQL SERVER:\n{e}")

    tables = args.tables or get_access_tables(src.cursor())
    print(f"Copying {len(tables)} table(s)...")

    for table in tables:
        print(f"- {table}")
        try:
            n = copy_table(src, dst, args.schema, table, args.if_exists)
            print(f"  {n} rows copied into {args.schema}.{table}")
        except Exception as e:
            dst.rollback()
            print(f"  FAILED: {e}")

    src.close()
    dst.close()
    print("Done.")


if __name__ == "__main__":
    main()
