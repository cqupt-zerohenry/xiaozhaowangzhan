"""Shared test fixtures using SQLite in-memory database."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.security import hash_password
from app.models import User


engine = create_engine(
    'sqlite://',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db, client):
    user = User(role='admin', name='Admin', email='admin@test.com', password_hash=hash_password('123456'), status='active')
    db.add(user)
    db.commit()
    resp = client.post('/api/users/login', json={'email': 'admin@test.com', 'password': '123456'})
    return resp.json()['token']


@pytest.fixture
def student_token(db, client):
    user = User(role='student', name='Student', email='student@test.com', password_hash=hash_password('123456'), status='active')
    db.add(user)
    db.commit()
    resp = client.post('/api/users/login', json={'email': 'student@test.com', 'password': '123456'})
    return resp.json()['token']
