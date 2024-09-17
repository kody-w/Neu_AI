import json
import os
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from skills.basic_skill import BasicSkill

class DispatchSkill(BasicSkill):
    def __init__(self):
        self.name = "DispatchSkill"
        self.metadata = {
            "name": self.name,
            "description": "Handles dispatch commands with robust tracking, auditing, and features inspired by real-time social communication systems.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to perform. One of: 'create', 'retrieve', 'update', 'revert', 'list', 'audit', 'track', 'receive', 'send', 'forward', 'reply', 'archive', 'unarchive', 'flag', 'unflag', 'endorse', 'unendorse', 'reshare', 'unreshare', 'follow', 'unfollow'."
                    },
                    "user": {
                        "type": "string",
                        "description": "The user performing the action."
                    },
                    "dispatch_id": {
                        "type": "string",
                        "description": "The ID of the dispatch to act upon."
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the dispatch (max 280 characters)."
                    },
                    "mentions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Users mentioned in the dispatch."
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags used in the dispatch."
                    },
                    "category": {
                        "type": "string",
                        "description": "The category of the dispatch."
                    },
                    "priority": {
                        "type": "string",
                        "description": "The priority of the dispatch."
                    },
                    "status": {
                        "type": "string",
                        "description": "The status of the dispatch."
                    },
                    "version": {
                        "type": "integer",
                        "description": "The version number to revert to."
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for flagging a dispatch."
                    },
                    "recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recipients for sending or forwarding a dispatch."
                    },
                    "additional_content": {
                        "type": "string",
                        "description": "Additional content for forwarding a dispatch."
                    },
                    "target_user": {
                        "type": "string",
                        "description": "The user to follow or unfollow."
                    },
                },
                "required": ["command", "user"]
            }
        }

        self.storage_file = 'dispatches.json'
        self.audit_file = 'dispatch_audit.json'
        self.user_file = 'users.json'
        self.load_dispatches()
        self.load_audit_log()
        self.load_users()

    def load_dispatches(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                self.dispatches = json.load(f)
        else:
            self.dispatches = {}

    def save_dispatches(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.dispatches, f, indent=2)

    def load_audit_log(self):
        if os.path.exists(self.audit_file):
            with open(self.audit_file, 'r') as f:
                self.audit_log = json.load(f)
        else:
            self.audit_log = []

    def save_audit_log(self):
        with open(self.audit_file, 'w') as f:
            json.dump(self.audit_log, f, indent=2)

    def load_users(self):
        if os.path.exists(self.user_file):
            with open(self.user_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def save_users(self):
        with open(self.user_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def log_action(self, action: str, dispatch_id: str, user: str, details: Dict[str, Any]):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "dispatch_id": dispatch_id,
            "user": user,
            "details": details
        }
        self.audit_log.append(log_entry)
        self.save_audit_log()

    def perform(self, command: str, user: str, dispatch_id: Optional[str] = None, content: Optional[str] = None,
                mentions: Optional[List[str]] = None, tags: Optional[List[str]] = None,
                category: Optional[str] = None, priority: Optional[str] = None,
                status: Optional[str] = None, version: Optional[int] = None,
                reason: Optional[str] = None, recipients: Optional[List[str]] = None,
                additional_content: Optional[str] = None, target_user: Optional[str] = None) -> str:
        try:
            if command == "create":
                if content is None:
                    raise ValueError("Missing required parameter: 'content'")
                return self._create_dispatch(user, content, mentions, tags, category, priority)
            elif command == "retrieve":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._retrieve_dispatch(user, dispatch_id)
            elif command == "update":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._update_dispatch(user, dispatch_id, content, mentions, tags)
            elif command == "revert":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._revert_dispatch(user, dispatch_id, version)
            elif command == "list":
                return self._list_dispatches(user, category, tags, status, priority)
            elif command == "audit":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._audit_dispatch(user, dispatch_id)
            elif command == "track":
                if dispatch_id is None or status is None:
                    raise ValueError("Missing required parameters: 'dispatch_id' and 'status'")
                return self._track_dispatch(user, dispatch_id, status, content)
            elif command == "receive":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._receive_dispatch(user, dispatch_id)
            elif command == "send":
                if dispatch_id is None or recipients is None:
                    raise ValueError("Missing required parameters: 'dispatch_id' and 'recipients'")
                return self._send_dispatch(user, dispatch_id, recipients)
            elif command == "forward":
                if dispatch_id is None or recipients is None:
                    raise ValueError("Missing required parameters: 'dispatch_id' and 'recipients'")
                return self._forward_dispatch(user, dispatch_id, recipients, additional_content)
            elif command == "reply":
                if dispatch_id is None or content is None:
                    raise ValueError("Missing required parameters: 'dispatch_id' and 'content'")
                return self._reply_to_dispatch(user, dispatch_id, content, mentions, tags)
            elif command == "archive":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._archive_dispatch(user, dispatch_id)
            elif command == "unarchive":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._unarchive_dispatch(user, dispatch_id)
            elif command == "flag":
                if dispatch_id is None or reason is None:
                    raise ValueError("Missing required parameters: 'dispatch_id' and 'reason'")
                return self._flag_dispatch(user, dispatch_id, reason)
            elif command == "unflag":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._unflag_dispatch(user, dispatch_id)
            elif command == "endorse":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._endorse_dispatch(user, dispatch_id)
            elif command == "unendorse":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._unendorse_dispatch(user, dispatch_id)
            elif command == "reshare":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._reshare_dispatch(user, dispatch_id)
            elif command == "unreshare":
                if dispatch_id is None:
                    raise ValueError("Missing required parameter: 'dispatch_id'")
                return self._unreshare_dispatch(user, dispatch_id)
            elif command == "follow":
                if target_user is None:
                    raise ValueError("Missing required parameter: 'target_user'")
                return self._follow_user(user, target_user)
            elif command == "unfollow":
                if target_user is None:
                    raise ValueError("Missing required parameter: 'target_user'")
                return self._unfollow_user(user, target_user)
            else:
                return "Error: Invalid command."
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_action("error", dispatch_id or "N/A", user, {"error": error_msg})
            return error_msg

    def _create_dispatch(self, user: str, content: str, mentions: Optional[List[str]] = None,
                         tags: Optional[List[str]] = None, category: Optional[str] = None,
                         priority: Optional[str] = "medium") -> str:
        if len(content) > 280:
            raise ValueError("Content must not exceed 280 characters.")

        dispatch_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        new_dispatch = {
            "dispatch_id": dispatch_id,
            "content": content,
            "category": category or "general",
            "mentions": mentions or [],
            "tags": tags or [],
            "created_at": timestamp,
            "created_by": user,
            "priority": priority,
            "endorsements": [],
            "reshares": [],
            "reply_to": None,
            "replies": [],
            "thread_id": dispatch_id,
            "message_id": f"<{dispatch_id}@dispatch.local>",
            "checksum": self._calculate_checksum(content)
        }

        self.dispatches[dispatch_id] = new_dispatch
        self.save_dispatches()

        if user not in self.users:
            self.users[user] = {"feed": [], "followers": [], "following": []}
        self.users[user]["feed"].insert(0, dispatch_id)
        self.save_users()

        for mentioned_user in mentions or []:
            if mentioned_user in self.users:
                if "mentions" not in self.users[mentioned_user]:
                    self.users[mentioned_user]["mentions"] = []
                self.users[mentioned_user]["mentions"].insert(0, dispatch_id)

        self.log_action("create", dispatch_id, user, new_dispatch)

        return f"Dispatch created with ID: {dispatch_id}, Content: {content[:50]}..."

    def _retrieve_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")

        dispatch = self.dispatches[dispatch_id]
        self.log_action("retrieve", dispatch_id, user, {})

        return json.dumps(dispatch, indent=2)

    def _update_dispatch(self, user: str, dispatch_id: str, content: Optional[str] = None,
                         mentions: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if dispatch['created_by'] != user:
            raise ValueError("Only the creator of a dispatch can update it.")
        update_details = {}
        if content:
            if len(content) > 280:
                raise ValueError("Content must not exceed 280 characters.")
            update_details['content'] = f"Changed from '{dispatch['content']}' to '{content}'"
            dispatch['content'] = content
            dispatch['checksum'] = self._calculate_checksum(content)
        if mentions is not None:
            update_details['mentions'] = f"Changed from {dispatch['mentions']} to {mentions}"
            dispatch['mentions'] = mentions
        if tags is not None:
            update_details['tags'] = f"Changed from {dispatch['tags']} to {tags}"
            dispatch['tags'] = tags
        self.save_dispatches()
        self.log_action("update", dispatch_id, user, update_details)
        return f"Dispatch with ID {dispatch_id} has been updated."

    def _revert_dispatch(self, user: str, dispatch_id: str, version: Optional[int] = None) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if dispatch['created_by'] != user:
            raise ValueError("Only the creator of a dispatch can revert it.")
        if not dispatch.get('history'):
            return f"No previous versions available for dispatch with ID {dispatch_id}."
        if version is None:
            previous_version = dispatch['history'].pop()
        else:
            if version < 1 or version > len(dispatch['history']):
                raise ValueError(f"Invalid version number. Available versions: 1 to {len(dispatch['history'])}")
            previous_version = dispatch['history'][version - 1]
            dispatch['history'] = dispatch['history'][:version - 1]
        for key, value in previous_version.items():
            if key != 'history':
                dispatch[key] = value
        self.save_dispatches()
        self.log_action("revert", dispatch_id, user, {"reverted_to_version": version or len(dispatch.get('history', [])) + 1})
        return f"Dispatch with ID {dispatch_id} has been reverted to version {version or len(dispatch.get('history', [])) + 1}."

    def _list_dispatches(self, user: str, category: Optional[str] = None, tags: Optional[List[str]] = None,
                         status: Optional[str] = None, priority: Optional[str] = None) -> str:
        filtered_dispatches = self.dispatches.items()
        if category:
            filtered_dispatches = filter(lambda x: x[1]['category'] == category, filtered_dispatches)
        if tags:
            filtered_dispatches = filter(lambda x: set(tags).issubset(set(x[1]['tags'])), filtered_dispatches)
        if status:
            filtered_dispatches = filter(lambda x: x[1].get('status') == status, filtered_dispatches)
        if priority:
            filtered_dispatches = filter(lambda x: x[1]['priority'] == priority, filtered_dispatches)
        result = "List of dispatches:\n"
        for dispatch_id, dispatch in filtered_dispatches:
            result += (
                f"ID: {dispatch_id}, Content: {dispatch['content'][:50]}..., "
                f"Category: {dispatch['category']}, Priority: {dispatch['priority']}, "
                f"Created by: {dispatch['created_by']}, Created at: {dispatch['created_at']}, "
                f"Endorsements: {len(dispatch['endorsements'])}, Reshares: {len(dispatch['reshares'])}, "
                f"Replies: {len(dispatch['replies'])}\n"
            )
        self.log_action("list", "N/A", user, {"category": category, "tags": tags, "status": status, "priority": priority})
        return result if result != "List of dispatches:\n" else "No dispatches found matching the criteria."

    def _audit_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        audit_entries = [entry for entry in self.audit_log if entry['dispatch_id'] == dispatch_id]
        result = f"Audit log for dispatch ID {dispatch_id}:\n"
        for entry in audit_entries:
            result += (f"Timestamp: {entry['timestamp']}, Action: {entry['action']}, "
                       f"User: {entry['user']}, Details: {json.dumps(entry['details'])}\n")
        self.log_action("audit", dispatch_id, user, {})
        return result if audit_entries else f"No audit entries found for dispatch ID {dispatch_id}."

    def _track_dispatch(self, user: str, dispatch_id: str, status: str, notes: Optional[str] = None) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        tracking_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "status": status,
            "notes": notes or ""
        }
        if 'tracking' not in dispatch:
            dispatch['tracking'] = []
        dispatch['tracking'].append(tracking_entry)
        dispatch['status'] = status
        self.save_dispatches()
        self.log_action("track", dispatch_id, user, tracking_entry)
        return f"Tracking update added for dispatch ID {dispatch_id}. New status: {status}."

    def _receive_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if 'received_by' not in dispatch:
            dispatch['received_by'] = []
        if user not in dispatch['received_by']:
            dispatch['received_by'].append(user)
            dispatch['received_at'] = datetime.now().isoformat()
            self.save_dispatches()
            self.log_action("receive", dispatch_id, user, {})
            return f"Dispatch with ID {dispatch_id} has been marked as received by {user}."
        else:
            return f"Dispatch with ID {dispatch_id} was already received by {user}."

    def _send_dispatch(self, user: str, dispatch_id: str, recipients: List[str]) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if dispatch['created_by'] != user:
            raise ValueError("Only the creator of a dispatch can send it.")
        dispatch['sent_to'] = recipients
        dispatch['sent_at'] = datetime.now().isoformat()
        self.save_dispatches()
        for recipient in recipients:
            if recipient in self.users:
                if 'inbox' not in self.users[recipient]:
                    self.users[recipient]['inbox'] = []
                self.users[recipient]['inbox'].insert(0, dispatch_id)
        self.save_users()
        self.log_action("send", dispatch_id, user, {"recipients": recipients})
        return f"Dispatch with ID {dispatch_id} has been sent to {', '.join(recipients)}."

    def _forward_dispatch(self, user: str, dispatch_id: str, recipients: List[str], additional_content: Optional[str] = None) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        original_dispatch = self.dispatches[dispatch_id]
        forward_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        forwarded_content = f"Forwarded message:\n{original_dispatch['content']}"
        if additional_content:
            forwarded_content = f"{additional_content}\n\n{forwarded_content}"
        forward_dispatch = {
            "dispatch_id": forward_id,
            "content": forwarded_content,
            "category": original_dispatch['category'],
            "mentions": original_dispatch['mentions'],
            "tags": original_dispatch['tags'],
            "created_at": timestamp,
            "created_by": user,
            "priority": original_dispatch['priority'],
            "endorsements": [],
            "reshares": [],
            "reply_to": None,
            "replies": [],
            "thread_id": forward_id,
            "message_id": f"<{forward_id}@dispatch.local>",
            "checksum": self._calculate_checksum(forwarded_content),
            "forwarded_from": dispatch_id
        }
        self.dispatches[forward_id] = forward_dispatch
        self.save_dispatches()
        return self._send_dispatch(user, forward_id, recipients)

    def _reply_to_dispatch(self, user: str, dispatch_id: str, content: str,
                           mentions: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        if len(content) > 280:
            raise ValueError("Content must not exceed 280 characters.")
        original_dispatch = self.dispatches[dispatch_id]
        reply_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        reply_dispatch = {
            "dispatch_id": reply_id,
            "content": content,
            "mentions": mentions or [],
            "tags": tags or [],
            "created_at": timestamp,
            "created_by": user,
            "endorsements": [],
            "reshares": [],
            "reply_to": dispatch_id,
            "replies": [],
            "thread_id": original_dispatch['thread_id'],
            "message_id": f"<{reply_id}@dispatch.local>",
            "checksum": self._calculate_checksum(content)
        }
        self.dispatches[reply_id] = reply_dispatch
        original_dispatch['replies'].append(reply_id)
        self.save_dispatches()
        if user not in self.users:
            self.users[user] = {"feed": [], "followers": [], "following": []}
        self.users[user]["feed"].insert(0, reply_id)
        self.save_users()
        self.log_action("reply", reply_id, user, {"original_dispatch_id": dispatch_id})
        return f"Reply created for dispatch with ID {dispatch_id}. New dispatch ID: {reply_id}."

    def _archive_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if dispatch['created_by'] != user:
            raise ValueError("Only the creator of a dispatch can archive it.")
        dispatch['archived'] = True
        self.save_dispatches()
        self.log_action("archive", dispatch_id, user, {})
        return f"Dispatch with ID {dispatch_id} has been archived."

    def _unarchive_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if dispatch['created_by'] != user:
            raise ValueError("Only the creator of a dispatch can unarchive it.")
        dispatch['archived'] = False
        self.save_dispatches()
        self.log_action("unarchive", dispatch_id, user, {})
        return f"Dispatch with ID {dispatch_id} has been unarchived."

    def _flag_dispatch(self, user: str, dispatch_id: str, reason: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if 'flags' not in dispatch:
            dispatch['flags'] = []
        flag = {"user": user, "reason": reason, "timestamp": datetime.now().isoformat()}
        dispatch['flags'].append(flag)
        self.save_dispatches()
        self.log_action("flag", dispatch_id, user, {"reason": reason})
        return f"Dispatch with ID {dispatch_id} has been flagged by {user}."

    def _unflag_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if 'flags' not in dispatch or not any(flag['user'] == user for flag in dispatch['flags']):
            return f"No flags by {user} found for dispatch with ID {dispatch_id}."
        dispatch['flags'] = [flag for flag in dispatch['flags'] if flag['user'] != user]
        self.save_dispatches()
        self.log_action("unflag", dispatch_id, user, {})
        return f"All flags by {user} have been removed from dispatch with ID {dispatch_id}."

    def _endorse_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if user not in dispatch['endorsements']:
            dispatch['endorsements'].append(user)
            self.save_dispatches()
            self.log_action("endorse", dispatch_id, user, {})
            return f"Dispatch with ID {dispatch_id} has been endorsed by {user}."
        else:
            return f"Dispatch with ID {dispatch_id} is already endorsed by {user}."

    def _unendorse_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if user in dispatch['endorsements']:
            dispatch['endorsements'].remove(user)
            self.save_dispatches()
            self.log_action("unendorse", dispatch_id, user, {})
            return f"Endorsement removed from dispatch with ID {dispatch_id} by {user}."
        else:
            return f"Dispatch with ID {dispatch_id} is not endorsed by {user}."

    def _reshare_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if user not in dispatch['reshares']:
            dispatch['reshares'].append(user)
            self.save_dispatches()
            if user not in self.users:
                self.users[user] = {"feed": [], "followers": [], "following": []}
            self.users[user]["feed"].insert(0, dispatch_id)
            self.save_users()
            self.log_action("reshare", dispatch_id, user, {})
            return f"Dispatch with ID {dispatch_id} has been reshared by {user}."
        else:
            return f"Dispatch with ID {dispatch_id} is already reshared by {user}."

    def _unreshare_dispatch(self, user: str, dispatch_id: str) -> str:
        if dispatch_id not in self.dispatches:
            raise ValueError("'dispatch_id' does not exist.")
        dispatch = self.dispatches[dispatch_id]
        if user in dispatch['reshares']:
            dispatch['reshares'].remove(user)
            self.save_dispatches()
            if user in self.users and dispatch_id in self.users[user]["feed"]:
                self.users[user]["feed"].remove(dispatch_id)
                self.save_users()
            self.log_action("unreshare", dispatch_id, user, {})
            return f"Reshare removed from dispatch with ID {dispatch_id} by {user}."
        else:
            return f"Dispatch with ID {dispatch_id} is not reshared by {user}."

    def _follow_user(self, user: str, target_user: str) -> str:
        if user == target_user:
            return "You cannot follow yourself."
        if user not in self.users:
            self.users[user] = {"feed": [], "followers": [], "following": []}
        if target_user not in self.users:
            self.users[target_user] = {"feed": [], "followers": [], "following": []}
        if target_user not in self.users[user]["following"]:
            self.users[user]["following"].append(target_user)
            self.users[target_user]["followers"].append(user)
            self.save_users()
            self.log_action("follow", "N/A", user, {"target_user": target_user})
            return f"{user} is now following {target_user}."
        else:
            return f"{user} is already following {target_user}."

    def _unfollow_user(self, user: str, target_user: str) -> str:
        if user not in self.users or target_user not in self.users:
            return "User not found."
        if target_user in self.users[user]["following"]:
            self.users[user]["following"].remove(target_user)
            self.users[target_user]["followers"].remove(user)
            self.save_users()
            self.log_action("unfollow", "N/A", user, {"target_user": target_user})
            return f"{user} has unfollowed {target_user}."
        else:
            return f"{user} is not following {target_user}."

    def _calculate_checksum(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()
