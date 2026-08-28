import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Outlet } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { LanguageProvider } from './context/LanguageContext'
import ProtectedRoute from './components/common/ProtectedRoute'
import Navbar from './components/common/Navbar'
import Footer from './components/common/Footer'

// Pages
import Login from './pages/Login'
import Register from './pages/Register'
import ChatTriage from './pages/ChatTriage'
import Confirmation from './pages/Confirmation'
import MyAppointments from './pages/MyAppointments'
import AdminDashboard from './pages/AdminDashboard'

function AppLayout() {
  return (
    <div className="flex min-h-svh flex-col">
      <Navbar />
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <LanguageProvider>
          <Routes>
            {/* Public routes (no layout) */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes (with layout) */}
            <Route element={<AppLayout />}>
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <ChatTriage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/appointments"
                element={
                  <ProtectedRoute>
                    <MyAppointments />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/confirmation"
                element={
                  <ProtectedRoute>
                    <Confirmation />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin"
                element={
                  <ProtectedRoute adminOnly>
                    <AdminDashboard />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </LanguageProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
