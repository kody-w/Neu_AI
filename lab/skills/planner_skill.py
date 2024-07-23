from skills.basic_skill import BasicSkill
from datetime import datetime, timedelta
import json

class PlannerSkill(BasicSkill):
    def __init__(self):
        self.name = "Planner"
        self.metadata = {
            "name": self.name,
            "description": "Creates and manages both short-term and long-term plans for tasks or goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "The action to perform: 'create', 'update', 'delete', or 'view'"
                    },
                    "plan_type": {
                        "type": "string",
                        "description": "The type of plan: 'short_term' or 'long_term'"
                    },
                    "task": {
                        "type": "string",
                        "description": "The task or goal to plan for"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "The due date for the task (format: YYYY-MM-DD)"
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of steps to accomplish the task"
                    }
                },
                "required": ["action", "plan_type"]
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)
        self.plans_file = "plans.json"

    def perform(self, action, plan_type, task=None, due_date=None, steps=None):
        if action == "create":
            return self.create_plan(plan_type, task, due_date, steps)
        elif action == "update":
            return self.update_plan(plan_type, task, due_date, steps)
        elif action == "delete":
            return self.delete_plan(plan_type, task)
        elif action == "view":
            return self.view_plans(plan_type)
        else:
            return "Invalid action. Please use 'create', 'update', 'delete', or 'view'."

    def load_plans(self):
        try:
            with open(self.plans_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {"short_term": {}, "long_term": {}}

    def save_plans(self, plans):
        with open(self.plans_file, 'w') as file:
            json.dump(plans, file, indent=2)

    def create_plan(self, plan_type, task, due_date, steps):
        plans = self.load_plans()
        if task in plans[plan_type]:
            return f"A {plan_type} plan for '{task}' already exists."
        
        plans[plan_type][task] = {
            "due_date": due_date,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "status": "In Progress"
        }
        self.save_plans(plans)
        return f"Created a new {plan_type} plan for '{task}'."

    def update_plan(self, plan_type, task, due_date, steps):
        plans = self.load_plans()
        if task not in plans[plan_type]:
            return f"No {plan_type} plan found for '{task}'."
        
        plans[plan_type][task]["due_date"] = due_date
        plans[plan_type][task]["steps"] = steps
        plans[plan_type][task]["updated_at"] = datetime.now().isoformat()
        self.save_plans(plans)
        return f"Updated the {plan_type} plan for '{task}'."

    def delete_plan(self, plan_type, task):
        plans = self.load_plans()
        if task not in plans[plan_type]:
            return f"No {plan_type} plan found for '{task}'."
        
        del plans[plan_type][task]
        self.save_plans(plans)
        return f"Deleted the {plan_type} plan for '{task}'."

    def view_plans(self, plan_type):
        plans = self.load_plans()
        if not plans[plan_type]:
            return f"No {plan_type} plans found."
        
        output = f"{plan_type.capitalize()} Plans:\n"
        for task, details in plans[plan_type].items():
            output += f"\nTask: {task}\n"
            output += f"Due Date: {details['due_date']}\n"
            output += f"Status: {details['status']}\n"
            output += "Steps:\n"
            for i, step in enumerate(details['steps'], 1):
                output += f"  {i}. {step}\n"
        
        return output