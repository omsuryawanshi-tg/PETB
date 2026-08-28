import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { authLogin, authRegister, authMe, getToken, setToken, clearToken } from '../services/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Hydrate user from stored token on mount
  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    authMe(token)
      .then(setUser)
      .catch(() => {
        clearToken()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await authLogin(email, password)
    setToken(data.access_token)
    setUser(data.user)
    return data
  }, [])

  const register = useCallback(async (payload) => {
    const data = await authRegister(payload)
    setToken(data.access_token)
    setUser(data.user)
    return data
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
  }), [user, loading, login, register, logout])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
