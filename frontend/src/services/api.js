import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 segundos de timeout
})

// Interceptor para adicionar token se necessário
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor para tratar erros de autenticação
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido ou expirado
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Itens
export const itensAPI = {
  listar: () => api.get('/api/itens'),
  buscar: (id) => api.get(`/api/itens/${id}`),
  criar: (data) => api.post('/api/itens', data),
  atualizar: (id, data) => api.put(`/api/itens/${id}`, data),
  deletar: (id) => api.delete(`/api/itens/${id}`),
}

// Compromissos
export const compromissosAPI = {
  listar: () => api.get('/api/compromissos'),
  buscar: (id) => api.get(`/api/compromissos/${id}`),
  criar: (data) => api.post('/api/compromissos', data),
  atualizar: (id, data) => api.put(`/api/compromissos/${id}`, data),
  deletar: (id) => api.delete(`/api/compromissos/${id}`),
}

// Disponibilidade
export const disponibilidadeAPI = {
  verificar: (data) => api.post('/api/disponibilidade', data),
}

// Estatísticas
export const statsAPI = {
  obter: () => api.get('/api/stats'),
}

// Categorias
export const categoriasAPI = {
  listar: () => api.get('/api/categorias'),
  obterCampos: (categoria) => api.get(`/api/categorias/${encodeURIComponent(categoria)}/campos`),
}

// Informações da API
export const infoAPI = {
  obter: () => api.get('/api/info'),
}

// Função de retry para login (até 2 tentativas com delay de 1s)
const retryLogin = async (credentials, maxRetries = 2) => {
  let lastError = null
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await api.post('/api/auth/login', credentials)
      return response
    } catch (error) {
      lastError = error
      
      // Se não for erro de timeout ou conexão, não tenta novamente
      if (error.code !== 'ECONNABORTED' && error.code !== 'ERR_NETWORK' && error.response?.status !== 408) {
        throw error
      }
      
      // Se não for a última tentativa, aguarda antes de tentar novamente
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 1000)) // 1 segundo de delay
      }
    }
  }
  
  throw lastError
}

// Autenticação
export const authAPI = {
  login: (credentials) => retryLogin(credentials),
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('usuario')
  },
  isAuthenticated: () => !!localStorage.getItem('token'),
}

export default api
