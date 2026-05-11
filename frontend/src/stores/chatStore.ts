import { create } from 'zustand';
import type { Conversation, Message } from '../types';
import { chatApi } from '../api/chat';

interface ChatState {
  conversations: Conversation[];
  activeConvId: number | null;
  messages: Message[];
  isStreaming: boolean;
  streamContent: string;
  loading: boolean;

  fetchConversations: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  newConversation: () => Promise<void>;
  deleteConversation: (id: number) => Promise<void>;
  setStreaming: (v: boolean) => void;
  appendStream: (text: string) => void;
  finalizeStream: () => void;
  addUserMessage: (text: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeConvId: null,
  messages: [],
  isStreaming: false,
  streamContent: '',
  loading: false,

  fetchConversations: async () => {
    const list = await chatApi.listConversations();
    set({ conversations: list });
  },

  selectConversation: async (id) => {
    set({ activeConvId: id, messages: [], loading: true });
    const msgs = await chatApi.getMessages(id);
    set({ messages: msgs, loading: false });
  },

  newConversation: async () => {
    const { id } = await chatApi.createConversation();
    set({ activeConvId: id, messages: [], streamContent: '' });
    await get().fetchConversations();
  },

  deleteConversation: async (id) => {
    await chatApi.deleteConversation(id);
    const { activeConvId } = get();
    if (activeConvId === id) {
      set({ activeConvId: null, messages: [] });
    }
    await get().fetchConversations();
  },

  setStreaming: (v) => set({ isStreaming: v }),
  appendStream: (text) => set(s => ({ streamContent: s.streamContent + text })),
  finalizeStream: () => set(s => {
    if (!s.streamContent) return { isStreaming: false, streamContent: '' };
    const msg: Message = {
      id: Date.now(),
      conversation_id: s.activeConvId ?? 0,
      role: 'assistant',
      content: s.streamContent,
      filepath: null,
      created_at: new Date().toISOString(),
    };
    return {
      messages: [...s.messages, msg],
      isStreaming: false,
      streamContent: '',
    };
  }),

  addUserMessage: (text) => set(s => {
    const msg: Message = {
      id: Date.now(),
      conversation_id: s.activeConvId ?? 0,
      role: 'user',
      content: text,
      filepath: null,
      created_at: new Date().toISOString(),
    };
    return { messages: [...s.messages, msg] };
  }),
}));
