"""Tests for application status transitions."""
from __future__ import annotations

from app.models import CompanyProfile, Job, Resume, StudentProfile, User
from app.security import hash_password


def _setup_job_and_student(db, client):
    """Create a company with job and a student with resume."""
    # Company
    company_user = User(role='company', name='Corp', email='appcorp@test.com',
                        password_hash=hash_password('123456'), status='active')
    db.add(company_user)
    db.flush()
    db.add(CompanyProfile(user_id=company_user.id, company_name='AppCorp', credit_code='AC001',
                          contact_name='Corp', contact_phone='123', status='approved'))
    db.flush()

    job = Job(company_id=company_user.id, job_name='Test Job', job_type='后端',
              city='Beijing', salary_min=10000, salary_max=20000,
              education='本科', description='test', requirement='test', skill_tags=['Python'])
    db.add(job)
    db.flush()

    # Student
    student_user = User(role='student', name='Stu', email='appstu@test.com',
                        password_hash=hash_password('123456'), status='active')
    db.add(student_user)
    db.flush()
    db.add(StudentProfile(user_id=student_user.id, name='Stu', student_no='S1',
                          school='U', major='CS', grade='2024', phone='123', email='appstu@test.com'))
    resume = Resume(student_id=student_user.id, resume_type='online',
                    content_json={'skills': ['Python']})
    db.add(resume)
    db.commit()

    company_token = client.post('/api/users/login', json={'email': 'appcorp@test.com', 'password': '123456'}).json()['token']
    student_token = client.post('/api/users/login', json={'email': 'appstu@test.com', 'password': '123456'}).json()['token']

    return company_token, student_token, job.id, student_user.id, resume.id


def test_create_application(db, client):
    _, student_token, job_id, student_id, resume_id = _setup_job_and_student(db, client)
    resp = client.post('/api/applications', json={
        'student_id': student_id, 'job_id': job_id, 'resume_id': resume_id,
    }, headers={'Authorization': f'Bearer {student_token}'})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'submitted'


def test_duplicate_application(db, client):
    _, student_token, job_id, student_id, resume_id = _setup_job_and_student(db, client)
    client.post('/api/applications', json={
        'student_id': student_id, 'job_id': job_id, 'resume_id': resume_id,
    }, headers={'Authorization': f'Bearer {student_token}'})
    resp = client.post('/api/applications', json={
        'student_id': student_id, 'job_id': job_id, 'resume_id': resume_id,
    }, headers={'Authorization': f'Bearer {student_token}'})
    assert resp.status_code == 400


def test_status_transition_company(db, client):
    company_token, student_token, job_id, student_id, resume_id = _setup_job_and_student(db, client)
    app_resp = client.post('/api/applications', json={
        'student_id': student_id, 'job_id': job_id, 'resume_id': resume_id,
    }, headers={'Authorization': f'Bearer {student_token}'})
    app_id = app_resp.json()['id']

    # Company transitions: submitted -> viewed
    resp = client.patch(f'/api/applications/{app_id}/status', json={'status': 'viewed'},
                        headers={'Authorization': f'Bearer {company_token}'})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'viewed'


def test_invalid_transition(db, client):
    company_token, student_token, job_id, student_id, resume_id = _setup_job_and_student(db, client)
    app_resp = client.post('/api/applications', json={
        'student_id': student_id, 'job_id': job_id, 'resume_id': resume_id,
    }, headers={'Authorization': f'Bearer {student_token}'})
    app_id = app_resp.json()['id']

    # submitted -> accepted is invalid
    resp = client.patch(f'/api/applications/{app_id}/status', json={'status': 'accepted'},
                        headers={'Authorization': f'Bearer {company_token}'})
    assert resp.status_code == 400


def test_student_withdraw(db, client):
    _, student_token, job_id, student_id, resume_id = _setup_job_and_student(db, client)
    app_resp = client.post('/api/applications', json={
        'student_id': student_id, 'job_id': job_id, 'resume_id': resume_id,
    }, headers={'Authorization': f'Bearer {student_token}'})
    app_id = app_resp.json()['id']

    resp = client.patch(f'/api/applications/{app_id}/status', json={'status': 'withdrawn'},
                        headers={'Authorization': f'Bearer {student_token}'})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'withdrawn'
