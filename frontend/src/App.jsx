import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { uploadDocument, getDocuments, deleteDocument, getStats, chatStream } from './api'

export default function App() {
  const [docs, setDocs] = useState([])
  const [stats, setStats] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedDocs, setSelectedDocs] = useState([])
  const [tab, setTab] = useState('chat')
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadDocs()
    loadStats()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadDocs = async () => {
    try {
      const res = await getDocuments()
      setDocs(res.data)
    } catch {}
  }

  const loadStats = async () => {
    try {
      const res = await getStats()
      setStats(res.data)
    } catch {}
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setUploadProgress(0)
    try {
      await uploadDocument(file, setUploadProgress)
      await loadDocs()
      await loadStats()
      setTimeout(loadDocs, 3000)
    } catch (err) {
      alert('上传失败：' + (err.response?.data?.detail || err.message))
    } finally {
      setUploading(false)
      setUploadProgress(0)
      fileInputRef.current.value = ''
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确认删除？')) return
    try {
      await deleteDocument(id)
      setDocs(prev => prev.filter(d => d.id !== id))
      setSelectedDocs(prev => prev.filter(d => d !== id))
      await loadStats()
    } catch {}
  }

  const toggleDoc = (id) => {
    setSelectedDocs(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    )
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const query = input.trim()
    setInput('')
    setLoading(true)

    const history = messages
      .filter(m => m.role !== 'system')
      .slice(-10)
      .map(m => ({ role: m.role, content: m.content }))

    setMessages(prev => [...prev, { role: 'user', content: query }])

    let answer = ''
    let sources = []

    setMessages(prev => [...prev, {
      role: 'assistant', content: '', sources: [], loading: true
    }])

    try {
      await chatStream(
        query,
        history,
        selectedDocs.length > 0 ? selectedDocs : null,
        (token) => {
          answer += token
          setMessages(prev => {
            const next = [...prev]
            next[next.length - 1] = {
              role: 'assistant', content: answer, sources, loading: true
            }
            return next
          })
        },
        (s) => { sources = s },
        () => {
          setMessages(prev => {
            const next = [...prev]
            next[next.length - 1] = {
              role: 'assistant', content: answer, sources, loading: false
            }
            return next
          })
          setLoading(false)
        }
      )
    } catch (err) {
      setMessages(prev => {
        const next = [...prev]
        next[next.length - 1] = {
          role: 'assistant',
          content: '❌ 请求失败：' + err.message,
          sources: [],
          loading: false
        }
        return next
      })
      setLoading(false)
    }
  }

  const statusColor = (s) => {
    if (s === 'ready') return '#52c41a'
    if (s === 'processing') return '#faad14'
    return '#ff4d4f'
  }

  const statusText = (s) => {
    if (s === 'ready') return '✅ 就绪'
    if (s === 'processing') return '⏳ 处理中'
    return '❌ 失败'
  }

  const formatSize = (b) => {
    if (b < 1024) return b + ' B'
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
    return (b / 1024 / 1024).toFixed(1) + ' MB'
  }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* 左侧边栏 */}
      <div style={{
        width: 280, background: '#fff', borderRight: '1px solid #e8e8e8',
        display: 'flex', flexDirection: 'column', flexShrink: 0
      }}>
        {/* Logo */}
        <div style={{
          padding: '20px 16px', borderBottom: '1px solid #e8e8e8',
          background: 'linear-gradient(135deg, #667eea, #764ba2)'
        }}>
          <div style={{ color: '#fff', fontSize: 18, fontWeight: 700 }}>
            🧠 RAG 知识库
          </div>
          <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12, marginTop: 4 }}>
            智能问答系统
          </div>
          <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 11, marginTop: 8, borderTop: '1px solid rgba(255,255,255,0.2)', paddingTop: 8 }}>
            👨‍💻 作者：贺劲尧
            <br/>西安电子科技大学 · AI专业
          </div>
        </div>

        {/* 统计 */}
        {stats && (
          <div style={{
            display: 'flex', padding: '12px 16px',
            borderBottom: '1px solid #e8e8e8', gap: 8
          }}>
            <div style={{
              flex: 1, background: '#f6f8ff', borderRadius: 8,
              padding: '8px 12px', textAlign: 'center'
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#667eea' }}>
                {stats.document_count}
              </div>
              <div style={{ fontSize: 11, color: '#888' }}>文档</div>
            </div>
            <div style={{
              flex: 1, background: '#f6ffed', borderRadius: 8,
              padding: '8px 12px', textAlign: 'center'
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>
                {stats.total_chunks}
              </div>
              <div style={{ fontSize: 11, color: '#888' }}>分块</div>
            </div>
          </div>
        )}

        {/* 上传按钮 */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #e8e8e8' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.docx,.md"
            onChange={handleUpload}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current.click()}
            disabled={uploading}
            style={{
              width: '100%', padding: '10px',
              background: uploading ? '#d9d9d9' : 'linear-gradient(135deg, #667eea, #764ba2)',
              color: '#fff', border: 'none', borderRadius: 8,
              cursor: uploading ? 'not-allowed' : 'pointer',
              fontSize: 14, fontWeight: 600
            }}
          >
            {uploading ? `上传中 ${uploadProgress}%` : '📁 上传文档'}
          </button>
          {uploading && (
            <div style={{
              marginTop: 6, height: 4, background: '#f0f0f0',
              borderRadius: 2, overflow: 'hidden'
            }}>
              <div style={{
                height: '100%', width: `${uploadProgress}%`,
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                transition: 'width 0.3s'
              }} />
            </div>
          )}
          <div style={{ fontSize: 11, color: '#aaa', marginTop: 6, textAlign: 'center' }}>
            支持 PDF / TXT / DOCX / MD
          </div>
        </div>

        {/* 文档列表 */}
        <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
          {docs.length === 0 ? (
            <div style={{
              textAlign: 'center', color: '#bbb',
              padding: '40px 16px', fontSize: 13
            }}>
              暂无文档<br />点击上传开始使用
            </div>
          ) : (
            docs.map(doc => (
              <div
                key={doc.id}
                onClick={() => toggleDoc(doc.id)}
                style={{
                  margin: '4px 8px', padding: '10px 12px',
                  borderRadius: 8, cursor: 'pointer',
                  border: `2px solid ${selectedDocs.includes(doc.id) ? '#667eea' : 'transparent'}`,
                  background: selectedDocs.includes(doc.id) ? '#f6f8ff' : '#fff',
                  transition: 'all 0.2s',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
                }}
              >
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  alignItems: 'flex-start'
                }}>
                  <div style={{
                    fontSize: 13, fontWeight: 500,
                    flex: 1, marginRight: 8,
                    overflow: 'hidden', textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    📄 {doc.original_name}
                  </div>
                  <button
                    onClick={e => { e.stopPropagation(); handleDelete(doc.id) }}
                    style={{
                      background: 'none', border: 'none',
                      cursor: 'pointer', color: '#ff4d4f',
                      fontSize: 14, padding: '0 2px', flexShrink: 0
                    }}
                  >✕</button>
                </div>
                <div style={{
                  display: 'flex', gap: 8, marginTop: 4,
                  fontSize: 11, color: '#999', alignItems: 'center'
                }}>
                  <span style={{ color: statusColor(doc.status) }}>
                    {statusText(doc.status)}
                  </span>
                  <span>{formatSize(doc.file_size)}</span>
                  {doc.chunk_count > 0 && <span>{doc.chunk_count} 块</span>}
                </div>
              </div>
            ))
          )}
        </div>

        {selectedDocs.length > 0 && (
          <div style={{
            padding: '8px 16px', borderTop: '1px solid #e8e8e8',
            fontSize: 12, color: '#667eea', textAlign: 'center'
          }}>
            已选 {selectedDocs.length} 个文档进行问答
          </div>
        )}
      </div>

      {/* 右侧主区域 */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden'
      }}>
        {/* 顶部标题栏 */}
        <div style={{
          padding: '0 24px', height: 56,
          background: '#fff', borderBottom: '1px solid #e8e8e8',
          display: 'flex', alignItems: 'center', gap: 16
        }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>💬 智能问答</span>
          {selectedDocs.length > 0 ? (
            <span style={{
              fontSize: 12, color: '#667eea',
              background: '#f6f8ff', padding: '2px 10px', borderRadius: 12
            }}>
              基于 {selectedDocs.length} 个选中文档
            </span>
          ) : (
            <span style={{
              fontSize: 12, color: '#888',
              background: '#f5f5f5', padding: '2px 10px', borderRadius: 12
            }}>
              基于全部文档
            </span>
          )}
          <button
            onClick={() => setMessages([])}
            style={{
              marginLeft: 'auto', background: 'none',
              border: '1px solid #e8e8e8', borderRadius: 6,
              padding: '4px 12px', cursor: 'pointer',
              fontSize: 12, color: '#888'
            }}
          >
            清空对话
          </button>
        </div>

        {/* 消息区域 */}
        <div style={{
          flex: 1, overflow: 'auto', padding: '24px',
          display: 'flex', flexDirection: 'column', gap: 16
        }}>
          {messages.length === 0 && (
            <div style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              color: '#bbb', gap: 12
            }}>
              <div style={{ fontSize: 48 }}>🧠</div>
              <div style={{ fontSize: 16, fontWeight: 500, color: '#999' }}>
                开始提问吧！
              </div>
              <div style={{ fontSize: 13, textAlign: 'center', lineHeight: 1.8 }}>
                先上传文档，然后针对文档内容提问<br />
                左侧点击文档可以限定问答范围
              </div>
              <div style={{
                display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap',
                justifyContent: 'center'
              }}>
                {['这份文档的主要内容是什么？', '帮我总结一下关键信息', '有哪些重要的数据？'].map(q => (
                  <button
                    key={q}
                    onClick={() => setInput(q)}
                    style={{
                      padding: '8px 16px', background: '#f6f8ff',
                      border: '1px solid #d6e4ff', borderRadius: 20,
                      cursor: 'pointer', fontSize: 13, color: '#667eea'
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              {msg.role === 'assistant' && (
                <div style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 16, flexShrink: 0, marginRight: 10, marginTop: 4
                }}>🧠</div>
              )}
              <div style={{ maxWidth: '72%' }}>
                <div style={{
                  padding: '12px 16px', borderRadius: 12,
                  background: msg.role === 'user'
                    ? 'linear-gradient(135deg, #667eea, #764ba2)'
                    : '#fff',
                  color: msg.role === 'user' ? '#fff' : '#333',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                  fontSize: 14, lineHeight: 1.7,
                  borderTopRightRadius: msg.role === 'user' ? 4 : 12,
                  borderTopLeftRadius: msg.role === 'assistant' ? 4 : 12,
                }}>
                  {msg.role === 'assistant' ? (
                    msg.loading && !msg.content ? (
                      <span style={{ color: '#999' }}>
                        ⏳ 思考中
                        <span style={{ animation: 'pulse 1s infinite' }}>...</span>
                      </span>
                    ) : (
                      <div className="markdown-body">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                        {msg.loading && <span style={{ color: '#999' }}>▌</span>}
                      </div>
                    )
                  ) : (
                    msg.content
                  )}
                </div>

                {/* 来源 */}
                {msg.sources && msg.sources.length > 0 && !msg.loading && (
                  <div style={{ marginTop: 8 }}>
                    <details>
                      <summary style={{
                        fontSize: 12, color: '#888', cursor: 'pointer',
                        userSelect: 'none', padding: '4px 0'
                      }}>
                        📚 {msg.sources.length} 条参考来源
                      </summary>
                      <div style={{
                        marginTop: 6, display: 'flex',
                        flexDirection: 'column', gap: 6
                      }}>
                        {msg.sources.map((s, si) => (
                          <div key={si} style={{
                            background: '#fafafa', border: '1px solid #e8e8e8',
                            borderRadius: 8, padding: '8px 12px', fontSize: 12
                          }}>
                            <div style={{
                              display: 'flex', justifyContent: 'space-between',
                              marginBottom: 4, color: '#666', fontWeight: 500
                            }}>
                              <span>
                                📄 {s.metadata?.original_name || s.metadata?.filename || '未知'}
                              </span>
                              <span style={{ color: '#52c41a' }}>
                                {(s.score * 100).toFixed(0)}% 相关
                              </span>
                            </div>
                            <div style={{
                              color: '#888', lineHeight: 1.5,
                              overflow: 'hidden',
                              display: '-webkit-box',
                              WebkitLineClamp: 3,
                              WebkitBoxOrient: 'vertical'
                            }}>
                              {s.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div style={{
                  width: 32, height: 32, borderRadius: '50%',
                  background: '#f0f0f0',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 16, flexShrink: 0, marginLeft: 10, marginTop: 4
                }}>👤</div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入框 */}
        <div style={{
          padding: '16px 24px', background: '#fff',
          borderTop: '1px solid #e8e8e8'
        }}>
          <div style={{
            display: 'flex', gap: 12, alignItems: 'flex-end',
            background: '#f5f5f5', borderRadius: 12,
            padding: '8px 8px 8px 16px',
            border: '2px solid transparent',
            transition: 'border-color 0.2s',
          }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder="输入问题，Enter 发送，Shift+Enter 换行..."
              rows={1}
              style={{
                flex: 1, background: 'none', border: 'none',
                outline: 'none', fontSize: 14, resize: 'none',
                lineHeight: 1.6, maxHeight: 120, overflow: 'auto',
                fontFamily: 'inherit'
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              style={{
                padding: '8px 20px', height: 40,
                background: loading || !input.trim()
                  ? '#d9d9d9'
                  : 'linear-gradient(135deg, #667eea, #764ba2)',
                color: '#fff', border: 'none', borderRadius: 8,
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                fontSize: 14, fontWeight: 600, flexShrink: 0,
                transition: 'all 0.2s'
              }}
            >
              {loading ? '⏳' : '发送 ↵'}
            </button>
          </div>
        </div>

         {/* 底部版权 */}
          <div style={{
            textAlign: 'center', fontSize: 11,
            color: '#bbb', padding: '4px',
            background: '#fff', borderTop: '1px solid #f0f0f0'
          }}>
            RAG 知识库问答系统 · 贺劲尧 · 西安电子科技大学 AI专业 · {new Date().getFullYear()}
          </div>
          
      </div>
    </div>
  )
}