from typing import List, Optional
import aiohttp
from task_tracker.config import settings


class LinearClient:
    def __init__(self):
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": settings.LINEAR_API_KEY
        }

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

    async def create_task(self, title: str, description: str, assignee_id: Optional[str] = None) -> dict:
        """Create a new task in Linear"""
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
                "description": description,
                "assigneeId": assignee_id
            }
        }
        result = await self.execute_query(mutation, variables)
        if not result.get("data", {}).get("issueCreate", {}).get("success"):
            raise ValueError("Failed to create issue")
        return result["data"]["issueCreate"]["issue"]
