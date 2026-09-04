/**
 * API service layer for CareConnect PETB.
 * All requests go through the Vite `/api` proxy → http://localhost:8000
 * Includes Bearer token interceptor for authenticated requests.
 */

import { getToken } from './auth'

async function parseError(response) {
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

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }

  const response = await fetch(path, { ...options, headers })

  if (!response.ok) {
    await parseError(response)
  }
  if (response.status === 204) return null
  return response.json()
}

/**
 * Multi-turn triage chat with the AI agent (authenticated).
 */
export async function sendChatMessage(messages, language = 'en') {
  return request('/api/v1/triage/chat', {
    method: 'POST',
    body: JSON.stringify({ messages, language }),
  })
}

/**
 * Fetch available appointment slots.
 */
export async function getAvailableSlots(date = '', specialty = '') {
  const params = new URLSearchParams()
  if (date) params.set('date', date)
  if (specialty) params.set('specialty', specialty)
  const qs = params.toString()
  return request(`/api/v1/appointments/slots${qs ? `?${qs}` : ''}`)
}

/**
 * Book an appointment slot (new schema: doctor_id + date + time_slot).
 */
export async function bookAppointment(doctorId, date, timeSlot, reason = '', triageSessionId = null) {
  return request('/api/v1/appointments/book', {
    method: 'POST',
    body: JSON.stringify({
      doctor_id: Number(doctorId),
      date,
      time_slot: timeSlot,
      reason_for_visit: reason,
      triage_session_id: triageSessionId,
    }),
  })
}

/**
 * Fetch authenticated user's appointment history.
 */
export async function getMyAppointments() {
  return request('/api/v1/appointments/my')
}

/**
 * Cancel an appointment by ID.
 */
export async function cancelAppointment(appointmentId) {
  return request(`/api/v1/appointments/${appointmentId}/cancel`, {
    method: 'DELETE',
  })
}

/**
 * Admin: Fetch dashboard stats.
 */
export async function getAdminStats() {
  return request('/api/v1/admin/stats')
}

/**
 * Admin: Fetch triage sessions with optional severity filter.
 */
export async function getAdminSessions(severity = '', limit = 50, offset = 0) {
  const params = new URLSearchParams()
  if (severity) params.set('severity', severity)
  params.set('limit', String(limit))
  params.set('offset', String(offset))
  return request(`/api/v1/admin/sessions?${params}`)
}
