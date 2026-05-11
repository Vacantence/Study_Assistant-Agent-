import { create } from 'zustand';
import type { LLMProvider } from '../types';
import { llmApi } from '../api/llm';

interface LLMState {
  providers: LLMProvider[];
  active: LLMProvider | null;
  loading: boolean;
  error: string | null;
  fetchProviders: () => Promise<void>;
  fetchActive: () => Promise<void>;
  addProvider: (name: string, apiBase: string, apiKey: string, model: string) => Promise<void>;
  updateProvider: (id: number, name: string, apiBase: string, apiKey: string, model: string) => Promise<void>;
  activateProvider: (id: number) => Promise<void>;
  deleteProvider: (id: number) => Promise<void>;
}

export const useLLMStore = create<LLMState>((set, get) => ({
  providers: [],
  active: null,
  loading: false,
  error: null,

  fetchProviders: async () => {
    try {
      const providers = await llmApi.list();
      set({ providers });
    } catch {
      // ignore
    }
  },

  fetchActive: async () => {
    try {
      const active = await llmApi.getActive();
      set({ active });
    } catch {
      // ignore
    }
  },

  addProvider: async (name, apiBase, apiKey, model) => {
    set({ loading: true, error: null });
    try {
      await llmApi.add(name, apiBase, apiKey, model);
      await get().fetchProviders();
      await get().fetchActive();
      set({ loading: false });
    } catch (e: any) {
      const msg = e.response?.data?.detail || '添加失败';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  updateProvider: async (id, name, apiBase, apiKey, model) => {
    set({ loading: true, error: null });
    try {
      await llmApi.update(id, name, apiBase, apiKey, model);
      await get().fetchProviders();
      await get().fetchActive();
      set({ loading: false });
    } catch (e: any) {
      const msg = e.response?.data?.detail || '更新失败';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  activateProvider: async (id) => {
    try {
      await llmApi.activate(id);
      await get().fetchProviders();
      await get().fetchActive();
    } catch {
      // ignore
    }
  },

  deleteProvider: async (id) => {
    try {
      await llmApi.delete(id);
      await get().fetchProviders();
      await get().fetchActive();
    } catch {
      // ignore
    }
  },
}));
