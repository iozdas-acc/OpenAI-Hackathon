from __future__ import annotations

import uuid
from typing import Any, Dict, List


def build_context_graph(run_id: str, source_profile: Dict[str, Any], target_profile: Dict[str, Any]) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    for profile in [source_profile, target_profile]:
        database = profile.get("database", {})
        database_id = _slug(database.get("name", "")) or uuid.uuid4().hex
        nodes.append(
            _node(
                run_id=run_id,
                node_id=database_id,
                label=database.get("name", "database"),
                type="database",
                data={"kind": database.get("kind"), "role": database.get("role")},
                metadata=database.get("config", {}),
            )
        )

        for schema in profile.get("schemas", []):
            schema_name = schema.get("name", "schema")
            schema_label = "{db}.{schema}".format(
                db=database.get("name", "database"),
                schema=schema_name,
            )
            schema_id = _slug(schema_label) or uuid.uuid4().hex
            nodes.append(
                _node(
                    run_id=run_id,
                    node_id=schema_id,
                    label=schema_label,
                    type="schema",
                    data={"role": database.get("role")},
                    metadata={},
                )
            )
            edges.append(_edge(run_id, database_id, schema_id, "contains"))

            for table in _tables_for_schema(profile.get("tables", []), schema_name):
                table_label = "{schema}.{table}".format(
                    schema=schema_name,
                    table=table.get("name", "table"),
                )
                table_id = _slug("{db}-{table}".format(db=database.get("name", ""), table=table_label)) or uuid.uuid4().hex
                nodes.append(
                    _node(
                        run_id=run_id,
                        node_id=table_id,
                        label=table_label,
                        type="table",
                        data={"role": database.get("role")},
                        metadata={"sample_source": table.get("sample_source")},
                    )
                )
                edges.append(_edge(run_id, schema_id, table_id, "contains"))

                for column in table.get("columns", []):
                    column_label = "{table}.{column}".format(
                        table=table_label,
                        column=column.get("name", "column"),
                    )
                    column_id = _slug("{db}-{column}".format(db=database.get("name", ""), column=column_label)) or uuid.uuid4().hex
                    nodes.append(
                        _node(
                            run_id=run_id,
                            node_id=column_id,
                            label=column_label,
                            type="column",
                            data={
                                "role": database.get("role"),
                                "data_type": column.get("type", "unknown"),
                            },
                            metadata={},
                        )
                    )
                    edges.append(_edge(run_id, table_id, column_id, "contains"))

    return {"nodes": _dedupe_nodes(nodes), "edges": _dedupe_edges(edges)}


def propose_mapping_candidates(run_id: str, graph: Dict[str, Any]) -> Dict[str, Any]:
    source_columns = [node for node in graph.get("nodes", []) if node.get("type") == "column" and node.get("data", {}).get("role") == "source"]
    target_columns = [node for node in graph.get("nodes", []) if node.get("type") == "column" and node.get("data", {}).get("role") == "target"]

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    target_by_slug = {_column_slug(node): node for node in target_columns}
    for source_node in source_columns:
        target_node = target_by_slug.get(_column_slug(source_node))
        if target_node is None:
            continue

        mapping_label = "Map {source} -> {target}".format(
            source=source_node["label"],
            target=target_node["label"],
        )
        mapping_id = _slug(mapping_label) or uuid.uuid4().hex
        nodes.append(
            _node(
                run_id=run_id,
                node_id=mapping_id,
                label=mapping_label,
                type="mapping_candidate",
                data={"confidence": 0.7},
                metadata={"strategy": "normalized_label_match"},
            )
        )
        edges.append(_edge(run_id, source_node["id"], mapping_id, "maps_to_candidate"))
        edges.append(_edge(run_id, mapping_id, target_node["id"], "maps_to_candidate"))

    return {"nodes": _dedupe_nodes(nodes), "edges": _dedupe_edges(edges)}


def _column_slug(node: Dict[str, Any]) -> str:
    label = node.get("label", "")
    suffix = label.split(".")[-1]
    return _slug(suffix)


def _tables_for_schema(tables: List[Dict[str, Any]], schema_name: str) -> List[Dict[str, Any]]:
    matched = [table for table in tables if table.get("schema", schema_name) == schema_name]
    return matched


def _node(run_id: str, node_id: str, label: str, type: str, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": node_id,
        "run_id": run_id,
        "label": label,
        "type": type,
        "data": data,
        "metadata": metadata,
    }


def _edge(run_id: str, source: str, target: str, relation: str) -> Dict[str, Any]:
    return {
        "id": uuid.uuid4().hex,
        "run_id": run_id,
        "source": source,
        "target": target,
        "relation": relation,
        "metadata": {},
    }


def _dedupe_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        deduped[node["id"]] = node
    return list(deduped.values())


def _dedupe_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: Dict[str, Dict[str, Any]] = {}
    for edge in edges:
        key = "{source}:{target}:{relation}".format(
            source=edge["source"],
            target=edge["target"],
            relation=edge["relation"],
        )
        deduped[key] = edge
    return list(deduped.values())


def _slug(value: str) -> str:
    sanitized = "".join(char.lower() if char.isalnum() else "-" for char in value)
    parts = [part for part in sanitized.split("-") if part]
    return "-".join(parts)
