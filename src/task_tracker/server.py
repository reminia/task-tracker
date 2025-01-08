import asyncio
import json
import logging
from typing import Any, Dict, List

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from task_tracker.api.linear_client import LinearClient
from task_tracker.api.timetracking_client import TimeTrackingClient

linear_client = LinearClient()
timetracking_client = TimeTrackingClient()
server = Server("task-tracker")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("task-tracker")
logger.info("task-tracker server started")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="create_task",
            description="Create a new task",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "assignee_id": {"type": "string", "optional": True}
                },
                "required": ["title", "description"]
            }
        ),
        types.Tool(
            name="log_time",
            description="Log time for a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "duration": {"type": "integer"},
                    "description": {"type": "string"}
                },
                "required": ["task_id", "duration", "description"]
            }
        ),
        types.Tool(
            name="start_tracking",
            description="Start time tracking for a task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["task_id", "description"]
            }
        ),
        types.Tool(
            name="stop_tracking",
            description="Stop current time tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "entry_id": {"type": "string"}
                },
                "required": ["entry_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if not arguments:
            raise ValueError("Missing arguments")

        if name == "create_task":
            result = await linear_client.create_task(
                title=arguments["title"],
                description=arguments["description"],
                assignee_id=arguments.get("assignee_id")
            )
            return [types.TextContent(
                type="text",
                text=f"Task created successfully: {json.dumps(result, indent=2)}"
            )]

        elif name == "log_time":
            result = await timetracking_client.log_time(
                task_id=arguments["task_id"],
                duration=arguments["duration"],
                description=arguments["description"]
            )
            return [types.TextContent(
                type="text",
                text=f"Time logged successfully: {json.dumps(result, indent=2)}"
            )]

        elif name == "start_tracking":
            result = await timetracking_client.start_tracking(
                task_id=arguments["task_id"],
                description=arguments["description"]
            )
            return [types.TextContent(
                type="text",
                text=f"Time tracking started: {json.dumps(result, indent=2)}"
            )]

        elif name == "stop_tracking":
            result = await timetracking_client.stop_tracking(
                entry_id=arguments["entry_id"]
            )
            return [types.TextContent(
                type="text",
                text=f"Time tracking stopped: {json.dumps(result, indent=2)}"
            )]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="tasks://all",
            name="All Tasks",
            mimeType="application/json",
            description="List of all tasks"
        ),
        types.Resource(
            uri="time://entries",
            name="Time Entries",
            mimeType="application/json",
            description="List of time entries"
        ),
        types.Resource(
            uri="time://active",
            name="Active Time Tracking",
            mimeType="application/json",
            description="Currently active time tracking session"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource"""
    if uri == "tasks://all":
        tasks = await linear_client.get_tasks()
        return json.dumps(tasks, indent=2)
    elif uri == "time://entries":
        entries = await timetracking_client.get_time_entries()
        return json.dumps(entries, indent=2)
    elif uri == "time://active":
        active = await timetracking_client.get_active_tracking()
        return json.dumps(active, indent=2)
    raise ValueError(f"Unknown resource: {uri}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream=read_stream,
            write_stream=write_stream,
            initialization_options=InitializationOptions(
                server_name="task-tracker",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 