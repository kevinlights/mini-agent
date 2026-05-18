// TypeScript type definitions
// TypeScript 类型定义

export interface Message {
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  agent_config?: AgentConfig
  history?: Message[]
}

export interface AgentConfig {
  name?: string
  system_prompt?: string
  temperature?: number
  max_tokens?: number | null
  max_history?: number
  enable_tools?: boolean
  max_tool_calls?: number
  debug?: boolean
}

export interface ChatResponse {
  response: string
  conversation_id: string
  agent_status: {
    active: boolean
    history_length: number
    agent_id: string
  }
}

export interface ErrorResponse {
  error: string
  detail?: string
}
