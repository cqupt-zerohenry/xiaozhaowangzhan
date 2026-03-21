"""Tests for job CRUD operations."""
from __future__ import annotations

from app.models import CompanyProfile
from app.security import hash_password
from app.models import User


def _create_approved_company(db, client):
    """Helper to create an approved company user."""
    user = User(role='company', name='Corp', email='jobcorp@test.com',
                password_hash=hash_password('123456'), status='active')
    db.add(user)
    db.flush()
    db.add(CompanyProfile(user_id=user.id, company_name='TestCorp', credit_code='TC001',
                          contact_name='Corp', contact_phone='123', status='approved'))
    db.commit()
    resp = client.post('/api/users/login', json={'email': 'jobcorp@test.com', 'password': '123456'})
    return resp.json()['token'], user.id


def test_create_job(db, client):
    token, company_id = _create_approved_company(db, client)
    resp = client.post('/api/jobs', json={
        'company_id': company_id, 'job_name': 'Backend Dev',
        'job_type': '后端', 'city': 'Beijing', 'salary_min': 10000,
        'salary_max': 20000, 'education': '本科', 'description': 'Build APIs',
        'requirement': 'Python', 'skill_tags': ['Python', 'FastAPI'],
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert resp.json()['job_name'] == 'Backend Dev'


def test_list_jobs(db, client):
    token, company_id = _create_approved_company(db, client)
    client.post('/api/jobs', json={
        'company_id': company_id, 'job_name': 'Frontend Dev',
        'job_type': '前端', 'city': 'Shanghai', 'salary_min': 8000,
        'salary_max': 15000, 'education': '本科', 'description': 'Build UI',
        'requirement': 'Vue', 'skill_tags': ['Vue', 'JavaScript'],
    }, headers={'Authorization': f'Bearer {token}'})

    resp = client.get('/api/jobs', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) >= 1


def test_delete_job(db, client):
    token, company_id = _create_approved_company(db, client)
    create_resp = client.post('/api/jobs', json={
        'company_id': company_id, 'job_name': 'To Delete',
        'job_type': '测试', 'city': 'Beijing', 'salary_min': 5000,
        'salary_max': 10000, 'education': '本科', 'description': 'tmp',
        'requirement': 'none', 'skill_tags': [],
    }, headers={'Authorization': f'Bearer {token}'})
    job_id = create_resp.json()['id']
    resp = client.delete(f'/api/jobs/{job_id}', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
