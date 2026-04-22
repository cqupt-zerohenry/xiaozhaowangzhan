export default function KnowledgeBaseRedesign() {
  const libraries = [
    {
      name: "SRE 知识库",
      desc: "运维手册 / 故障排查 / 面试题",
      docs: 12,
      chunks: 246,
      active: true,
    },
    {
      name: "后端知识库",
      desc: "FastAPI / MySQL / Docker",
      docs: 8,
      chunks: 132,
      active: false,
    },
  ];

  const docs = [
    {
      title: "devops_sre_interview_playbook.md",
      time: "2 分钟前更新",
      chunks: 6,
      tags: ["面试", "SRE", "Markdown"],
      status: "已就绪",
    },
    {
      title: "k8s_troubleshooting_notes.pdf",
      time: "今天 14:32 上传",
      chunks: 18,
      tags: ["K8s", "排障", "PDF"],
      status: "向量化完成",
    },
    {
      title: "mysql_perf_checklist.docx",
      time: "昨天 19:08 上传",
      chunks: 9,
      tags: ["MySQL", "性能", "Docx"],
      status: "切块完成",
    },
  ];

  const chunks = [
    {
      id: "Chunk 01",
      label: "告警降噪策略",
      text: "告警治理应优先处理重复告警、无效告警和缺少上下文的告警。推荐从告警分级、聚合规则、抑制窗口和责任人映射四个维度进行治理。",
      tags: ["告警", "治理", "SRE"],
    },
    {
      id: "Chunk 02",
      label: "容量评估",
      text: "容量评估不应只看 CPU 和内存峰值，还应结合请求趋势、突发流量、磁盘增长速度以及扩容提前量进行综合判断。",
      tags: ["容量", "资源", "规划"],
    },
    {
      id: "Chunk 03",
      label: "变更回滚",
      text: "所有高风险变更都需要定义回滚条件、回滚负责人和回滚时限。上线前应验证回滚脚本可执行，避免故障时临时补救。",
      tags: ["变更", "回滚", "发布"],
    },
  ];

  return (
    <div className="min-h-screen bg-[#f4f7f2] text-slate-900">
      <div className="mx-auto max-w-[1500px] px-6 py-6 lg:px-8">
        <div className="mb-6 flex flex-col gap-4 rounded-[28px] border border-[#d9e6d7] bg-white/90 p-6 shadow-[0_12px_40px_rgba(36,64,45,0.08)] backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center rounded-full border border-[#dce9da] bg-[#f7fbf6] px-3 py-1 text-xs font-medium text-[#4c6b53]">
              知识库 · 文档 · 分块
            </div>
            <h1 className="text-3xl font-semibold tracking-tight">知识库管理</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
              统一管理知识库、文档接入、切块内容与检索状态，让 RAG 数据准备流程更清晰。
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button className="rounded-2xl border border-[#d9e6d7] bg-white px-4 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50">
              导入模板
            </button>
            <button className="rounded-2xl bg-[#1f9d55] px-4 py-2.5 text-sm font-medium text-white shadow-[0_8px_20px_rgba(31,157,85,0.28)] transition hover:translate-y-[-1px] hover:bg-[#188848]">
              + 新建知识库
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[300px_minmax(460px,1fr)_380px]">
          <aside className="space-y-6">
            <section className="rounded-[26px] border border-[#d9e6d7] bg-white p-5 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">我的知识库</h2>
                <span className="rounded-full bg-[#eff7ee] px-2.5 py-1 text-xs font-medium text-[#3d7a4f]">
                  8 个
                </span>
              </div>

              <div className="space-y-3">
                {libraries.map((item) => (
                  <div
                    key={item.name}
                    className={`rounded-2xl border p-4 transition ${
                      item.active
                        ? "border-[#97d5ac] bg-[#f3fbf5] shadow-[0_10px_24px_rgba(31,157,85,0.10)]"
                        : "border-[#e6ece4] bg-[#fbfcfb] hover:border-[#cfe0cb]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-base font-semibold">{item.name}</div>
                        <div className="mt-1 text-sm text-slate-500">{item.desc}</div>
                      </div>
                      {item.active && (
                        <span className="rounded-full bg-[#dff3e5] px-2 py-1 text-[11px] font-medium text-[#237644]">
                          当前
                        </span>
                      )}
                    </div>
                    <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
                      <span className="rounded-full bg-white px-2.5 py-1">{item.docs} 文档</span>
                      <span className="rounded-full bg-white px-2.5 py-1">{item.chunks} 分块</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[26px] border border-[#d9e6d7] bg-white p-5 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <h2 className="mb-4 text-lg font-semibold">快速模板</h2>
              <div className="grid grid-cols-2 gap-3">
                {[
                  "后端知识",
                  "前端知识",
                  "算法题库",
                  "面试笔记",
                ].map((item) => (
                  <button
                    key={item}
                    className="rounded-2xl border border-[#e4ebe2] bg-[#fafcfa] px-3 py-3 text-sm font-medium text-slate-700 transition hover:border-[#b8d4be] hover:bg-[#f4faf4]"
                  >
                    {item}
                  </button>
                ))}
              </div>
              <button className="mt-4 w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800">
                一键创建示例知识库
              </button>
            </section>
          </aside>

          <main className="space-y-6">
            <section className="rounded-[26px] border border-[#d9e6d7] bg-white p-6 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="text-sm text-slate-500">当前知识库</div>
                  <div className="mt-1 text-2xl font-semibold">SRE 知识库</div>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                    <span className="rounded-full bg-[#f4f7f3] px-2.5 py-1">12 篇文档</span>
                    <span className="rounded-full bg-[#f4f7f3] px-2.5 py-1">246 个分块</span>
                    <span className="rounded-full bg-[#eaf8ef] px-2.5 py-1 text-[#257245]">检索可用</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  {[
                    ["TopK", "8"],
                    ["召回模式", "混合检索"],
                    ["Embedding", "bge-m3"],
                  ].map(([k, v]) => (
                    <div key={k} className="rounded-2xl border border-[#e7eee5] bg-[#fbfcfb] px-4 py-3">
                      <div className="text-xs text-slate-500">{k}</div>
                      <div className="mt-1 text-sm font-semibold">{v}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-[26px] border border-[#d9e6d7] bg-white p-6 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">添加文档</h2>
                  <p className="mt-1 text-sm text-slate-500">支持粘贴内容或上传 txt / md / pdf / docx 文件。</p>
                </div>
                <label className="inline-flex items-center gap-2 rounded-full border border-[#d9e6d7] bg-[#f8fbf8] px-3 py-2 text-sm text-slate-600">
                  <input type="checkbox" defaultChecked className="h-4 w-4 rounded" />
                  自动重算向量
                </label>
              </div>

              <div className="grid gap-4">
                <input
                  className="h-12 rounded-2xl border border-[#dfe8dd] bg-[#fbfcfb] px-4 text-sm outline-none transition focus:border-[#8bcc9e] focus:ring-4 focus:ring-[#dff3e5]"
                  placeholder="输入文档标题"
                />
                <textarea
                  className="min-h-[150px] rounded-2xl border border-[#dfe8dd] bg-[#fbfcfb] px-4 py-3 text-sm outline-none transition focus:border-[#8bcc9e] focus:ring-4 focus:ring-[#dff3e5]"
                  placeholder="粘贴知识内容，例如技术文档、SRE 排障流程、面试题库、课程笔记等"
                />
                <div className="flex flex-wrap items-center gap-3">
                  <button className="rounded-2xl bg-[#1f9d55] px-5 py-3 text-sm font-medium text-white shadow-[0_10px_24px_rgba(31,157,85,0.24)] transition hover:bg-[#188848]">
                    添加文档
                  </button>
                  <button className="rounded-2xl border border-dashed border-[#bdd5bf] bg-[#f9fcf8] px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-[#f2f8f2]">
                    上传文件
                  </button>
                  <span className="text-sm text-slate-400">支持拖拽上传，单文件最大 20MB</span>
                </div>
              </div>
            </section>

            <section className="rounded-[26px] border border-[#d9e6d7] bg-white p-6 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">文档列表</h2>
                  <p className="mt-1 text-sm text-slate-500">最近上传与已完成切块的文档。</p>
                </div>
                <div className="flex items-center gap-2 rounded-2xl border border-[#e6ece4] bg-[#fbfcfb] px-3 py-2 text-sm text-slate-500">
                  <span>共 {docs.length} 篇</span>
                </div>
              </div>

              <div className="space-y-4">
                {docs.map((doc) => (
                  <div
                    key={doc.title}
                    className="rounded-2xl border border-[#e4ebe2] bg-[#fcfdfc] p-4 transition hover:border-[#bdd6c0] hover:shadow-[0_8px_22px_rgba(36,64,45,0.06)]"
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div>
                        <div className="text-base font-semibold">{doc.title}</div>
                        <div className="mt-1 text-sm text-slate-500">{doc.time} · {doc.chunks} 个切片</div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {doc.tags.map((tag) => (
                            <span key={tag} className="rounded-full bg-[#f1f5f0] px-2.5 py-1 text-xs text-slate-600">
                              {tag}
                            </span>
                          ))}
                          <span className="rounded-full bg-[#eaf8ef] px-2.5 py-1 text-xs text-[#257245]">{doc.status}</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <button className="rounded-2xl border border-[#dce6da] bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
                          查看分块
                        </button>
                        <button className="rounded-2xl border border-[#f0d4d4] bg-white px-4 py-2 text-sm font-medium text-[#b34444] transition hover:bg-[#fff7f7]">
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </main>

          <aside className="space-y-6">
            <section className="rounded-[26px] border border-[#d9e6d7] bg-white p-5 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">分块详情</h2>
                  <p className="mt-1 text-sm text-slate-500">选择文档后查看切块内容与标签。</p>
                </div>
                <span className="rounded-full bg-[#eff7ee] px-2.5 py-1 text-xs font-medium text-[#3d7a4f]">
                  6 个切片
                </span>
              </div>

              <div className="space-y-3">
                {chunks.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-[#e5ece3] bg-[#fbfcfb] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-800">{item.id}</div>
                        <div className="mt-1 text-sm text-slate-500">{item.label}</div>
                      </div>
                      <button className="rounded-xl border border-[#dbe5d9] bg-white px-3 py-1.5 text-xs font-medium text-slate-600">
                        预览
                      </button>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-600">{item.text}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.tags.map((tag) => (
                        <span key={tag} className="rounded-full bg-[#f1f5f0] px-2.5 py-1 text-xs text-slate-600">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[26px] border border-[#d9e6d7] bg-[linear-gradient(135deg,#f5fbf6_0%,#ffffff_100%)] p-5 shadow-[0_10px_30px_rgba(36,64,45,0.06)]">
              <h2 className="text-lg font-semibold">设计优化点</h2>
              <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
                <li>将“知识库 / 文档 / 分块”改成三栏层级，信息关系更清晰。</li>
                <li>弱化大面积空白，增加卡片层次、状态标签和统计概览。</li>
                <li>统一圆角、边框和按钮样式，更接近现代 AI SaaS 控制台风格。</li>
                <li>把“上传、切块、状态、查看”串成一个连续操作流，降低使用成本。</li>
              </ul>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
