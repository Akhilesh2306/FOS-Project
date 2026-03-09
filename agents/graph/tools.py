"""Tool contracts and stub implementations for FOS agents"""

# Import external libraries
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# Import internal modules
from graph.errors import SemanticGuardError

# Setup logging
logger = logging.getLogger(__name__)


# === Tool Protocols (Interfaces) ===

@runtime_checkable
class SemanticQueryFunction(Protocol):
    """
    Executes a read-only SQL query against the SEMANTIC schema.
    Implementation must enforce SEMANTIC-only access.

    :returns rows as list of dicts, where each dict maps column name to value.
    """
    def __call__(self, sql: str) -> list[dict[str, Any]]:
        ...


@runtime_checkable
class CortexLLMFunction(Protocol):
    """ 
    Calls Snowflake Cortex LLM for text generation.
    """

    def __call__(
        self,
        prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        ...


@runtime_checkable
class HybridTableWriteFunction(Protocol):
    """ 
    Writes a row to Bronze Hybrid Table via Snowpark SDK.

    :param table_name: Name of the target hybrid table
    :param row_data: Column-value mapping to insert or update in the hybrid table. 
    """

    def __call__(self, table_name: str, row_data: dict[str, Any]) -> None:
        ...


@runtime_checkable
class EventPublishFunction(Protocol):
    """ 
    Publishes a JSON message to an Azure Event Hubs topic.
    """

    def __call__(self, topic: str, message: dict[str, Any]) -> None:
        ...


# === SEMANTIC Query Guardrail ===

# Match DDL/DML keywords to prevent non-SELECT queries.
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|RENAME|TRUNCATE|MERGE|GRANT|REVOKE|COPY|PUT|EXEC|EXECUTE|CALL)\b",
    re.IGNORECASE,
)

# Matches schema-qualified references to non-SEMANTIC schemas
_NON_SEMANTIC_SCHEMA = re.compile(
    r"\b(BRONZE|SILVER|GOLD)\s*\.",
    re.IGNORECASE,
)


def validate_semantic_query(sql: str) -> None:
    """Enforce the SEMANTIC-only guard on a SQL string.

    Raises SemanticGuardError if the query:
      1. Is empty
      2. Doesn't start with SELECT or WITH (CTE)
      3. Contains any DML/DDL keyword
      4. References BRONZE, SILVER, or GOLD schemas
    """
    stripped = sql.strip().rstrip(";").strip()

    # Check 1: Not empty
    if not stripped:
        raise SemanticGuardError("Empty SQL query")

    # Check 2: Must start with SELECT or WITH (for CTEs)
    first_keyword = stripped.split()[0].upper()
    if first_keyword not in ("SELECT", "WITH"):
        raise SemanticGuardError(
            f"Only SELECT queries are allowed. Got: {first_keyword}..."
        )

    # Check 3: No DML/DDL keywords anywhere in the query
    match = _FORBIDDEN_KEYWORDS.search(stripped)
    if match:
        raise SemanticGuardError(
            f"Forbidden SQL keyword detected: {match.group()}"
        )

    # Check 4: No references to non-SEMANTIC schemas
    schema_match = _NON_SEMANTIC_SCHEMA.search(stripped)
    if schema_match:
        raise SemanticGuardError(
            f"Query references non-SEMANTIC schema: {schema_match.group()}. "
            "Agents must query SEMANTIC views only."
        )

# === Stub Defaults (for optional tools) ===

def stub_hybrid_write(
    table_name: str, row_data: dict[str, Any]
) -> None:
    """Stub: logs the write but does nothing."""
    logger.debug(
        f"STUB write_hybrid_table: table={table_name}, keys={list(row_data.keys())}"
    )

def stub_event_publish(
    topic: str, message: dict[str, Any]
) -> None:
    """Stub: logs the event but does nothing."""
    logger.debug(
        f"STUB publish_event: topic={topic}, type={message.get('event_type', 'unknown')}"
    )


# === Agent Toolkit (Dependency Bundle) ===

@dataclass(frozen=True)
class AgentToolkit:
    """
    Bundles all tools an agent needs into a single injectable object.
    """

    query_semantic: SemanticQueryFunction
    call_llm: CortexLLMFunction
    write_hybrid_table: HybridTableWriteFunction = field(
        default=stub_hybrid_write
    )
    publish_event: EventPublishFunction = field(
        default=stub_event_publish
    )