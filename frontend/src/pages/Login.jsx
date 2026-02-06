import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Lock, User, LogIn, AlertCircle } from 'lucide-react'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'
import api from '../services/api'

export default function Login() {
  const [usuario, setUsuario] = useState('')
  const [senha, setSenha] = useState('')
  const [loading, setLoading] = useState(false)
  const [checkingServer, setCheckingServer] = useState(true)
  const [serverReady, setServerReady] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('Entrando...')
  const [showColdStartMessage, setShowColdStartMessage] = useState(false)
  const navigate = useNavigate()

  // Preflight check: verifica se servidor está online
  useEffect(() => {
    const checkServer = async () => {
      try {
        await api.get('/api/health', { timeout: 3000 })
        setServerReady(true)
      } catch (error) {
        setServerReady(false)
        setShowColdStartMessage(true)
      } finally {
        setCheckingServer(false)
      }
    }
    
    checkServer()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setLoadingMessage('Entrando...')
    setShowColdStartMessage(false)

    // Mostra mensagem de cold start após 3 segundos (reduzido de 5s)
    const coldStartTimer = setTimeout(() => {
      if (loading) {
        setLoadingMessage('Aguardando servidor...')
        setShowColdStartMessage(true)
      }
    }, 3000)

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
      
      // Mensagens otimizadas de erro
      let errorMessage = 'Erro ao fazer login'
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'Tempo esgotado. O servidor está iniciando. Tente novamente em 10 segundos.'
      } else if (error.code === 'ERR_NETWORK' || !error.response) {
        errorMessage = 'Sem conexão. Verifique sua internet.'
      } else if (error.response?.status === 401) {
        errorMessage = 'Usuário ou senha incorretos'
      } else {
        errorMessage = error.response?.data?.detail || 'Erro inesperado'
      }
      
      toast.error(errorMessage)
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
            
            {/* Status do servidor */}
            {checkingServer && (
              <div className="mt-4 flex items-center justify-center gap-2 text-sm text-dark-400">
                <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-primary-500"></div>
                Verificando servidor...
              </div>
            )}
            {!checkingServer && !serverReady && (
              <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg flex items-start gap-2">
                <AlertCircle className="text-yellow-400 flex-shrink-0 mt-0.5" size={16} />
                <p className="text-xs text-yellow-400 text-left">
                  Servidor inicializando. Aguarde 10-30s e tente fazer login.
                </p>
              </div>
            )}
            {!checkingServer && serverReady && (
              <div className="mt-4 flex items-center justify-center gap-2 text-xs text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                Servidor online
              </div>
            )}
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
                  ⏳ Servidor iniciando (cold start). Isso pode levar 10-30 segundos.
                </p>
              </div>
            )}
          </form>
        </div>
      </motion.div>
    </div>
  )
}
