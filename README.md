# Task Tracker

![ci](https://github.com/reminia/task-tracker/actions/workflows/ci.yml/badge.svg)

A Model Context Protocol server that integrates Linear task management and TrackingTime time tracking.

![task-tracker-demo](https://res.cloudinary.com/leecy-me/image/upload/v1736674972/open/tasktracker_fd3neu.gif)

## Motivation

I've been using Linear for task management and TrackingTime for time tracking for a long time. I found it could be very helpful to use LLM to automate my workflows and tasks.
With the benifits of large language models, I can use natural language to create tasks, update task statuses, start and stop time tracking, and more.

If I develop more MCP servers tailored to my own needs, I can make the Claude client an all-in-one workspace for me.

## Features

- Integration with Linear API for task management
  - Create new task with optional project, description and state assignments
  - Set current working team
  - Get projects
  - View tasks by status (backlog, todo, duplicate, in progress, done, canceled)
  - Search tasks by title
  - Update task status
- Integration with TrackingTime for task time tracking
  - Start time tracking for tasks
  - Stop active time tracking
  - View currently active tracked task
  - Add notes to tracking task

## Setup

1. setup the environment, refer to the [.env.example](.env.example) file.
2. `sh scripts/setup.sh` to build the package or run below uv commands directly.

  ```bash
  uv build 
  uv run task-tracker
  ```

3. setup it in the Claude Desktop:

  ```json
  {
  "mcpServers": {
      "task-tracker": {
          "command": "uv",
          "args": [
              "--directory",
              "/path/to/task-tracker",
              "run",
              "task-tracker"
          ]
      }
  }
}
```
