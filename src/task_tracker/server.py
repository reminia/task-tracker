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

linear_client = asyncio.run(LinearClient.create())
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
            description="Create a new task in Linear",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string", "optional": True},
                    "assignee_id": {"type": "string", "optional": True},
                    "team_id": {"type": "string"}
                },
                "required": ["title", "team_id"]
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
                    "project": {
                        "type": "string",
                        "description": "task project"
                    },
                    "description": {
                        "type": "string",
                        "description": "task name"
                    }
                },
                "required": ["project", "description"]
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
        ),
        types.Tool(
            name="set_current_team",
            description="Set the current team by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "team_name": {"type": "string"}
                },
                "required": ["team_name"]
            }
        ),
        types.Tool(
            name="get_my_tasks",
            description="Get tasks assigned to me. Support task status: backlog, unstarted, started, completed, canceled, triage. Default is unstarted.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "array",
                        "items": {"type": "string"},
                        "optional": True,
                        "description": "List of task status to filter by"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="search_tasks",
            description="Search for tasks by title or identifier",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Text to search for in task titles or identifiers"
                    }
                },
                "required": ["search_term"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if arguments is None:
            raise ValueError("Missing arguments")

        if name == "create_task":
            result = await linear_client.create_task(
                title=arguments["title"],
                description=arguments.get("description"),
                assignee_id=arguments.get("assignee_id"),
                team_id=arguments.get("team_id")
            )
            return [types.TextContent(
                type="text",
                text=f"Task created successfully: {
                    json.dumps(result, indent=2)}"
            )]

        elif name == "log_time":
            result = await timetracking_client.log_time(
                task_id=arguments["task_id"],
                duration=arguments["duration"],
                description=arguments["description"]
            )
            return [types.TextContent(
                type="text",
                text=f"Time logged successfully: {
                    json.dumps(result, indent=2)}"
            )]

        elif name == "start_tracking":
            result = await timetracking_client.start_tracking(
                project=arguments["project"],
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

        elif name == "set_current_team":
            team_name = arguments["team_name"]
            await linear_client.set_current_team(team_name)
            return [types.TextContent(
                type="text",
                text=f"Set current team to: {team_name}"
            )]

        elif name == "get_my_tasks":
            states = arguments.get("states", ["unstarted"])
            tasks = await linear_client.get_tasks(states=states)
            return [types.TextContent(
                type="text",
                text=f"Your pending tasks:\n{json.dumps(tasks, indent=2)}"
            )]

        elif name == "search_tasks":
            search_term = arguments.get("search_term")
            if not search_term:
                return [types.TextContent(
                    type="text",
                    text="Please provide a search term"
                )]

            tasks = await linear_client.search_tasks(search_term)
            if not tasks:
                return [types.TextContent(
                    type="text",
                    text=f"No tasks found matching '{search_term}'"
                )]

            return [types.TextContent(
                type="text",
                text=f"Found {len(tasks)} tasks matching '{search_term}':\n{
                    json.dumps(tasks, indent=2)}"
            )]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


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
