# apps/pulser-hub/handlers/github.py
"""GitHub App webhook handler for Pulser-Hub.

Handles GitHub webhooks for the InsightPulseAI GitHub App:
- App ID: 2191216
- Client ID: Iv23liwGL7fnYySPPAjS
- Repository: Insightpulseai-net/pulser-agent-framework
"""

import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import httpx
import jwt
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


class GitHubEventType(str, Enum):
    """Supported GitHub webhook event types."""

    PUSH = "push"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    CHECK_RUN = "check_run"
    CHECK_SUITE = "check_suite"
    WORKFLOW_RUN = "workflow_run"
    INSTALLATION = "installation"
    INSTALLATION_REPOSITORIES = "installation_repositories"


@dataclass
class WebhookPayload:
    """Parsed GitHub webhook payload."""

    event_type: GitHubEventType
    action: Optional[str]
    repository: str
    sender: str
    delivery_id: str
    raw_payload: dict
    timestamp: datetime


class GitHubWebhookHandler:
    """Handler for GitHub App webhooks.

    Validates webhook signatures, parses payloads, and dispatches
    to appropriate handlers based on event type.
    """

    def __init__(
        self,
        app_id: str = None,
        private_key: str = None,
        webhook_secret: str = None,
        client_id: str = None,
    ):
        """Initialize the webhook handler.

        Args:
            app_id: GitHub App ID (default from env: GITHUB_APP_ID)
            private_key: GitHub App private key PEM (from env: GITHUB_PRIVATE_KEY)
            webhook_secret: Webhook secret for signature validation
            client_id: GitHub App Client ID
        """
        self.app_id = app_id or os.getenv("GITHUB_APP_ID", "2191216")
        self.private_key = private_key or os.getenv("GITHUB_PRIVATE_KEY")
        self.webhook_secret = webhook_secret or os.getenv("GITHUB_WEBHOOK_SECRET")
        self.client_id = client_id or os.getenv("GITHUB_CLIENT_ID", "Iv23liwGL7fnYySPPAjS")

        # Event handlers registry
        self._handlers: dict[GitHubEventType, list[Callable]] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default event handlers."""
        self.register_handler(GitHubEventType.PUSH, self._handle_push)
        self.register_handler(GitHubEventType.PULL_REQUEST, self._handle_pull_request)
        self.register_handler(GitHubEventType.WORKFLOW_RUN, self._handle_workflow_run)
        self.register_handler(GitHubEventType.CHECK_SUITE, self._handle_check_suite)

    def register_handler(self, event_type: GitHubEventType, handler: Callable):
        """Register a handler for a specific event type.

        Args:
            event_type: The GitHub event type to handle
            handler: Async function to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """Validate GitHub webhook signature.

        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping validation")
            return True

        if not signature:
            logger.error("No signature provided in webhook request")
            return False

        # Compute expected signature
        expected = "sha256=" + hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)

    def parse_payload(
        self,
        raw_payload: dict,
        event_type: str,
        delivery_id: str,
    ) -> WebhookPayload:
        """Parse a GitHub webhook payload.

        Args:
            raw_payload: The parsed JSON payload
            event_type: X-GitHub-Event header value
            delivery_id: X-GitHub-Delivery header value

        Returns:
            Parsed WebhookPayload object
        """
        try:
            event = GitHubEventType(event_type)
        except ValueError:
            logger.warning(f"Unknown event type: {event_type}")
            event = GitHubEventType.PUSH  # Default fallback

        repository = raw_payload.get("repository", {}).get("full_name", "unknown")
        sender = raw_payload.get("sender", {}).get("login", "unknown")
        action = raw_payload.get("action")

        return WebhookPayload(
            event_type=event,
            action=action,
            repository=repository,
            sender=sender,
            delivery_id=delivery_id,
            raw_payload=raw_payload,
            timestamp=datetime.utcnow(),
        )

    async def handle_webhook(
        self,
        payload: WebhookPayload,
    ) -> dict[str, Any]:
        """Process a webhook payload.

        Args:
            payload: Parsed webhook payload

        Returns:
            Handler response dict
        """
        logger.info(
            f"Processing webhook: {payload.event_type.value} "
            f"from {payload.repository} by {payload.sender}"
        )

        handlers = self._handlers.get(payload.event_type, [])
        results = []

        for handler in handlers:
            try:
                result = await handler(payload)
                results.append({"handler": handler.__name__, "result": result})
            except Exception as e:
                logger.exception(f"Handler {handler.__name__} failed: {e}")
                results.append({"handler": handler.__name__, "error": str(e)})

        return {
            "event_type": payload.event_type.value,
            "action": payload.action,
            "repository": payload.repository,
            "delivery_id": payload.delivery_id,
            "handlers_executed": len(results),
            "results": results,
        }

    # Default Event Handlers

    async def _handle_push(self, payload: WebhookPayload) -> dict:
        """Handle push events.

        Triggers when commits are pushed to a repository.
        Used to trigger Docs2Code pipeline on main/develop branches.
        """
        commits = payload.raw_payload.get("commits", [])
        ref = payload.raw_payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")

        logger.info(f"Push to {branch}: {len(commits)} commit(s)")

        # Check if this is a docs2code-relevant push
        trigger_pipeline = False
        if branch in ["main", "develop"]:
            # Check if any docs changed
            for commit in commits:
                modified = commit.get("modified", []) + commit.get("added", [])
                if any(f.startswith("docs/") for f in modified):
                    trigger_pipeline = True
                    break

        return {
            "branch": branch,
            "commits": len(commits),
            "trigger_pipeline": trigger_pipeline,
            "pusher": payload.raw_payload.get("pusher", {}).get("name"),
        }

    async def _handle_pull_request(self, payload: WebhookPayload) -> dict:
        """Handle pull request events.

        Actions: opened, closed, synchronize, reopened, edited
        """
        pr = payload.raw_payload.get("pull_request", {})
        action = payload.action

        pr_number = pr.get("number")
        title = pr.get("title")
        state = pr.get("state")
        merged = pr.get("merged", False)

        logger.info(f"PR #{pr_number} {action}: {title}")

        # Check if this is a docs2code PR
        is_docs2code_pr = (
            title and (
                "docs2code" in title.lower() or
                "doc-to-code" in title.lower() or
                "[auto]" in title.lower()
            )
        )

        return {
            "action": action,
            "pr_number": pr_number,
            "title": title,
            "state": state,
            "merged": merged,
            "is_docs2code_pr": is_docs2code_pr,
            "base_branch": pr.get("base", {}).get("ref"),
            "head_branch": pr.get("head", {}).get("ref"),
        }

    async def _handle_workflow_run(self, payload: WebhookPayload) -> dict:
        """Handle workflow run events.

        Actions: requested, completed, in_progress
        """
        workflow_run = payload.raw_payload.get("workflow_run", {})

        return {
            "action": payload.action,
            "workflow_name": workflow_run.get("name"),
            "run_id": workflow_run.get("id"),
            "status": workflow_run.get("status"),
            "conclusion": workflow_run.get("conclusion"),
            "branch": workflow_run.get("head_branch"),
        }

    async def _handle_check_suite(self, payload: WebhookPayload) -> dict:
        """Handle check suite events.

        Actions: completed, requested, rerequested
        """
        check_suite = payload.raw_payload.get("check_suite", {})

        return {
            "action": payload.action,
            "status": check_suite.get("status"),
            "conclusion": check_suite.get("conclusion"),
            "head_sha": check_suite.get("head_sha"),
        }

    # GitHub App Authentication

    def generate_jwt(self) -> str:
        """Generate a JWT for GitHub App authentication.

        Returns:
            JWT token string
        """
        if not self.private_key:
            raise ValueError("GitHub App private key not configured")

        now = int(datetime.utcnow().timestamp())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago (clock drift)
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self.app_id,
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_token(self, installation_id: str) -> str:
        """Get an installation access token.

        Args:
            installation_id: GitHub App installation ID

        Returns:
            Installation access token
        """
        jwt_token = self.generate_jwt()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["token"]

    async def create_commit(
        self,
        installation_id: str,
        owner: str,
        repo: str,
        branch: str,
        files: list[dict],
        commit_message: str,
    ) -> dict:
        """Create a commit with multiple files.

        Args:
            installation_id: GitHub App installation ID
            owner: Repository owner
            repo: Repository name
            branch: Branch to commit to
            files: List of {path, content} dicts
            commit_message: Commit message

        Returns:
            Commit response
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            # 1. Get the current commit SHA
            ref_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}",
                headers=headers,
            )
            ref_response.raise_for_status()
            current_sha = ref_response.json()["object"]["sha"]

            # 2. Get the current tree
            commit_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/commits/{current_sha}",
                headers=headers,
            )
            commit_response.raise_for_status()
            base_tree = commit_response.json()["tree"]["sha"]

            # 3. Create blobs for each file
            tree_items = []
            for file in files:
                blob_response = await client.post(
                    f"https://api.github.com/repos/{owner}/{repo}/git/blobs",
                    headers=headers,
                    json={"content": file["content"], "encoding": "utf-8"},
                )
                blob_response.raise_for_status()
                blob_sha = blob_response.json()["sha"]

                tree_items.append({
                    "path": file["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_sha,
                })

            # 4. Create a new tree
            tree_response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees",
                headers=headers,
                json={"base_tree": base_tree, "tree": tree_items},
            )
            tree_response.raise_for_status()
            new_tree_sha = tree_response.json()["sha"]

            # 5. Create the commit
            commit_response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/git/commits",
                headers=headers,
                json={
                    "message": commit_message,
                    "tree": new_tree_sha,
                    "parents": [current_sha],
                },
            )
            commit_response.raise_for_status()
            new_commit_sha = commit_response.json()["sha"]

            # 6. Update the branch reference
            ref_update = await client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
                headers=headers,
                json={"sha": new_commit_sha},
            )
            ref_update.raise_for_status()

            return {
                "commit_sha": new_commit_sha,
                "branch": branch,
                "files_changed": len(files),
            }

    async def create_pull_request(
        self,
        installation_id: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> dict:
        """Create a pull request.

        Args:
            installation_id: GitHub App installation ID
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Source branch
            base: Target branch (default: main)

        Returns:
            PR response including URL
        """
        token = await self.get_installation_token(installation_id)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                },
            )
            response.raise_for_status()
            pr_data = response.json()

            return {
                "pr_number": pr_data["number"],
                "pr_url": pr_data["html_url"],
                "state": pr_data["state"],
            }
