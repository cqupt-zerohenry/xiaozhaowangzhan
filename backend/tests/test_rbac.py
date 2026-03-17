import pytest
from fastapi import HTTPException

pytest.importorskip('pymysql')

from app.dependencies import require_self_or_roles


class FakeUser:
    def __init__(self, user_id: int, role: str) -> None:
        self.id = user_id
        self.role = role


def test_require_self_or_roles_self_allowed() -> None:
    require_self_or_roles(1, FakeUser(1, 'student'), {'admin'})


def test_require_self_or_roles_role_allowed() -> None:
    require_self_or_roles(1, FakeUser(2, 'admin'), {'admin'})


def test_require_self_or_roles_denied() -> None:
    with pytest.raises(HTTPException):
        require_self_or_roles(1, FakeUser(2, 'student'), {'admin'})
