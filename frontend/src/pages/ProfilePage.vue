<template>
  <div class="page-wrap">
    <section class="page-hero">
      <div class="container hero-panel">
        <div class="hero-row">
          <div>
            <h1>学生档案</h1>
            <p>统一维护个人资料、求职意向、简历与就业分析。</p>
          </div>
          <div class="hero-actions">
            <span class="tag mono" :class="profile.verified ? 'ok' : 'pending'">
              {{ profile.verified ? '学校已核验' : '待学校核验' }}
            </span>
            <button class="btn" @click="saveAll">保存资料</button>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div class="summary-grid">
          <div class="card summary-card">
            <strong>{{ profileCompletion }}%</strong>
            <span class="mono">档案完整度</span>
          </div>
          <div class="card summary-card">
            <strong>{{ resumes.length }}</strong>
            <span class="mono">简历数量</span>
          </div>
          <div class="card summary-card">
            <strong>{{ verifications.length }}</strong>
            <span class="mono">核验请求</span>
          </div>
          <div class="card summary-card summary-card-switch">
            <div class="summary-switch-head">
              <span class="mono">接受实习</span>
              <strong>{{ intention.accept_internship ? '开启' : '关闭' }}</strong>
            </div>
            <label class="switch">
              <input
                type="checkbox"
                :checked="Boolean(intention.accept_internship)"
                :disabled="internshipSwitchSaving"
                @change="toggleInternshipAcceptance($event.target.checked)"
              />
              <span class="switch-slider"></span>
            </label>
            <span class="mono">{{ internshipSwitchSaving ? '同步中...' : '状态会同步给企业端' }}</span>
          </div>
        </div>

        <div class="module-tabs">
          <button class="module-btn" :class="{ active: activeTab === 'profile' }" @click="switchTab('profile')">基础信息</button>
          <button class="module-btn" :class="{ active: activeTab === 'intention' }" @click="switchTab('intention')">求职意向</button>
          <button class="module-btn" :class="{ active: activeTab === 'resume' }" @click="switchTab('resume')">简历中心</button>
          <button class="module-btn" :class="{ active: activeTab === 'insight' }" @click="switchInsightTab">分析与核验</button>
        </div>
      </div>
    </section>

    <section>
      <div class="container">
        <div v-if="activeTab === 'profile'" class="grid profile-stack">
          <div class="card section-card">
            <div class="section-head">
              <h3>个人信息</h3>
              <span class="mono section-tip">建议填写真实信息，便于企业联系</span>
            </div>
            <div class="field-grid profile-field-grid">
              <label class="field">
                <span class="field-label">姓名</span>
                <input v-model="profile.name" placeholder="请输入姓名" />
              </label>
              <label class="field">
                <span class="field-label">学号</span>
                <input v-model="profile.student_no" placeholder="请输入学号" />
              </label>
              <label class="field">
                <span class="field-label">学校</span>
                <input v-model="profile.school" placeholder="请输入学校" />
              </label>
              <label class="field">
                <span class="field-label">专业</span>
                <input v-model="profile.major" placeholder="请输入专业" />
              </label>
              <label class="field">
                <span class="field-label">年级</span>
                <input v-model="profile.grade" placeholder="如 2023 级" />
              </label>
              <label class="field">
                <span class="field-label">手机号</span>
                <input v-model="profile.phone" placeholder="请输入手机号" />
              </label>
              <label class="field field-full">
                <span class="field-label">邮箱</span>
                <input v-model="profile.email" placeholder="请输入邮箱" />
              </label>
            </div>
          </div>

          <div class="card section-card experience-card">
            <div class="section-head">
              <h3>个人经历</h3>
              <span class="mono section-tip">支持多行输入，信息展示更完整</span>
            </div>
            <div class="experience-grid profile-field-grid">
              <div class="list-editor field-full">
                <div class="list-head">
                  <div class="list-title-row">
                    <span class="field-label">技能能力</span>
                    <span class="mono list-count">{{ skillItems.length }} 项</span>
                  </div>
                  <div class="list-tools">
                    <span class="mono list-sub">支持逐条添加和批量粘贴</span>
                    <button type="button" class="list-clear" :disabled="skillItems.length === 0" @click="clearSkillItems">清空</button>
                  </div>
                </div>
                <div class="list-chip-wrap">
                  <span v-for="(item, idx) in skillItems" :key="`skill-${idx}-${item}`" class="list-chip">
                    {{ item }}
                    <button type="button" class="chip-x" @click="removeSkillItem(idx)">×</button>
                  </span>
                  <span v-if="skillItems.length === 0" class="mono list-empty">暂无技能标签，可从下方添加</span>
                </div>
                <div class="list-add-row">
                  <input
                    v-model="skillDraft"
                    placeholder="例如：Vue3 / Spring Boot / 数据分析"
                    @keydown.enter.prevent="addSkillItem"
                  />
                  <button type="button" class="btn btn-outline btn-mini" @click="addSkillItem">+ 添加</button>
                </div>
                <label class="field batch-area">
                  <span class="field-label">批量粘贴（每行一个）</span>
                  <textarea v-model="skillsInput" rows="4" placeholder="例如&#10;Vue3&#10;FastAPI&#10;MySQL"></textarea>
                </label>
              </div>

              <div class="list-editor field-full">
                <div class="list-head">
                  <div class="list-title-row">
                    <span class="field-label">获奖情况</span>
                    <span class="mono list-count">{{ awardItems.length }} 项</span>
                  </div>
                  <div class="list-tools">
                    <span class="mono list-sub">建议写完整奖项名称</span>
                    <button type="button" class="list-clear" :disabled="awardItems.length === 0" @click="clearAwardItems">清空</button>
                  </div>
                </div>
                <div class="list-chip-wrap">
                  <span v-for="(item, idx) in awardItems" :key="`award-${idx}-${item}`" class="list-chip">
                    {{ item }}
                    <button type="button" class="chip-x" @click="removeAwardItem(idx)">×</button>
                  </span>
                  <span v-if="awardItems.length === 0" class="mono list-empty">暂无获奖记录，可从下方添加</span>
                </div>
                <div class="list-add-row">
                  <input
                    v-model="awardDraft"
                    placeholder="例如：数学建模省一等奖"
                    @keydown.enter.prevent="addAwardItem"
                  />
                  <button type="button" class="btn btn-outline btn-mini" @click="addAwardItem">+ 添加</button>
                </div>
                <label class="field batch-area">
                  <span class="field-label">批量粘贴（每行一个）</span>
                  <textarea v-model="awardsInput" rows="4" placeholder="例如&#10;数学建模省一等奖&#10;校级优秀毕业生"></textarea>
                </label>
              </div>

              <div class="experience-group field-full">
                <div class="experience-group-head">
                  <h4>实习经历</h4>
                  <button type="button" class="btn btn-outline btn-mini" @click="addExperience('internship')">+ 新增实习</button>
                </div>
                <div class="experience-list">
                  <div class="experience-item" v-for="(item, idx) in internshipItems" :key="item.id">
                    <div class="experience-item-head">
                      <span class="mono">实习经历 #{{ idx + 1 }}</span>
                      <button type="button" class="btn btn-outline btn-mini" @click="removeExperience('internship', item.id)">删除</button>
                    </div>
                    <div class="experience-item-grid">
                      <label class="field">
                        <span class="field-label">岗位名称</span>
                        <input v-model="item.title" placeholder="如 后端开发实习生" />
                      </label>
                      <label class="field">
                        <span class="field-label">公司/组织</span>
                        <input v-model="item.organization" placeholder="如 XX 科技有限公司" />
                      </label>
                      <label class="field">
                        <span class="field-label">时间范围</span>
                        <input v-model="item.period" placeholder="如 2025.07 - 2025.10" />
                      </label>
                    </div>
                    <label class="field field-full">
                      <span class="field-label">经历描述</span>
                      <textarea v-model="item.description" rows="5" placeholder="描述负责内容、成果和量化结果"></textarea>
                    </label>
                  </div>
                </div>
              </div>

              <div class="experience-group field-full">
                <div class="experience-group-head">
                  <h4>项目经历</h4>
                  <button type="button" class="btn btn-outline btn-mini" @click="addExperience('project')">+ 新增项目</button>
                </div>
                <div class="experience-list">
                  <div class="experience-item" v-for="(item, idx) in projectItems" :key="item.id">
                    <div class="experience-item-head">
                      <span class="mono">项目经历 #{{ idx + 1 }}</span>
                      <button type="button" class="btn btn-outline btn-mini" @click="removeExperience('project', item.id)">删除</button>
                    </div>
                    <div class="experience-item-grid">
                      <label class="field">
                        <span class="field-label">项目名称</span>
                        <input v-model="item.title" placeholder="如 校园招聘平台" />
                      </label>
                      <label class="field">
                        <span class="field-label">项目角色</span>
                        <input v-model="item.organization" placeholder="如 全栈开发 / 后端负责人" />
                      </label>
                      <label class="field">
                        <span class="field-label">时间范围</span>
                        <input v-model="item.period" placeholder="如 2024.03 - 2024.08" />
                      </label>
                    </div>
                    <label class="field field-full">
                      <span class="field-label">项目描述</span>
                      <textarea v-model="item.description" rows="5" placeholder="描述技术栈、职责和项目成果"></textarea>
                    </label>
                  </div>
                </div>
              </div>

              <label class="field field-full bio-field">
                <span class="field-label">自我评价</span>
                <textarea v-model="profile.bio" rows="6" placeholder="突出你的核心优势、项目成果和求职方向"></textarea>
              </label>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'intention'" class="grid two-col">
          <div class="card section-card">
            <div class="section-head">
              <h3>求职意向</h3>
              <span class="mono section-tip">完善越完整，推荐越准确</span>
            </div>
            <div class="field-grid">
              <label class="field">
                <span class="field-label">期望岗位</span>
                <input v-model="intention.expected_job" placeholder="如 前端开发工程师" />
              </label>
              <label class="field">
                <span class="field-label">期望城市</span>
                <input v-model="intention.expected_city" placeholder="如 上海 / 深圳" />
              </label>
              <label class="field">
                <span class="field-label">期望薪资</span>
                <input v-model="intention.expected_salary" placeholder="如 15K-20K" />
              </label>
              <label class="field">
                <span class="field-label">期望行业</span>
                <input v-model="intention.expected_industry" placeholder="如 互联网 / AI" />
              </label>
              <label class="field">
                <span class="field-label">到岗时间</span>
                <input v-model="intention.arrival_time" placeholder="如 2 周内" />
              </label>
            </div>
            <div class="switch-row">
              <div>
                <strong>接受实习机会</strong>
                <p class="mono">
                  {{ internshipSwitchSaving ? '正在同步到企业端...' : '开启后将同步匹配实习岗位，并反馈给企业端' }}
                </p>
              </div>
              <label class="switch">
                <input
                  type="checkbox"
                  :checked="Boolean(intention.accept_internship)"
                  :disabled="internshipSwitchSaving"
                  @change="toggleInternshipAcceptance($event.target.checked)"
                />
                <span class="switch-slider"></span>
              </label>
            </div>
          </div>

          <div class="card intention-tip">
            <h3>建议</h3>
            <p>补齐期望岗位与城市，可提升岗位推荐准确度。</p>
            <p>保持薪资预期区间合理，有助于提升面试邀请率。</p>
            <p>更新到岗时间，便于企业做流程安排。</p>
          </div>
        </div>

        <div v-else-if="activeTab === 'resume'" class="grid one-col">
          <div class="card">
            <div class="section-head">
              <h3>简历列表</h3>
              <div class="actions">
                <button class="btn btn-outline" @click="openResumeDialog">新增在线简历</button>
                <label class="upload-label">
                  上传 PDF 简历
                  <input type="file" accept=".pdf,.doc,.docx" @change="uploadResumePdf" />
                </label>
              </div>
            </div>
            <p class="mono">在线简历支持新增、编辑和删除；已用于投递的简历会保留，避免影响既有投递记录。</p>

            <div v-if="resumes.length === 0" class="empty-state card">暂无简历</div>
            <div v-else class="resume-list">
	              <div class="resume-item" v-for="resume in resumes" :key="resume.id">
	                <div class="resume-main">
	                  <strong>版本 {{ resume.version_no }}</strong>
	                  <p class="mono">{{ resumeModeText(resume) }}</p>
	                </div>
	                <div class="resume-actions">
	                  <span class="mono">{{ formatTime(resume.create_time) }}</span>
	                  <button class="btn btn-outline" @click="previewResume = previewResume === resume.id ? null : resume.id">
	                    {{ previewResume === resume.id ? '收起' : '预览' }}
	                  </button>
                    <button
                      v-if="resume.resume_type === 'online'"
                      class="btn btn-outline"
                      @click="editResume(resume)"
                    >
                      编辑
                    </button>
	                  <a v-if="resume.file_url" :href="resume.file_url" target="_blank" class="btn btn-outline">下载</a>
                    <button
                      class="btn btn-outline danger-btn"
                      :disabled="deletingResumeId === resume.id"
                      @click="removeResumeItem(resume)"
                    >
                      {{ deletingResumeId === resume.id ? '删除中...' : '删除' }}
                    </button>
	                </div>

	                <div v-if="previewResume === resume.id" class="resume-preview detailed-preview">
	                  <template v-if="hasStructuredResumeContent(resume)">
	                    <div class="preview-grid">
	                      <div class="preview-card" v-if="resume.content_json.summary">
	                        <span class="mono preview-label">个人摘要</span>
	                        <p>{{ resume.content_json.summary }}</p>
	                      </div>
	                      <div class="preview-card" v-if="resume.content_json.job_target || intention.expected_job">
	                        <span class="mono preview-label">求职方向</span>
	                        <p>{{ resume.content_json.job_target || intention.expected_job }}</p>
	                      </div>
	                      <div class="preview-card" v-if="resume.content_json.education">
	                        <span class="mono preview-label">教育背景</span>
	                        <p>{{ resume.content_json.education }}</p>
	                      </div>
	                      <div class="preview-card" v-if="resume.content_json.experience">
	                        <span class="mono preview-label">实习/工作经历</span>
	                        <p>{{ resume.content_json.experience }}</p>
	                      </div>
	                      <div class="preview-card" v-if="resume.content_json.achievements">
	                        <span class="mono preview-label">成果亮点</span>
	                        <p>{{ resume.content_json.achievements }}</p>
	                      </div>
	                    </div>

	                    <div class="preview-section" v-if="resumeSkillTags(resume).length">
	                      <strong>技能标签</strong>
	                      <div class="tags">
	                        <span class="tag" v-for="s in resumeSkillTags(resume)" :key="s">{{ s }}</span>
	                      </div>
	                    </div>

	                    <div class="preview-section" v-if="resumeProjectItems(resume).length">
	                      <strong>项目经历</strong>
	                      <ul class="preview-list">
	                        <li v-for="item in resumeProjectItems(resume)" :key="item">{{ item }}</li>
	                      </ul>
	                    </div>
	                  </template>

	                  <template v-else-if="resume.file_url">
	                    <div class="preview-file-head">
	                      <strong>附件简历预览</strong>
	                      <span class="mono">格式：{{ resumeFileExt(resume).toUpperCase() || '未知' }}</span>
	                    </div>
	                    <iframe
	                      v-if="canEmbedResumeFile(resume)"
	                      :src="resume.file_url"
	                      class="resume-file-frame"
	                      title="附件简历预览"
	                    ></iframe>
	                    <div v-else class="mono">
	                      当前文件暂不支持页面内预览，请点击“下载”查看原文件。
	                    </div>
	                  </template>

	                  <template v-else>
	                    <div class="mono">该简历暂无可预览内容。</div>
	                  </template>
	                </div>
	              </div>
	            </div>
	          </div>

          <div class="card">
            <div class="section-head">
              <h3>简历智能解析</h3>
              <label class="upload-label">
                选择简历文件解析
                <input type="file" accept=".pdf,.docx,.doc,.txt" @change="handleParseResume" />
              </label>
            </div>
            <p class="mono">上传 PDF/DOCX，AI 自动提取并可一键回填到个人信息，同时新增一份在线简历。</p>
            <div v-if="parseLoading" class="mono">解析中...</div>
            <div v-if="parseResult" class="resume-preview">
              <p><strong>姓名：</strong>{{ parseResult.name || '--' }}</p>
              <p><strong>学校：</strong>{{ parseResult.school || '--' }}</p>
              <p><strong>专业：</strong>{{ parseResult.major || '--' }}</p>
              <p><strong>手机：</strong>{{ parseResult.phone || '--' }}</p>
              <p v-if="parseResult.skills?.length"><strong>技能：</strong>{{ parseResult.skills.join(', ') }}</p>
              <div v-if="parsedExperienceLines.length" class="preview-section">
                <strong>经历提取：</strong>
                <ul class="preview-list">
                  <li v-for="line in parsedExperienceLines" :key="line">{{ line }}</li>
                </ul>
              </div>
              <button class="btn" :disabled="parseApplying" @click="applyParseResult">
                {{ parseApplying ? '应用中...' : '应用并保存（含新简历）' }}
              </button>
            </div>
          </div>
        </div>

        <div v-else class="grid two-col">
          <div class="card">
            <div class="section-head">
              <h3>就业分析</h3>
              <button class="btn btn-outline" @click="loadAnalytics" :disabled="analyticsLoading">
                {{ analyticsLoading ? '加载中...' : '查看分析' }}
              </button>
            </div>

            <div v-if="!analytics" class="empty-state card">点击“查看分析”加载数据</div>
            <div v-else>
              <h4>技能竞争力</h4>
              <div v-for="sk in analytics.skill_competitiveness" :key="sk.skill" class="skill-bar-row">
                <div class="skill-meta">
                  <span>{{ sk.skill }}</span><span class="mono">稀缺度 {{ sk.percentile }}%</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill" :style="{ width: sk.percentile + '%' }"></div>
                </div>
              </div>

              <h4>薪资基准</h4>
              <div v-if="analytics.salary_benchmark.sample_count" class="mono">
                范围 {{ analytics.salary_benchmark.min }}~{{ analytics.salary_benchmark.max }}
                | 均值 {{ analytics.salary_benchmark.avg_min }}~{{ analytics.salary_benchmark.avg_max }}
                ({{ analytics.salary_benchmark.sample_count }} 个样本)
              </div>
              <div v-else class="mono muted">暂无匹配薪资数据</div>

              <h4>投递统计</h4>
              <div v-if="analytics.application_stats" class="mono">
                投递 {{ analytics.application_stats.total_applied }}
                | 面试率 {{ analytics.application_stats.interview_rate }}%
                | Offer率 {{ analytics.application_stats.offer_rate }}%
              </div>
            </div>
          </div>

          <div class="card">
            <h3>企业核验请求</h3>
            <div v-if="!verifications.length" class="empty-state card">暂无核验请求</div>
            <div v-else class="verification-list">
              <div
                v-for="v in verifications"
                :key="v.id"
                class="verification-item"
                :class="{
                  clickable: canRespondVerification(v),
                  expanded: expandedVerificationId === v.id
                }"
                @click="toggleVerificationCard(v)"
              >
                <div class="verification-head">
                  <div class="verification-company">
                    <span class="company-avatar">{{ companyAvatarText(v) }}</span>
                    <div class="company-meta">
                      <strong>{{ companyDisplayName(v) }}</strong>
                      <span class="mono">企业ID: {{ v.company_id || '--' }}</span>
                    </div>
                  </div>
                  <span class="status-pill" :class="statusClass(v.status)">{{ statusText(v.status) }}</span>
                </div>
                <div class="verification-fields">
                  <span class="mono">企业正在核验：</span>
                  <span>{{ formatVerificationFields(v.fields) || '未说明' }}</span>
                </div>
                <div v-if="canRespondVerification(v)" class="verification-tip mono">点击卡片可选择同意或拒绝</div>
                <transition name="verification-actions">
                  <div
                    v-if="expandedVerificationId === v.id && canRespondVerification(v)"
                    class="verification-actions"
                    @click.stop
                  >
                    <button
                      class="btn"
                      :disabled="verificationActionLoadingId === v.id"
                      @click="respondVerification(v, 'accept')"
                    >
                      {{ verificationActionLoadingId === v.id ? '提交中...' : '同意并提交校方核验' }}
                    </button>
                    <button
                      class="btn btn-outline"
                      :disabled="verificationActionLoadingId === v.id"
                      @click="respondVerification(v, 'reject')"
                    >
                      拒绝本次核验
                    </button>
                  </div>
                </transition>
                <div v-if="v.result" class="verification-result">核验结果：{{ v.result }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="resumeDialogVisible" class="resume-dialog-mask" @click.self="closeResumeDialog">
      <div class="card resume-dialog">
        <div class="section-head">
          <h3>{{ editingResumeId ? '编辑在线简历' : '新增在线简历' }}</h3>
          <button class="btn btn-outline" @click="closeResumeDialog">关闭</button>
        </div>
	        <div class="field-grid">
	          <div class="resume-identity field-full">
	            <div class="identity-item">
	              <span class="mono">姓名</span>
	              <strong>{{ profile.name || '--' }}</strong>
	            </div>
	            <div class="identity-item">
	              <span class="mono">学校/专业</span>
	              <strong>{{ `${profile.school || '--'} / ${profile.major || '--'}` }}</strong>
	            </div>
	            <div class="identity-item">
	              <span class="mono">联系方式</span>
	              <strong>{{ profile.phone || profile.email || '--' }}</strong>
	            </div>
	          </div>
	          <label class="field field-full">
	            <span class="field-label">个人摘要</span>
	            <textarea v-model="resumeDraft.summary" rows="3" placeholder="一句话概括你的求职优势"></textarea>
	          </label>
	          <label class="field">
	            <span class="field-label">求职方向</span>
	            <input v-model="resumeDraft.jobTarget" placeholder="如：前端开发 / AI算法 / 产品经理" />
	          </label>
	          <label class="field">
	            <span class="field-label">成果亮点</span>
	            <input v-model="resumeDraft.achievements" placeholder="如：主导项目上线，性能提升 40%" />
	          </label>
	          <label class="field field-full">
	            <span class="field-label">教育背景</span>
	            <textarea v-model="resumeDraft.education" rows="3" placeholder="学校、专业、核心课程、成绩亮点"></textarea>
          </label>
          <label class="field field-full">
            <span class="field-label">实习/工作经历</span>
            <textarea v-model="resumeDraft.experience" rows="4" placeholder="描述岗位职责、成果和量化指标"></textarea>
          </label>
          <label class="field field-full">
            <span class="field-label">项目经历（每行一条）</span>
            <textarea v-model="resumeDraft.projectsText" rows="4" placeholder="如：校园招聘系统（负责后端接口和推荐算法）"></textarea>
          </label>
          <label class="field field-full">
            <span class="field-label">技能标签（逗号分隔）</span>
            <input v-model="resumeDraft.skillsText" placeholder="如：Vue3, FastAPI, MySQL, Redis" />
          </label>
        </div>
        <div class="actions">
          <button class="btn" :disabled="resumeSaving" @click="saveOnlineResumeFromDialog">
            {{ resumeSaving ? '保存中...' : editingResumeId ? '保存修改' : '创建在线简历' }}
          </button>
          <button class="btn btn-outline" :disabled="resumeSaving" @click="closeResumeDialog">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createResume,
  deleteResume,
  fetchResumes,
  fetchStudentIntention,
  fetchStudentProfile,
  updateResume,
  updateStudentIntention,
  updateStudentProfile,
  uploadFile,
  parseResume,
  fetchStudentAnalytics,
  fetchStudentVerifications,
  respondStudentVerification,
  fetchCompanies,
  fetchCompany,
} from "../services/api";
import { useAuth } from "../store/auth";
import toast from '../utils/toast';

const auth = useAuth();
const route = useRoute();
const router = useRouter();
const userId = auth.user.value?.id || 0;

const profile = ref({
  user_id: userId,
  name: auth.user.value?.name || "",
  student_no: "",
  school: "",
  major: "",
  grade: "",
  phone: "",
  email: auth.user.value?.email || "",
  skills: [],
  awards: [],
  internships: [],
  projects: [],
  bio: "",
  verified: false,
});

const intention = ref({
  student_id: userId,
  expected_job: "",
  expected_city: "",
  expected_salary: "",
  expected_industry: "",
  arrival_time: "",
  accept_internship: true,
});

const resumes = ref([]);
const skillsInput = ref('');
const awardsInput = ref('');
const skillDraft = ref('');
const awardDraft = ref('');
const internshipItems = ref([createExperienceItem('internship')]);
const projectItems = ref([createExperienceItem('project')]);
const previewResume = ref(null);
const resumeDialogVisible = ref(false);
const editingResumeId = ref(0);
const resumeSaving = ref(false);
const deletingResumeId = ref(0);
const resumeDraft = ref({
  summary: "",
  jobTarget: "",
  achievements: "",
  education: "",
  experience: "",
  projectsText: "",
  skillsText: ""
});
const parseLoading = ref(false);
const parseResult = ref(null);
const parseApplying = ref(false);
const internshipSwitchSaving = ref(false);
const analytics = ref(null);
const analyticsLoading = ref(false);
const verifications = ref([]);
const verificationCompanyNameMap = ref({});
const expandedVerificationId = ref(null);
const verificationActionLoadingId = ref(0);
const activeTab = ref('profile');

function createExperienceItem(type) {
  return {
    id: `${type}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    title: '',
    organization: '',
    period: '',
    description: '',
  };
}

function parseExperienceItem(raw, type) {
  const text = String(raw || '').trim();
  if (!text) return createExperienceItem(type);
  const parts = text.split('||');
  if (parts.length === 1) {
    return { ...createExperienceItem(type), title: parts[0] };
  }
  return {
    ...createExperienceItem(type),
    title: parts[0] || '',
    organization: parts[1] || '',
    period: parts[2] || '',
    description: parts[3] || '',
  };
}

function serializeExperienceItem(item) {
  const title = String(item.title || '').trim();
  const organization = String(item.organization || '').trim();
  const period = String(item.period || '').trim();
  const description = String(item.description || '').trim();
  if (!title && !organization && !period && !description) return '';
  return [title, organization, period, description].join('||');
}

function ensureExperienceList(list, type) {
  return list.length ? list : [createExperienceItem(type)];
}

function addExperience(type) {
  if (type === 'internship') {
    internshipItems.value.push(createExperienceItem(type));
    return;
  }
  projectItems.value.push(createExperienceItem(type));
}

function removeExperience(type, id) {
  if (type === 'internship') {
    internshipItems.value = internshipItems.value.filter((item) => item.id !== id);
    internshipItems.value = ensureExperienceList(internshipItems.value, 'internship');
    return;
  }
  projectItems.value = projectItems.value.filter((item) => item.id !== id);
  projectItems.value = ensureExperienceList(projectItems.value, 'project');
}

function dedupeList(list) {
  const seen = new Set();
  return list.filter((item) => {
    const key = String(item || '').toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function parseListInput(value, options = { unique: true }) {
  const { unique = true } = options;
  const rawList = Array.isArray(value) ? value : String(value || '').split(/[\n,，]/);
  const list = rawList
    .map((item) => String(item || '').trim())
    .filter(Boolean);
  return unique ? dedupeList(list) : list;
}

function formatListInput(list) {
  return parseListInput(list).join('\n');
}

function normalizeParseExperienceLines(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean);
  }
  return String(value || '')
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function hasExperienceContent(list) {
  return (list || []).some((item) =>
    [item?.title, item?.organization, item?.period, item?.description]
      .some((value) => String(value || '').trim().length > 0)
  );
}

function createExperienceItemsFromParse(lines, type) {
  return lines.map((line) => {
    const briefTitle = line.split(/[，,。；;：:]/)[0]?.trim() || '';
    return {
      ...createExperienceItem(type),
      title: briefTitle.slice(0, 40),
      description: line
    };
  });
}

const skillItems = computed(() => parseListInput(skillsInput.value));
const awardItems = computed(() => parseListInput(awardsInput.value));
const parsedExperienceLines = computed(() => normalizeParseExperienceLines(parseResult.value?.experience));

function addListItem(targetRef, draftRef) {
  const value = String(draftRef.value || '').trim();
  if (!value) return;
  const next = parseListInput(targetRef.value, { unique: false });
  const duplicated = next.some((item) => item.toLowerCase() === value.toLowerCase());
  if (duplicated) {
    toast.info('该条目已存在，无需重复添加');
    draftRef.value = '';
    return;
  }
  next.push(value);
  targetRef.value = formatListInput(next);
  draftRef.value = '';
}

function removeListItem(targetRef, index) {
  const next = parseListInput(targetRef.value);
  next.splice(index, 1);
  targetRef.value = formatListInput(next);
}

function addSkillItem() {
  addListItem(skillsInput, skillDraft);
}

function removeSkillItem(index) {
  removeListItem(skillsInput, index);
}

function addAwardItem() {
  addListItem(awardsInput, awardDraft);
}

function removeAwardItem(index) {
  removeListItem(awardsInput, index);
}

function clearSkillItems() {
  skillsInput.value = '';
  skillDraft.value = '';
}

function clearAwardItems() {
  awardsInput.value = '';
  awardDraft.value = '';
}

const profileCompletion = computed(() => {
  const fields = [
    profile.value.name,
    profile.value.student_no,
    profile.value.school,
    profile.value.major,
    profile.value.grade,
    profile.value.phone,
    profile.value.email,
    profile.value.bio,
    intention.value.expected_job,
    intention.value.expected_city,
    intention.value.expected_salary,
  ];
  const filled = fields.filter((v) => String(v || '').trim().length > 0).length;
  return Math.round((filled / fields.length) * 100);
});

async function loadData() {
  if (!userId) return;
  try {
    profile.value = await fetchStudentProfile(userId);
    skillsInput.value = formatListInput(profile.value.skills);
    awardsInput.value = formatListInput(profile.value.awards);
    internshipItems.value = ensureExperienceList(
      (profile.value.internships || []).map((row) => parseExperienceItem(row, 'internship')),
      'internship'
    );
    projectItems.value = ensureExperienceList(
      (profile.value.projects || []).map((row) => parseExperienceItem(row, 'project')),
      'project'
    );
  } catch (err) {
    // keep defaults
  }
  try {
    intention.value = await fetchStudentIntention(userId);
  } catch (err) {
    // keep defaults
  }
  try {
    resumes.value = await fetchResumes(userId);
  } catch (err) {
    resumes.value = [];
  }
}

async function saveAll() {
  if (!userId) return;
  profile.value.skills = parseListInput(skillsInput.value);
  profile.value.awards = parseListInput(awardsInput.value);
  profile.value.internships = internshipItems.value.map(serializeExperienceItem).filter(Boolean);
  profile.value.projects = projectItems.value.map(serializeExperienceItem).filter(Boolean);
  try {
    await updateStudentProfile(userId, profile.value);
    await updateStudentIntention(userId, intention.value);
    toast.success('资料已保存');
  } catch (err) {
    toast.error('保存失败，请重试');
  }
}

async function toggleInternshipAcceptance(nextValue) {
  if (!userId) return;
  const previous = Boolean(intention.value.accept_internship);
  const target = Boolean(nextValue);
  if (previous === target) return;

  intention.value.accept_internship = target;
  internshipSwitchSaving.value = true;
  try {
    await updateStudentIntention(userId, intention.value);
    toast.success(target ? '已开启接受实习，企业端可见' : '已关闭接受实习，企业端可见');
  } catch (err) {
    intention.value.accept_internship = previous;
    toast.error('更新失败，请稍后重试');
  } finally {
    internshipSwitchSaving.value = false;
  }
}

function openResumeDialog() {
  editingResumeId.value = 0;
  const defaultProjects = projectItems.value
    .map((item) => String(item.title || item.description || '').trim())
    .filter(Boolean)
    .join('\n');
  resumeDraft.value = {
    summary: profile.value.bio || '',
    jobTarget: intention.value.expected_job || '',
    achievements: '',
    education: `${profile.value.school || ''} ${profile.value.major || ''}`.trim(),
    experience: internshipItems.value
      .map((item) => String(item.description || '').trim())
      .filter(Boolean)
      .join('\n'),
    projectsText: defaultProjects,
    skillsText: parseListInput(skillsInput.value).join(', ')
  };
  resumeDialogVisible.value = true;
}

function closeResumeDialog() {
  resumeDialogVisible.value = false;
  editingResumeId.value = 0;
}

function editResume(resume) {
  const content = resume?.content_json || {};
  editingResumeId.value = Number(resume?.id || 0);
  resumeDraft.value = {
    summary: String(content.summary || '').trim(),
    jobTarget: String(content.job_target || '').trim(),
    achievements: String(content.achievements || '').trim(),
    education: String(content.education || '').trim(),
    experience: String(content.experience || '').trim(),
    projectsText: resumeProjectItems(resume).join('\n'),
    skillsText: resumeSkillTags(resume).join(', ')
  };
  resumeDialogVisible.value = true;
}

async function saveOnlineResumeFromDialog() {
  if (!userId) return;
  const projects = parseListInput(resumeDraft.value.projectsText);
  const skills = parseListInput(resumeDraft.value.skillsText);
  const hasTextContent = [
    resumeDraft.value.summary,
    resumeDraft.value.jobTarget,
    resumeDraft.value.achievements,
    resumeDraft.value.education,
    resumeDraft.value.experience
  ].some((value) => String(value || '').trim().length > 0);
  if (!skills.length && !projects.length && !hasTextContent) {
    toast.warn('请至少填写一项简历内容');
    return;
  }
  const payload = {
    student_id: userId,
    resume_type: "online",
    content_json: {
      summary: resumeDraft.value.summary.trim(),
      job_target: resumeDraft.value.jobTarget.trim(),
      achievements: resumeDraft.value.achievements.trim(),
      education: resumeDraft.value.education.trim(),
      experience: resumeDraft.value.experience.trim(),
      skills,
      projects
    },
    file_url: "",
    version_no: 1,
  };
  resumeSaving.value = true;
  try {
    if (editingResumeId.value) {
      await updateResume(userId, editingResumeId.value, payload);
      toast.success('简历已更新');
    } else {
      await createResume(userId, payload);
      toast.success('简历已创建');
    }
    closeResumeDialog();
    await loadData();
  } catch (err) {
    toast.error(editingResumeId.value ? '更新简历失败' : '创建简历失败');
  } finally {
    resumeSaving.value = false;
  }
}

function resumeModeText(resume) {
  if (resume?.file_url) return `附件简历 (${resumeFileExt(resume).toUpperCase() || 'FILE'})`;
  return '在线简历';
}

function resumeFileExt(resume) {
  const fileUrl = String(resume?.file_url || '');
  if (!fileUrl) return '';
  const clean = fileUrl.split('?')[0];
  const parts = clean.split('.');
  if (parts.length < 2) return '';
  return String(parts[parts.length - 1] || '').toLowerCase();
}

function canEmbedResumeFile(resume) {
  return resumeFileExt(resume) === 'pdf';
}

function hasStructuredResumeContent(resume) {
  const content = resume?.content_json;
  if (!content || typeof content !== 'object') return false;
  const keys = ['summary', 'job_target', 'achievements', 'education', 'experience'];
  const hasText = keys.some((key) => String(content[key] || '').trim().length > 0);
  return hasText || resumeSkillTags(resume).length > 0 || resumeProjectItems(resume).length > 0;
}

function resumeSkillTags(resume) {
  const skills = resume?.content_json?.skills;
  if (Array.isArray(skills)) return skills.filter(Boolean);
  return parseListInput(skills || '');
}

function resumeProjectItems(resume) {
  const projects = resume?.content_json?.projects;
  if (Array.isArray(projects)) return projects.filter(Boolean);
  return parseListInput(projects || '');
}

async function uploadResumePdf(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  try {
    const result = await uploadFile(file);
    await createResume(userId, {
      student_id: userId,
      resume_type: 'file',
      content_json: null,
      file_url: result.file_url,
      version_no: 1,
    });
    toast.success('简历上传成功');
    await loadData();
  } catch (e) {
    toast.error('上传失败');
  }
}

async function removeResumeItem(resume) {
  if (!userId || !resume?.id) return;
  const label = resume.resume_type === 'online' ? '这份在线简历' : '这份附件简历';
  if (!window.confirm(`确定要删除${label}吗？`)) return;

  deletingResumeId.value = Number(resume.id);
  try {
    await deleteResume(userId, resume.id);
    if (previewResume.value === resume.id) {
      previewResume.value = null;
    }
    toast.success('简历已删除');
    await loadData();
  } catch (err) {
    const reason = String(err?.message || '');
    if (reason.includes('Resume is already used in applications')) {
      toast.warn('该简历已用于投递，暂不支持删除');
    } else {
      toast.error('删除简历失败');
    }
  } finally {
    deletingResumeId.value = 0;
  }
}

async function handleParseResume(event) {
  const file = event?.target?.files?.[0];
  if (!file) return;
  parseLoading.value = true;
  parseResult.value = null;
  try {
    parseResult.value = await parseResume(file);
    toast.success('解析完成');
  } catch (e) {
    const reason = String(e?.message || '').trim();
    toast.error(reason ? `解析失败：${reason}` : '解析失败');
  }
  parseLoading.value = false;
}

async function applyParseResult() {
  if (!parseResult.value || !userId) return;
  const r = parseResult.value;

  if (r.name) profile.value.name = String(r.name).trim();
  if (r.school) profile.value.school = String(r.school).trim();
  if (r.major) profile.value.major = String(r.major).trim();
  if (r.phone) profile.value.phone = String(r.phone).trim();
  if (r.email) profile.value.email = String(r.email).trim();

  const parsedSkills = parseListInput(r.skills || []);
  if (parsedSkills.length) {
    const mergedSkills = dedupeList([...parseListInput(skillsInput.value), ...parsedSkills]);
    skillsInput.value = formatListInput(mergedSkills);
    profile.value.skills = mergedSkills;
  }

  const parsedExperiences = normalizeParseExperienceLines(r.experience);
  if (parsedExperiences.length) {
    const parsedItems = createExperienceItemsFromParse(parsedExperiences, 'internship');
    if (!hasExperienceContent(internshipItems.value)) {
      internshipItems.value = ensureExperienceList(parsedItems, 'internship');
    } else {
      const existing = new Set(
        internshipItems.value
          .map((item) => String(item.description || '').trim().toLowerCase())
          .filter(Boolean)
      );
      const appendItems = parsedItems.filter(
        (item) => !existing.has(String(item.description || '').trim().toLowerCase())
      );
      internshipItems.value = ensureExperienceList(
        [...internshipItems.value, ...appendItems],
        'internship'
      );
    }
  }

  profile.value.internships = internshipItems.value.map(serializeExperienceItem).filter(Boolean);
  profile.value.projects = projectItems.value.map(serializeExperienceItem).filter(Boolean);
  profile.value.skills = parseListInput(skillsInput.value);
  profile.value.awards = parseListInput(awardsInput.value);
  const projects = projectItems.value
    .map((item) => String(item.title || item.description || '').trim())
    .filter(Boolean);
  const experienceText = internshipItems.value
    .map((item) => String(item.description || item.title || '').trim())
    .filter(Boolean)
    .join('\n');
  const parsedRawSummary = String(r.raw_text || '')
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(' ');
  const onlineResumePayload = {
    summary: String(profile.value.bio || parsedRawSummary || '').trim(),
    job_target: String(intention.value.expected_job || '').trim(),
    achievements: '',
    education: [profile.value.school, profile.value.major, profile.value.grade]
      .map((part) => String(part || '').trim())
      .filter(Boolean)
      .join(' · '),
    experience: experienceText,
    skills: parseListInput(skillsInput.value),
    projects
  };

  parseApplying.value = true;
  let resumeCreateFailed = false;
  try {
    await updateStudentProfile(userId, profile.value);
    try {
      await createResume(userId, {
        student_id: userId,
        resume_type: 'online',
        content_json: onlineResumePayload,
        file_url: '',
        version_no: 1,
      });
    } catch (_) {
      resumeCreateFailed = true;
    }
    await loadData();
    switchTab('profile');
    toast.success(resumeCreateFailed ? '个人信息已更新' : '解析结果已保存，并新增一份在线简历');
    if (resumeCreateFailed) {
      toast.warn('在线简历创建失败，请稍后重试');
    }
  } catch (e) {
    toast.warn('已应用到页面，但保存失败，请点击“保存资料”重试');
  } finally {
    parseApplying.value = false;
  }
}

async function loadAnalytics() {
  analyticsLoading.value = true;
  try {
    analytics.value = await fetchStudentAnalytics(userId);
  } catch (e) {
    toast.error('加载分析失败');
  }
  analyticsLoading.value = false;
}

async function loadVerifications() {
  try {
    const list = await fetchStudentVerifications(userId);
    verifications.value = list || [];
    if (expandedVerificationId.value && !verifications.value.some((item) => item.id === expandedVerificationId.value)) {
      expandedVerificationId.value = null;
    }
    await loadVerificationCompanyNames(verifications.value);
  } catch (e) {
    verifications.value = [];
    verificationCompanyNameMap.value = {};
    expandedVerificationId.value = null;
  }
}

function switchInsightTab() {
  switchTab('insight');
  if (!analytics.value) loadAnalytics();
}

function switchTab(tab, options = { syncRoute: true }) {
  const validTabs = ['profile', 'intention', 'resume', 'insight'];
  if (!validTabs.includes(tab)) return;
  activeTab.value = tab;
  if (options.syncRoute && route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } });
  }
}

function statusClass(status) {
  if (status === 'pending' || status === 'pending_student' || status === 'pending_admin') return 'pending';
  if (status === 'approved') return 'ok';
  if (status === 'rejected' || status === 'student_rejected') return 'bad';
  return 'pending';
}

function statusText(status) {
  if (status === 'pending' || status === 'pending_student') return '待你确认';
  if (status === 'pending_admin') return '待校方审核';
  if (status === 'student_rejected') return '你已拒绝';
  if (status === 'approved') return '已通过';
  if (status === 'rejected') return '已驳回';
  return '待处理';
}

function canRespondVerification(item) {
  return ['pending', 'pending_student'].includes(String(item?.status || ''));
}

function toggleVerificationCard(item) {
  if (!canRespondVerification(item)) return;
  expandedVerificationId.value = expandedVerificationId.value === item.id ? null : item.id;
}

async function respondVerification(item, action) {
  if (!item?.id || !canRespondVerification(item)) return;
  verificationActionLoadingId.value = item.id;
  try {
    await respondStudentVerification(userId, item.id, { action });
    toast.success(action === 'accept' ? '已同意核验，等待校方审核' : '已拒绝本次核验');
    expandedVerificationId.value = null;
    await loadVerifications();
  } catch (e) {
    toast.error(action === 'accept' ? '同意失败，请稍后重试' : '拒绝失败，请稍后重试');
  } finally {
    verificationActionLoadingId.value = 0;
  }
}

async function loadVerificationCompanyNames(list) {
  const ids = [...new Set((list || []).map((item) => Number(item.company_id || 0)).filter(Boolean))];
  if (!ids.length) {
    verificationCompanyNameMap.value = {};
    return;
  }

  try {
    const companies = await fetchCompanies();
    const map = {};
    for (const company of companies || []) {
      const candidateId = Number(company.user_id || company.id || 0);
      if (candidateId && ids.includes(candidateId) && company.company_name) {
        map[candidateId] = company.company_name;
      }
    }
    const missing = ids.filter((id) => !map[id]);
    if (missing.length) {
      const fallback = await Promise.all(
        missing.map(async (id) => {
          try {
            const company = await fetchCompany(id);
            return [id, company?.company_name || ''];
          } catch (_) {
            return [id, ''];
          }
        })
      );
      for (const [id, name] of fallback) {
        if (name) map[id] = name;
      }
    }
    verificationCompanyNameMap.value = map;
  } catch (_) {
    const fallback = await Promise.all(
      ids.map(async (id) => {
        try {
          const company = await fetchCompany(id);
          return [id, company?.company_name || ''];
        } catch (_) {
          return [id, ''];
        }
      })
    );
    const map = {};
    for (const [id, name] of fallback) {
      if (name) map[id] = name;
    }
    verificationCompanyNameMap.value = map;
  }
}

function companyDisplayName(item) {
  const rawName = String(item?.company_name || '').trim();
  if (rawName) return rawName;
  const id = Number(item?.company_id || 0);
  if (id && verificationCompanyNameMap.value[id]) return verificationCompanyNameMap.value[id];
  return id ? `企业 #${id}` : '企业';
}

function companyAvatarText(item) {
  const name = companyDisplayName(item);
  const display = String(name || '').trim();
  if (!display) return '企';
  const first = display.replace(/^企业\s*#?\d+\s*/g, '').trim().charAt(0);
  return first || '企';
}

const verificationFieldLabels = {
  name: '姓名',
  student_no: '学号',
  school: '学校',
  major: '专业',
  grade: '年级',
  phone: '手机号',
  email: '邮箱',
  education: '学历',
  skills: '技能标签',
  awards: '获奖经历',
  internships: '实习经历',
  projects: '项目经历'
};

function formatVerificationFields(fields) {
  const list = Array.isArray(fields) ? fields : [];
  if (!list.length) return '';
  return list.map((field) => verificationFieldLabels[field] || String(field || '')).filter(Boolean).join('、');
}

function formatTime(value) {
  if (!value) return "";
  return value.replace("T", " ").slice(0, 16);
}

onMounted(() => {
  const tab = typeof route.query.tab === 'string' ? route.query.tab : '';
  if (tab) {
    switchTab(tab, { syncRoute: false });
  }
  loadData();
  loadVerifications();
});

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab !== 'string' || !tab) return;
    if (tab === activeTab.value) return;
    switchTab(tab, { syncRoute: false });
  }
);
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero {
  padding: 28px 0 10px;
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag.ok {
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
}

.tag.pending {
  background: rgba(240, 160, 32, 0.15);
  color: #9a6710;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.summary-card {
  border: 1px solid #d8eee1;
  gap: 4px;
}

.summary-card strong {
  font-size: 28px;
  color: #0b7d45;
}

.summary-card-switch {
  align-items: flex-start;
  gap: 8px;
}

.summary-switch-head {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.summary-card-switch strong {
  font-size: 20px;
}

.module-tabs {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.module-btn {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
}

.module-btn.active {
  border-color: var(--accent);
  background: rgba(24, 160, 88, 0.12);
  color: var(--accent-dark);
  font-weight: 600;
}

.two-col {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.one-col {
  grid-template-columns: 1fr;
}

.profile-stack {
  grid-template-columns: 1fr;
}

.section-card {
  border: 1px solid #d8eee1;
}

.section-tip {
  color: #7d8d88;
}

.field-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.profile-field-grid {
  grid-template-columns: 1fr;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  color: #6a7f77;
  font-weight: 600;
}

.field-full {
  grid-column: 1 / -1;
}

.field textarea {
  min-height: 132px;
}

.experience-card {
  background: linear-gradient(180deg, #ffffff 0%, #f9fcfa 100%);
}

.experience-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.experience-field textarea {
  min-height: 170px;
}

.list-editor {
  border: 1px solid #dcefe4;
  border-radius: 14px;
  background: #ffffff;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.list-title-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.list-count {
  border: 1px solid #d8ebe1;
  background: #f3faf6;
  color: #396f55;
  border-radius: 999px;
  padding: 2px 8px;
}

.list-tools {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.list-sub {
  color: #7d8d88;
}

.list-clear {
  border: none;
  background: transparent;
  color: #3f8d64;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.list-clear:disabled {
  color: #a5b4ae;
  cursor: not-allowed;
}

.list-chip-wrap {
  min-height: 40px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-start;
}

.list-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ebf8f1;
  border: 1px solid #cfeadb;
  color: #1b6f4d;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 13px;
  line-height: 1.2;
}

.chip-x {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
}

.chip-x:hover {
  color: #0f8f59;
}

.list-empty {
  color: #93a29c;
}

.list-add-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.list-add-row input {
  flex: 1;
}

.list-add-row .btn {
  flex-shrink: 0;
}

.batch-area textarea {
  min-height: 96px;
}

.experience-group {
  border: 1px solid #dcefe4;
  border-radius: 14px;
  background: #ffffff;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.experience-group-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.experience-group-head h4 {
  margin: 0;
}

.experience-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.experience-item {
  border: 1px solid #dbece3;
  border-radius: 12px;
  background: #f9fcfa;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.experience-item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.experience-item-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.btn-mini {
  padding: 6px 12px;
  font-size: 12px;
}

.bio-field textarea {
  min-height: 240px;
}

.switch-row {
  margin-top: 4px;
  border: 1px solid #dcefe4;
  background: #f6fbf8;
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.switch-row p {
  margin: 4px 0 0;
}

.switch {
  position: relative;
  width: 46px;
  height: 26px;
  display: inline-block;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: #c8d8d2;
  transition: 0.2s ease;
  cursor: pointer;
}

.switch-slider::before {
  content: "";
  position: absolute;
  width: 20px;
  height: 20px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 6px rgba(16, 30, 24, 0.2);
  transition: 0.2s ease;
}

.switch input:checked + .switch-slider {
  background: #18a058;
}

.switch input:checked + .switch-slider::before {
  transform: translateX(20px);
}

.switch input:disabled + .switch-slider {
  opacity: 0.6;
  cursor: not-allowed;
}

.intention-tip {
  border: 1px solid #d8eee1;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.upload-label {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: var(--muted);
  cursor: pointer;
}

.upload-label input[type="file"] {
  display: none;
}

.resume-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-item {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-main p {
  margin: 6px 0 0;
}

.resume-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.danger-btn {
  border-color: #efb5b5;
  color: #a04444;
}

.danger-btn:hover:not(:disabled) {
  background: #fff5f5;
}

.resume-preview {
  border: 1px dashed var(--line);
  border-radius: 12px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #f9fcfa;
}

.resume-preview p {
  margin: 0;
  white-space: pre-wrap;
}

.detailed-preview {
  gap: 12px;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.preview-card {
  border: 1px solid #dceee4;
  border-radius: 10px;
  background: #fff;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preview-label {
  color: #7b8f87;
  font-size: 12px;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-list {
  margin: 0;
  padding-left: 18px;
  color: #2f4d41;
  line-height: 1.5;
}

.preview-file-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.resume-file-frame {
  width: 100%;
  min-height: 520px;
  border: 1px solid #dbece2;
  border-radius: 10px;
  background: #fff;
}

.resume-identity {
  border: 1px solid #dceee4;
  border-radius: 12px;
  background: #f7fbf9;
  padding: 10px 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}

.identity-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.identity-item strong {
  font-size: 14px;
  color: #264338;
}

.resume-dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 24, 20, 0.42);
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 14px;
}

.resume-dialog {
  width: min(760px, 100%);
  max-height: min(82vh, 860px);
  overflow: auto;
}

.skill-bar-row {
  margin-bottom: 10px;
}

.skill-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}

.bar-track {
  height: 7px;
  background: #e1ebe6;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: #18a058;
  border-radius: inherit;
}

.muted {
  color: #95a39e;
}

.verification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 10px;
}

.verification-item {
  border: 1px solid #d9ece2;
  border-radius: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fcfa 100%);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 8px 18px rgba(14, 96, 58, 0.06);
}

.verification-item.clickable {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.verification-item.clickable:hover {
  transform: translateY(-1px);
  border-color: #c5e4d6;
  box-shadow: 0 12px 22px rgba(14, 96, 58, 0.1);
}

.verification-item.expanded {
  border-color: #b7dec9;
}

.verification-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.verification-company {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.company-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(180deg, #3cab69 0%, #2e9156 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.company-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.company-meta strong {
  color: #1d3a2f;
  font-size: 15px;
  line-height: 1.3;
}

.verification-fields {
  border: 1px solid #deeee5;
  background: #f6fbf8;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.55;
  color: #35554a;
}

.verification-fields .mono {
  color: #6f8780;
}

.verification-tip {
  font-size: 12px;
  color: #7f938b;
}

.verification-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  overflow: hidden;
}

.verification-actions-enter-active,
.verification-actions-leave-active {
  transition: all 0.22s ease;
}

.verification-actions-enter-from,
.verification-actions-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}

.verification-actions-enter-to,
.verification-actions-leave-from {
  opacity: 1;
  transform: translateY(0);
  max-height: 120px;
}

.verification-result {
  font-size: 13px;
  line-height: 1.5;
  color: #2b4a3f;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-pill.ok {
  background: #e9f8ef;
  color: #0f8f59;
}

.status-pill.bad {
  background: #f3f6f4;
  color: #5e7569;
}

.status-pill.pending {
  background: #f8f3e8;
  color: #99711c;
}

@media (max-width: 760px) {
  .resume-file-frame {
    min-height: 420px;
  }

  .verification-head {
    align-items: stretch;
  }

  .status-pill {
    align-self: flex-start;
  }

  .company-meta strong {
    font-size: 14px;
  }

  .verification-actions .btn {
    width: 100%;
  }

  .list-tools {
    width: 100%;
    justify-content: space-between;
  }

  .list-add-row {
    flex-direction: column;
    align-items: stretch;
  }

  .list-add-row .btn {
    width: 100%;
  }
}
</style>
