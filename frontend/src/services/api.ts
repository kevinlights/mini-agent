// API service layer for communicating with backend
// 与后端通信的 API 服务层

import type { ChatRequest, ChatResponse } from '../types'

const API_BASE = '/api/v1'

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error('Backend is not healthy')
  }
  return response.json()
}
