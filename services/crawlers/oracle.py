from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List


def crawl_oracle_source(connection: Any, files: Iterable[Any]) -> Dict[str, Any]:
    config = getattr(connection, "config", {}) or {}
    metadata = getattr(connection, "metadata", {}) or {}
    schemas = _schema_entries(config=config, fallback_name="oracle_source")
    default_schema = schemas[0]["name"]
    tables = _tables_from_files(files, default_schema=default_schema)

    return {
        "database": {
            "name": getattr(connection, "name", "Oracle Source"),
            "kind": "oracle",
            "role": "source",
            "config": _safe_connection_summary(config),
            "metadata": metadata,
        },
        "schemas": schemas,
        "tables": tables,
    }


def _tables_from_files(files: Iterable[Any], default_schema: str) -> List[Dict[str, Any]]:
    tables: List[Dict[str, Any]] = []
    for file_record in files:
        metadata = getattr(file_record, "metadata", {}) or {}
        path_value = metadata.get("path")
        filename = getattr(file_record, "filename", "")
        table_name = Path(filename).stem or getattr(file_record, "name", "source_table")
        columns = _read_preview_columns(path_value)
        tables.append(
            {
                "name": table_name,
                "schema": default_schema,
                "columns": columns,
                "sample_source": filename,
            }
        )
    return tables


def _read_preview_columns(path_value: str | None) -> List[Dict[str, Any]]:
    if not path_value:
        return []

    path = Path(path_value)
    if not path.exists():
        return []

    try:
        first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except IndexError:
        return []

    separator = "," if "," in first_line else "\t" if "\t" in first_line else None
    if separator is None:
        return []

    columns = []
    for raw_name in first_line.split(separator):
        name = raw_name.strip().strip('"')
        if not name:
            continue
        columns.append({"name": name, "type": "unknown"})
    return columns


def _schema_entries(config: Dict[str, Any], fallback_name: str) -> List[Dict[str, Any]]:
    raw_schemas = config.get("schemas")
    if isinstance(raw_schemas, list) and raw_schemas:
        return [{"name": str(item)} for item in raw_schemas]
    return [{"name": fallback_name}]


def _safe_connection_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    allowed = ["dsn", "host", "port", "service_name", "database", "schema"]
    return {key: config[key] for key in allowed if key in config}
