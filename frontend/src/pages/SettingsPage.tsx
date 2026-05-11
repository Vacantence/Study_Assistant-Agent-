import { useEffect, useState } from 'react';
import { useLLMStore } from '../stores/llmStore';
import type { LLMProvider } from '../types';

export default function SettingsPage() {
  const { providers, active, fetchProviders, fetchActive, addProvider, updateProvider, activateProvider, deleteProvider, loading } = useLLMStore();

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<LLMProvider | null>(null);
  const [name, setName] = useState('');
  const [apiBase, setApiBase] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProviders();
    fetchActive();
  }, []);

  const resetForm = () => {
    setName('');
    setApiBase('https://api.deepseek.com/v1');
    setApiKey('');
    setModel('deepseek-chat');
    setError('');
    setEditing(null);
    setShowForm(false);
  };

  const handleEdit = (p: LLMProvider) => {
    setEditing(p);
    setName(p.name);
    setApiBase(p.api_base);
    setApiKey(p.api_key);
    setModel(p.model);
    setError('');
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!name.trim() || !apiBase.trim() || !apiKey.trim() || !model.trim()) {
      setError('所有字段均为必填');
      return;
    }
    try {
      if (editing) {
        await updateProvider(editing.id!, name.trim(), apiBase.trim(), apiKey.trim(), model.trim());
      } else {
        await addProvider(name.trim(), apiBase.trim(), apiKey.trim(), model.trim());
      }
      resetForm();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const maskedKey = (key: string) => {
    if (key.length <= 8) return '••••••••';
    return key.slice(0, 4) + '••••' + key.slice(-4);
  };

  return (
    <div className="h-full overflow-y-auto p-6" style={{ color: 'var(--color-text-primary)' }}>
      <h1 className="text-xl font-bold mb-6">设置</h1>

      {/* LLM 提供商 */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">LLM 提供商</h2>
          <button
            onClick={() => { resetForm(); setShowForm(true); }}
            className="px-4 py-1.5 rounded-lg text-sm font-medium cursor-pointer transition-colors"
            style={{ backgroundColor: 'var(--color-accent)', color: '#fff' }}
          >
            + 添加
          </button>
        </div>

        {/* Active Provider Info */}
        {active && (
          <div
            className="p-3 rounded-lg mb-4 text-sm"
            style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-accent-light)' }}
          >
            <span className="font-medium">当前使用：</span>
            {active.name} ({active.model})
          </div>
        )}

        {error && (
          <div className="p-2 mb-3 text-sm rounded" style={{ color: 'var(--color-danger)', backgroundColor: 'var(--color-danger-bg, #fef2f2)' }}>
            {error}
          </div>
        )}

        {/* Add/Edit Form */}
        {showForm && (
          <div
            className="p-4 rounded-lg mb-4 space-y-3"
            style={{ backgroundColor: 'var(--color-surface-alt)', border: '1px solid var(--color-border)' }}
          >
            <h3 className="text-sm font-medium">{editing ? '编辑提供商' : '新增提供商'}</h3>
            <input
              placeholder="名称（如：我的 DeepSeek、OpenAI）"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
            />
            <input
              placeholder="API 地址（如：https://api.deepseek.com/v1）"
              value={apiBase}
              onChange={e => setApiBase(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
            />
            <input
              placeholder="API Key"
              type="password"
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
            />
            <input
              placeholder="模型名称（如：deepseek-chat、gpt-4o）"
              value={model}
              onChange={e => setModel(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: 'var(--color-surface)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
            />
            <div className="flex gap-2 pt-1">
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-4 py-1.5 rounded-lg text-sm font-medium cursor-pointer transition-opacity disabled:opacity-50"
                style={{ backgroundColor: 'var(--color-accent)', color: '#fff' }}
              >
                {loading ? '保存中...' : '保存'}
              </button>
              <button
                onClick={resetForm}
                className="px-4 py-1.5 rounded-lg text-sm cursor-pointer"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* Provider List */}
        {providers.length === 0 && !showForm && (
          <div className="text-sm py-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
            还没有添加 LLM 提供商。添加后即可在对话中使用。
            <br />
            默认使用 .env 中的 DeepSeek 配置。
          </div>
        )}

        <div className="space-y-2">
          {providers.map(p => (
            <div
              key={p.id}
              className="flex items-center justify-between p-3 rounded-lg text-sm"
              style={{
                backgroundColor: 'var(--color-surface-alt)',
                border: p.is_active ? '1px solid var(--color-accent-light)' : '1px solid transparent',
              }}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate">{p.name}</span>
                  {p.is_active && (
                    <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: 'var(--color-accent-light)', color: 'var(--color-accent)' }}>
                      当前
                    </span>
                  )}
                </div>
                <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                  {p.model} — {maskedKey(p.api_key)}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-3">
                {!p.is_active && (
                  <button
                    onClick={() => activateProvider(p.id!)}
                    className="px-2 py-1 rounded text-xs cursor-pointer transition-colors"
                    style={{ color: 'var(--color-accent)' }}
                  >
                    切换
                  </button>
                )}
                <button
                  onClick={() => handleEdit(p)}
                  className="px-2 py-1 rounded text-xs cursor-pointer transition-colors"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  编辑
                </button>
                <button
                  onClick={() => deleteProvider(p.id!)}
                  className="px-2 py-1 rounded text-xs cursor-pointer transition-colors"
                  style={{ color: 'var(--color-danger)' }}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
        <p>提示：LLM 提供商需兼容 OpenAI API 格式。API Key 仅存储在本地数据库中，不会上传到第三方。</p>
        <p className="mt-1">常用服务商：DeepSeek (api.deepseek.com/v1)、OpenAI (api.openai.com/v1)、智谱 (open.bigmodel.cn/api/paas/v4)、通义千问 (dashscope.aliyuncs.com/compatible-mode/v1)</p>
      </section>
    </div>
  );
}
