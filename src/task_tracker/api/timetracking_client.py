from typing import Optional
import aiohttp
from datetime import datetime
from task_tracker.config import settings

class TimeTrackingClient:
    def __init__(self):
        self.api_key = settings.TIMETRACKING_API_KEY
        self.base_url = "https://api.trackingtime.co/v4"
        self.auth = aiohttp.BasicAuth(self.api_key, 'api-token')
        self.headers = {"Content-Type": "application/json"}

    async def start_tracking(self, task_id: str, description: str) -> dict:
        """Start time tracking for a task using TrackingTime API

        Args:
            task_id: The ID of the task to track
            description: Description of the time entry

        Returns:
            dict: Response from TrackingTime API containing the tracking session details
        """
        async with aiohttp.ClientSession(auth=self.auth, headers=self.headers) as session:
            async with session.post(
                f"{self.base_url}/time_entries/start",
                json={
                    "task_id": task_id,
                    "description": description,
                    "start_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
                    "end_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
