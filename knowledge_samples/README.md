# 知识库样例文档（可直接上传）

本目录用于测试知识库上传、自动切片、分块标签与 RAG 检索效果。

## 文件清单

- `frontend/frontend_interview_playbook.md`
- `backend/backend_interview_playbook.md`
- `devops/devops_sre_interview_playbook.md`
- `mixed/interview_question_bank.md`

## 建议上传方式

1. 在 AI 助手 -> 知识库管理中先创建一个知识库。
2. 依次上传本目录下的 md 文件。
3. 上传完成后点击“自动重算向量”（可选，用于全量重建）。
4. 在文档列表里点击“查看分块”，确认：
   - 是否被切成多块
   - 每块大小是否合理
   - 是否自动生成了分块标签

## 建议验证问题

- 前端：`如何回答虚拟 DOM 和 diff 的核心价值？`
- 后端：`Redis 缓存击穿和雪崩如何治理？`
- 运维：`Kubernetes 中如何定位一个服务间歇性超时问题？`
- 综合：`请给我一套后端实习生的面试复习路径`
