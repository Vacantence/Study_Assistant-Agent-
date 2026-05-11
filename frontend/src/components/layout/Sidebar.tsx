import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useChatStore } from '../../stores/chatStore';
import { chatApi } from '../../api/chat';
import { miscApi } from '../../api/misc';
import type { MemoryItem, CacheEntry, Stats } from '../../types';

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { conversations, activeConvId, fetchConversations, selectConversation, newConversation, deleteConversation } = useChatStore();

  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [showMem, setShowMem] = useState(false);
  const [showCache, setShowCache] = useState(false);
  const [cacheEntries, setCacheEntries] = useState<CacheEntry[]>([]);

  useEffect(() => {
    fetchConversations();
    miscApi.getStats().then(setStats).catch(() => {});
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const loadMemories = async () => {
    setShowMem(!showMem);
    if (!showMem) {
      miscApi.getMemory().then(setMemories).catch(() => {});
    }
  };

  const loadCache = async () => {
    setShowCache(!showCache);
    if (!showCache) {
      miscApi.getCache().then(setCacheEntries).catch(() => {});
    }
  };

  const handleExport = async () => {
    if (!activeConvId) return;
    const { title, markdown } = await chatApi.exportConversation(activeConvId);
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <aside
      className="w-64 h-screen flex flex-col border-r shrink-0"
      style={{ backgroundColor: 'var(--color-surface-alt)', borderColor: 'var(--color-border)' }}
    >
      {/* User Info */}
      <div className="flex items-center justify-between p-3 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <span className="text-sm font-medium truncate">{user?.name || '用户'}</span>
        <button onClick={handleLogout} className="text-xs px-2 py-1 rounded cursor-pointer" style={{ color: 'var(--color-danger)' }}>
          退出
        </button>
      </div>

      {/* New Chat */}
      <div className="p-2">
        <button
          onClick={newConversation}
          className="w-full py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer"
          style={{ backgroundColor: 'var(--color-accent)', color: '#fff' }}
        >
          + 新对话
        </button>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {conversations.map((c) => (
          <div
            key={c.id}
            className="flex items-center group rounded-lg cursor-pointer"
            style={{
              backgroundColor: c.id === activeConvId ? 'var(--color-surface-hover)' : 'transparent',
            }}
          >
            <button
              onClick={() => selectConversation(c.id)}
              className="flex-1 text-left truncate py-2 px-2 text-sm"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {c.title || '新对话'}
              <span className="ml-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>({c.msg_count})</span>
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); deleteConversation(c.id); }}
              className="opacity-0 group-hover:opacity-100 px-2 text-xs cursor-pointer transition-opacity"
              style={{ color: 'var(--color-danger)' }}
            >
              删除
            </button>
          </div>
        ))}
        {conversations.length === 0 && (
          <p className="text-xs text-center py-4" style={{ color: 'var(--color-text-muted)' }}>暂无对话</p>
        )}
      </div>

      {/* Export */}
      {activeConvId && (
        <div className="p-2 border-t" style={{ borderColor: 'var(--color-border)' }}>
          <button onClick={handleExport} className="w-full py-1.5 text-xs rounded-lg cursor-pointer transition-colors"
            style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text-secondary)' }}>
            导出当前对话
          </button>
        </div>
      )}

      {/* Memory Panel */}
      <div className="border-t" style={{ borderColor: 'var(--color-border)' }}>
        <button onClick={loadMemories} className="w-full text-left px-3 py-2 text-xs font-medium cursor-pointer"
          style={{ color: 'var(--color-text-secondary)' }}>
          记忆 ({memories.length})
        </button>
        {showMem && memories.length > 0 && (
          <div className="px-3 pb-2 space-y-1">
            {memories.map((m, i) => (
              <div key={i} className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                <strong>{m.key}:</strong> {m.value.slice(0, 60)}
              </div>
            ))}
          </div>
        )}
        {showMem && memories.length === 0 && (
          <p className="px-3 pb-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>暂无记忆</p>
        )}
      </div>

      {/* Cache Panel */}
      <div className="border-t" style={{ borderColor: 'var(--color-border)' }}>
        <button onClick={loadCache} className="w-full text-left px-3 py-2 text-xs font-medium cursor-pointer"
          style={{ color: 'var(--color-text-secondary)' }}>
          知识库 ({cacheEntries.length})
        </button>
        {showCache && cacheEntries.slice(0, 5).map((e) => (
          <div key={e.id} className="px-3 pb-1 text-xs truncate" style={{ color: 'var(--color-text-muted)' }}>
            {e.query}
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="px-3 py-2 border-t text-xs" style={{ color: 'var(--color-text-muted)', borderColor: 'var(--color-border)' }}>
        {stats ? `${stats.review_due} 张待复习 | ${stats.graph_nodes} 个知识点` : '加载中...'}
      </div>
    </aside>
  );
}
