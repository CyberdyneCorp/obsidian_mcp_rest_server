"""Apache AGE graph adapter."""

import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AgeGraphAdapter:
    """Apache AGE graph provider implementation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.graph_name = "obsidian_graph"

    def _escape_cypher_string(self, value: str) -> str:
        """Escape a string for use in Cypher queries.

        Uses double quotes for strings to avoid issues with apostrophes
        in text like "Newton's Laws". Escapes special characters properly.
        """
        # Escape backslashes first (must be first!)
        escaped = value.replace("\\", "\\\\")
        # Escape double quotes
        escaped = escaped.replace('"', '\\"')
        # Escape newlines and other control characters
        escaped = escaped.replace("\n", "\\n")
        escaped = escaped.replace("\r", "\\r")
        escaped = escaped.replace("\t", "\\t")
        # Return with double quotes
        return f'"{escaped}"'

    async def _execute_cypher(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute a Cypher query via AGE."""
        # Set up AGE
        await self.session.execute(text("LOAD 'age'"))
        await self.session.execute(text("SET search_path = ag_catalog, '$user', public"))

        # Format params into query
        formatted_query = query
        if params:
            for key, value in params.items():
                if isinstance(value, UUID):
                    value = str(value)
                if isinstance(value, str):
                    # Use double-quoted strings to avoid apostrophe issues
                    value = self._escape_cypher_string(value)
                formatted_query = formatted_query.replace(f"${key}", str(value))

        # AGE's cypher() requires string constants, not bind parameters.
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", self.graph_name):
            raise ValueError("Invalid graph name")

        dollar_tag = "$cypher$"
        if dollar_tag in formatted_query:
            dollar_tag = "$cypher_safe$"
        if dollar_tag in formatted_query:
            raise ValueError("Cypher query contains an unsupported delimiter token")

        sql = f"""
        SELECT *
        FROM cypher('{self.graph_name}', {dollar_tag}
            {formatted_query}
        {dollar_tag}) AS result(v agtype);
        """

        try:
            raw_conn = await self.session.connection()
            result = await raw_conn.exec_driver_sql(sql)
            rows = result.fetchall()
            return [{"v": row[0]} for row in rows]
        except Exception as e:
            logger.warning(f"AGE graph query failed: {e}")
            # Re-raise to let caller handle it
            raise

    async def create_document_node(
        self,
        document_id: UUID,
        vault_id: UUID,
        title: str,
        path: str,
    ) -> None:
        """Create a document node in the graph."""
        query = """
        CREATE (d:Document {
            id: $doc_id,
            vault_id: $vault_id,
            title: $title,
            path: $path
        })
        RETURN d
        """
        await self._execute_cypher(query, {
            "doc_id": str(document_id),
            "vault_id": str(vault_id),
            "title": title,
            "path": path,
        })

    async def delete_document_node(self, document_id: UUID) -> None:
        """Delete a document node and all its edges."""
        query = """
        MATCH (d:Document {id: $doc_id})
        DETACH DELETE d
        """
        await self._execute_cypher(query, {"doc_id": str(document_id)})

    async def create_link_edge(
        self,
        source_id: UUID,
        target_id: UUID,
        link_type: str,
        display_text: str | None = None,
    ) -> None:
        """Create a link edge between documents."""
        # Note: Using [r:LINKS_TO] syntax to avoid SQLAlchemy interpreting :LINKS_TO as a bind param
        query = """
        MATCH (s:Document {id: $source_id})
        MATCH (t:Document {id: $target_id})
        CREATE (s)-[r:LINKS_TO {type: $link_type, display_text: $display_text}]->(t)
        """
        await self._execute_cypher(query, {
            "source_id": str(source_id),
            "target_id": str(target_id),
            "link_type": link_type,
            "display_text": display_text or "",
        })

    async def delete_link_edge(
        self,
        source_id: UUID,
        target_id: UUID,
    ) -> None:
        """Delete a link edge between documents."""
        query = """
        MATCH (s:Document {id: $source_id})-[r:LINKS_TO]->(t:Document {id: $target_id})
        DELETE r
        """
        await self._execute_cypher(query, {
            "source_id": str(source_id),
            "target_id": str(target_id),
        })

    async def delete_outgoing_edges(self, source_id: UUID) -> int:
        """Delete all outgoing edges from a document."""
        query = """
        MATCH (s:Document {id: $source_id})-[r:LINKS_TO]->()
        DELETE r
        RETURN count(r) as deleted
        """
        result = await self._execute_cypher(query, {"source_id": str(source_id)})
        return result[0].get("deleted", 0) if result else 0

    async def get_connections(
        self,
        document_id: UUID,
        vault_id: UUID,
        depth: int = 2,
    ) -> list[dict[str, Any]]:
        """Get connected documents within N hops."""
        query = f"""
        MATCH (d:Document {{id: $doc_id}})-[*1..{depth}]-(connected:Document)
        WHERE connected.vault_id = $vault_id AND d <> connected
        RETURN DISTINCT {{id: connected.id, title: connected.title, path: connected.path}}
        """
        results = await self._execute_cypher(query, {
            "doc_id": str(document_id),
            "vault_id": str(vault_id),
        })

        connections = []
        for row in results:
            v = row.get("v")
            if v:
                if isinstance(v, dict):
                    connections.append({
                        "id": v.get("id"),
                        "title": v.get("title"),
                        "path": v.get("path"),
                        "distance": 1,
                        "link_type": "connected",
                    })
                else:
                    import json
                    try:
                        parsed = json.loads(str(v))
                        connections.append({
                            "id": parsed.get("id"),
                            "title": parsed.get("title"),
                            "path": parsed.get("path"),
                            "distance": 1,
                            "link_type": "connected",
                        })
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Could not parse connection result: {v}")
        return connections

    async def get_shortest_path(
        self,
        source_id: UUID,
        target_id: UUID,
        vault_id: UUID,
    ) -> list[dict[str, Any]] | None:
        """Get shortest path between two documents.

        AGE doesn't support shortestPath(), so we try paths of increasing length.
        """
        _ = vault_id
        # Try paths of increasing length (BFS simulation)
        for max_hops in range(1, 6):  # Try up to 5 hops
            query = f"""
            MATCH p = (a:Document {{id: $source_id}})-[*1..{max_hops}]-(b:Document {{id: $target_id}})
            UNWIND nodes(p) as node
            RETURN {{id: node.id, title: node.title, path: node.path}}
            LIMIT 1
            """
            try:
                results = await self._execute_cypher(query, {
                    "source_id": str(source_id),
                    "target_id": str(target_id),
                })
                if results:
                    break
            except Exception:
                continue
        else:
            results = []

        if not results:
            return None

        path_nodes = []
        for row in results:
            v = row.get("v")
            if v:
                if isinstance(v, dict):
                    path_nodes.append({
                        "id": v.get("id"),
                        "title": v.get("title"),
                        "path": v.get("path"),
                    })
                else:
                    import json
                    try:
                        parsed = json.loads(str(v))
                        path_nodes.append({
                            "id": parsed.get("id"),
                            "title": parsed.get("title"),
                            "path": parsed.get("path"),
                        })
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Could not parse path node: {v}")
        return path_nodes if path_nodes else None

    async def get_orphans(self, vault_id: UUID) -> list[dict[str, Any]]:
        """Get documents with no connections."""
        # Use NOT EXISTS syntax which is supported by AGE
        # The ()-[:LABEL]-() syntax doesn't work in WHERE clauses in AGE
        query = """
        MATCH (d:Document {vault_id: $vault_id})
        WHERE NOT EXISTS((d)-[]->()) AND NOT EXISTS(()<-[]-(d))
        RETURN {id: d.id, title: d.title, path: d.path}
        """
        results = await self._execute_cypher(query, {"vault_id": str(vault_id)})

        orphans = []
        for row in results:
            v = row.get("v")
            if v:
                if isinstance(v, dict):
                    orphans.append({
                        "id": v.get("id"),
                        "title": v.get("title"),
                        "path": v.get("path"),
                    })
                else:
                    import json
                    try:
                        parsed = json.loads(str(v))
                        orphans.append({
                            "id": parsed.get("id"),
                            "title": parsed.get("title"),
                            "path": parsed.get("path"),
                        })
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Could not parse orphan result: {v}")
        return orphans

    async def get_hubs(
        self,
        vault_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get most connected documents.

        Note: AGE doesn't support complex WITH clauses well, so we get all documents
        and count connections for each, then sort in Python.
        """
        # Get all documents with their IDs
        query = """
        MATCH (d:Document {vault_id: $vault_id})
        RETURN {id: d.id, title: d.title, path: d.path}
        """
        results = await self._execute_cypher(query, {"vault_id": str(vault_id)})

        docs = []
        for row in results:
            v = row.get("v")
            if v:
                if isinstance(v, dict):
                    docs.append(v)
                else:
                    import json
                    try:
                        parsed = json.loads(str(v))
                        docs.append(parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass

        # Count connections for each document
        hubs = []
        for doc in docs:
            doc_id = doc.get("id")
            if doc_id:
                # Count edges for this document
                count_query = """
                MATCH (d:Document {id: $doc_id})-[r]-()
                RETURN count(r)
                """
                count_result = await self._execute_cypher(count_query, {"doc_id": doc_id})
                connections = 0
                if count_result:
                    v = count_result[0].get("v")
                    if v is not None:
                        # AGE returns agtype which may be string, int, or other
                        try:
                            connections = int(v)
                        except (ValueError, TypeError):
                            connections = 0

                hubs.append({
                    "id": doc_id,
                    "title": doc.get("title"),
                    "path": doc.get("path"),
                    "connections": connections,
                })

        # Sort by connections and limit
        hubs.sort(key=lambda x: x["connections"], reverse=True)
        return hubs[:limit]
