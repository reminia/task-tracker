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

    async def get_tasks(self, status: Optional[str] = None) -> List[dict]:
        """Fetch tasks from Linear with pagination"""
        query = """
        query Issues($after: String) {
            issues(first: 50, after: $after, orderBy: updatedAt) {
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
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        result = await self.execute_query(query)
        return result["data"]["issues"]["nodes"]

    async def set_current_team(self, team_name: str) -> None:
        """Set the current team ID for task operations"""
        team = await self.fetch_team(team_name)
        if not team:
            raise ValueError(f"Team '{team_name}' not found")
        self._current_team_id = team["id"]
        self._current_team_name = team["name"]

    async def get_current_team(self) -> Optional[dict]:
        """Get the current team's details"""
        if not self._current_team_id:
            return None

        query = """
        query Team($id: String!) {
            team(id: $id) {
                id
                name
            }
        }
        """
        result = await self.execute_query(query, {"id": self._current_team_id})
        return {
            "id": result["data"]["team"]["id"],
            "name": result["data"]["team"]["name"]
        }

    async def create_task(
        self,
        title: str,
        team_id: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None
    ) -> dict:
        """Create a new task in Linear

        Args:
            title: Task title
            team_id: Team ID (uses current team if not specified)
            description: Task description (optional)
            assignee_id: User ID to assign the task to (optional)
        """
        if not team_id and not self._current_team_id:
            raise ValueError(
                "team_id must be provided or current team must be set")

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
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                }
            }
        }
        """
        variables = {
            "input": {
                "title": title,
                "teamId": team_id or self._current_team_id,
                **({"description": description} if description else {}),
                **({"assigneeId": assignee_id} if assignee_id else {})
            }
        }

        result = await self.execute_query(mutation, variables)
        if not result.get("data", {}).get("issueCreate", {}).get("success"):
            raise ValueError("Failed to create issue")
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

    async def get_my_pending_tasks(self, states: Union[str, List[str]] = "unstarted") -> List[dict]:
        """Fetch tasks assigned to the authenticated user filtered by state(s)
        
        Args:
            states: State type(s) to filter by (default: "unstarted")
                   Can be a single state string or list of states
                   Valid values: "backlog", "unstarted", "started", "completed", "canceled", "triage"
        
        Returns:
            List[dict]: List of tasks matching the criteria
            
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
