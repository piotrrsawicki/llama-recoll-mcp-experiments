#!/usr/bin/env python3
"""
Recoll MCP Server - Natural Language Interface to Indexed Filesystem

Provides Claude with access to your Recoll-indexed filesystem through MCP.
Supports natural language queries with semantic understanding.
"""

import os
import json
from datetime import datetime
from typing import Any, Literal
from recoll import recoll
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
import uvicorn
from urllib.parse import unquote
from starlette.middleware.cors import CORSMiddleware


# Set Recoll config directory
os.environ['RECOLL_CONFDIR'] = os.path.expanduser('~/.recoll')

# Initialize Recoll database connection
try:
    db = recoll.connect()
except Exception as e:
    print(f"Warning: Could not connect to Recoll database: {e}", flush=True)
    db = None

# Create an MCP server instance using FastMCP
# stateless_http and json_response are recommended for HTTP servers
mcp = FastMCP("recoll-search", stateless_http=True, json_response=True)

def format_doc_result(doc: Any, include_preview: bool = True) -> dict:
    """Format a Recoll document result as a structured dict."""
    result = {
        "filename": doc.filename,
        "url": doc.url,
        "mimetype": doc.mimetype,
        "size": doc.fbytes,
        "mtime": doc.mtime,
        "mtime_readable": datetime.fromtimestamp(int(doc.mtime[1:])).strftime("%Y-%m-%d %H:%M:%S"),
    }

    if include_preview and hasattr(doc, 'abstract'):
        result["preview"] = doc.abstract[:300]

    return result


def create_tool_result(data: dict) -> CallToolResult:
    """Creates a CallToolResult with only unstructured, JSON-compliant content."""
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data, indent=2))]
        # The structuredContent field is omitted to work around a suspected serialization
        # bug in the MCP framework that incorrectly handles boolean values.
    )


@mcp.tool()
def search_filesystem(
    query_str: str,
    max_results: int = 20,
    include_preview: Literal["Yes", "No"] = "Yes",
    sort_by: Literal["relevance", "date_desc", "date_asc"] = "relevance",
) -> CallToolResult:
    """Search the indexed filesystem using keywords or phrases.
    Supports Boolean queries (AND, OR, NOT), phrase searches ("exact phrase"),
    and wildcards. Results are ranked by relevance or sorted by date.
    """
    if db is None:
        return create_tool_result({"error": "Recoll database not available. Check configuration."})

    # Convert the string literal back to a boolean for internal use
    should_include_preview = include_preview == "Yes"

    try:
        query = db.query()
        if sort_by == "date_desc":
            query.sortby(field="mtime", ascending=False)
        elif sort_by == "date_asc":
            query.sortby(field="mtime", ascending=True)
        nres = query.execute(query_str)

        results = []
        for i in range(min(max_results, nres)):
            doc = query.fetchone()
            results.append(format_doc_result(doc, should_include_preview))

        result_dict = {
            "query": query_str,
            "total_results": nres,
            "returned_results": len(results),
            "results": results,
        }
        return create_tool_result(result_dict)
    except Exception as e:
        return create_tool_result({"error": f"Error executing search: {str(e)}"})


@mcp.tool()
def search_by_date(
    query_str: str, start_date: str | None = None, end_date: str | None = None, max_results: int = 20
) -> CallToolResult:
    """Search files filtered by modification date range."""
    if db is None:
        return create_tool_result({"error": "Recoll database not available. Check configuration."})

    try:
        date_filter = ""
        if start_date and end_date:
            date_filter = f" date:{start_date}/{end_date}"
        elif start_date:
            date_filter = f" date:{start_date}/"
        elif end_date:
            date_filter = f" date:/{end_date}"
        full_query = query_str + date_filter

        query = db.query()
        nres = query.execute(full_query)

        results = [format_doc_result(query.fetchone()) for i in range(min(max_results, nres))]
        result_dict = {
            "query": full_query,
            "total_results": nres,
            "returned_results": len(results),
            "results": results,
        }
        return create_tool_result(result_dict)
    except Exception as e:
        return create_tool_result({"error": f"Error executing search: {str(e)}"})


@mcp.tool()
def search_by_filetype(query_str: str, filetype: str, max_results: int = 20) -> CallToolResult:
    """Search files filtered by file type/mimetype (e.g., 'pdf', 'markdown', 'text')."""
    if db is None:
        return create_tool_result({"error": "Recoll database not available. Check configuration."})

    try:
        full_query = f"{query_str} mime:{filetype}"
        query = db.query()
        nres = query.execute(full_query)

        results = [format_doc_result(query.fetchone()) for i in range(min(max_results, nres))]
        result_dict = {
            "query": full_query,
            "total_results": nres,
            "returned_results": len(results),
            "results": results,
        }
        return create_tool_result(result_dict)
    except Exception as e:
        return create_tool_result({"error": f"Error executing search: {str(e)}"})


@mcp.tool()
def get_document_content(url: str) -> CallToolResult:
    """Retrieve the full content of a document by its file URL."""
    if db is None:
        return create_tool_result({"error": "Recoll database not available. Check configuration."})

    try:
        # For file:// URLs, convert to an absolute path and query by 'filename'
        # as it is more reliably indexed than 'url'.
        if not url.startswith("file://"):
            return create_tool_result({"error": f"URL scheme not supported: {url}. Only 'file://' is supported."})

        # Decode percent-encoded characters and remove the 'file://' prefix.
        filepath = unquote(url[7:])
        import os
        basename = os.path.basename(filepath)
        dirname = os.path.dirname(filepath)
        
        query = db.query()
        nres = query.execute(f'dir:"{dirname}" filename:"{basename}"', fetchtext=True)

        if nres == 0:
            return create_tool_result({"error": f"Document with path '{filepath}' (from URL '{url}') not found in index."})
        if nres > 1:
            return create_tool_result({"error": f"Multiple documents found for path '{filepath}'."})

        doc = query.fetchone()
        content = doc.text
        result_dict = {
            "url": url,
            "content": content[:10000],
            "truncated": len(content) > 10000,
        }
        return create_tool_result(result_dict)
    except Exception as e:
        return create_tool_result({"error": f"Error getting content for '{url}': {e}"})


@mcp.tool()
def list_recent_files(days: int = 7, max_results: int = 20) -> CallToolResult:
    """List recently modified files in the index."""
    if db is None:
        return create_tool_result({"error": "Recoll database not available. Check configuration."})

    try:
        query = db.query()
        nres = query.execute(f"date:{days}d/")

        results = [format_doc_result(query.fetchone()) for i in range(min(max_results, nres))]
        result_dict = {
            "days": days,
            "total_results": nres,
            "returned_results": len(results),
            "results": results,
        }
        return create_tool_result(result_dict)
    except Exception as e:
        return create_tool_result({"error": f"Error executing search: {str(e)}"})


def main():
    """Run the Recoll MCP server using the Streamable HTTP transport."""
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8081"))
    print(f"Starting Recoll MCP server on http://{host}:{port}", flush=True)

    # Get the underlying Starlette app from the FastMCP instance
    app = mcp.streamable_http_app()

    # Add CORS middleware to allow cross-origin requests from web UIs like llama.cpp
    app = CORSMiddleware(
        app,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["Mcp-Session-Id"], # Required by MCP spec for browser clients
    )

    # Run the wrapped app with uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
