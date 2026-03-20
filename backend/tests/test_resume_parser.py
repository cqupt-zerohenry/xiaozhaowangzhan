"""Tests for resume parser rule-based extraction."""
from __future__ import annotations

from app.resume_parser import parse_resume_rule_based


def test_extract_phone():
    result = parse_resume_rule_based('联系电话 13812345678 北京')
    assert result['phone'] == '13812345678'


def test_extract_email():
    result = parse_resume_rule_based('邮箱：test@example.com')
    assert result['email'] == 'test@example.com'


def test_extract_name():
    result = parse_resume_rule_based('姓名：张三\n学校：北京大学')
    assert result['name'] == '张三'


def test_extract_school():
    result = parse_resume_rule_based('教育背景\n北京大学 计算机科学与技术')
    assert '北京大学' in result['school']


def test_extract_skills():
    result = parse_resume_rule_based('技能：Python, Java, Docker, MySQL, Redis')
    assert 'Python' in result['skills']
    assert 'Docker' in result['skills']


def test_first_line_name():
    result = parse_resume_rule_based('李华\n电话 13900000000\n学校 清华大学')
    assert result['name'] == '李华'


def test_empty_text():
    result = parse_resume_rule_based('')
    assert result['name'] == ''
    assert result['skills'] == []
