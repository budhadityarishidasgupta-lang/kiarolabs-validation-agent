from __future__ import annotations

from dataclasses import dataclass

from validation_agent.client import ApiClient, LoginContext


@dataclass
class AuditContext:
    base_url: str
    client: ApiClient | None
    admin_login: LoginContext | None
    student_login: LoginContext | None

