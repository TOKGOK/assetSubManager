import axios from 'axios'
import { message } from 'antd'
import i18n from '../i18n'
import type { ApiResponse } from '../types'

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
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
    const msg = error.response?.data?.message || error.message || i18n.t('common.networkError')
    message.error(msg)
    return Promise.reject(error)
  },
)

export default client
