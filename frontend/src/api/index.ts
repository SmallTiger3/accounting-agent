import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

// ÇëÇóÀ¹½ØÆ÷
api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// ÏìÓ¦À¹½ØÆ÷
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default api

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  register: (username: string, email: string, password: string) =>
    api.post('/auth/register', { username, email, password }),
}

// Accounts API
export const accountsApi = {
  list: () => api.get('/accounts/'),
  create: (data: any) => api.post('/accounts/', data),
  get: (id: number) => api.get(`/accounts/${id}`),
  update: (id: number, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
}

// Transactions API
export const transactionsApi = {
  list: (params?: any) => api.get('/transactions/', { params }),
  create: (data: any) => api.post('/transactions/', data),
  delete: (id: number) => api.delete(`/transactions/${id}`),
}

// Categories API
export const categoriesApi = {
  list: (type?: string) => api.get('/categories/', { params: { category_type: type } }),
}

// Budgets API
export const budgetsApi = {
  list: (year?: number, month?: number) => api.get('/budgets/', { params: { year, month } }),
  create: (data: any) => api.post('/budgets/', data),
  delete: (id: number) => api.delete(`/budgets/${id}`),
}

// Chat API
export const chatApi = {
  getSessions: () => api.get('/chat/sessions'),
  getMessages: (sessionId: number) => api.get(`/chat/sessions/${sessionId}/messages`),
  sendMessage: (content: string, sessionId?: number) =>
    api.post('/chat/message', { content, session_id: sessionId }),
  deleteSession: (sessionId: number) => api.delete(`/chat/sessions/${sessionId}`),
}
