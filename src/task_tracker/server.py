import asyncio
import json
from typing import Any, Dict, List

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from task_tracker.api.linear_client import LinearClient
from task_tracker.api.trackingtime_client import TrackingTimeClient
from task_tracker.logger import get_logger

logger = get_logger(__name__)
logger.info("starting task-tracker server")

linear_client = asyncio.run(LinearClient.create())
trackingtime_client = TrackingTimeClient()
server = Server("task-tracker")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="create_task",
            description="Create a new task in Linear, you can specify the project and team",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string", "optional": True},
                    "team_id": {"type": "string", "optional": True},
                    "project": {"type": "string", "optional": True}
                },
                "required": ["title"]
            }
        ),
        types.Tool(
            name="set_current_team",
            description="Set the current Linear team by name",
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
            description=(
                "Get the Linear tasks assigned to me. "
                "Support task status: backlog, unstarted, started, completed, canceled, triage. "
                "Default is unstarted."
            ),
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
            description="Search Linear tasks by title",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Text to search for in task titles"
                    }
                },
                "required": ["search_term"]
            }
        ),
        types.Tool(
            name="get_all_projects",
            description="Get all Linear projects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
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
                    "task": {
                        "type": "string",
                        "description": "task name which is composed by identifier and title"
                    }
                },
                "required": ["project", "task"]
            }
        ),
        types.Tool(
            name="stop_tracking",
            description="Stop current time tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "task id"
                    },
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="get_active_tracking",
            description="Get the currently active tracking task",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="update_task_status",
            description="Update a Linear task's status",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status (backlog, unstarted, started, done, canceled)"
                    }
                },
                "required": ["task_id", "status"]
            }
        ),
        types.Tool(
            name="add_tracking_note",
            description="Add a note to the current tracking entry",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "ID of the active tracking event to add notes to"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes to add to the time entry"
                    }
                },
                "required": ["event_id", "notes"]
            }
        ),
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
                project=arguments.get("project"),
                team_id=arguments.get("team_id")
            )
            return [types.TextContent(
                type="text",
                text=f"Task created successfully: {
                    json.dumps(result, indent=2)}"
            )]

        elif name == "set_current_team":
            team_name = arguments["team_name"]
            await linear_client.set_current_team(team_name)
            return [types.TextContent(
                type="text",
                text=f"Set current team to: {team_name}"
            )]

        elif name == "get_my_tasks":
            states = arguments.get("status", ["unstarted"])
            tasks = await linear_client.filter_tasks(states=states)
            return [types.TextContent(
                type="text",
                text=f"Your tasks:\n{json.dumps(tasks, indent=2)}"
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

        elif name == "get_all_projects":
            projects = await linear_client.get_projects()
            return [types.TextContent(
                type="text",
                text=f"All your projects:\n{
                    json.dumps(projects, indent=2)}"
            )]

        elif name == "update_task_status":
            result = await linear_client.update_task_status(
                task_id=arguments["task_id"],
                status=arguments["status"]
            )
            return [types.TextContent(
                type="text",
                text=f"Task status updated successfully: {
                    json.dumps(result, indent=2)}"
            )]

        elif name == "start_tracking":
            result = await trackingtime_client.start_tracking(
                project=arguments["project"],
                task=arguments["task"]
            )
            return [types.TextContent(
                type="text",
                text=f"Time tracking started: {json.dumps(result, indent=2)}"
            )]

        elif name == "stop_tracking":
            result = await trackingtime_client.stop_tracking(
                task_id=arguments["task_id"]
            )
            return [types.TextContent(
                type="text",
                text=f"Time tracking stopped: {json.dumps(result, indent=2)}"
            )]

        elif name == "get_active_tracking":
            result = await trackingtime_client.get_tracking_task(filter="TRACKING")
            if not result:
                return [types.TextContent(
                    type="text",
                    text="No active time tracking task found"
                )]
            return [types.TextContent(
                type="text",
                text=f"Current tracking task:\n{json.dumps(result, indent=2)}"
            )]

        elif name == "add_tracking_note":
            result = await trackingtime_client.update_entry_notes(
                event_id=arguments["event_id"],
                notes=arguments["notes"]
            )
            return [types.TextContent(
                type="text",
                text=f"Added note to tracking entry: {
                    json.dumps(result, indent=2)}"
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
