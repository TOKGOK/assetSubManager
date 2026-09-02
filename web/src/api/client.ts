import axios from 'axios'
import { message } from 'antd'
import i18n from '../i18n'
import { useConnectionStore } from '../stores/connectionStore'
import type { ApiResponse } from '../types'

// 网络错误去重标志：连续网络错误只弹一次提示
let connectionErrorShown = false

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

// 请求拦截器：自动附加 auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => {
    // 成功响应：重置网络错误去重标志
    connectionErrorShown = false

    // blob 响应（文件下载）不做 JSON 格式校验
    if (response.config.responseType === 'blob') {
      return response
    }
    const data = response.data as ApiResponse<unknown>
    if (data.code !== 0) {
      message.error(data.message || i18n.t('common.requestFailed'))
      return Promise.reject(new Error(data.message))
    }
    return response
  },
  (error) => {
    // ── 网络错误（无 response）：连接断开 / DNS 失败 / CORS 等 ──
    if (!error.response) {
      useConnectionStore.getState().setDisconnected(error.message)
      if (!connectionErrorShown) {
        connectionErrorShown = true
        message.error(i18n.t('common.networkError'))
      }
      return Promise.reject(error)
    }

    // ── HTTP 状态码错误 ──
    if (error.response.status === 401) {
      localStorage.removeItem('auth_token')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
    // FastAPI HTTPException wraps the detail in { detail: { code, message } }
    const detail = error.response.data?.detail
    const msg = (typeof detail === 'object' ? detail?.message : detail)
      || error.response.data?.message
      || error.message
      || i18n.t('common.networkError')
    message.error(msg)
    return Promise.reject(error)
  },
)

export default client
