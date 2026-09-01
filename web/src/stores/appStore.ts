import { create } from 'zustand'

interface AppState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark') => void
  toggleTheme: () => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  theme: (localStorage.getItem('theme') as 'light' | 'dark') || 'light',
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setTheme: (theme) => {
    localStorage.setItem('theme', theme)
    set({ theme })
  },
  toggleTheme: () => set((state) => {
    const newTheme = state.theme === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', newTheme)
    return { theme: newTheme }
  }),
}))
