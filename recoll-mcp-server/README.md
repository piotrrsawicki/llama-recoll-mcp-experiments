# Recoll MCP Server

Natural language interface to your Recoll-indexed filesystem through Claude Desktop.

## Overview

This MCP (Model Context Protocol) server gives Claude AI access to your Recoll search index, enabling natural language queries of your entire indexed filesystem.

## Features

- **Natural Language Search**: Ask Claude to find files using plain English
- **Advanced Filtering**: Search by date range, file type, and more
- **Content Access**: Retrieve full document contents
- **Recent Files**: List recently modified files
- **Fast**: Direct access to Xapian index via Recoll Python API

## Requirements

- Python 3.10+
- Recoll (with Python bindings)
- Claude Desktop

## Installation

### On Ubuntu/Debian

1. Install the Recoll Python bindings and virtual environment tools using your system's package manager:
```bash
sudo apt update
sudo apt install python3-recoll python3-venv
```

2. Create a Python virtual environment. You **must** use the `--system-site-packages` flag so the environment can access the system-installed `python3-recoll` package:
```bash
python3 -m venv venv --system-site-packages
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Install the required Python packages into your virtual environment:
```bash
pip install -U "mcp<2" starlette uvicorn websockets
```

2. Configure Claude Desktop:

Edit `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "recoll-search": {
      "command": "python3",
      "args": [
        "/home/sam/src/recoll-mcp-server/recoll_mcp_server.py"
      ],
      "env": {
        "RECOLL_CONFDIR": "/home/sam/.config/recoll"
      }
    }
  }
}
```

3. Restart Claude Desktop

## Usage Examples

Once configured, you can ask Claude:

- "Find my notes about YubiKey from December"
- "Search for PDFs containing 'machine learning'"
- "Show me files I modified this week"
- "Find markdown files about Nextcloud"

## Available Tools

### search_filesystem
Search using keywords or phrases with Boolean operators (AND, OR, NOT).

### search_by_date
Filter results by modification date range.

### search_by_filetype
Filter by file type/mimetype (pdf, markdown, text, etc.).

### get_document_content
Retrieve full content of a specific document.

### list_recent_files
List recently modified files in the index.

## Development

Test the Recoll API directly:
```bash
python test_recoll_api.py
```

## Architecture

```
User (natural language)
    ↓
Claude Desktop (with MCP)
    ↓
Recoll MCP Server (Python)
    ↓
Recoll Python API
    ↓
Xapian Index (your filesystem)
```

## License

Apache 2.0
