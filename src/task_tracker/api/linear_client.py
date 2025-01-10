from typing import List, Optional, Union
import aiohttp
from task_tracker.config import settings


class LinearClient:
    def __init__(self):
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": settings.LINEAR_API_KEY
        }
        self._current_team_id = None
        self._current_team_name = None
        self._current_user_id = None
        self._current_user_name = None

    @classmethod
    async def create(cls, team_name: Optional[str] = settings.LINEAR_TEAM) -> "LinearClient":
        client = cls()
        if team_name:
            await client.set_current_team(team_name)
        user = await client.get_current_user()
        client._current_user_id = user["id"]
        client._current_user_name = user["name"]
        return client

    async def execute_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query against Linear API"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json={"query": query, "variables": variables or {}},
                headers=self.headers
            ) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    raise ValueError(f"Linear API error: {error_data}")
                return await response.json()

    async def get_current_user(self) -> dict:
        """Get details of the authenticated user

        Returns:
            dict: User details including id, name and email

        Raises:
            ValueError: If the API request fails
        """
        query = """
        query Me {
            viewer {
                id
                name
                email
            }
        }
        """
        result = await self.execute_query(query)
        return result["data"]["viewer"]

    async def set_current_team(self, team_name: str) -> None:
        """Set the current team ID for task operations"""
        team = await self.fetch_team(team_name)
        if not team:
            raise ValueError(f"Team '{team_name}' not found")
        self._current_team_id = team["id"]
        self._current_team_name = team["name"]

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        project: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> dict:
        """Create a new task in Linear

        Args:
            title: Task title
            description: Task description (optional)
            project: Project name to associate the task with (optional)
            team_id: Team ID (uses current team if not specified)
        """
        if not team_id and not self._current_team_id:
            raise ValueError(
                "team_id must be provided or current team must be set")

        project_id = None
        if project:
            project = await self.fetch_project(project)
            if project:
                project_id = project["id"]
            else:
                raise ValueError(f"Project '{project}' not found")

        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    project {
                        name
                    }
                    assignee {
                        id
                    }
                    createdAt
                    updatedAt
                }
            }
        }
        """
        variables = {
            "input": {
                "title": title,
                "teamId": team_id or self._current_team_id,
                "description": description if description else None,
                "projectId": project_id if project_id else None,
                "assigneeId": self._current_user_id if self._current_user_id else None,
            }
        }

        result = await self.execute_query(mutation, variables)
        if not result.get("data", {}).get("issueCreate", {}).get("success"):
            raise ValueError("Failed to create task")

        return result["data"]["issueCreate"]["issue"]

    async def fetch_team(self, team_name: str) -> Optional[dict]:
        """Get team details by team name

        Args:
            team_name: Name of the team to find

        Returns:
            Optional[dict]: Team details if found, None otherwise
        """
        query = """
        query Teams($filter: TeamFilter) {
            teams(filter: $filter) {
                nodes {
                    id
                    name
                    key
                    description
                }
            }
        }
        """
        variables = {
            "filter": {
                "name": {"eq": team_name}
            }
        }

        result = await self.execute_query(query, variables)
        teams = result["data"]["teams"]["nodes"]
        return teams[0] if teams else None

    async def filter_tasks(self, states: Union[str, List[str]] = "unstarted") -> List[dict]:
        """Fetch tasks assigned to the authenticated user filtered by state(s)

        Args:
            states: State type(s) to filter by (default: "unstarted")
                   Can be a single state string or list of states
                   Valid values: "backlog", "unstarted", "started", "completed", "canceled", "triage"

        Returns:
            List[dict]: List of tasks matching the criteria, including project information

        Raises:
            ValueError: If no current team is set
        """
        if not self._current_team_id:
            raise ValueError("Current team must be set before fetching tasks")

        # Convert single state to list for consistent handling
        state_list = [states] if isinstance(states, str) else states

        query = """
        query MyIssues($teamId: ID!, $states: [String!]!) {
            issues(
                first: 50,
                filter: {
                    assignee: { isMe: { eq: true } },
                    state: { type: { in: $states } },
                    team: { id: { eq: $teamId } }
                },
                orderBy: updatedAt
            ) {
                nodes {
                    id
                    identifier
                    title
                    description
                    project {
                        id
                        name
                    }
                    state {
                        id
                        name
                        type
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    updatedAt
                }
            }
        }
        """
        result = await self.execute_query(
            query,
            {
                "teamId": self._current_team_id,
                "states": state_list
            }
        )
        return result["data"]["issues"]["nodes"]

    async def search_tasks(self, search_term: str) -> List[dict]:
        """Search for tasks by title/description across the current team

        Args:
            search_term: Text to search for in task titles and descriptions

        Returns:
            List[dict]: List of tasks matching the search criteria

        Raises:
            ValueError: If no current team is set
        """
        if not self._current_team_id:
            raise ValueError("Current team must be set before searching tasks")

        query = """
        query SearchIssues($teamId: ID!, $searchTerm: String!) {
            issues(
                first: 50,
                filter: {
                    team: { id: { eq: $teamId } },
                    or: [
                        { title: { contains: $searchTerm } },
                        { description: { contains: $searchTerm } }
                    ]
                },
                orderBy: updatedAt
            ) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state {
                        id
                        name
                        type
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    updatedAt
                }
            }
        }
        """
        result = await self.execute_query(
            query,
            {
                "teamId": self._current_team_id,
                "searchTerm": search_term
            }
        )
        return result["data"]["issues"]["nodes"]

    async def fetch_project(self, project: str) -> Optional[dict]:
        """Get project details by project name within the current team

        Args:
            project: Name of the project to find

        Returns:
            Optional[dict]: Project details

        Raises:
            ValueError: If no current team is set
        """
        if not self._current_team_id:
            raise ValueError(
                "Current team must be set before fetching project")

        query = """
        query Projects($name: String!) {
            projects(filter: { name: { eq: $name } }) {
                nodes {
                    id
                    name
                    description
                    teams {
                        nodes {
                            id
                        }
                    }
                }
            }
        }
        """
        variables = {
            "name": project
        }

        result = await self.execute_query(query, variables)
        projects = result["data"]["projects"]["nodes"]
        # Filter projects by team ID
        for project in projects:
            team_ids = [team["id"] for team in project["teams"]["nodes"]]
            if self._current_team_id in team_ids:
                return {
                    "id": project["id"],
                    "name": project["name"],
                    "description": project["description"]
                }

        raise ValueError(f"Project '{project}' not found in current team")
