import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useChatStore } from '../stores/chatStore';
import { buildStreamUrl } from '../api/stream';
import Markdown from 'react-markdown';

export default function ChatPage() {
  const { convId } = useParams();
  const { activeConvId, messages, isStreaming, streamContent, selectConversation, setStreaming, appendStream, finalizeStream, addUserMessage, fetchConversations } = useChatStore();
  const [input, setInput] = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = convId ? Number(convId) : activeConvId;
    if (id && id !== activeConvId) {
      selectConversation(id);
    }
  }, [convId]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, streamContent]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput('');
    addUserMessage(text);

    setStreaming(true);
    abortRef.current = new AbortController();
    const token = localStorage.getItem('token');
    const url = buildStreamUrl(text, activeConvId ?? undefined);

    try {
      const resp = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
        signal: abortRef.current.signal,
      });
      const reader = resp.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.token) appendStream(parsed.token);
            } catch { /* skip malformed */ }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') console.error(err);
    }
    finalizeStream();
    fetchConversations();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-xl font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>AI 学习助手</h2>
              <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>输入你想学习的问题，开始探索</p>
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[75%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap"
              style={{
                backgroundColor: msg.role === 'user' ? 'var(--color-chat-user)' : 'var(--color-chat-ai)',
                color: 'var(--color-text-primary)',
              }}
            >
              {msg.role === 'assistant' ? <Markdown>{msg.content}</Markdown> : msg.content}
            </div>
          </div>
        ))}
        {isStreaming && streamContent && (
          <div className="flex justify-start">
            <div
              className="max-w-[75%] rounded-2xl px-4 py-2.5 text-sm"
              style={{ backgroundColor: 'var(--color-chat-ai)', color: 'var(--color-text-primary)' }}
            >
              <Markdown>{streamContent}</Markdown>
              <span className="animate-pulse">▌</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex gap-2 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            placeholder="输入你想学习的问题..."
            className="flex-1 px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 transition-colors"
            style={{
              backgroundColor: 'var(--color-surface)',
              borderColor: 'var(--color-border)',
              color: 'var(--color-text-primary)',
            }}
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim()}
            className="px-5 py-2.5 rounded-xl text-white text-sm font-medium transition-colors disabled:opacity-50 cursor-pointer"
            style={{ backgroundColor: 'var(--color-accent)' }}
          >
            {isStreaming ? '...' : '发送'}
          </button>
        </div>
      </div>
    </div>
  );
}
