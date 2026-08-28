import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const data: any = await authApi.login(username, password)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await loadUser()
    return data
  }

  async function loadUser() {
    if (!token.value) return null
    try {
      user.value = await authApi.me()
      return user.value
    } catch (error) {
      logout()
      throw error
    }
  }

  async function register(username: string, email: string, password: string) {
    return await authApi.register(username, email, password)
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    loadUser,
  }
})
