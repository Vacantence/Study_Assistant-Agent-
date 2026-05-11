import { create } from 'zustand';

interface ThemeState {
  mode: 'light' | 'dark';
  toggle: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  mode: (localStorage.getItem('theme') as 'light' | 'dark') || 'light',

  toggle: () => set((s) => {
    const next = s.mode === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', next);
    if (next === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    return { mode: next };
  }),
}));

// Initialize theme on load
const init = localStorage.getItem('theme');
if (init === 'dark') {
  document.documentElement.classList.add('dark');
}
