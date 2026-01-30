import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, User, LogIn } from 'lucide-react'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function Login() {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Entrando...')
  const [showColdStartMessage, setShowColdStartMessage] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setLoadingMessage('Entrando...')
    setShowColdStartMessage(false)

    // Mostra mensagem de cold start após 5 segundos
    const coldStartTimer = setTimeout(() => {
      if (loading) {
        setLoadingMessage('Aguardando servidor...')
        setShowColdStartMessage(true)
      }
    }, 5000)

    try {
      const response = await authAPI.login({ usuario, senha })
      
      clearTimeout(coldStartTimer)
      
      if (response.data.success) {
        localStorage.setItem('token', response.data.token)
        localStorage.setItem('usuario', usuario)
        toast.success('Login realizado com sucesso!')
        navigate('/')
      } else {
        toast.error('Usuário ou senha incorretos')
      }
    } catch (error) {
      clearTimeout(coldStartTimer)
      console.error('Erro no login:', error)
      
      // Mensagens específicas para diferentes tipos de erro
      let errorMessage = 'Erro ao fazer login'
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'Tempo de espera esgotado. O servidor pode estar iniciando. Tente novamente.'
      } else if (error.code === 'ERR_NETWORK' || !error.response) {
        errorMessage = 'Erro de conexão. Verifique sua internet ou tente novamente em alguns instantes.'
      } else if (error.response?.status === 401) {
        errorMessage = 'Usuário ou senha incorretos'
      } else if (error.response?.status === 408) {
        errorMessage = 'Tempo de espera esgotado. Tente novamente.'
      } else {
        errorMessage = error.response?.data?.detail || error.message || 'Erro ao fazer login'
      }
      
      toast.error(errorMessage)
      
      // Debug adicional
      if (error.response) {
        console.error('Status:', error.response.status)
        console.error('Data:', error.response.data)
      }
    } finally {
      setLoading(false)
      setLoadingMessage('Entrando...')
      setShowColdStartMessage(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="card bg-dark-800 border-dark-700">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600/20 rounded-full mb-4">
              <LogIn className="text-primary-400" size={32} />
            </div>
            <h1 className="text-3xl font-bold text-dark-50 mb-2">CRM Gestão</h1>
            <p className="text-dark-400">Faça login para continuar</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="usuario" className="block text-sm font-medium text-dark-300 mb-2">
                Usuário
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="text-dark-400" size={20} />
                </div>
                <input
                  id="usuario"
                  type="text"
                  value={usuario}
                  onChange={(e) => setUsuario(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-dark-700 border border-dark-600 rounded-lg text-dark-50 placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Digite seu usuário"
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            <div>
              <label htmlFor="senha" className="block text-sm font-medium text-dark-300 mb-2">
                Senha
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="text-dark-400" size={20} />
                </div>
                <input
                  id="senha"
                  type="password"
                  value={senha}
                  onChange={(e) => setSenha(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-dark-700 border border-dark-600 rounded-lg text-dark-50 placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Digite sua senha"
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
                  <span>{loadingMessage}</span>
                </>
              ) : (
                <>
                  <LogIn size={20} />
                  <span>Entrar</span>
                </>
              )}
            </button>
            
            {showColdStartMessage && (
              <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <p className="text-sm text-blue-400 text-center">
                  ⏳ O servidor está iniciando. Isso pode levar alguns segundos na primeira requisição.
                </p>
              </div>
            )}
          </form>
        </div>
      </motion.div>
    </div>
  )
}
