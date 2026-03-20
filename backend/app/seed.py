from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Announcement,
    Application,
    CompanyProfile,
    Job,
    Message,
    Resume,
    StudentIntention,
    StudentProfile,
    User,
)
from app.security import hash_password

DEMO_PASSWORD = '123456'


def seed_data(db: Session) -> None:
    """数据库为空时创建展示账号和基础数据，用于功能演示。"""
    user_count = db.scalar(select(func.count()).select_from(User))
    if user_count and user_count > 0:
        return

    # ── 管理员 ──
    admin = User(role='admin', name='系统管理员', email='admin@test.com',
                 password_hash=hash_password(DEMO_PASSWORD))

    # ── 企业用户 ──
    c1 = User(role='company', name='星云科技HR', email='company@test.com',
              password_hash=hash_password(DEMO_PASSWORD))
    c2 = User(role='company', name='极光实验室HR', email='company2@test.com',
              password_hash=hash_password(DEMO_PASSWORD))
    db.add_all([admin, c1, c2])
    db.flush()

    db.add_all([
        CompanyProfile(
            user_id=c1.id, company_name='星云科技有限公司',
            credit_code='91310000MA1G0000X1', contact_name='王招聘',
            contact_phone='13800001111', status='approved',
            description='专注云原生与 AI 基础设施的技术企业，团队 200+ 人。',
            industry='互联网/云计算', scale='200-500人', address='上海市浦东新区',
            website='https://nebula-tech.example.com',
            welfare_tags=['五险一金', '弹性工作', '学习基金', '免费三餐'],
        ),
        CompanyProfile(
            user_id=c2.id, company_name='极光智能实验室',
            credit_code='91330000MA1G0000X2', contact_name='李招聘',
            contact_phone='13700003333', status='approved',
            description='AI 平台研发团队，面向校园招聘实习岗。',
            industry='人工智能', scale='50-200人', address='杭州市西湖区',
            website='https://aurora-labs.example.com',
            welfare_tags=['培训体系', '弹性工时', '实习转正'],
        ),
    ])

    # ── 学生用户 ──
    s1 = User(role='student', name='李华', email='student@test.com',
              password_hash=hash_password(DEMO_PASSWORD))
    s2 = User(role='student', name='张三', email='student2@test.com',
              password_hash=hash_password(DEMO_PASSWORD))
    s3 = User(role='student', name='王五', email='student3@test.com',
              password_hash=hash_password(DEMO_PASSWORD))
    db.add_all([s1, s2, s3])
    db.flush()

    # 学生档案
    db.add_all([
        StudentProfile(
            user_id=s1.id, name='李华', student_no='20250001',
            school='重庆邮电大学', major='计算机科学与技术', grade='2025',
            phone='13900002222', email='student@test.com',
            skills=['Python', 'Linux', 'Docker', 'Kubernetes', 'MySQL'],
            awards=['省级程序设计竞赛二等奖'],
            internships=['某云计算公司 SRE 实习 3 个月'],
            projects=['校园微服务监控平台', '容器化部署自动化工具'],
            bio='计算机科学与技术专业，熟悉云原生技术栈，目标 SRE/运维开发方向。',
            verified=True,
        ),
        StudentProfile(
            user_id=s2.id, name='张三', student_no='20250002',
            school='重庆大学', major='软件工程', grade='2025',
            phone='13600004444', email='student2@test.com',
            skills=['Java', 'Spring Boot', 'MySQL', 'Redis', 'Docker'],
            awards=['校级优秀毕业设计'],
            internships=['某互联网公司后端开发实习 4 个月'],
            projects=['电商秒杀系统', '分布式任务调度框架'],
            bio='软件工程专业，擅长 Java 后端开发，有分布式系统实践经验。',
            verified=True,
        ),
        StudentProfile(
            user_id=s3.id, name='王五', student_no='20250003',
            school='重庆邮电大学', major='人工智能', grade='2025',
            phone='13500005555', email='student3@test.com',
            skills=['Python', 'PyTorch', 'SQL', 'TensorFlow', 'Docker'],
            awards=['数学建模竞赛一等奖', 'Kaggle 银牌'],
            internships=['某 AI 公司算法实习 3 个月'],
            projects=['图像分类模型优化', '自然语言处理情感分析系统'],
            bio='人工智能专业，专注深度学习与 NLP 方向，目标 AI 工程师。',
            verified=True,
        ),
    ])

    # 求职意向
    db.add_all([
        StudentIntention(student_id=s1.id, expected_job='SRE/运维开发',
                         expected_city='上海', expected_salary='8000-12000',
                         expected_industry='互联网/云计算', arrival_time='2026-07',
                         accept_internship=True),
        StudentIntention(student_id=s2.id, expected_job='后端开发工程师',
                         expected_city='杭州', expected_salary='10000-15000',
                         expected_industry='人工智能', arrival_time='2026-07',
                         accept_internship=True),
        StudentIntention(student_id=s3.id, expected_job='AI算法工程师',
                         expected_city='杭州', expected_salary='12000-18000',
                         expected_industry='人工智能', arrival_time='2026-07',
                         accept_internship=True),
    ])

    # 简历
    r1 = Resume(student_id=s1.id, resume_type='online',
                content_json={'skills': ['Python', 'Linux', 'Docker', 'Kubernetes', 'MySQL'],
                              'major': '计算机科学与技术', 'school': '重庆邮电大学'}, version_no=1)
    r2 = Resume(student_id=s2.id, resume_type='online',
                content_json={'skills': ['Java', 'Spring Boot', 'MySQL', 'Redis', 'Docker'],
                              'major': '软件工程', 'school': '重庆大学'}, version_no=1)
    r3 = Resume(student_id=s3.id, resume_type='online',
                content_json={'skills': ['Python', 'PyTorch', 'SQL', 'TensorFlow', 'Docker'],
                              'major': '人工智能', 'school': '重庆邮电大学'}, version_no=1)
    db.add_all([r1, r2, r3])
    db.flush()

    # ── 岗位 ──
    j1 = Job(company_id=c1.id, job_name='SRE 运维开发实习生', job_type='SRE/运维',
             city='上海', salary_min=8000, salary_max=12000, education='本科',
             description='负责云平台可靠性保障与自动化运维工具开发，参与容器化部署与监控告警体系建设。',
             requirement='1. 熟悉 Linux 操作系统\n2. 了解 Docker/Kubernetes\n3. 掌握 Python 或 Go\n4. 有监控/日志系统使用经验优先',
             skill_tags=['Linux', 'Docker', 'Kubernetes', 'Python'], status='active', deadline='2026-06-30')
    j2 = Job(company_id=c2.id, job_name='Java 后端开发实习生', job_type='后端开发',
             city='杭州', salary_min=9000, salary_max=13000, education='本科',
             description='参与 AI 平台后端服务开发，负责接口设计、数据库优化与微服务治理。',
             requirement='1. 熟练掌握 Java/Spring Boot\n2. 熟悉 MySQL/Redis\n3. 了解微服务架构\n4. 有实际项目经验优先',
             skill_tags=['Java', 'Spring Boot', 'MySQL', 'Redis', 'Docker'], status='active', deadline='2026-06-30')
    j3 = Job(company_id=c2.id, job_name='AI 算法实习生', job_type='AI/算法',
             city='杭州', salary_min=10000, salary_max=16000, education='本科',
             description='参与模型训练流水线搭建与 AI 服务部署，研究前沿算法并落地到业务场景。',
             requirement='1. 熟练掌握 Python\n2. 熟悉 PyTorch/TensorFlow\n3. 有机器学习项目经验\n4. 了解数据处理流程',
             skill_tags=['Python', 'PyTorch', 'TensorFlow', 'SQL'], status='active', deadline='2026-06-30')
    j4 = Job(company_id=c1.id, job_name='前端开发实习生', job_type='前端开发',
             city='上海', salary_min=8000, salary_max=11000, education='本科',
             description='参与内部管理系统与数据可视化平台的前端开发，使用 Vue3 技术栈。',
             requirement='1. 熟悉 HTML/CSS/JavaScript\n2. 掌握 Vue 或 React\n3. 了解 HTTP 协议\n4. 有组件化开发经验优先',
             skill_tags=['Vue', 'JavaScript', 'HTML', 'CSS'], status='active', deadline='2026-06-30')
    db.add_all([j1, j2, j3, j4])
    db.flush()

    # ── 投递记录 ──
    db.add_all([
        Application(student_id=s1.id, job_id=j1.id, resume_id=r1.id, status='submitted'),
        Application(student_id=s1.id, job_id=j2.id, resume_id=r1.id, status='reviewing'),
        Application(student_id=s2.id, job_id=j1.id, resume_id=r2.id, status='submitted'),
        Application(student_id=s2.id, job_id=j2.id, resume_id=r2.id, status='to_contact'),
        Application(student_id=s3.id, job_id=j2.id, resume_id=r3.id, status='submitted'),
        Application(student_id=s3.id, job_id=j3.id, resume_id=r3.id, status='accepted'),
    ])

    # ── 消息 ──
    db.add(Message(sender_id=c1.id, receiver_id=s1.id,
                   content='李华同学你好，看到你投递了 SRE 实习岗位，方便这周三下午进行线上面试吗？',
                   message_type='text'))
    db.add(Message(sender_id=s1.id, receiver_id=c1.id,
                   content='您好，可以的，请问是腾讯会议还是飞书？',
                   message_type='text'))
    db.add(Message(sender_id=c2.id, receiver_id=s3.id,
                   content='王五同学，恭喜你通过了 AI 算法实习的面试，请尽快确认入职时间。',
                   message_type='system'))

    # ── 公告 ──
    db.add(Announcement(
        title='2026 年春季校园招聘周启动通知',
        content='各位同学：\n\n2026 年春季校园招聘周将于下周一正式开始，届时将有 20+ 家企业入驻平台发布实习及校招岗位。请提前完善个人档案和简历，祝大家求职顺利！\n\n—— 就业指导中心',
        status='published', pinned=True,
    ))
    db.add(Announcement(
        title='平台功能更新：AI 智能面试上线',
        content='AI 智能面试功能已正式上线，学生可在 AI 助手页面上传学习内容，系统将自动生成定制面试题并给出反馈建议。欢迎体验！',
        status='published', pinned=False,
    ))

    db.commit()
