import axios from 'axios'

const BASE = 'http://localhost:8000'

// 上传文档
export const uploadDocument = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return axios.post(`${BASE}/api/documents/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total))
    },
  })
}

// 获取文档列表
export const getDocuments = () =>
  axios.get(`${BASE}/api/documents/`)

// 删除文档
export const deleteDocument = (id) =>
  axios.delete(`${BASE}/api/documents/${id}`)

// 获取统计
export const getStats = () =>
  axios.get(`${BASE}/api/documents/stats/overview`)

// 流式问答
export const chatStream = async (query, history, docIds, onToken, onSources, onDone) => {
  const resp = await fetch(`${BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history, doc_ids: docIds }),
  })

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value)
    const lines = text.split('\n').filter(l => l.startsWith('data: '))

    for (const line of lines) {
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'sources') onSources(data.data)
        else if (data.type === 'token') onToken(data.data)
        else if (data.type === 'done') onDone()
      } catch {}
    }
  }
}