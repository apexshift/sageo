"""GSC Connector pack — SageO-owned read-only MCP tool surface."""

from sageo.connectors.gsc.pack import (
    REQUIRED_ENV,
    SCOPE,
    TOOL_NAMES,
    ToolResult,
    call_tool,
)

__all__ = [
    "REQUIRED_ENV",
    "SCOPE",
    "TOOL_NAMES",
    "ToolResult",
    "call_tool",
]
