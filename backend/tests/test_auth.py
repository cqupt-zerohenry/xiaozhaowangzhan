"""Tests for authentication and registration."""
from __future__ import annotations


def test_register_student(client):
    resp = client.post('/api/auth/register/student', json={
        'name': 'Test', 'email': 'test@example.com', 'password': '123456',
        'student_no': 'S001', 'school': 'Test Univ', 'major': 'CS',
        'grade': '2024', 'phone': '13800138000',
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data['role'] == 'student'
    assert data['email'] == 'test@example.com'


def test_register_duplicate_email(client):
    payload = {
        'name': 'Test', 'email': 'dup@example.com', 'password': '123456',
        'student_no': 'S001', 'school': 'Test Univ', 'major': 'CS',
        'grade': '2024', 'phone': '13800138000',
    }
    client.post('/api/auth/register/student', json=payload)
    resp = client.post('/api/auth/register/student', json=payload)
    assert resp.status_code == 400


def test_register_company(client):
    resp = client.post('/api/auth/register/company', json={
        'company_name': 'Test Corp', 'credit_code': '123ABC',
        'contact_name': 'Boss', 'contact_phone': '13900139000',
        'email': 'corp@example.com', 'password': '123456',
    })
    assert resp.status_code == 200
    assert resp.json()['role'] == 'company'


def test_login_success(client):
    client.post('/api/auth/register/student', json={
        'name': 'Test', 'email': 'login@example.com', 'password': '123456',
        'student_no': 'S001', 'school': 'Test Univ', 'major': 'CS',
        'grade': '2024', 'phone': '13800138000',
    })
    resp = client.post('/api/users/login', json={'email': 'login@example.com', 'password': '123456'})
    assert resp.status_code == 200
    assert 'token' in resp.json()


def test_login_wrong_password(client):
    client.post('/api/auth/register/student', json={
        'name': 'Test', 'email': 'wrong@example.com', 'password': '123456',
        'student_no': 'S001', 'school': 'Test Univ', 'major': 'CS',
        'grade': '2024', 'phone': '13800138000',
    })
    resp = client.post('/api/users/login', json={'email': 'wrong@example.com', 'password': 'bad'})
    assert resp.status_code == 401
