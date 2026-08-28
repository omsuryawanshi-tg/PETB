/**
 * API service layer for CareConnect Triage.
 * All requests go through the Vite `/api` proxy → http://localhost:8000
 */

const APPOINTMENTS_STORAGE_KEY = 'petb_appointments';

async function parseError(response) {
  let detail = `Request failed (${response.status})`;
  try {
    const body = await response.json();
    if (typeof body?.detail === 'string') {
      detail = body.detail;
    } else if (Array.isArray(body?.detail)) {
      detail = body.detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
    } else if (body?.message) {
      detail = body.message;
    }
  } catch {
    // ignore JSON parse errors
  }
  const error = new Error(detail);
  error.status = response.status;
  throw error;
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    await parseError(response);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

/**
 * Multi-turn triage chat with the LLM agent.
 * @param {Array<{role: string, content: string}>} messages
 * @param {string} language
 * @param {string} patient_name
 */
export async function sendChatMessage(
  messages,
  language = 'en',
  patient_name = 'Patient',
) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ messages, language, patient_name }),
  });
}

/**
 * Fetch available appointment slots.
 * @param {string} date Optional YYYY-MM-DD filter (forward-compatible)
 */
export async function getAvailableSlots(date = '') {
  const params = date ? `?date=${encodeURIComponent(date)}` : '';
  return request(`/api/appointments/slots${params}`);
}

/**
 * Book an appointment slot by ID.
 * Maps slot_id → appointment_id for the FastAPI BookingRequest schema.
 * @param {number|string} slot_id
 * @param {string} patient_name
 */
export async function bookAppointment(slot_id, patient_name) {
  return request('/api/appointments/book', {
    method: 'POST',
    body: JSON.stringify({
      appointment_id: Number(slot_id),
      patient_name,
    }),
  });
}

/**
 * Persist a confirmed booking locally so Appointments history works
 * even when `/api/triage/history` is not yet available.
 */
export function saveLocalAppointment(booking) {
  if (!booking) return;
  try {
    const existing = JSON.parse(
      localStorage.getItem(APPOINTMENTS_STORAGE_KEY) || '[]',
    );
    const id =
      booking.appointment_id ??
      booking.booking_id ??
      booking.id ??
      Date.now();
    const normalized = {
      id,
      booking_id: String(id),
      doctor_id: booking.doctor_id || booking.doctor_name || '—',
      doctor_name: booking.doctor_name || booking.doctor_id || '—',
      date: booking.date || '',
      time_slot: booking.time_slot || booking.time || '',
      status: booking.status || 'Confirmed',
      patient_name: booking.patient_name || 'Patient',
      created_at: booking.created_at || new Date().toISOString(),
    };
    const withoutDup = existing.filter(
      (a) => String(a.id) !== String(normalized.id),
    );
    localStorage.setItem(
      APPOINTMENTS_STORAGE_KEY,
      JSON.stringify([normalized, ...withoutDup]),
    );
  } catch {
    // ignore storage errors
  }
}

function readLocalAppointments() {
  try {
    return JSON.parse(localStorage.getItem(APPOINTMENTS_STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

/**
 * Fetch appointment / triage history.
 * Tries GET /api/triage/history, then falls back to locally saved bookings.
 */
export async function getAppointmentHistory() {
  try {
    const data = await request('/api/triage/history');
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.appointments)) return data.appointments;
    if (Array.isArray(data?.history)) return data.history;
  } catch {
    // Endpoint may not exist yet — use local fallback
  }

  return readLocalAppointments();
}
