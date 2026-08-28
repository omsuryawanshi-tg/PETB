import { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CalendarCheck,
  Loader2,
  Search,
} from 'lucide-react'
import { getAdminStats, getAdminSessions } from '../services/api'
import clsx from 'clsx'

const SEVERITY_COLORS = {
  low: 'bg-green-50 text-green-700',
  medium: 'bg-amber-50 text-amber-700',
  high: 'bg-red-50 text-red-700',
  emergency: 'bg-red-100 text-red-800 font-bold',
  unassessed: 'bg-slate-100 text-slate-600',
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [sessions, setSessions] = useState([])
  const [sessionsTotal, setSessionsTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [severityFilter, setSeverityFilter] = useState('')

  useEffect(() => {
    loadData()
  }, [severityFilter])

  async function loadData() {
    setLoading(true)
    try {
      const [statsData, sessionsData] = await Promise.all([
        getAdminStats(),
        getAdminSessions(severityFilter, 50, 0),
      ])
      setStats(statsData)
      setSessions(sessionsData.sessions || [])
      setSessionsTotal(sessionsData.total || 0)
    } catch (err) {
      console.error('Admin data load failed:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex flex-1 items-center justify-center gap-2 text-sm text-slate-500">
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
        Loading dashboard…
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Admin Dashboard
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Triage analytics, severity breakdown, and session management.
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Activity}
            label="Total Triages"
            value={stats.total_triages}
            color="brand"
          />
          <StatCard
            icon={AlertTriangle}
            label="High Severity"
            value={stats.high_severity_cases}
            color="red"
          />
          <StatCard
            icon={CalendarCheck}
            label="Appointments"
            value={stats.total_appointments}
            color="emerald"
          />
          <StatCard
            icon={BarChart3}
            label="Conversion Rate"
            value={`${stats.conversion_rate}%`}
            color="amber"
          />
        </div>
      )}

      {/* Severity Breakdown */}
      {stats?.severity_breakdown && (
        <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Severity Breakdown
          </h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(stats.severity_breakdown).map(([sev, count]) => (
              <div
                key={sev}
                className={clsx(
                  'rounded-xl px-4 py-2 text-sm font-semibold',
                  SEVERITY_COLORS[sev] || SEVERITY_COLORS.unassessed,
                )}
              >
                {sev}: {count}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sessions Table */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-soft overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-700">
            Recent Triage Sessions
            <span className="ml-2 text-xs font-normal text-slate-400">
              ({sessionsTotal} total)
            </span>
          </h2>
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-slate-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100"
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
        </div>

        {sessions.length === 0 ? (
          <div className="px-5 py-12 text-center text-sm text-slate-400">
            No triage sessions found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/50">
                  <th className="px-5 py-3 font-semibold text-slate-500">Patient</th>
                  <th className="px-5 py-3 font-semibold text-slate-500">Complaint</th>
                  <th className="px-5 py-3 font-semibold text-slate-500">Severity</th>
                  <th className="px-5 py-3 font-semibold text-slate-500">Date</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr
                    key={s.id}
                    className="border-b border-slate-50 transition hover:bg-slate-50/50"
                  >
                    <td className="px-5 py-3">
                      <div className="font-medium text-slate-800">{s.patient_name}</div>
                      <div className="text-xs text-slate-400">{s.patient_email}</div>
                    </td>
                    <td className="max-w-xs truncate px-5 py-3 text-slate-600">
                      {s.chief_complaint || '—'}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={clsx(
                          'inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold',
                          SEVERITY_COLORS[s.severity] || SEVERITY_COLORS.unassessed,
                        )}
                      >
                        {s.severity || 'N/A'}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3 text-xs text-slate-500">
                      {s.created_at
                        ? new Date(s.created_at).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorClasses = {
    brand: 'from-brand-50 to-brand-100/50 text-brand-700',
    red: 'from-red-50 to-red-100/50 text-red-700',
    emerald: 'from-emerald-50 to-emerald-100/50 text-emerald-700',
    amber: 'from-amber-50 to-amber-100/50 text-amber-700',
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-soft transition hover:shadow-card">
      <div
        className={clsx(
          'mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br',
          colorClasses[color] || colorClasses.brand,
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="mt-0.5 text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
    </div>
  )
}
