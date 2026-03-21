from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Application, Job, StudentProfile


def cosine_similarity(a: set[int], b: set[int]) -> float:
    if not a or not b:
        return 0.0
    common = len(a & b)
    if common == 0:
        return 0.0
    return common / ((len(a) * len(b)) ** 0.5)


def collaborative_rank(train_map: dict[int, set[int]], student_id: int, all_jobs: list[int]) -> list[int]:
    target = train_map.get(student_id, set())
    scores = defaultdict(float)

    if target:
        for other_id, other_jobs in train_map.items():
            if other_id == student_id:
                continue
            sim = cosine_similarity(target, other_jobs)
            if sim <= 0:
                continue
            for job_id in other_jobs:
                if job_id not in target:
                    scores[job_id] += sim

    if not scores:
        popularity = defaultdict(int)
        for jobs in train_map.values():
            for job_id in jobs:
                popularity[job_id] += 1
        sorted_jobs = sorted(all_jobs, key=lambda x: popularity[x], reverse=True)
        return sorted_jobs

    ranked = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    # append unseen jobs to keep full ranking
    tail = [job_id for job_id in all_jobs if job_id not in ranked]
    return ranked + tail


def evaluate(k: int = 5) -> dict:
    db = SessionLocal()
    try:
        apps = db.scalars(select(Application).where(Application.status != 'withdrawn')).all()
        all_jobs = [job.id for job in db.scalars(select(Job)).all()]
        students = [student.user_id for student in db.scalars(select(StudentProfile)).all()]

        by_student: dict[int, list[Application]] = defaultdict(list)
        for app in apps:
            by_student[app.student_id].append(app)

        train_map: dict[int, set[int]] = {}
        ground_truth: dict[int, int] = {}

        for sid in students:
            records = sorted(by_student.get(sid, []), key=lambda x: x.id)
            if len(records) < 2:
                continue
            test_item = records[-1]
            ground_truth[sid] = test_item.job_id
            train_map[sid] = {item.job_id for item in records[:-1]}

        if not ground_truth:
            return {
                'k': k,
                'evaluated_students': 0,
                'precision_at_k': 0.0,
                'recall_at_k': 0.0,
                'hit_rate_at_k': 0.0,
                'note': 'Not enough interaction data for leave-one-out evaluation.'
            }

        hits = 0
        for sid, truth_job in ground_truth.items():
            ranked = collaborative_rank(train_map, sid, all_jobs)
            topk = ranked[:k]
            if truth_job in topk:
                hits += 1

        evaluated = len(ground_truth)
        precision = hits / (evaluated * k)
        recall = hits / evaluated
        hit_rate = recall

        return {
            'k': k,
            'evaluated_students': evaluated,
            'hits': hits,
            'precision_at_k': round(precision, 4),
            'recall_at_k': round(recall, 4),
            'hit_rate_at_k': round(hit_rate, 4),
            'note': 'Leave-one-out evaluation over application interaction data.'
        }
    finally:
        db.close()


def write_report(result: dict) -> Path:
    report_dir = Path(__file__).resolve().parents[1] / 'reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / 'recommendation_eval_report.md'

    content = f"""# 推荐算法评估报告

- 生成时间：{datetime.now().isoformat(timespec='seconds')}
- 评估方法：{result['note']}
- K：{result['k']}
- 评估学生数：{result['evaluated_students']}
- 命中数：{result.get('hits', 0)}

## 指标

- Precision@K: {result['precision_at_k']}
- Recall@K: {result['recall_at_k']}
- HitRate@K: {result['hit_rate_at_k']}

## 结论

当前数据规模较小时，指标波动会较大。建议后续扩充交互数据后重复评估，并记录不同 K 值与参数下的结果。
"""
    report_path.write_text(content, encoding='utf-8')
    return report_path


if __name__ == '__main__':
    result = evaluate(k=5)
    path = write_report(result)
    print(f'Report generated: {path}')
    print(result)
