<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>AI 助手</h1>
            <p>{{ aiHeroSubtitle }}</p>
          </div>
          <div class="hero-right">
            <span class="tag mono">{{ aiWorkflowTag }}</span>
            <button class="btn btn-outline" :disabled="aiBusy" @click="refreshRoleData">刷新 AI 数据</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container ai-grid">
        <div class="card ai-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="tab"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <strong>{{ tab.title }}</strong>
            <span>{{ tab.desc }}</span>
          </button>
          <div class="ai-summary">
            <h3>AI 使用建议</h3>
            <ul>
              <li v-for="tip in aiTips" :key="tip">{{ tip }}</li>
            </ul>
          </div>
        </div>

        <div class="ai-panel">
          <div v-if="activeTab === 'knowledge-base'" class="panel-content-kb">
            <div class="kb-shell">
              <div class="kb-header">
                <div>
                  <div class="kb-pill">
                    知识库 · 文档 · 分块
                  </div>
                  <h2 class="kb-title">知识库管理</h2>
                  <p class="kb-subtitle">
                    统一管理知识库、文档接入、切块内容与检索状态，让 RAG 数据准备流程更清晰。
                  </p>
                </div>
                <div class="kb-header-actions">
                  <button
                    type="button"
                    class="kb-header-btn-secondary"
                    :disabled="aiBusy"
                    @click="createSampleKnowledgeBase"
                  >
                    导入模板
                  </button>
                  <button
                    type="button"
                    class="kb-header-btn-primary"
                    :disabled="aiBusy"
                    @click="createKB"
                  >
                    + 新建知识库
                  </button>
                </div>
              </div>

              <div class="kb-layout-grid">
                <aside class="kb-column kb-column-left">
                  <section class="kb-card kb-card-shadow">
                    <div class="kb-section-head">
                      <h3>我的知识库</h3>
                      <span class="kb-chip-count">
                        {{ knowledgeBases.length }} 个
                      </span>
                    </div>
                    <div v-if="knowledgeBases.length === 0" class="mono kb-empty">
                      暂无知识库，请先创建
                    </div>
                    <div v-else class="kb-list">
                      <button
                        v-for="kb in knowledgeBases"
                        :key="kb.id"
                        type="button"
                        class="kb-lib-item"
                        :class="{ active: String(selectedKbId) === String(kb.id) }"
                        @click="selectKB(kb.id)"
                      >
                        <div class="kb-lib-main">
                          <div class="kb-lib-name">{{ kb.name }}</div>
                          <div class="kb-lib-desc mono">{{ kb.description || '无描述' }}</div>
                        </div>
                        <span
                          v-if="String(selectedKbId) === String(kb.id)"
                          class="kb-chip-current"
                        >
                          当前
                        </span>
                      </button>
                    </div>
                  </section>

                  <section class="kb-card kb-card-shadow">
                    <h3 class="kb-section-title">快速模板</h3>
                    <div class="kb-template-grid">
                      <button
                        v-for="label in ['后端知识', '前端知识', '算法题库', '面试笔记']"
                        :key="label"
                        type="button"
                        class="kb-template-btn"
                        :disabled="aiBusy"
                        @click="handleQuickTemplate(label)"
                      >
                        {{ label }}
                      </button>
                    </div>
                    <button
                      type="button"
                      class="kb-oneclick-btn"
                      :disabled="aiBusy"
                      @click="createSampleKnowledgeBase"
                    >
                      一键创建示例知识库
                    </button>
                  </section>

                  <section class="kb-card kb-card-shadow">
                    <h3 class="kb-section-title">新建知识库</h3>
                    <div class="kb-compact-form">
                      <input v-model="kbForm.name" placeholder="知识库名称（如：SRE 知识库）" />
                      <input v-model="kbForm.description" placeholder="描述（可选）" />
                      <button
                        type="button"
                        class="btn"
                        :disabled="aiBusy"
                        @click="createKB"
                      >
                        创建知识库
                      </button>
                    </div>
                  </section>
                </aside>

                <section class="kb-column kb-column-middle">
                  <section class="kb-card kb-card-shadow kb-current">
                    <div class="kb-section-head">
                      <div>
                        <h3>
                          {{ selectedKb ? `当前知识库：${selectedKb.name}` : '当前知识库：未选择' }}
                        </h3>
                        <p class="mono kb-current-desc">
                          {{ selectedKb?.description || '先在左侧选择一个知识库，然后在中栏添加文档。' }}
                        </p>
                      </div>
                      <div v-if="selectedKb" class="kb-current-meta">
                        <span class="kb-meta-chip">
                          {{ kbDocuments.length }} 篇文档
                        </span>
                        <span class="kb-meta-chip">
                          {{ chunkStats.total_chunks || 0 }} 个分块
                        </span>
                        <span class="kb-meta-pill">
                          检索可用
                        </span>
                      </div>
                    </div>
                    <div v-if="selectedKb" class="kb-current-tags">
                      <span class="kb-tag" data-label="TopK">5</span>
                      <span class="kb-tag" data-label="召回模式">混合检索</span>
                      <span class="kb-tag" data-label="Embedding">bge-m3</span>
                    </div>
                  </section>

                  <section class="kb-card kb-card-shadow" :class="{ 'is-disabled': !selectedKbId }">
                    <div class="kb-section-head kb-section-head-add-doc">
                      <h3>添加文档到知识库</h3>
                      <button
                        type="button"
                        class="btn btn-outline btn-compact kb-rebuild-btn"
                        :disabled="aiBusy || kbRebuilding || !selectedKbId"
                        @click="rebuildSelectedKbEmbeddings"
                      >
                        {{ kbRebuilding ? '重算中...' : '自动重算向量' }}
                      </button>
                    </div>
                    <template v-if="selectedKbId">
                      <div class="kb-compact-form">
                        <input v-model="kbDocForm.title" placeholder="文档标题" />
                        <textarea
                          v-model="kbDocForm.content"
                          rows="4"
                          placeholder="支持粘贴知识内容，例如技术文档、SRE 排障笔记、课程笔记等"
                        ></textarea>
                      </div>
                      <div class="kb-add-actions">
                        <button
                          type="button"
                          class="btn"
                          :disabled="aiBusy"
                          @click="addDocPaste"
                        >
                          添加文档
                        </button>
                        <label class="file-picker" :class="{ 'is-disabled': aiBusy }">
                          <span class="btn btn-outline file-picker-btn">上传文件</span>
                          <span class="mono file-picker-name">
                            {{ kbUploadFileName || '支持上传 txt / md / pdf / docx 文件，单个不超过 20MB' }}
                          </span>
                          <input
                            type="file"
                            :disabled="aiBusy"
                            accept=".txt,.md,.pdf,.doc,.docx"
                            @change="uploadDoc"
                          />
                        </label>
                      </div>
                    </template>
                    <div v-else class="mono kb-empty">请先在左侧选择知识库。</div>
                  </section>

                  <section class="kb-card kb-card-shadow kb-doc-list">
                    <div class="kb-section-head">
                      <h3>文档列表</h3>
                      <span class="mono">共 {{ kbDocuments.length }} 篇</span>
                    </div>
                    <div v-if="!selectedKbId" class="mono kb-empty">
                      选择知识库后可查看文档。
                    </div>
                    <div v-else-if="kbDocuments.length === 0" class="mono kb-empty">
                      暂无文档，可先在上方添加文档或上传文件。
                    </div>
                    <div v-else class="kb-doc-items">
                      <article
                        v-for="doc in kbDocuments"
                        :key="doc.id"
                        class="kb-doc-item"
                        :class="{ active: chunkViewDocId === doc.id }"
                      >
                        <div class="kb-doc-main">
                          <strong>{{ doc.title }}</strong>
                          <p class="mono">
                            {{ doc.source_type }} · {{ doc.chunk_count }} 个分块
                          </p>
                          <div class="kb-doc-tags">
                            <span class="kb-doc-tag">{{ doc.source_type }}</span>
                            <span class="kb-doc-status">{{ doc.status }}</span>
                          </div>
                        </div>
                        <div class="actions kb-item-actions">
                          <button
                            type="button"
                            class="btn btn-outline btn-compact"
                            :disabled="aiBusy"
                            @click.stop="openDocChunks(doc)"
                          >
                            查看分块
                          </button>
                          <button
                            type="button"
                            class="btn btn-outline btn-compact kb-doc-remove-btn"
                            :disabled="aiBusy"
                            @click.stop="removeDoc(doc.id)"
                          >
                            删除
                          </button>
                        </div>
                      </article>
                    </div>
                  </section>
                </section>

                <aside class="kb-column kb-column-right">
                  <section class="kb-card kb-card-shadow kb-chunk-panel">
                    <div class="kb-section-head">
                      <h3>分块详情</h3>
                      <button
                        v-if="chunkViewDocId"
                        type="button"
                        class="btn btn-outline btn-compact"
                        :disabled="aiBusy"
                        @click="clearChunkView"
                      >
                        关闭
                      </button>
                    </div>
                    <div v-if="!selectedKbId" class="mono kb-empty">请先选择知识库。</div>
                    <div v-else-if="!chunkViewDocId" class="mono kb-empty">
                      从中栏选择一篇文档查看分块内容和标签。
                    </div>
                    <template v-else>
                      <div class="chunk-viewer-head">
                        <strong>{{ chunkViewDocTitle || '分块详情' }}</strong>
                        <span class="mono">
                          共 {{ chunkStats.total_chunks }} 块 · 平均 {{ chunkStats.avg_chunk_chars }} 字/块
                        </span>
                      </div>
                      <div v-if="chunkList.length === 0" class="mono kb-empty">暂无分块数据</div>
                      <div v-else class="chunk-list">
                        <div class="chunk-card" v-for="chunk in chunkList" :key="chunk.id">
                          <div class="chunk-card-head">
                            <strong>
                              {{ `Chunk ${String(chunk.chunk_index + 1).padStart(2, '0')}` }}
                            </strong>
                            <span class="mono">
                              {{ chunk.char_count }} 字 · {{ chunk.token_count }} token
                            </span>
                          </div>
                          <div class="result-tags">
                            <span
                              v-for="tag in chunk.tags"
                              :key="`${chunk.id}-${tag}`"
                              class="tag mono"
                            >
                              {{ tag }}
                            </span>
                          </div>
                          <p class="mono">{{ chunk.content_preview }}</p>
                          <details>
                            <summary class="mono">查看完整分块内容</summary>
                            <pre class="chunk-content">{{ chunk.content }}</pre>
                          </details>
                        </div>
                      </div>
                    </template>
                  </section>

                  <section class="kb-card kb-card-shadow kb-design-notes">
                    <h3 class="kb-section-title">设计优化点</h3>
                    <ul>
                      <li>将“知识库 / 文档 / 分块”改成三栏层级，信息关系更清晰。</li>
                      <li>弱化大面积空白，增加卡片层次、状态标签和统计概览。</li>
                      <li>统一圆角、边框和按钮样式，更接近现代 AI SaaS 控制台风格。</li>
                      <li>把“上传、切块、状态、查看”串成一个连续操作流，降低使用成本。</li>
                    </ul>
                  </section>
                </aside>
              </div>

              <p v-if="kbStatus" class="mono kb-status">{{ kbStatus }}</p>
            </div>
          </div>

          <div v-else-if="activeTab === 'match'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>岗位匹配</h2>
                <p>输入技能后自动计算匹配度与差距。</p>
              </div>
            </div>
            <textarea v-model="matchSkills" rows="3" placeholder="技能，如 Linux, Docker, Kubernetes"></textarea>
            <button class="btn" :disabled="aiBusy" @click="runRecommend">开始匹配</button>
            <div v-if="matchResult" class="result-grid">
              <div class="result-card" v-for="match in matchResult.matches" :key="match.job_id">
                <div class="result-head">
                  <strong>{{ match.job_name }}</strong>
                  <span class="mono">总分 {{ match.final_score }}%</span>
                </div>
                <div class="progress">
                  <div class="progress-bar" :style="{ width: match.final_score + '%' }"></div>
                </div>
                <!-- Score breakdown bar -->
                <div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden; margin: 8px 0;">
                  <div :style="{ width: Math.max(match.content_score, 5) + '%', background: '#18a058' }" :title="'内容得分 ' + match.content_score + '%'"></div>
                  <div :style="{ width: Math.max(match.collaborative_score, 5) + '%', background: '#0f8f59' }" :title="'协同得分 ' + match.collaborative_score + '%'"></div>
                </div>
                <div style="display: flex; gap: 16px; font-size: 12px; margin-bottom: 8px;">
                  <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#18a058;margin-right:4px;"></span>内容 {{ match.content_score }}%</span>
                  <span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#0f8f59;margin-right:4px;"></span>协同 {{ match.collaborative_score }}%</span>
                </div>
                <!-- Skill tags -->
                <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">
                  <span v-for="s in match.matched_skills" :key="s" class="tag" style="background: rgba(24,160,88,0.12); color: #18a058; font-size: 11px;">{{ s }}</span>
                  <span v-for="s in match.missing_skills" :key="'m'+s" class="tag" style="background: rgba(24,160,88,0.08); color: #0f8f59; font-size: 11px; text-decoration: line-through;">{{ s }}</span>
                </div>
                <!-- Expandable reason -->
                <details v-if="match.reason" style="margin-top: 4px;">
                  <summary style="cursor: pointer; font-size: 13px; color: #18a058;">为什么推荐？</summary>
                  <p class="mono" style="white-space:pre-wrap;font-size:12px;color:var(--muted);margin-top:6px;padding:8px;background:#f8faf9;border-radius:8px">{{ match.reason }}</p>
                </details>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'rag'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>职业 RAG 助手</h2>
                <p>基于知识库检索回答职业问题。</p>
              </div>
            </div>
            <select v-model="ragKbId" class="field-select">
              <option :value="null">全部知识库（默认）</option>
              <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
            </select>
            <textarea v-model="ragQuestion" rows="3" placeholder="例如：SRE 需要学习什么？"></textarea>
            <button class="btn" :disabled="aiBusy" @click="runRag">提问</button>
            <div v-if="ragAnswer" class="result-block">
              <p style="white-space:pre-wrap">{{ ragAnswer.answer }}</p>
              <div class="result-tags">
                <span class="tag" v-for="path in ragAnswer.learning_path" :key="path">{{ path }}</span>
              </div>
              <p class="mono">技能树：{{ ragAnswer.skill_tree.join(' | ') }}</p>
              <template v-if="ragAnswer.sources && ragAnswer.sources.length > 0">
                <div class="divider"></div>
                <h4>检索来源</h4>
                <div class="list">
                  <div class="list-item" v-for="(src, idx) in ragAnswer.sources" :key="idx">
                    <div>
                      <strong>{{ src.document_title }}</strong>
                      <p class="mono">{{ src.chunk_content.slice(0, 150) }}{{ src.chunk_content.length > 150 ? '...' : '' }}</p>
                    </div>
                    <span class="tag mono">{{ (src.relevance_score * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div v-else-if="activeTab === 'company-match'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>岗位匹配度检测</h2>
                <p>直接选择应聘者，结合目标岗位与模板做匹配度评估。</p>
              </div>
            </div>
            <div class="form-grid">
              <select v-model.number="companyMatchForm.application_id" class="field-select">
                <option :value="0">选择应聘者</option>
                <option
                  v-for="item in companyCandidateList"
                  :key="item.application_id"
                  :value="item.application_id"
                >
                  {{ item.student_name }}｜{{ item.job_name }}｜{{ item.school }}{{ item.verified_for_company ? "｜已核验" : "｜未核验" }}
                </option>
              </select>
              <select v-model.number="companyMatchForm.target_job_id" class="field-select">
                <option :value="0">选择目标岗位</option>
                <option v-for="job in companyJobs" :key="job.id" :value="job.id">{{ job.job_name }}</option>
              </select>
            </div>
            <div class="form-grid">
              <select v-model.number="companyMatchForm.template_id" class="field-select">
                <option :value="0">选择评估模板</option>
                <option v-for="item in templates" :key="item.id" :value="item.id">
                  {{ item.name }}（{{ item.job_title }}）
                </option>
              </select>
              <select v-model="companyMatchForm.kb_id" class="field-select">
                <option :value="null">不使用筛选知识库</option>
                <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
              </select>
            </div>
            <button class="btn" :disabled="aiBusy" @click="runCompanyMatch">执行匹配度检测</button>

            <div v-if="companyMatchResult" class="result-block">
              <p class="mono">
                应聘者：{{ companyMatchResult.application.student_name }}｜目标岗位：{{ companyMatchResult.targetJob.job_name }}｜得分 {{ companyMatchResult.score }}
              </p>
              <p>{{ companyMatchResult.evaluation }}</p>
              <p class="mono">结论：{{ companyMatchResult.recommendation }}</p>
              <div class="result-tags">
                <span class="tag" v-for="skill in companyMatchResult.matchedSkills" :key="`m-${skill}`">{{ skill }}</span>
                <span class="tag mono" v-for="skill in companyMatchResult.missingSkills" :key="`u-${skill}`" style="opacity:0.72">
                  待补：{{ skill }}
                </span>
              </div>
              <div v-if="companyMatchResult.dimension_scores?.length" class="dimension-grid">
                <div class="dimension-item" v-for="dim in companyMatchResult.dimension_scores" :key="dim.dimension">
                  <div class="dim-header">
                    <span>{{ dim.dimension }}</span>
                    <strong>{{ dim.score }}分</strong>
                  </div>
                  <div class="progress"><div class="progress-bar" :style="{ width: dim.score + '%' }"></div></div>
                  <p class="mono" style="font-size:11px">{{ dim.comment }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'company-written-test'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 笔试出题与发送</h2>
                <p>结合企业模板与知识库自动出题，并一键发送给应聘者。</p>
              </div>
              <div class="actions">
                <button
                  class="btn btn-outline btn-compact"
                  :disabled="creatingSampleKb"
                  @click="quickCreateKbForScreening"
                >
                  {{ creatingSampleKb ? '创建中...' : '一键创建测试知识库' }}
                </button>
              </div>
            </div>
            <div class="form-grid">
              <select v-model.number="companyWrittenForm.application_id" class="field-select">
                <option :value="0">选择应聘者</option>
                <option
                  v-for="item in companyCandidateList"
                  :key="item.application_id"
                  :value="item.application_id"
                >
                  {{ item.student_name }}｜{{ item.job_name }}｜{{ item.verified_for_company ? "已核验" : "未核验" }}
                </option>
              </select>
              <select v-model.number="companyWrittenForm.template_id" class="field-select">
                <option :value="0">选择题型模板</option>
                <option v-for="item in templates" :key="item.id" :value="item.id">
                  {{ item.name }}（{{ item.job_title }}）
                </option>
              </select>
            </div>
            <div class="form-grid">
              <select v-model="companyWrittenForm.kb_id" class="field-select">
                <option :value="null">不使用题库知识库</option>
                <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
              </select>
              <input v-model="companyWrittenForm.deadline" placeholder="答题截止时间（可选，如 2026-05-01 18:00）" />
            </div>
            <div class="actions">
              <button class="btn" :disabled="aiBusy" @click="runCompanyWrittenTestGenerate">生成笔试题目</button>
              <button class="btn btn-outline" :disabled="aiBusy || writtenSending || !writtenTestPack" @click="sendCompanyWrittenTest">
                {{ writtenSending ? "发送中..." : "发送给应聘者" }}
              </button>
            </div>

            <div v-if="writtenTestPack" class="result-block">
              <p class="mono">应聘者：{{ writtenTestPack.application.student_name }}｜模板：{{ writtenTestPack.template.name }}</p>
              <ul>
                <li v-for="question in writtenTestPack.questions" :key="question">{{ question }}</li>
              </ul>
              <p class="mono">评分建议：{{ writtenTestPack.recommendation }}</p>
            </div>
          </div>

          <div v-else-if="activeTab === 'company-template'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>企业题型模板</h2>
                <p>设置企业笔试题型，供匹配检测与筛选统一复用。</p>
              </div>
            </div>
            <div class="form-grid">
              <input v-model="templateForm.name" placeholder="模板名称（如 Java 后端初筛）" />
              <input v-model="templateForm.job_title" placeholder="目标岗位" />
              <input v-model="templateForm.question_types_input" placeholder="题型，逗号分隔：技术基础,项目经验,场景分析" />
              <select v-model="templateForm.difficulty" class="field-select" :disabled="aiBusy">
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
              <input v-model.number="templateForm.question_count" type="number" min="1" max="20" placeholder="题目数量" />
            </div>
            <textarea v-model="templateForm.scoring_rules" rows="3" placeholder="评分规则（可选）"></textarea>
            <div class="actions">
              <button class="btn" @click="saveTemplate">保存模板</button>
              <button class="btn btn-outline" @click="resetTemplateForm">清空</button>
            </div>
            <p v-if="templateStatus" class="mono">{{ templateStatus }}</p>

            <div class="list-wrap">
              <div class="list-header">
                <h3>我的模板</h3>
              </div>
              <div v-if="templates.length === 0" class="mono">暂无模板</div>
              <div v-else class="list">
                <div class="list-item" v-for="item in templates" :key="item.id">
                  <div>
                    <strong>{{ item.name }}</strong>
                    <p class="mono">{{ item.job_title }} · {{ item.difficulty }} · {{ item.question_count }} 题</p>
                    <p class="mono">题型：{{ (item.question_types || []).join(', ') || '默认' }}</p>
                  </div>
                  <div class="actions">
                    <button class="btn btn-outline" @click="fillTemplateForm(item)">编辑</button>
                    <button class="btn btn-outline" @click="removeTemplate(item.id)">删除</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'company-screening'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 简历筛选排名</h2>
                <p>系统自动读取应聘者信息，对核验通过候选人进行打分、排序与建议输出。</p>
              </div>
              <div class="actions">
                <button
                  class="btn btn-outline btn-compact"
                  :disabled="creatingSampleKb"
                  @click="quickCreateKbForScreening"
                >
                  {{ creatingSampleKb ? '创建中...' : '一键创建测试知识库' }}
                </button>
              </div>
            </div>
            <div class="form-grid">
              <select v-model.number="companyScreeningForm.job_id" class="field-select">
                <option :value="0">选择目标岗位</option>
                <option v-for="job in companyJobs" :key="job.id" :value="job.id">{{ job.job_name }}</option>
              </select>
              <select v-model.number="companyScreeningForm.template_id" class="field-select">
                <option :value="0">选择筛选模板</option>
                <option v-for="item in templates" :key="item.id" :value="item.id">
                  {{ item.name }}（{{ item.job_title }}）
                </option>
              </select>
            </div>
            <div class="form-grid">
              <select v-model="companyScreeningForm.kb_id" class="field-select">
                <option :value="null">不使用知识库</option>
                <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
              </select>
              <label class="switch-row">
                <input type="checkbox" v-model="screeningOnlyVerified" />
                <span>仅筛选“核验通过”的应聘者</span>
              </label>
            </div>
            <button class="btn" :disabled="aiBusy || screeningRunning" @click="runScreening">
              {{ screeningRunning ? "筛选中..." : "开始筛选并排名" }}
            </button>

            <div class="list-wrap">
              <div class="list-header">
                <h3>筛选结果排名</h3>
                <span class="mono">共 {{ rankingResult.length }} 人</span>
              </div>
              <div v-if="rankingResult.length === 0" class="mono">暂无结果，点击上方按钮执行筛选。</div>
              <div v-else class="list">
                <div class="list-item" v-for="(item, idx) in rankingResult" :key="`${item.application_id}-${item.student_id}`">
                  <div>
                    <strong>#{{
                      idx + 1
                    }} {{ item.student_name }} · {{ item.job_name }}</strong>
                    <p class="mono">{{ item.school }} · {{ item.major }} · {{ item.verified_for_company ? "核验通过" : "未核验" }}</p>
                    <p class="mono">结论：{{ item.recommendation }}</p>
                  </div>
                  <span class="tag mono">得分 {{ item.score }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === 'resume-optimize'" class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 简历优化建议</h2>
                <p>输入目标岗位，AI 分析你的简历并给出优化建议。</p>
              </div>
            </div>
            <input v-model="resumeJobTitle" placeholder="目标岗位（如：后端开发工程师）" />
            <button class="btn" @click="runResumeOptimize" :disabled="resumeLoading || aiBusy">
              {{ resumeLoading ? '分析中...' : '开始分析' }}
            </button>
            <div v-if="resumeResult" class="result-block">
              <p><strong>总评：</strong>{{ resumeResult.summary }}</p>
              <div v-if="resumeResult.strengths.length">
                <strong>优势</strong>
                <div class="tags" style="margin-top:6px">
                  <span class="tag" v-for="s in resumeResult.strengths" :key="s">{{ s }}</span>
                </div>
              </div>
              <div v-if="resumeResult.suggestions.length">
                <strong>改进建议</strong>
                <ul>
                  <li v-for="s in resumeResult.suggestions" :key="s">{{ s }}</li>
                </ul>
              </div>
              <div v-if="resumeResult.missing_skills.length">
                <strong>建议补充的技能</strong>
                <div class="tags" style="margin-top:6px">
                  <span class="tag" v-for="s in resumeResult.missing_skills" :key="s" style="background:rgba(24,160,88,0.1);color:#0f8f59">{{ s }}</span>
                </div>
              </div>
              <div v-if="resumeResult.bio_rewrite">
                <strong>自我评价改写建议</strong>
                <p style="white-space:pre-wrap;background:#f8faf9;padding:12px;border-radius:10px;margin-top:6px">{{ resumeResult.bio_rewrite }}</p>
              </div>
            </div>
          </div>

          <div v-else class="card panel-content">
            <div class="panel-header">
              <div>
                <h2>AI 助手</h2>
                <p>请选择左侧功能模块。</p>
              </div>
            </div>
          </div>

          <AiProcessingOverlay
            :visible="aiProcessing.visible"
            :title="aiProcessing.title"
            :description="aiProcessing.description"
            :progress="aiProcessing.progress"
            :stages="aiProcessing.stages"
            :stage-index="aiProcessing.stageIndex"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  addKBDocumentPaste,
  createInterviewTemplate,
  createKnowledgeBase,
  deleteInterviewTemplate,
  deleteKBDocument,
  deleteKnowledgeBase,
  updateKnowledgeBase,
  fetchInterviewTemplates,
  fetchKBDocumentChunks,
  fetchKBDocuments,
  fetchCompanyApplications,
  fetchCompanyVerificationRequests,
  fetchKnowledgeBases,
  fetchJobs,
  jobRecommend,
  rag,
  rebuildKBEmbeddings,
  resumeOptimize,
  sendMessage,
  screeningInterview,
  updateInterviewTemplate,
  uploadKBDocument,
  uploadKBDocumentExtended
} from "../services/api";
import { useAuth } from "../store/auth";
import toast from '../utils/toast';
import AiProcessingOverlay from "../components/AiProcessingOverlay.vue";

const auth = useAuth();
const route = useRoute();
const router = useRouter();
const role = computed(() => auth.role.value);
const canManageTemplates = computed(() => role.value === "company");
const canStudentMockUpload = computed(() => role.value === "student");
const aiHeroSubtitle = computed(() => (
  role.value === "company"
    ? "应聘者匹配检测、AI 笔试出题与简历筛选排名一体化。"
    : "岗位匹配、企业初筛与简历优化一体化。"
));
const aiWorkflowTag = computed(() => (
  role.value === "company" ? "Company Hiring AI Workflow" : "Interview Workflow"
));
const aiTips = computed(() => (
  canManageTemplates.value
    ? [
      "先配置企业笔试模板，再做匹配度检测与筛选排名。",
      "简历筛选默认优先使用核验通过的应聘者信息，结果更可信。",
      "笔试题目可结合知识库生成，并通过系统消息直接下发应聘者。"
    ]
    : [
      "先做岗位匹配，再用简历优化建议提升投递质量。",
      "保持技能标签和项目经历更新，推荐会更准确。",
      "保留历史会话，便于复盘与改进。"
    ]
));

const tabs = computed(() => {
  if (canManageTemplates.value) {
    return [
      { key: "company-match", title: "岗位匹配度检测", desc: "选择应聘者直接测匹配度" },
      { key: "company-written-test", title: "AI 笔试出题发送", desc: "结合模板与知识库生成并发送" },
      { key: "company-screening", title: "AI 简历筛选排名", desc: "核验通过候选人自动打分排序" },
      { key: "company-template", title: "笔试模板设置", desc: "维护企业题型模板" }
    ];
  }
  const base = [
    { key: "match", title: "岗位匹配", desc: "技能匹配与差距" }
  ];
  if (canStudentMockUpload.value) {
    base.push({ key: "resume-optimize", title: "简历优化", desc: "AI 优化建议" });
  }
  return base;
});

const activeTab = ref("match");
watch(
  tabs,
  (nextTabs) => {
    if (!nextTabs.find((tab) => tab.key === activeTab.value)) {
      activeTab.value = nextTabs[0]?.key || "match";
    }
  },
  { immediate: true }
);

function setActiveTabFromRoute() {
  const routeTab = typeof route.query.tab === "string" ? route.query.tab : "";
  if (!routeTab) return;
  if (tabs.value.some((item) => item.key === routeTab)) {
    activeTab.value = routeTab;
  }
}

const matchSkills = ref("");
const ragQuestion = ref("");
const matchResult = ref(null);
const ragAnswer = ref(null);

const templates = ref([]);
const templateStatus = ref("");
const templateForm = ref({
  id: null,
  name: "",
  job_title: "",
  question_types_input: "",
  difficulty: "medium",
  question_count: 5,
  scoring_rules: ""
});
const creatingSampleKb = ref(false);
const kbRebuilding = ref(false);
const companyApplications = ref([]);
const companyJobs = ref([]);
const companyVerifications = ref([]);
const companyMatchResult = ref(null);
const writtenTestPack = ref(null);
const rankingResult = ref([]);
const screeningOnlyVerified = ref(true);
const screeningRunning = ref(false);
const writtenSending = ref(false);
const companyMatchForm = ref({
  application_id: 0,
  target_job_id: 0,
  template_id: 0,
  kb_id: null
});
const companyWrittenForm = ref({
  application_id: 0,
  template_id: 0,
  kb_id: null,
  deadline: ""
});
const companyScreeningForm = ref({
  job_id: 0,
  template_id: 0,
  kb_id: null
});

// Knowledge Base state
const knowledgeBases = ref([]);
const kbForm = ref({ name: "", description: "" });
const kbDocForm = ref({ title: "", content: "" });
const selectedKbId = ref(null);
const selectedKb = computed(() => (
  knowledgeBases.value.find((kb) => String(kb.id) === String(selectedKbId.value ?? "")) || null
));
const kbDocuments = ref([]);
const kbStatus = ref("");
const chunkViewDocId = ref(0);
const chunkViewDocTitle = ref("");
const chunkList = ref([]);
const chunkStats = ref({ total_chunks: 0, avg_chunk_chars: 0 });
const kbUploadFileName = ref("");
const ragKbId = ref(null);
const resumeJobTitle = ref('');
const resumeResult = ref(null);
const resumeLoading = ref(false);
const aiProcessing = ref({
  visible: false,
  title: 'AI 正在处理中',
  description: '',
  progress: 0,
  stages: [],
  stageIndex: 0
});
const aiBusy = computed(() => aiProcessing.value.visible);
let aiProgressTimer = null;
let aiStageTimer = null;
let aiHideTimer = null;
const approvedStudentIds = computed(() => (
  new Set(
    (companyVerifications.value || [])
      .filter((item) => item.status === "approved")
      .map((item) => Number(item.student_id))
  )
));
const companyCandidateList = computed(() => (
  (companyApplications.value || []).map((item) => ({
    ...item,
    verified_for_company: approvedStudentIds.value.has(Number(item.student_id))
  }))
));
const KB_DOC_TEMPLATES = {
  backend: {
    title: "后端岗位学习路线（示例）",
    content: [
      "岗位方向：后端开发工程师",
      "核心能力：Python、FastAPI、MySQL、Redis、Docker、接口安全",
      "学习路径：",
      "1. 掌握 RESTful API 设计与权限校验（JWT + RBAC）",
      "2. 学习 SQL 索引优化、事务与并发场景",
      "3. 完成缓存设计（热点数据 + 失效策略）",
      "4. 掌握日志、异常处理、限流和输入清洗",
      "面试重点：接口幂等、数据库一致性、缓存击穿与雪崩、服务降级。"
    ].join("\n")
  },
  frontend: {
    title: "前端岗位学习路线（示例）",
    content: [
      "岗位方向：前端开发工程师",
      "核心能力：Vue3、组合式 API、状态管理、性能优化、工程化",
      "学习路径：",
      "1. 熟悉 Vue Router、组件通信和异步状态流",
      "2. 掌握页面性能优化和首屏加载优化",
      "3. 学习可复用组件设计与表单交互规范",
      "4. 完成 API 错误处理、重试、兜底提示",
      "面试重点：响应式原理、虚拟 DOM、路由守卫、SSR 和打包优化。"
    ].join("\n")
  },
  algorithm: {
    title: "推荐算法与AI面试（示例）",
    content: [
      "主题：人岗匹配中的协同过滤 + 内容分析",
      "内容重点：",
      "1. 协同过滤：基于浏览、收藏、投递行为建立隐式反馈矩阵",
      "2. 内容分析：根据技能、城市、行业、薪资计算匹配度",
      "3. 融合策略：最终分数 = 协同得分 * w1 + 内容得分 * w2",
      "4. 冷启动策略：历史行为不足时提高内容权重",
      "AI面试建议：围绕项目贡献、问题拆解、团队协作和表达能力进行多维评估。"
    ].join("\n")
  }
};

function handleQuickTemplate(label) {
  if (label.includes("后端")) {
    fillSampleDocument("backend");
    return;
  }
  if (label.includes("前端")) {
    fillSampleDocument("frontend");
    return;
  }
  if (label.includes("算法")) {
    fillSampleDocument("algorithm");
    return;
  }
  if (label.includes("面试")) {
    fillSampleDocument("backend");
  }
}

function parseList(text) {
  return (text || "")
    .split(/[,，\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function clearChunkView() {
  chunkViewDocId.value = 0;
  chunkViewDocTitle.value = "";
  chunkList.value = [];
  chunkStats.value = { total_chunks: 0, avg_chunk_chars: 0 };
}

function clearAiProcessingTimers() {
  if (aiProgressTimer) clearInterval(aiProgressTimer);
  if (aiStageTimer) clearInterval(aiStageTimer);
  if (aiHideTimer) clearTimeout(aiHideTimer);
  aiProgressTimer = null;
  aiStageTimer = null;
  aiHideTimer = null;
}

function beginAiProcessing({ title, description = "", stages = [] }) {
  clearAiProcessingTimers();
  aiProcessing.value = {
    visible: true,
    title: title || "AI 正在处理中",
    description,
    progress: 8,
    stages,
    stageIndex: 0
  };
  aiProgressTimer = setInterval(() => {
    if (!aiProcessing.value.visible) return;
    const now = aiProcessing.value.progress;
    if (now >= 92) return;
    aiProcessing.value.progress = Math.min(92, now + Math.max(1, Math.floor((95 - now) / 8)));
  }, 220);
  if (stages.length > 1) {
    aiStageTimer = setInterval(() => {
      if (!aiProcessing.value.visible) return;
      aiProcessing.value.stageIndex = Math.min(stages.length - 1, aiProcessing.value.stageIndex + 1);
    }, 1050);
  }
}

function endAiProcessing() {
  return new Promise((resolve) => {
    if (!aiProcessing.value.visible) {
      resolve();
      return;
    }
    aiProcessing.value.progress = 100;
    if (aiProcessing.value.stages.length) {
      aiProcessing.value.stageIndex = aiProcessing.value.stages.length - 1;
    }
    if (aiProgressTimer) clearInterval(aiProgressTimer);
    if (aiStageTimer) clearInterval(aiStageTimer);
    aiProgressTimer = null;
    aiStageTimer = null;
    aiHideTimer = setTimeout(() => {
      aiProcessing.value.visible = false;
      resolve();
    }, 240);
  });
}

async function withAiProcessing(options, task) {
  beginAiProcessing(options);
  try {
    return await task();
  } finally {
    await endAiProcessing();
  }
}

async function runRecommend() {
  try {
    await withAiProcessing(
      {
        title: "AI 正在计算岗位匹配",
        description: "会综合内容匹配和协同信号",
        stages: ["解析技能", "计算匹配度", "生成推荐理由"]
      },
      async () => {
        matchResult.value = await jobRecommend({
          student_id: auth.user.value?.id || null,
          skills: parseList(matchSkills.value)
        });
      }
    );
  } catch (err) {
    matchResult.value = null;
    toast.error('岗位匹配失败，请稍后重试');
  }
}

async function runRag() {
  try {
    await withAiProcessing(
      {
        title: "AI 正在检索知识库",
        description: "会先检索相关文档，再生成回答",
        stages: ["向量检索", "融合上下文", "生成回答"]
      },
      async () => {
        ragAnswer.value = await rag({
          question: ragQuestion.value,
          kb_id: ragKbId.value || undefined,
          top_k: 5
        });
      }
    );
  } catch (err) {
    ragAnswer.value = null;
    toast.error('提问失败，请稍后重试');
  }
}

async function loadTemplates() {
  if (!canManageTemplates.value) return;
  try {
    templates.value = await fetchInterviewTemplates();
    setCompanyFormDefaults();
  } catch (err) {
    templates.value = [];
  }
}

function resetTemplateForm() {
  templateForm.value = {
    id: null,
    name: "",
    job_title: "",
    question_types_input: "",
    difficulty: "medium",
    question_count: 5,
    scoring_rules: ""
  };
}

function fillTemplateForm(item) {
  templateForm.value = {
    id: item.id,
    name: item.name,
    job_title: item.job_title,
    question_types_input: (item.question_types || []).join(","),
    difficulty: item.difficulty || "medium",
    question_count: item.question_count || 5,
    scoring_rules: item.scoring_rules || ""
  };
}

async function saveTemplate() {
  if (!templateForm.value.name || !templateForm.value.job_title) {
    templateStatus.value = "请先填写模板名称和岗位";
    return;
  }

  const payload = {
    name: templateForm.value.name,
    job_title: templateForm.value.job_title,
    question_types: parseList(templateForm.value.question_types_input),
    difficulty: templateForm.value.difficulty,
    question_count: Number(templateForm.value.question_count) || 5,
    scoring_rules: templateForm.value.scoring_rules
  };

  try {
    if (templateForm.value.id) {
      await updateInterviewTemplate(templateForm.value.id, payload);
      templateStatus.value = "模板已更新";
    } else {
      await createInterviewTemplate(payload);
      templateStatus.value = "模板已创建";
    }
    resetTemplateForm();
    await loadTemplates();
  } catch (err) {
    templateStatus.value = "保存失败";
  }
}

async function removeTemplate(id) {
  if (!confirm('确定要删除该面试模板吗？')) return;
  try {
    await deleteInterviewTemplate(id);
    templateStatus.value = "模板已删除";
    await loadTemplates();
  } catch (err) {
    templateStatus.value = "删除失败";
  }
}

function findTemplateById(templateId) {
  return templates.value.find((item) => Number(item.id) === Number(templateId)) || null;
}

function findApplicationById(applicationId) {
  return companyCandidateList.value.find((item) => Number(item.application_id) === Number(applicationId)) || null;
}

function findCompanyJobById(jobId) {
  return companyJobs.value.find((item) => Number(item.id) === Number(jobId)) || null;
}

function normalizeResumeArray(rawValue) {
  if (Array.isArray(rawValue)) {
    return rawValue.map((item) => String(item || "").trim()).filter(Boolean);
  }
  if (typeof rawValue === "string") {
    return rawValue.split(/\n|；|;|，|,/).map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function buildCandidatePayload(app) {
  const resume = app?.resume_content && typeof app.resume_content === "object" ? app.resume_content : {};
  const resumeSkills = normalizeResumeArray(resume.skills);
  const mergedSkills = Array.from(new Set([...(app.skills || []), ...resumeSkills]));
  const summaryParts = [
    `学校：${app.school || "-"}`,
    `专业：${app.major || "-"}`,
    `年级：${app.grade || "-"}`,
    resume.bio ? `简历摘要：${resume.bio}` : "",
    resume.summary ? `个人简介：${resume.summary}` : ""
  ].filter(Boolean);
  const experienceParts = [
    ...normalizeResumeArray(resume.internships),
    ...normalizeResumeArray(resume.projects),
    ...normalizeResumeArray(resume.experience)
  ];
  return {
    candidate_name: app.student_name || `学生${app.student_id}`,
    candidate_summary: summaryParts.join("；"),
    candidate_skills: mergedSkills,
    candidate_experience: experienceParts.join("；")
  };
}

function setCompanyFormDefaults() {
  const firstCandidate = companyCandidateList.value[0];
  const firstTemplate = templates.value[0];
  const firstJob = companyJobs.value[0];
  if (!companyMatchForm.value.application_id && firstCandidate) {
    companyMatchForm.value.application_id = Number(firstCandidate.application_id);
  }
  if (!companyMatchForm.value.target_job_id && firstJob) {
    companyMatchForm.value.target_job_id = Number(firstJob.id);
  }
  if (!companyMatchForm.value.template_id && firstTemplate) {
    companyMatchForm.value.template_id = Number(firstTemplate.id);
  }
  if (!companyWrittenForm.value.application_id && firstCandidate) {
    companyWrittenForm.value.application_id = Number(firstCandidate.application_id);
  }
  if (!companyWrittenForm.value.template_id && firstTemplate) {
    companyWrittenForm.value.template_id = Number(firstTemplate.id);
  }
  if (!companyScreeningForm.value.job_id && firstJob) {
    companyScreeningForm.value.job_id = Number(firstJob.id);
  }
  if (!companyScreeningForm.value.template_id && firstTemplate) {
    companyScreeningForm.value.template_id = Number(firstTemplate.id);
  }
}

async function loadCompanyAiData() {
  const companyId = Number(auth.user.value?.id || 0);
  if (!companyId || !canManageTemplates.value) return;
  try {
    const [applications, jobs, verifications] = await Promise.all([
      fetchCompanyApplications(),
      fetchJobs({ company_id: companyId, status: "active" }),
      fetchCompanyVerificationRequests(companyId)
    ]);
    companyApplications.value = Array.isArray(applications) ? applications : [];
    companyJobs.value = Array.isArray(jobs) ? jobs : [];
    companyVerifications.value = Array.isArray(verifications) ? verifications : [];
    setCompanyFormDefaults();
  } catch (_) {
    companyApplications.value = [];
    companyJobs.value = [];
    companyVerifications.value = [];
  }
}

async function runCompanyMatch() {
  const app = findApplicationById(companyMatchForm.value.application_id);
  const template = findTemplateById(companyMatchForm.value.template_id);
  const targetJob = findCompanyJobById(companyMatchForm.value.target_job_id);
  if (!app || !template || !targetJob) {
    toast.warn("请先选择应聘者、目标岗位和模板");
    return;
  }
  const candidate = buildCandidatePayload(app);
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在执行岗位匹配度检测",
        description: "会基于岗位、候选信息与可选知识库综合评估",
        stages: ["解析候选信息", "岗位能力对齐", "输出匹配结论"]
      },
      async () => screeningInterview({
        template_id: Number(template.id),
        candidate_name: candidate.candidate_name,
        candidate_summary: candidate.candidate_summary,
        candidate_skills: candidate.candidate_skills,
        candidate_experience: candidate.candidate_experience,
        kb_id: companyMatchForm.value.kb_id || undefined
      })
    );
    const targetSkills = Array.isArray(targetJob.skill_tags) ? targetJob.skill_tags : [];
    const candidateSkillLower = new Set(candidate.candidate_skills.map((item) => String(item).toLowerCase()));
    const matchedSkills = targetSkills.filter((item) => candidateSkillLower.has(String(item).toLowerCase()));
    const missingSkills = targetSkills.filter((item) => !candidateSkillLower.has(String(item).toLowerCase()));
    companyMatchResult.value = {
      ...result,
      application: app,
      targetJob,
      matchedSkills,
      missingSkills
    };
  } catch (_) {
    companyMatchResult.value = null;
    toast.error("岗位匹配度检测失败，请稍后重试");
  }
}

async function runCompanyWrittenTestGenerate() {
  const app = findApplicationById(companyWrittenForm.value.application_id);
  const template = findTemplateById(companyWrittenForm.value.template_id);
  if (!app || !template) {
    toast.warn("请先选择应聘者和模板");
    return;
  }
  const candidate = buildCandidatePayload(app);
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在生成企业笔试题目",
        description: "会融合企业题型模板和可选知识库内容出题",
        stages: ["读取模板配置", "知识库融合出题", "整理可发送笔试内容"]
      },
      async () => screeningInterview({
        template_id: Number(template.id),
        candidate_name: candidate.candidate_name,
        candidate_summary: candidate.candidate_summary,
        candidate_skills: candidate.candidate_skills,
        candidate_experience: candidate.candidate_experience,
        kb_id: companyWrittenForm.value.kb_id || undefined
      })
    );
    writtenTestPack.value = {
      ...result,
      application: app,
      template
    };
  } catch (_) {
    writtenTestPack.value = null;
    toast.error("笔试题目生成失败，请稍后重试");
  }
}

async function sendCompanyWrittenTest() {
  if (!writtenTestPack.value?.application?.student_id || !writtenTestPack.value?.questions?.length) {
    toast.warn("请先生成笔试题目");
    return;
  }
  const studentId = Number(writtenTestPack.value.application.student_id);
  const senderId = Number(auth.user.value?.id || 0);
  if (!senderId) {
    toast.error("发送失败：未获取到当前企业账号");
    return;
  }
  const deadlineText = companyWrittenForm.value.deadline ? `请在 ${companyWrittenForm.value.deadline} 前完成。` : "请尽快完成。";
  const content = [
    `【企业AI笔试】岗位：${writtenTestPack.value.template?.job_title || "目标岗位"}`,
    deadlineText,
    "",
    ...writtenTestPack.value.questions.map((q, idx) => `${idx + 1}. ${q}`),
    "",
    "请在消息中逐题回复答案。"
  ].join("\n");
  writtenSending.value = true;
  try {
    await withAiProcessing(
      {
        title: "AI 正在发送笔试题目",
        description: "会将题目通过系统消息发送给应聘者",
        stages: ["整理题目内容", "发送系统消息", "完成下发"]
      },
      async () => sendMessage({
        sender_id: senderId,
        receiver_id: studentId,
        content,
        message_type: "system"
      })
    );
    toast.success("笔试题目已发送给应聘者");
  } catch (_) {
    toast.error("发送失败，请稍后重试");
  } finally {
    writtenSending.value = false;
  }
}

async function runScreening() {
  const targetJob = findCompanyJobById(companyScreeningForm.value.job_id);
  const template = findTemplateById(companyScreeningForm.value.template_id);
  if (!targetJob || !template) {
    toast.warn("请先选择目标岗位和模板");
    return;
  }
  const candidates = companyCandidateList.value.filter((item) => (
    Number(item.job_id) === Number(targetJob.id)
      && (!screeningOnlyVerified.value || item.verified_for_company)
  ));
  if (candidates.length === 0) {
    toast.warn("当前条件下暂无可筛选应聘者");
    rankingResult.value = [];
    return;
  }
  screeningRunning.value = true;
  try {
    const resultList = [];
    await withAiProcessing(
      {
        title: "AI 正在执行简历筛选排名",
        description: `共 ${candidates.length} 位应聘者，正在逐个评估`,
        stages: ["读取候选信息", "结合模板与知识库评分", "输出排序结果"]
      },
      async () => {
        for (let i = 0; i < candidates.length; i += 1) {
          const app = candidates[i];
          aiProcessing.value.description = `正在评估 ${i + 1}/${candidates.length}：${app.student_name}`;
          const candidate = buildCandidatePayload(app);
          const pack = await screeningInterview({
            template_id: Number(template.id),
            candidate_name: candidate.candidate_name,
            candidate_summary: candidate.candidate_summary,
            candidate_skills: candidate.candidate_skills,
            candidate_experience: candidate.candidate_experience,
            kb_id: companyScreeningForm.value.kb_id || undefined
          });
          resultList.push({
            application_id: app.application_id,
            student_id: app.student_id,
            student_name: app.student_name,
            school: app.school,
            major: app.major,
            job_name: app.job_name,
            verified_for_company: app.verified_for_company,
            score: Number(pack.score || 0),
            recommendation: pack.recommendation || "",
            focus_areas: pack.focus_areas || [],
            dimension_scores: pack.dimension_scores || [],
            questions: pack.questions || [],
            evaluation: pack.evaluation || ""
          });
        }
      }
    );
    resultList.sort((a, b) => b.score - a.score);
    rankingResult.value = resultList;
  } catch (_) {
    rankingResult.value = [];
    toast.error("简历筛选失败，请稍后重试");
  } finally {
    screeningRunning.value = false;
  }
}

async function runResumeOptimize() {
  if (!resumeJobTitle.value) { toast.warn('请输入目标岗位'); return; }
  resumeLoading.value = true;
  try {
    await withAiProcessing(
      {
        title: "AI 正在分析简历",
        description: "会从匹配度、表达和技能缺口给出建议",
        stages: ["解析简历", "岗位对齐分析", "生成优化建议"]
      },
      async () => {
        resumeResult.value = await resumeOptimize({ job_title: resumeJobTitle.value });
      }
    );
  } catch (e) {
    toast.error('简历优化分析失败');
    resumeResult.value = null;
  } finally {
    resumeLoading.value = false;
  }
}

// --- Knowledge Base functions ---
async function loadKnowledgeBases() {
  try {
    knowledgeBases.value = await fetchKnowledgeBases();
    if (knowledgeBases.value.length === 0) {
      selectedKbId.value = null;
      kbDocuments.value = [];
      clearChunkView();
      return;
    }
    const hasSelected = selectedKbId.value !== null
      && knowledgeBases.value.some((kb) => String(kb.id) === String(selectedKbId.value));
    if (!hasSelected) {
      await selectKB(knowledgeBases.value[0].id);
    }
  } catch (e) {
    knowledgeBases.value = [];
    selectedKbId.value = null;
    kbDocuments.value = [];
    clearChunkView();
  }
}

async function createKB() {
  if (!kbForm.value.name) { kbStatus.value = "请输入知识库名称"; return; }
  try {
    await withAiProcessing(
      {
        title: "AI 正在创建知识库",
        description: "会完成知识库初始化并准备索引",
        stages: ["创建知识库", "写入基础信息", "准备完成"]
      },
      async () => {
        await createKnowledgeBase(kbForm.value);
      }
    );
    kbForm.value = { name: "", description: "" };
    kbStatus.value = "知识库已创建";
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "创建失败"; }
}

function fillSampleDocument(type) {
  const template = KB_DOC_TEMPLATES[type];
  if (!template) return;
  kbDocForm.value.title = template.title;
  kbDocForm.value.content = template.content;
  kbStatus.value = "示例文档已填充，可直接添加到当前知识库";
}

async function createSampleKnowledgeBase() {
  const template = KB_DOC_TEMPLATES.algorithm;
  const name = `测试知识库-${new Date().toISOString().slice(0, 10)}`;
  try {
    const kb = await withAiProcessing(
      {
        title: "AI 正在创建测试知识库",
        description: "会自动写入示例文档并完成向量化",
        stages: ["创建知识库", "写入示例文档", "切片与向量化"]
      },
      async () => {
        const created = await createKnowledgeBase({
          name,
          description: "用于测试 RAG 问答和 AI 面试功能的示例知识库"
        });
        await addKBDocumentPaste(created.id, {
          title: template.title,
          content: template.content
        });
        return created;
      }
    );
    kbStatus.value = "测试知识库已创建并写入示例文档";
    await loadKnowledgeBases();
    await selectKB(kb.id);
    return kb.id;
  } catch (e) {
    kbStatus.value = "一键创建测试知识库失败";
    return null;
  }
}

async function quickCreateKbForScreening() {
  if (creatingSampleKb.value) return;
  creatingSampleKb.value = true;
  try {
    const kbId = await createSampleKnowledgeBase();
    if (kbId) {
      companyMatchForm.value.kb_id = kbId;
      companyWrittenForm.value.kb_id = kbId;
      companyScreeningForm.value.kb_id = kbId;
      templateStatus.value = "测试知识库已创建，可直接用于匹配、出题和筛选";
    } else {
      templateStatus.value = "测试知识库创建失败，请稍后重试";
    }
  } finally {
    creatingSampleKb.value = false;
  }
}

async function renameKB(kb) {
  const newName = prompt('输入新名称', kb.name);
  if (!newName || newName === kb.name) return;
  try {
    await withAiProcessing(
      {
        title: "AI 正在更新知识库",
        description: "会保存新的知识库名称",
        stages: ["校验名称", "更新知识库", "刷新列表"]
      },
      async () => {
        await updateKnowledgeBase(kb.id, { name: newName, description: kb.description });
      }
    );
    kbStatus.value = '知识库已更名';
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = '更名失败'; }
}

async function removeKB(kbId) {
  if (!confirm('确定要删除该知识库吗？相关文档将一并删除。')) return;
  try {
    await withAiProcessing(
      {
        title: "AI 正在删除知识库",
        description: "会同时清理关联文档与向量切片",
        stages: ["校验权限", "删除文档与切片", "删除知识库"]
      },
      async () => {
        await deleteKnowledgeBase(kbId);
      }
    );
    if (String(selectedKbId.value) === String(kbId)) {
      selectedKbId.value = null;
      kbDocuments.value = [];
    }
    clearChunkView();
    kbStatus.value = "知识库已删除";
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "删除失败"; }
}

async function selectKB(kbId) {
  selectedKbId.value = kbId;
  clearChunkView();
  try {
    kbDocuments.value = await fetchKBDocuments(kbId);
  } catch (e) { kbDocuments.value = []; }
}

async function openDocChunks(doc) {
  if (!selectedKbId.value || !doc?.id) return;
  if (chunkViewDocId.value === doc.id && chunkList.value.length > 0) {
    return;
  }
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在读取分块详情",
        description: "会展示分块内容、大小和自动标签",
        stages: ["读取分块", "分析标签", "整理展示"]
      },
      async () => fetchKBDocumentChunks(selectedKbId.value, doc.id)
    );
    chunkViewDocId.value = doc.id;
    chunkViewDocTitle.value = String(doc.title || "");
    chunkList.value = Array.isArray(result?.chunks) ? result.chunks : [];
    chunkStats.value = {
      total_chunks: Number(result?.total_chunks || chunkList.value.length || 0),
      avg_chunk_chars: Number(result?.avg_chunk_chars || 0),
    };
  } catch (e) {
    toast.error("读取分块失败，请稍后重试");
  }
}

async function addDocPaste() {
  if (!selectedKbId.value) { kbStatus.value = "请先选择知识库"; return; }
  if (!kbDocForm.value.title || !kbDocForm.value.content) { kbStatus.value = "请填写标题和内容"; return; }
  try {
    await withAiProcessing(
      {
        title: "AI 正在处理文档",
        description: "会自动切片并向量化写入知识库",
        stages: ["接收文档", "文本切片", "向量化并入库"]
      },
      async () => {
        await addKBDocumentPaste(selectedKbId.value, kbDocForm.value);
      }
    );
    kbDocForm.value = { title: "", content: "" };
    kbStatus.value = "文档已添加并完成向量化";
    await selectKB(selectedKbId.value);
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "添加失败"; }
}

async function rebuildSelectedKbEmbeddings() {
  if (!selectedKbId.value) {
    kbStatus.value = "请先选择知识库";
    return;
  }
  kbRebuilding.value = true;
  try {
    const result = await withAiProcessing(
      {
        title: "AI 正在重算向量",
        description: "会重新编码切片并更新向量索引",
        stages: ["读取切片", "批量向量化", "写回索引"]
      },
      async () => rebuildKBEmbeddings(selectedKbId.value)
    );
    kbStatus.value = `重算完成：重算 ${result.reembedded_chunks} 条，已就绪 ${result.already_ready_chunks} 条，空内容 ${result.skipped_empty_chunks} 条`;
    await selectKB(selectedKbId.value);
  } catch (e) {
    kbStatus.value = "向量重算失败";
    toast.error("向量重算失败，请稍后重试");
  } finally {
    kbRebuilding.value = false;
  }
}

async function uploadDoc(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  kbUploadFileName.value = String(file.name || "");
  if (!selectedKbId.value) {
    kbStatus.value = "请先选择知识库";
    return;
  }
  const lower = String(file.name || "").toLowerCase();
  try {
    await withAiProcessing(
      {
        title: "AI 正在上传并向量化文件",
        description: "会提取文本、切片并更新知识库索引",
        stages: ["上传文件", "提取文本", "向量化并入库"]
      },
      async () => {
        if (lower.endsWith(".pdf") || lower.endsWith(".docx") || lower.endsWith(".doc")) {
          await uploadKBDocumentExtended(selectedKbId.value, file);
        } else {
          await uploadKBDocument(selectedKbId.value, file);
        }
      }
    );
    kbStatus.value = "文件已上传并完成向量化";
    await selectKB(selectedKbId.value);
    await loadKnowledgeBases();
  } catch (e) { kbStatus.value = "上传失败"; }
}

async function removeDoc(docId) {
  if (!selectedKbId.value) return;
  try {
    await withAiProcessing(
      {
        title: "AI 正在删除文档",
        description: "会同步清理该文档关联的向量切片",
        stages: ["定位文档", "删除切片", "刷新索引"]
      },
      async () => {
        await deleteKBDocument(selectedKbId.value, docId);
      }
    );
    kbStatus.value = "文档已删除";
    if (chunkViewDocId.value === docId) {
      clearChunkView();
    }
    await selectKB(selectedKbId.value);
  } catch (e) { kbStatus.value = "删除失败"; }
}

async function refreshRoleData() {
  await loadKnowledgeBases();
  if (canManageTemplates.value) {
    await Promise.all([loadTemplates(), loadCompanyAiData()]);
    return;
  }
}

onMounted(async () => {
  setActiveTabFromRoute();
  await refreshRoleData();
});

watch(
  () => route.query.tab,
  () => {
    setActiveTabFromRoute();
  }
);

watch(
  activeTab,
  (tab) => {
    if (route.query.tab === tab) return;
    router.replace({ query: { ...route.query, tab } });
  }
);

watch(
  () => companyMatchForm.value.application_id,
  (applicationId) => {
    if (!applicationId) return;
    const app = findApplicationById(applicationId);
    if (!app) return;
    companyMatchForm.value.target_job_id = Number(app.job_id || 0);
  }
);

onUnmounted(() => {
  clearAiProcessingTimers();
});
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero {
  padding: 32px 0 16px;
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.ai-grid {
  display: grid;
  grid-template-columns: minmax(220px, 0.25fr) minmax(0, 1fr);
  gap: 24px;
}

.ai-tabs {
  padding: 20px;
  gap: 12px;
}

.ai-panel {
  position: relative;
  overflow: hidden;
  min-height: 560px;
}

.tab {
  text-align: left;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #fff;
  cursor: pointer;
}

.tab strong {
  font-size: 15px;
}

.tab span {
  color: var(--muted);
  font-size: 12px;
}

.tab.active {
  border-color: rgba(24, 160, 88, 0.4);
  background: rgba(24, 160, 88, 0.1);
}

.ai-summary {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
}

.ai-summary ul {
  padding-left: 18px;
  color: var(--muted);
}

.sample-box {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 12px;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-content-kb {
  gap: 16px;
}

.kb-shell {
  background: #f4f7f2;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.kb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  flex-wrap: wrap;
  padding: 24px;
  border-radius: 28px;
  border: 1px solid #d9e6d7;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 40px rgba(36, 64, 45, 0.08);
  backdrop-filter: blur(8px);
}

.kb-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid #dce9da;
  background: #f7fbf6;
  font-size: 12px;
  font-weight: 500;
  color: #4c6b53;
  margin-bottom: 8px;
}

.kb-title {
  margin: 0;
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.kb-subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 24px;
  color: #64748b;
  max-width: 520px;
}

.kb-header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.kb-header-btn-secondary {
  border-radius: 16px;
  border: 1px solid #d9e6d7;
  background: #ffffff;
  color: #334155;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: background-color 0.2s;
}

.kb-header-btn-secondary:hover {
  background-color: #f8fafc;
}

.kb-header-btn-primary {
  border-radius: 16px;
  background: #1f9d55;
  color: #ffffff;
  border: none;
  box-shadow: 0 8px 20px rgba(31, 157, 85, 0.28);
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, background-color 0.2s;
}

.kb-header-btn-primary:hover {
  background-color: #188848;
  transform: translateY(-1px);
}

.kb-layout-grid {
  display: grid;
  grid-template-columns: 300px minmax(460px, 1fr) 380px;
  gap: 24px;
  align-items: flex-start;
}

@media (max-width: 1400px) {
  .kb-layout-grid {
    grid-template-columns: 1fr 1fr;
    grid-auto-flow: row;
    grid-auto-rows: auto;
  }

  .kb-column-left {
    grid-column: 1;
    grid-row: 1;
    min-width: 0;
  }

  .kb-column-middle {
    grid-column: 2;
    grid-row: 1;
    min-width: 0;
  }

  .kb-column-right {
    grid-column: 1 / -1;
    grid-row: 2;
    min-width: 0;
  }

  .kb-column-right .kb-chunk-panel {
    min-height: 360px;
  }

  .kb-column-right .chunk-list {
    max-height: 320px;
  }
}

@media (max-width: 900px) {
  .kb-layout-grid {
    grid-template-columns: 1fr;
  }

  .kb-column-left {
    grid-column: 1;
    grid-row: 1;
  }

  .kb-column-middle {
    grid-column: 1;
    grid-row: 2;
  }

  .kb-column-right {
    grid-column: 1;
    grid-row: 3;
  }

  .kb-list,
  .kb-doc-items,
  .kb-column-right .chunk-list {
    max-height: none;
  }
}

.kb-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.kb-card-shadow {
  border-radius: 26px;
  border: 1px solid #d9e6d7;
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(36, 64, 45, 0.06);
  padding: 20px;
}

.kb-chip-count {
  padding: 4px 10px;
  border-radius: 999px;
  background: #eff7ee;
  font-size: 12px;
  font-weight: 500;
  color: #3d7a4f;
}

.kb-empty {
  font-size: 12px;
  color: var(--muted);
}

.kb-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #fff;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kb-card.is-disabled {
  opacity: 0.72;
}

.kb-section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.kb-section-head h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.kb-section-title {
  margin: 0 0 6px;
}

.kb-compact-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kb-compact-form input,
.kb-compact-form textarea {
  border-radius: 16px;
  border: 1px solid #dfe8dd;
  background: #fbfcfb;
  padding: 12px 16px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  width: 100%;
}

.kb-compact-form input:focus,
.kb-compact-form textarea:focus {
  border-color: #8bcc9e;
  box-shadow: 0 0 0 4px #dff3e5;
}

.kb-compact-form textarea {
  min-height: 150px;
  resize: vertical;
}

.kb-list,
.kb-doc-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kb-doc-item {
  border: 1px solid #e4ebe2;
  border-radius: 16px;
  padding: 16px;
  background: #fcfdfc;
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

@media (min-width: 1024px) {
  .kb-doc-item {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.kb-doc-item:hover {
  border-color: #bdd6c0;
  box-shadow: 0 8px 22px rgba(36, 64, 45, 0.06);
}

.kb-doc-item.active {
  border-color: #97d5ac;
  background: #f3fbf5;
}

.kb-doc-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kb-doc-main strong {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.kb-doc-main p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.kb-doc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.kb-doc-tag {
  padding: 2px 10px;
  border-radius: 999px;
  background: #f1f5f0;
  font-size: 12px;
  color: #475569;
}

.kb-doc-status {
  padding: 2px 10px;
  border-radius: 999px;
  background: #eaf8ef;
  font-size: 12px;
  color: #257245;
}

.kb-lib-item {
  border-radius: 16px;
  border: 1px solid #e6ece4;
  background: #fbfcfb;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}

.kb-lib-item:hover {
  border-color: #cfe0cb;
}

.kb-lib-item.active {
  border-color: #97d5ac;
  background: #f3fbf5;
  box-shadow: 0 10px 24px rgba(31, 157, 85, 0.1);
}

.kb-lib-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kb-lib-name {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.kb-lib-desc {
  font-size: 14px;
  color: #64748b;
  margin-top: 4px;
}

.kb-chip-current {
  padding: 4px 8px;
  border-radius: 999px;
  background: #dff3e5;
  font-size: 11px;
  font-weight: 500;
  color: #237644;
}

.kb-list-item:hover,
.kb-doc-item:hover {
  border-color: rgba(24, 160, 88, 0.35);
}

.kb-list-item.active,
.kb-doc-item.active {
  border-color: rgba(24, 160, 88, 0.45);
  background: rgba(24, 160, 88, 0.08);
}

.kb-list-main p {
  margin: 4px 0 0;
}

.kb-item-actions {
  justify-content: flex-end;
}

.kb-current {
  padding: 24px;
}

.kb-current .kb-section-head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

@media (min-width: 1024px) {
  .kb-current .kb-section-head {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.kb-current h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.kb-current-desc {
  font-size: 14px;
  color: #64748b;
  margin: 4px 0 0;
}

.kb-current-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.kb-meta-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: #f4f7f3;
  font-size: 12px;
  color: #64748b;
}

.kb-meta-pill {
  padding: 4px 10px;
  border-radius: 999px;
  background: #eaf8ef;
  font-size: 12px;
  color: #257245;
}

.kb-current-tags {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 16px;
  border-top: 1px solid #f1f5f9;
  padding-top: 16px;
}

.kb-tag {
  border-radius: 16px;
  border: 1px solid #e7eee5;
  background: #fbfcfb;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kb-tag::before {
  content: attr(data-label);
  font-size: 12px;
  font-weight: 400;
  color: #64748b;
}

.kb-doc-list {
  min-height: 280px;
}

.kb-column-right .kb-chunk-panel {
  min-height: 560px;
}

.kb-column-right .chunk-list {
  max-height: 520px;
  overflow: auto;
  padding-right: 2px;
}

.kb-template-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.kb-template-btn {
  border-radius: 16px;
  border: 1px solid #e4ebe2;
  background: #fafcfa;
  padding: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.kb-template-btn:hover {
  border-color: #b8d4be;
  background: #f4faf4;
}

.kb-oneclick-btn {
  margin-top: 16px;
  width: 100%;
  border-radius: 16px;
  background: #0f172a;
  color: #ffffff;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.kb-oneclick-btn:hover {
  background: #1e293b;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.switch-row {
  min-height: 46px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: #fff;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #4b5f58;
  font-size: 13px;
}

.switch-row input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.result-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.result-card {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress {
  height: 8px;
  background: rgba(24, 160, 88, 0.1);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #8ce0b6);
}

.result-block {
  border: 1px dashed var(--line);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.list-wrap {
  border-top: 1px dashed var(--line);
  padding-top: 12px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.list-item.active {
  border-color: rgba(24, 160, 88, 0.4);
  background: rgba(24, 160, 88, 0.08);
}

.chunk-viewer {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chunk-viewer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chunk-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chunk-card {
  border: 1px solid #e5ece3;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #fbfcfb;
}

.chunk-card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.chunk-card-head strong {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.chunk-card-head .mono {
  font-size: 14px;
  color: #64748b;
}

.chunk-content {
  margin: 8px 0 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
}

.divider {
  height: 1px;
  background: var(--line);
  margin: 8px 0;
}

h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.kb-section-head-add-doc {
  margin-bottom: 20px;
}

.kb-rebuild-btn {
  border-radius: 999px;
  background: #f8fbf8;
  border-color: #d9e6d7;
  color: #475569;
  font-weight: 500;
  padding: 6px 12px;
}

.kb-doc-remove-btn {
  border-color: #f0d4d4;
  color: #b34444;
  background: white;
}

.kb-doc-remove-btn:hover {
  background: #fff7f7;
}

.kb-design-notes {
  background: linear-gradient(135deg, #f5fbf6 0%, #ffffff 100%);
}

.kb-design-notes .kb-section-title {
  margin-bottom: 12px;
  font-size: 18px;
  font-weight: 600;
}

.kb-design-notes ul {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kb-add-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.kb-add-actions .btn {
  border-radius: 16px;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
}

.kb-add-actions .btn:not(.btn-outline) {
  background: #1f9d55;
  color: #ffffff;
  border: none;
  box-shadow: 0 10px 24px rgba(31, 157, 85, 0.24);
  transition: background-color 0.2s;
}

.kb-add-actions .btn:not(.btn-outline):hover {
  background: #188848;
}

.file-picker {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.file-picker input[type="file"] {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-picker.is-disabled {
  opacity: 0.6;
  pointer-events: none;
}

.kb-add-actions .file-picker-btn {
  border: 1px dashed #bdd5bf;
  background: #f9fcf8;
  color: #334155;
  transition: background-color 0.2s;
  min-height: auto;
  border-radius: 16px;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.kb-add-actions .file-picker-btn:hover {
  background: #f2f8f2;
}

.kb-add-actions .file-picker-name {
  font-size: 14px;
  color: #94a3b8;
}

.file-picker-btn {
  min-height: 38px;
  min-width: 102px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.file-picker-name {
  color: var(--muted);
  font-size: 13px;
}

textarea,
input,
select {
  width: 100%;
}

.field-select {
  width: 100%;
  height: 46px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  padding: 0 14px;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, #6b7c78 50%),
    linear-gradient(135deg, #6b7c78 50%, transparent 50%);
  background-position:
    calc(100% - 18px) calc(50% + 1px),
    calc(100% - 12px) calc(50% + 1px);
  background-size: 6px 6px, 6px 6px;
  background-repeat: no-repeat;
}

.field-select:focus {
  border-color: rgba(24, 160, 88, 0.45);
  box-shadow: 0 0 0 3px rgba(24, 160, 88, 0.12);
  outline: none;
}

.btn-compact {
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1;
}

.dimension-grid {
  display: grid;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--line);
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

</style>
