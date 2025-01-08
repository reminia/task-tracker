# Task Tracker

A Model Context Protocol server that integrates Linear task management and TrackingTime time tracking.

## Features

- Integration with Linear API for task management
- Integration with TrackingTime for task time tracking

## Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/mcp-task-manager.git
cd mcp-task-manager
```

2. Run the setup script:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the MCP server:

```bash
python -m mcp_task_manager
```
