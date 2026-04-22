"""Resume parsing service: extract text first, then build structured resume data."""
from __future__ import annotations

import io
import json
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md'}
_TEXT_EXTRACT_SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'resume_text_extractor.py'


def _normalize_text(text: str) -> str:
    if not text:
        return ''
    normalized = (
        text.replace('\r\n', '\n')
        .replace('\r', '\n')
        .replace('\x00', '')
        .replace('\u200b', '')
    )
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    return normalized.strip()


def _decode_text_bytes(file_bytes: bytes) -> str:
    for enc in ('utf-8', 'utf-8-sig', 'gb18030', 'gbk', 'latin-1'):
        try:
            return file_bytes.decode(enc)
        except Exception:
            continue
    return file_bytes.decode('utf-8', errors='ignore')


def _extract_text_via_script(file_bytes: bytes, filename: str) -> str:
    if not _TEXT_EXTRACT_SCRIPT.exists():
        return ''

    suffix = Path(filename).suffix or '.txt'
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as fp:
            fp.write(file_bytes)
            tmp_path = Path(fp.name)

        proc = subprocess.run(
            [sys.executable, str(_TEXT_EXTRACT_SCRIPT), str(tmp_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=25,
            check=False,
        )
        if not proc.stdout.strip():
            if proc.stderr.strip():
                logger.warning('Resume text script stderr: %s', proc.stderr.strip())
            return ''
        payload = json.loads(proc.stdout)
        return _normalize_text(str(payload.get('text') or ''))
    except Exception:
        logger.exception('Script-based resume text extraction failed')
        return ''
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                logger.warning('Failed to cleanup temp resume file: %s', tmp_path)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or '' for page in reader.pages]
        return _normalize_text('\n'.join(pages))
    except Exception:
        logger.exception('Failed to extract text from PDF')
        return ''


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        return _normalize_text('\n'.join(p.text for p in doc.paragraphs))
    except Exception:
        logger.exception('Failed to extract text from DOCX')
        return ''


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from uploaded file by extension."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in SUPPORTED_RESUME_EXTENSIONS:
        text = _extract_text_via_script(file_bytes, filename)
        if text:
            return text

    if ext == 'pdf':
        return extract_text_from_pdf(file_bytes)
    if ext == 'docx':
        return extract_text_from_docx(file_bytes)
    if ext == 'doc':
        return ''
    return _normalize_text(_decode_text_bytes(file_bytes))


def _normalize_string_list(value: object) -> list[str]:
    if isinstance(value, str):
        parts = re.split(r'[，,;；\n]+', value)
        return [p.strip() for p in parts if p and p.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


# Common tech skills for keyword matching
_TECH_SKILLS = [
    'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++', 'C#',
    'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring',
    'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes', 'K8s',
    'AWS', 'Linux', 'Git', 'CI/CD', 'TensorFlow', 'PyTorch', 'Machine Learning',
    'Deep Learning', 'NLP', 'Computer Vision', 'HTML', 'CSS', 'SQL',
    'Spark', 'Hadoop', 'Kafka', 'RabbitMQ', 'Nginx', 'GraphQL', 'REST',
    'Pandas', 'NumPy', 'Scikit-learn', 'OpenCV', 'LLM', 'RAG',
    '机器学习', '深度学习', '自然语言处理', '计算机视觉', '数据分析', '数据库',
    '前端开发', '后端开发', '全栈', '运维', '测试', '算法',
]


def parse_resume_rule_based(text: str) -> dict:
    """Extract structured fields from resume text using regex patterns."""
    result: dict = {
        'name': '',
        'phone': '',
        'email': '',
        'school': '',
        'major': '',
        'skills': [],
        'experience': [],
        'raw_text': _normalize_text(text),
    }

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Phone
    phone_match = re.search(r'1[3-9]\d{9}', text)
    if phone_match:
        result['phone'] = phone_match.group()

    # Email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    if email_match:
        result['email'] = email_match.group()

    # Name: look for 姓名 label or first short line
    for line in lines[:5]:
        name_match = re.search(r'姓\s*名[：:]\s*(\S+)', line)
        if name_match:
            result['name'] = name_match.group(1)
            break
    if not result['name'] and lines:
        first = lines[0].strip()
        if 2 <= len(first) <= 4 and re.match(r'^[\u4e00-\u9fff]+$', first):
            result['name'] = first

    # School
    for line in lines:
        school_match = re.search(r'([\u4e00-\u9fff]{2,10}(?:大学|学院|University|College))', line)
        if school_match:
            result['school'] = school_match.group(1)
            break

    # Major
    for line in lines:
        major_match = re.search(r'专\s*业[：:]\s*(.+?)(?:\s|$)', line)
        if major_match:
            result['major'] = major_match.group(1).strip()
            break

    # Skills
    text_lower = text.lower()
    found_skills = []
    for skill in _TECH_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    result['skills'] = list(dict.fromkeys(found_skills))  # dedupe preserving order

    # Experience sections
    experience_headers = ['工作经历', '实习经历', '项目经历', '项目经验', '实习经验']
    current_section: list[str] = []
    in_section = False
    for line in lines:
        if any(h in line for h in experience_headers):
            in_section = True
            continue
        if in_section:
            if re.match(r'^(教育|技能|荣誉|获奖|自我|个人)', line):
                break
            current_section.append(line)
    if current_section:
        result['experience'] = current_section[:10]  # limit to 10 lines

    return result


def parse_resume_llm(text: str) -> dict | None:
    """Try LLM-based parsing (returns None if unavailable)."""
    try:
        from app.llm_service import chat
        prompt = (
            '请从以下简历文本中提取结构化信息，以JSON格式返回，包含字段：'
            'name, phone, email, school, major, skills(数组), experience(数组)。\n\n'
            f'简历内容：\n{text[:5000]}'
        )
        response = chat('你是简历解析助手，只输出JSON。', prompt, temperature=0.1)
        if response:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
    except Exception:
        logger.exception('LLM resume parsing failed')
    return None


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """Main entry: extract text then parse structured data."""
    text = extract_text_from_file(file_bytes, filename)

    if not text.strip():
        return {'name': '', 'phone': '', 'email': '', 'school': '', 'major': '',
                'skills': [], 'experience': [], 'raw_text': ''}

    # Try LLM first, fall back to rule-based
    llm_result = parse_resume_llm(text)
    if llm_result:
        return {
            'name': str(llm_result.get('name') or '').strip(),
            'phone': str(llm_result.get('phone') or '').strip(),
            'email': str(llm_result.get('email') or '').strip(),
            'school': str(llm_result.get('school') or '').strip(),
            'major': str(llm_result.get('major') or '').strip(),
            'skills': _normalize_string_list(llm_result.get('skills')),
            'experience': _normalize_string_list(llm_result.get('experience')),
            'raw_text': text,
        }

    return parse_resume_rule_based(text)
