import { useNavigate, useLocation } from 'react-router-dom';
import { useThemeStore } from '../../stores/themeStore';

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
      <button
        onClick={toggle}
        className="px-3 py-1.5 rounded-lg text-sm cursor-pointer transition-colors"
        style={{ color: 'var(--color-text-muted)' }}
        title={mode === 'dark' ? '切换到亮色模式' : '切换到暗色模式'}
      >
        {mode === 'dark' ? '亮' : '暗'}
      </button>
    </nav>
  );
}
