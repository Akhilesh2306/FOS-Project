"""Exception hierarchy for FOS agent errors."""

from __future__ import annotations


class FOSAgentError(Exception):
    """Base exception for all FOS agent errors."""


# === Retry Classification ===
class RetryableError(FOSAgentError):
    """Transient failure - node wrapper will retry with backoff."""

class PermanentError(FOSAgentError):
    """Permanent failure - retrying will not help."""


# === Specific Error Types ===
class AgentConfigError(PermanentError):
    """Agent misconfigured - missing required settings or invalid state."""

class CortexLLMError(RetryableError):
    """Cortex LLM call failed"""

class CortexTimeoutError(CortexLLMError):
    """Cortex LLM call timed out"""

class HybridTableWriteError(RetryableError):
    """Failed to write results to hybrid table"""

class SemanticGuardError(PermanentError):
    """Query attempted to acces schema other than SEMANTIC"""
