import { useNavigate, useLocation } from 'react-router-dom';
import { useThemeStore } from '../../stores/themeStore';
import { useLLMStore } from '../../stores/llmStore';
import { useEffect } from 'react';

const NAV_ITEMS = [
  { key: 'chat', label: '对话', path: '/chat' },
  { key: 'documents', label: '资料库', path: '/documents' },
  { key: 'review', label: '复习', path: '/review' },
  { key: 'graph', label: '知识图谱', path: '/graph' },
];

export default function TopNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const current = location.pathname.split('/')[1] || 'chat';
  const { mode, toggle } = useThemeStore();
  const { active, fetchActive } = useLLMStore();

  useEffect(() => { fetchActive(); }, []);

  return (
    <nav
      className="flex items-center justify-between h-12 px-4 border-b shrink-0"
      style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
    >
      <div className="flex gap-1">
        {NAV_ITEMS.map(item => {
          const active = current === item.key;
          return (
            <button
              key={item.key}
              onClick={() => navigate(item.path)}
              className="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer"
              style={{
                backgroundColor: active ? 'var(--color-accent-light)' : 'transparent',
                color: active ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              }}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="flex items-center gap-3">
        {/* Active LLM indicator */}
        <button
          onClick={() => navigate('/settings')}
          className="text-xs px-2 py-1 rounded cursor-pointer transition-colors"
          style={{ color: 'var(--color-text-muted)', backgroundColor: 'var(--color-surface-alt)' }}
          title="切换 LLM 提供商"
        >
          {active ? active.name : '默认'}
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="px-3 py-1.5 rounded-lg text-sm cursor-pointer transition-colors"
          style={{ color: 'var(--color-text-muted)' }}
          title={mode === 'dark' ? '切换到亮色模式' : '切换到暗色模式'}
        >
          {mode === 'dark' ? '亮' : '暗'}
        </button>

        {/* Settings */}
        <button
          onClick={() => navigate('/settings')}
          className="px-2 py-1.5 rounded-lg text-sm cursor-pointer transition-colors"
          style={{
            color: current === 'settings' ? 'var(--color-accent)' : 'var(--color-text-muted)',
            backgroundColor: current === 'settings' ? 'var(--color-accent-light)' : 'transparent',
          }}
          title="设置"
        >
          设置
        </button>
      </div>
    </nav>
  );
}
