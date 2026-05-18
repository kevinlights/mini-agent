// ChatInterface component
// 聊天界面组件

import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../services/api'
import type { Message } from '../types'

interface ChatInterfaceProps {
  className?: string
}

export default function ChatInterface({ className }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendChat({
        message: userMessage.content,
        conversation_id: conversationId,
        history: messages,
      })

      setConversationId(response.conversation_id)
      setMessages((prev) => [...prev, { role: 'assistant', content: response.response }])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${errorMessage}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleReset = () => {
    setMessages([])
    setConversationId(undefined)
    setError(null)
  }

  return (
    <div className={`chat-container ${className || ''}`}>
      <div className="chat-header">
        <h2>Mini-Agent</h2>
        {conversationId && (
          <button onClick={handleReset} className="reset-btn">
            New Chat
          </button>
        )}
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Send a message to start the conversation.</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <div className="message-content">
              <strong>{msg.role === 'user' ? 'You' : 'Agent'}</strong>
              <p>{msg.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <strong>Agent</strong>
              <p className="typing-indicator">Thinking...</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (Enter to send)"
          disabled={isLoading}
          rows={1}
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>

      <style>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100%;
          max-width: 800px;
          margin: 0 auto;
          background: white;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .chat-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          background: #1a1a2e;
          color: white;
        }

        .chat-header h2 {
          margin: 0;
          font-size: 1.2rem;
        }

        .reset-btn {
          background: rgba(255, 255, 255, 0.2);
          border: none;
          color: white;
          padding: 6px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.85rem;
        }

        .reset-btn:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .welcome-message {
          text-align: center;
          color: #999;
          padding: 40px 0;
        }

        .message {
          display: flex;
        }

        .message.user {
          justify-content: flex-end;
        }

        .message.assistant {
          justify-content: flex-start;
        }

        .message-content {
          max-width: 70%;
          padding: 12px 16px;
          border-radius: 12px;
          word-wrap: break-word;
        }

        .message.user .message-content {
          background: #007bff;
          color: white;
          border-bottom-right-radius: 4px;
        }

        .message.assistant .message-content {
          background: #f0f0f0;
          color: #333;
          border-bottom-left-radius: 4px;
        }

        .message-content strong {
          display: block;
          font-size: 0.8rem;
          margin-bottom: 4px;
          opacity: 0.7;
        }

        .message-content p {
          margin: 0;
          line-height: 1.5;
        }

        .typing-indicator {
          color: #999 !important;
          font-style: italic;
        }

        .error-banner {
          background: #fee;
          color: #c00;
          padding: 8px 16px;
          text-align: center;
          font-size: 0.85rem;
        }

        .chat-input {
          display: flex;
          gap: 8px;
          padding: 16px 20px;
          border-top: 1px solid #eee;
          background: #fafafa;
        }

        .chat-input textarea {
          flex: 1;
          padding: 10px 14px;
          border: 1px solid #ddd;
          border-radius: 8px;
          resize: none;
          font-size: 0.95rem;
          font-family: inherit;
          outline: none;
        }

        .chat-input textarea:focus {
          border-color: #007bff;
        }

        .chat-input textarea:disabled {
          background: #f0f0f0;
        }

        .chat-input button {
          padding: 10px 20px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 0.95rem;
          white-space: nowrap;
        }

        .chat-input button:hover:not(:disabled) {
          background: #0056b3;
        }

        .chat-input button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  )
}
