import { create } from 'zustand'
import client from '../api/client'

interface ConnectionState {
  status: 'checking' | 'connected' | 'disconnected'
  error: string | null
  setConnected: () => void
  setDisconnected: (error?: string) => void
  checkConnection: () => Promise<void>
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  status: 'checking',
  error: null,

  setConnected: () => set({ status: 'connected', error: null }),

  setDisconnected: (error?: string) => set({
    status: 'disconnected',
    error: error ?? null,
  }),

  checkConnection: async () => {
    try {
      await client.get('/health')
      set({ status: 'connected', error: null })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      set({ status: 'disconnected', error: message })
    }
  },
}))
