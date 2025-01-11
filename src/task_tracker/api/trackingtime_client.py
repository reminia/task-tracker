from typing import Optional
import aiohttp
from datetime import datetime
from task_tracker.config import settings
from task_tracker.logger import get_logger

logger = get_logger(__name__)


class TrackingTimeClient:
    def __init__(
        self,
        username: Optional[str] = settings.TRACKINGTIME_USERNAME,
        password: Optional[str] = settings.TRACKINGTIME_PASSWORD
    ):
        self.base_url = "https://app.trackingtime.co/api/v4"
        self.headers = {"Content-Type": "application/json"}

        if username and password:
            self.auth = aiohttp.BasicAuth(username, password)
        else:
            self.api_key = settings.TRACKINGTIME_API_KEY
            self.auth = aiohttp.BasicAuth.decode(f"Basic {self.api_key}")

    async def start_tracking(self, project: str, task: str) -> dict:
        """Start time tracking a task

        Args:
            project: name of the project to create the task in
            description: description of the task

        Returns:
            dict: json containing the tracking_task_id
        """
        async with aiohttp.ClientSession(auth=self.auth) as session:
            # Get local time
            local_tz = datetime.now().astimezone().tzinfo
            current_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

            async with session.post(
                f"{self.base_url}/tasks/track",
                params={
                    "date": current_time,
                    "task_name": task,
                    "project_name": project,
                    "return_task": "true",
                }
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def stop_tracking(self, task_id: str) -> dict:
        """Stop time tracking a task given its ID

        Args:
            task_id: The ID of the task to stop

        Returns:
            dict: Response from TrackingTime API containing the task details
        """
        async with aiohttp.ClientSession(auth=self.auth, headers=self.headers) as session:
            # stop and start timezone must match, otherwise server 500
            local_tz = datetime.now().astimezone().tzinfo
            current_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")

            async with session.post(
                f"{self.base_url}/tasks/stop",
                params={
                    "date": current_time,
                    "task_id": task_id,
                    "return_task": "true"
                }
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_tracking_task(self, filter: str = "TRACKING") -> Optional[dict]:
        """Fetch the tracking task with the given filter, defaults to "TRACKING"

        Returns:
            Optional[dict]: Active time entry if exists, None otherwise
        """
        async with aiohttp.ClientSession(auth=self.auth, headers=self.headers) as session:
            async with session.get(
                f"{self.base_url}/tasks",
                params={
                    "filter": filter
                }
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def update_entry_notes(self, event_id: str, notes: str) -> dict:
        """Update the notes for a time entry

        Args:
            event_id: The ID of the active tracking event to update
            notes: Notes to add to the time entry (up to 5000 characters)

        Returns:
            dict: Response from TrackingTime API containing the updated entry details
        """
        async with aiohttp.ClientSession(auth=self.auth, headers=self.headers) as session:
            # stop and start timezone must match, otherwise server 500
            local_tz = datetime.now().astimezone().tzinfo
            current_time = datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S")
            async with session.post(
                f"{self.base_url}/events/update/{event_id}",
                params={
                    "notes": notes,
                }
            ) as response:
                if not response.ok:
                    logger.error(f"Failed to update entry notes: {await response.text()}")
                    response.raise_for_status()
                return await response.json()
