from skills.basic_skill import BasicSkill
import json
import requests
from typing import Dict, Any, Optional, List

class PostMessagePowerAutomateSkill(BasicSkill):
    def __init__(self):
        self.name = "PostMessagePowerAutomateSkill"
        self.metadata = {
            "name": self.name,
            "description": "Drafts an email with proper formatting and sends it to a Microsoft Power Automate flow endpoint for processing and delivery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "The subject line of the email."
                    },
                    "to": {
                        "type": "string",
                        "description": "Email address of the primary recipient."
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional. List of email addresses to CC."
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional. List of email addresses to BCC."
                    },
                    "body": {
                        "type": "string",
                        "description": "The full body of the email. This can include any content the caller desires."
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional. List of attachment file names or identifiers."
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional. Additional metadata for the email.",
                        "additionalProperties": True
                    }
                },
                "required": ["subject", "to", "body"],
                "example": {
                    "subject": "Project Update - Critical Milestones",
                    "to": "projectteam@example.com",
                    "cc": ["stakeholders@example.com"],
                    "bcc": ["manager@example.com"],
                    "body": "Dear Project Team,\n\nI hope this email finds you well...\n\nBest regards,\nProject Manager",
                    "attachments": ["ProjectReport.pdf", "ClientFeedback.docx"],
                    "metadata": {
                        "importance": "high",
                        "isHtml": True
                    }
                }
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(
        self,
        subject: str,
        to: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        importance: Optional[str] = "normal"
    ) -> str:
        try:
            # Ensure required parameters are provided and not empty
            if not subject.strip():
                raise ValueError("The 'subject' parameter is required and cannot be empty.")
            if not to.strip():
                raise ValueError("The 'to' parameter is required and cannot be empty.")
            if not body.strip():
                raise ValueError("The 'body' parameter is required and cannot be empty.")

            # Convert the plain text body to HTML by replacing line breaks with <br> tags
            body_html = body.replace('\n', '<br>')

            # Alternatively, wrap paragraphs in <p> tags
            # paragraphs = body.split('\n\n')
            # body_html = ''.join(f'<p>{p}</p>' for p in paragraphs)

            # Construct the email draft
            email_draft = {
                "subject": subject,
                "to": to,
                "cc": cc or [],
                "bcc": bcc or [],
                "body": body_html,
                "attachments": attachments or [],
                "metadata": {
                    "importance": importance,
                    "isHtml": True  # Indicate that the body is HTML
                }
            }

            # Power Automate flow URL
            url = (
                "https://prod-143.westus.logic.azure.com:443/workflows/78dd7c70ef7548c1ad560e28d65e4c77/"
                "triggers/manual/paths/invoke"
                "?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun"
                "&sv=1.0&sig=wY5I74anXiDOKf5N0YYzU9N9Y0-N61Vomuv00Y8-GCE"
            )

            # Prepare the payload for Power Automate
            payload = email_draft

            # Set up the headers for the request
            headers = {
                "Content-Type": "application/json"
            }

            # Send the POST request to Power Automate
            response = requests.post(url, json=payload, headers=headers)

            # Process the response
            if response.status_code in [200, 202]:
                return json.dumps({
                    "status": "success",
                    "message": "Email draft sent to Power Automate successfully",
                    "response": response.text[:1000]  # Truncate response to 1000 characters
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to send email draft to Power Automate. Status code: {response.status_code}",
                    "response": response.text[:1000]  # Truncate response to 1000 characters
                })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            })
