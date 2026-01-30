import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Itens from './pages/Itens'
import Compromissos from './pages/Compromissos'
import Disponibilidade from './pages/Disponibilidade'
import Calendario from './pages/Calendario'
import VisualizarDados from './pages/VisualizarDados'
import ContasReceber from './pages/ContasReceber'
import ContasPagar from './pages/ContasPagar'
import DashboardFinanceiro from './pages/DashboardFinanceiro'
import { authAPI } from './services/api'

function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null)

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('token')
      setIsAuthenticated(!!token)
    }
    checkAuth()
  }, [])

  if (isAuthenticated === null) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/itens" element={<Itens />} />
                  <Route path="/compromissos" element={<Compromissos />} />
                  <Route path="/disponibilidade" element={<Disponibilidade />} />
                  <Route path="/calendario" element={<Calendario />} />
                  <Route path="/visualizar" element={<VisualizarDados />} />
                  <Route path="/contas-receber" element={<ContasReceber />} />
                  <Route path="/contas-pagar" element={<ContasPagar />} />
                  <Route path="/financeiro" element={<DashboardFinanceiro />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
