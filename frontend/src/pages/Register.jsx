import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { HeartPulse, Loader2, UserPlus } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    age: '',
    gender: '',
    preferred_language: 'en',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function update(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    try {
      await register({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        age: form.age ? parseInt(form.age, 10) : null,
        gender: form.gender || null,
        preferred_language: form.preferred_language,
      })
      toast.success('Account created successfully!')
      navigate('/', { replace: true })
    } catch (err) {
      setError(err?.message || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-accent-600 text-white shadow-elevated">
            <HeartPulse className="h-7 w-7" strokeWidth={2} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Create Account</h1>
          <p className="mt-1 text-sm text-slate-500">Join CareConnect for AI-powered health guidance</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="reg-name" className="mb-1.5 block text-sm font-medium text-slate-700">
                Full Name *
              </label>
              <input
                id="reg-name"
                type="text"
                value={form.full_name}
                onChange={update('full_name')}
                required
                placeholder="Priya Sharma"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
              />
            </div>

            <div>
              <label htmlFor="reg-email" className="mb-1.5 block text-sm font-medium text-slate-700">
                Email *
              </label>
              <input
                id="reg-email"
                type="email"
                value={form.email}
                onChange={update('email')}
                required
                autoComplete="email"
                placeholder="priya@example.com"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="reg-age" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Age
                </label>
                <input
                  id="reg-age"
                  type="number"
                  min="1"
                  max="120"
                  value={form.age}
                  onChange={update('age')}
                  placeholder="28"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
                />
              </div>
              <div>
                <label htmlFor="reg-gender" className="mb-1.5 block text-sm font-medium text-slate-700">
                  Gender
                </label>
                <select
                  id="reg-gender"
                  value={form.gender}
                  onChange={update('gender')}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
                >
                  <option value="">Select</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="reg-password" className="mb-1.5 block text-sm font-medium text-slate-700">
                Password *
              </label>
              <input
                id="reg-password"
                type="password"
                value={form.password}
                onChange={update('password')}
                required
                minLength={6}
                autoComplete="new-password"
                placeholder="Min 6 characters"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
              />
            </div>

            <div>
              <label htmlFor="reg-confirm" className="mb-1.5 block text-sm font-medium text-slate-700">
                Confirm Password *
              </label>
              <input
                id="reg-confirm"
                type="password"
                value={form.confirmPassword}
                onChange={update('confirmPassword')}
                required
                autoComplete="new-password"
                placeholder="••••••••"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100"
              />
            </div>

            {error && (
              <div className="rounded-lg border border-red-100 bg-red-50 px-4 py-2.5 text-sm text-red-700" role="alert">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !form.full_name || !form.email || !form.password}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-brand-700 px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:from-brand-700 hover:to-brand-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-semibold text-brand-600 transition hover:text-brand-700"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
