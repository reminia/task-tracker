# Task Tracker

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![ci](https://github.com/reminia/task-tracker/actions/workflows/ci.yml/badge.svg)

A Model Context Protocol server that integrates Linear task management and TrackingTime time tracking.

## Features

- Integration with Linear API for task management
- Integration with TrackingTime for task time tracking

## Setup

1. setup the environment, refer to the [.env.example](.env.example) file.
2. `sh scripts/setup.sh` to build the package or run below uv commands directly.

  ```bash
  uv build 
  uv run task-tracker
  ```
