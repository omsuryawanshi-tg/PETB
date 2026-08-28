/**
 * Auth service — login, register, get current user, token management.
 */

const TOKEN_KEY = 'petb_access_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function authHeaders(token) {
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
      else if (Array.isArray(body?.detail))
        detail = body.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
      else if (body?.message) detail = body.message
    } catch {
      // ignore
    }
    const error = new Error(detail)
    error.status = response.status
    throw error
  }
  if (response.status === 204) return null
  return response.json()
}

export async function authLogin(email, password) {
  const res = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return handleResponse(res)
}

export async function authRegister(payload) {
  const res = await fetch('/api/v1/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(res)
}

export async function authMe(token) {
  const res = await fetch('/api/v1/auth/me', {
    headers: authHeaders(token || getToken()),
  })
  return handleResponse(res)
}
