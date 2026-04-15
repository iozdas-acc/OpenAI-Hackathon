from __future__ import annotations

from typing import Any, Dict


def execute_supabase_migration(run: Any, graph_snapshot: Any) -> Dict[str, Any]:
    mapping_nodes = [
        node for node in getattr(graph_snapshot, "nodes", [])
        if getattr(node, "type", "") == "mapping_candidate"
    ]
    return {
        "mode": "mock",
        "status": "completed",
        "mapping_count": len(mapping_nodes),
        "records_written": 0,
    }
