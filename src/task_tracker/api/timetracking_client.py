from typing import Optional, Union
import aiohttp
from datetime import datetime, timezone
from task_tracker.config import settings


class TimeTrackingClient:
    def __init__(self):
        self.api_key = settings.TIMETRACKING_API_KEY
        self.base_url = "https://app.trackingtime.co/api/v4"
        self.auth = aiohttp.BasicAuth.decode(f"Basic {self.api_key}")
        self.headers = {"Content-Type": "application/json"}

    async def start_tracking(self, project: str, description: str) -> Union[dict, str]:
        """Start tracking a task

        Args:
            project: Name of the project to create the task in
            description: Description/name of the task

        Returns:
            Union[dict, str]: Response from TrackingTime API - either JSON dict or raw text if not JSON
        """
        async with aiohttp.ClientSession(auth=self.auth) as session:
            current_time = datetime.now(
                timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            async with session.post(
                f"{self.base_url}/tasks/track",
                params={
                    "date": current_time,
                    "task_name": description,
                    "project_name": project
                }
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def stop_tracking(self, entry_id: str) -> dict:
        """Stop time tracking for a task using TrackingTime API

        Args:
            entry_id: The ID of the time entry to stop

        Returns:
            dict: Response from TrackingTime API containing the completed time entry
        """
        async with aiohttp.ClientSession(auth=self.auth, headers=self.headers) as session:
            async with session.post(
                f"{self.base_url}/time_entries/{entry_id}/stop",
                json={
                    "end_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                }
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_active_tracking(self) -> Optional[dict]:
        """Get currently active tracking session if any using TrackingTime API

        Returns:
            Optional[dict]: Active time entry if exists, None otherwise
        """
        async with aiohttp.ClientSession(auth=self.auth, headers=self.headers) as session:
            async with session.get(f"{self.base_url}/time_entries/current") as response:
                response.raise_for_status()
                return await response.json()
