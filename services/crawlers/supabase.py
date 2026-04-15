from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from ipaddress import ip_address

from dotenv import dotenv_values
from psycopg import connect, sql
from psycopg.rows import dict_row


def crawl_supabase_target(connection: Any) -> Dict[str, Any]:
    config = _resolved_connection_config(getattr(connection, "config", {}) or {})
    metadata = getattr(connection, "metadata", {}) or {}
    warnings: List[Dict[str, Any]] = []

    with connect(
        host=config["host"],
        port=config["port"],
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        sslmode=config["sslmode"],
        connect_timeout=5,
        row_factory=dict_row,
    ) as db:
        schemas = _load_schemas(db, configured_schemas=config.get("schemas"))
        tables = _load_tables(db, schemas=schemas)
        _attach_columns(db, tables=tables)
        _attach_sample_rows(db, tables=tables, row_limit=3, warnings=warnings)

    return {
        "database": {
            "name": getattr(connection, "name", "Supabase Target"),
            "kind": "supabase",
            "role": "target",
            "config": _safe_connection_summary(config),
            "metadata": metadata,
        },
        "schemas": [{"name": schema_name} for schema_name in schemas],
        "tables": tables,
        "warnings": warnings,
    }


def _resolved_connection_config(config: Dict[str, Any]) -> Dict[str, Any]:
    env = _load_repo_env()

    def pick(*keys: str, default: Any = None) -> Any:
        for key in keys:
            value = config.get(key)
            if value not in (None, ""):
                return value
            env_value = os.getenv(key) or env.get(key)
            if env_value not in (None, ""):
                return env_value
        return default

    resolved = {
        "host": pick("host", "POSTGRES_HOST"),
        "port": int(pick("port", "POSTGRES_PORT", default=5432)),
        "dbname": pick("database", "dbname", "POSTGRES_DB"),
        "user": pick("user", "POSTGRES_USER"),
        "password": pick("password", "POSTGRES_PASSWORD"),
        "sslmode": pick("sslmode", "POSTGRES_SSLMODE", default=_default_sslmode(pick("host", "POSTGRES_HOST"))),
        "schemas": _configured_schemas(config),
    }

    missing = [key for key in ["host", "dbname", "user", "password"] if not resolved[key]]
    if missing:
        raise RuntimeError(
            "Missing Postgres connection config values: {keys}".format(keys=", ".join(sorted(missing)))
        )

    return resolved


def _load_schemas(db: Any, configured_schemas: Optional[List[str]]) -> List[str]:
    if configured_schemas:
        return [str(item) for item in configured_schemas]

    with db.cursor() as cur:
        cur.execute(
            """
            select schema_name
            from information_schema.schemata
            where schema_name not in ('pg_catalog', 'information_schema')
              and schema_name not in ('auth', 'extensions', 'pgbouncer', 'realtime', 'storage', 'supabase_functions')
              and schema_name not like 'pg_toast%%'
              and schema_name not like 'pg_temp%%'
            order by schema_name
            """
        )
        rows = cur.fetchall()
    return [row["schema_name"] for row in rows]


def _load_tables(db: Any, schemas: List[str]) -> List[Dict[str, Any]]:
    with db.cursor() as cur:
        cur.execute(
            """
            select
              t.table_schema,
              t.table_name,
              coalesce(c.reltuples::bigint, 0) as estimated_rows
            from information_schema.tables t
            left join pg_class c on c.relname = t.table_name
            left join pg_namespace n on n.oid = c.relnamespace and n.nspname = t.table_schema
            where t.table_type = 'BASE TABLE'
              and t.table_schema = any(%s)
            order by t.table_schema, t.table_name
            """,
            (schemas,),
        )
        rows = cur.fetchall()

    return [
        {
            "name": row["table_name"],
            "schema": row["table_schema"],
            "estimated_rows": int(row["estimated_rows"] or 0),
            "columns": [],
            "sample_rows": [],
        }
        for row in rows
    ]


def _attach_columns(db: Any, tables: List[Dict[str, Any]]) -> None:
    if not tables:
        return

    schemas = sorted({table["schema"] for table in tables})
    with db.cursor() as cur:
        cur.execute(
            """
            select
              table_schema,
              table_name,
              column_name,
              data_type,
              is_nullable
            from information_schema.columns
            where table_schema = any(%s)
            order by table_schema, table_name, ordinal_position
            """,
            (schemas,),
        )
        rows = cur.fetchall()

    table_index = {
        (table["schema"], table["name"]): table
        for table in tables
    }
    for row in rows:
        key = (row["table_schema"], row["table_name"])
        table = table_index.get(key)
        if table is None:
            continue
        table["columns"].append(
            {
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
            }
        )


def _attach_sample_rows(db: Any, tables: List[Dict[str, Any]], row_limit: int, warnings: List[Dict[str, Any]]) -> None:
    for table in tables:
        identifier = sql.Identifier(table["schema"], table["name"])
        query = sql.SQL("select * from {} limit {}").format(
            identifier,
            sql.Literal(row_limit),
        )
        try:
            with db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
        except Exception as exc:
            table["sample_rows"] = []
            warnings.append(
                {
                    "table": "{schema}.{table}".format(schema=table["schema"], table=table["name"]),
                    "stage": "sample_rows",
                    "message": str(exc),
                }
            )
            continue

        table["sample_rows"] = [dict(row) for row in rows]


def _load_repo_env() -> Dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if not env_path.exists():
        return {}

    return {
        key: value
        for key, value in dotenv_values(env_path).items()
        if key and value is not None
    }


def _split_csv(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _configured_schemas(config: Dict[str, Any]) -> Optional[List[str]]:
    if "schemas" in config:
        value = _split_csv(config.get("schemas"))
        return value or None
    if "schema" in config:
        value = _split_csv(config.get("schema"))
        return value or None
    return None


def _default_sslmode(host: Any) -> str:
    if not host:
        return "require"

    host_value = str(host)
    if host_value in ("localhost", "127.0.0.1"):
        return "prefer"

    try:
        parsed = ip_address(host_value)
        if parsed.is_private or parsed.is_loopback:
            return "prefer"
    except ValueError:
        pass

    return "require"


def _safe_connection_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    allowed = ["host", "port", "dbname", "sslmode", "schemas"]
    return {key: config[key] for key in allowed if key in config}
