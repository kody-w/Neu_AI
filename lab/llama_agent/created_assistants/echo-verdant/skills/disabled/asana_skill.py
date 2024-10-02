from skills.basic_skill import BasicSkill
import asana
from asana.rest import ApiException
import json
import os
from datetime import datetime, timedelta

class AsanaSkill(BasicSkill):
    def __init__(self):
        self.name = 'AsanaSkill'
        self.metadata = {
            "name": self.name,
            "description": "Manages tasks and projects in Asana",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_project", "create_task", "get_projects", "get_tasks"],
                        "description": "The Asana action to perform"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "The name of the project (for create_project action)"
                    },
                    "task_name": {
                        "type": "string",
                        "description": "The name of the task (for create_task action)"
                    },
                    "project_gid": {
                        "type": "string",
                        "description": "The GID of the project (for create_task and get_tasks actions)"
                    },
                    "due_on": {
                        "type": "string",
                        "description": "The due date for the task or project (format: YYYY-MM-DD)"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        
        configuration = asana.Configuration()
        configuration.access_token = os.getenv('ASANA_ACCESS_TOKEN', '')
        self.api_client = asana.ApiClient(configuration)
        self.projects_api = asana.ProjectsApi(self.api_client)
        self.tasks_api = asana.TasksApi(self.api_client)
        self.workspace_gid = os.getenv("ASANA_WORKPLACE_ID", "")

    def perform(self, action, **params):
        """
        Perform the specified Asana action with the given parameters.

        Args:
            action (str): The Asana action to perform.
            **params: Additional parameters for the action.

        Returns:
            str: The result of the Asana action.
        """
        actions = {
            "create_project": self.create_project,
            "create_task": self.create_task,
            "get_projects": self.get_projects,
            "get_tasks": self.get_tasks
        }
        if action not in actions:
            return f"Invalid action: {action}. Valid actions are: {', '.join(actions.keys())}"
        return actions[action](**params)

    def create_project(self, project_name, due_on=None):
        """
        Create a new project in Asana.

        Args:
            project_name (str): The name of the project.
            due_on (str, optional): The due date of the project (format: YYYY-MM-DD).

        Returns:
            str: A message indicating the result of the project creation.
        """
        body = {
            "data": {
                "name": project_name,
                "due_on": due_on,
                "workspace": self.workspace_gid
            }
        }
        try:
            api_response = self.projects_api.create_project(body, {})
            return f"Project '{project_name}' created successfully with GID: {api_response.get('gid')}"
        except ApiException as e:
            return f"Exception when calling ProjectsApi->create_project: {e}"

    def create_task(self, task_name, project_gid, due_on=None):
        """
        Create a new task in Asana.

        Args:
            task_name (str): The name of the task.
            project_gid (str): The GID of the project to add the task to.
            due_on (str, optional): The due date of the task (format: YYYY-MM-DD).

        Returns:
            str: A message indicating the result of the task creation.
        """
        task_body = {
            "data": {
                "name": task_name,
                "due_on": due_on,
                "projects": [project_gid]
            }
        }
        try:
            api_response = self.tasks_api.create_task(task_body, {})
            return f"Task '{task_name}' created successfully with GID: {api_response.get('gid')}"
        except ApiException as e:
            return f"Exception when calling TasksApi->create_task: {e}"

    def get_projects(self):
        """
        Get all projects in the Asana workspace.

        Returns:
            str: A JSON string containing the list of projects.
        """
        opts = {
            'limit': 50,
            'workspace': self.workspace_gid,
            'archived': False
        }
        try:
            api_response = self.projects_api.get_projects(opts)
            return json.dumps(list(api_response), indent=2)
        except ApiException as e:
            return f"Exception when calling ProjectsApi->get_projects: {e}"

    def get_tasks(self, project_gid):
        """
        Get all tasks in a specific Asana project.

        Args:
            project_gid (str): The GID of the project to fetch tasks from.

        Returns:
            str: A JSON string containing the list of tasks.
        """
        opts = {
            'project': project_gid,
            'limit': 50,
            'opt_fields': "name,due_on,completed"
        }
        try:
            api_response = self.tasks_api.get_tasks(opts)
            return json.dumps(list(api_response), indent=2)
        except ApiException as e:
            return f"Exception when calling TasksApi->get_tasks: {e}"