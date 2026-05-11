import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function AuthPage() {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [err, setErr] = useState('');
  const { login, register, loading } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr('');
    if (!name || !password) { setErr('请填写所有字段'); return; }
    if (tab === 'register' && password !== confirm) { setErr('两次密码不一致'); return; }
    try {
      if (tab === 'login') {
        await login(name, password);
      } else {
        await register(name, password);
      }
      navigate('/chat');
    } catch (msg: any) {
      setErr(msg.message || '操作失败');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-surface-alt)]">
      <div className="w-full max-w-sm bg-[var(--color-surface)] rounded-xl shadow-lg p-8 border border-[var(--color-border)]">
        <h1 className="text-2xl font-bold text-center mb-2" style={{ color: 'var(--color-accent)' }}>
          AI 学习助手
        </h1>
        <p className="text-sm text-center mb-6" style={{ color: 'var(--color-text-secondary)' }}>
          个性化学习，提升效率
        </p>

        <div className="flex mb-6 border-b border-[var(--color-border)]">
          <button
            className={`flex-1 pb-2 text-sm font-medium transition-colors ${tab === 'login' ? 'border-b-2' : ''}`}
            style={{
              borderColor: tab === 'login' ? 'var(--color-accent)' : 'transparent',
              color: tab === 'login' ? 'var(--color-accent)' : 'var(--color-text-muted)',
            }}
            onClick={() => { setTab('login'); setErr(''); }}
          >
            登录
          </button>
          <button
            className={`flex-1 pb-2 text-sm font-medium transition-colors ${tab === 'register' ? 'border-b-2' : ''}`}
            style={{
              borderColor: tab === 'register' ? 'var(--color-accent)' : 'transparent',
              color: tab === 'register' ? 'var(--color-accent)' : 'var(--color-text-muted)',
            }}
            onClick={() => { setTab('register'); setErr(''); }}
          >
            注册
          </button>
        </div>

        {err && (
          <div className="mb-4 p-3 rounded-lg text-sm" style={{ backgroundColor: '#fef2f2', color: '#dc2626' }}>
            {err}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              用户名
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 transition-colors"
              style={{
                backgroundColor: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-primary)',
              }}
              placeholder="请输入用户名"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 transition-colors"
              style={{
                backgroundColor: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
                color: 'var(--color-text-primary)',
              }}
              placeholder={tab === 'register' ? '至少4个字符' : '请输入密码'}
            />
          </div>
          {tab === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                确认密码
              </label>
              <input
                type="password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border focus:outline-none focus:ring-2 transition-colors"
                style={{
                  backgroundColor: 'var(--color-surface)',
                  borderColor: 'var(--color-border)',
                  color: 'var(--color-text-primary)',
                }}
                placeholder="再次输入密码"
              />
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg text-white font-medium transition-colors disabled:opacity-50"
            style={{ backgroundColor: 'var(--color-accent)' }}
          >
            {loading ? '处理中...' : tab === 'login' ? '登录' : '注册'}
          </button>
        </form>
      </div>
    </div>
  );
}
