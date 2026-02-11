import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { financeiroAPI, contasReceberAPI, contasPagarAPI } from '../services/api'
import { DollarSign, TrendingUp, TrendingDown, AlertCircle, Calendar } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatDate } from '../utils/format'

export default function DashboardFinanceiro() {
  const [dashboard, setDashboard] = useState(null)
  const [proximosVencimentos, setProximosVencimentos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
    loadProximosVencimentos()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const response = await financeiroAPI.dashboard()
      setDashboard(response.data)
    } catch (error) {
      toast.error('Erro ao carregar dashboard financeiro')
    } finally {
      setLoading(false)
    }
  }

  const loadProximosVencimentos = async () => {
    try {
      const hoje = new Date()
      const proximos7Dias = new Date(hoje.getTime() + 7 * 24 * 60 * 60 * 1000)
      
      const [receberResponse, pagarResponse] = await Promise.all([
        contasReceberAPI.listar({ status: 'Pendente' }),
        contasPagarAPI.listar({ status: 'Pendente' })
      ])
      
      const receber = (receberResponse.data || []).filter(c => {
        const venc = new Date(c.data_vencimento)
        return venc <= proximos7Dias && venc >= hoje
      })
      
      const pagar = (pagarResponse.data || []).filter(c => {
        const venc = new Date(c.data_vencimento)
        return venc <= proximos7Dias && venc >= hoje
      })
      
      const todos = [
        ...receber.map(c => ({ ...c, tipo: 'receber' })),
        ...pagar.map(c => ({ ...c, tipo: 'pagar' }))
      ].sort((a, b) => new Date(a.data_vencimento) - new Date(b.data_vencimento)).slice(0, 10)
      
      setProximosVencimentos(todos)
    } catch (error) {
      console.error('Erro ao carregar próximos vencimentos:', error)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!dashboard) {
    return <div className="text-center py-12 text-dark-400">Erro ao carregar dados</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-dark-50">Dashboard Financeiro</h1>

      {/* Cards de Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-dark-400">Saldo Atual</h3>
            <DollarSign className="text-primary-400" size={24} />
          </div>
          <p className={`text-2xl font-bold ${dashboard.saldo_atual >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(dashboard.saldo_atual)}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-dark-400">Receitas do Mês</h3>
            <TrendingUp className="text-green-400" size={24} />
          </div>
          <p className="text-2xl font-bold text-green-400">
            {formatCurrency(dashboard.receitas_mes)}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-dark-400">Despesas do Mês</h3>
            <TrendingDown className="text-red-400" size={24} />
          </div>
          <p className="text-2xl font-bold text-red-400">
            {formatCurrency(dashboard.despesas_mes)}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-dark-400">Saldo Previsto</h3>
            <DollarSign className="text-yellow-400" size={24} />
          </div>
          <p className={`text-2xl font-bold ${dashboard.saldo_previsto >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatCurrency(dashboard.saldo_previsto)}
          </p>
        </motion.div>
      </div>

      {/* Alertas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {dashboard.contas_vencidas > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card bg-red-600/10 border-red-600/20 p-6"
          >
            <div className="flex items-center gap-3 mb-2">
              <AlertCircle className="text-red-400" size={24} />
              <h3 className="text-lg font-semibold text-red-400">Contas Vencidas</h3>
            </div>
            <p className="text-3xl font-bold text-red-400">{dashboard.contas_vencidas}</p>
            <p className="text-sm text-dark-400 mt-2">Contas que precisam de atenção imediata</p>
          </motion.div>
        )}

        {dashboard.contas_a_vencer_7_dias > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card bg-yellow-600/10 border-yellow-600/20 p-6"
          >
            <div className="flex items-center gap-3 mb-2">
              <Calendar className="text-yellow-400" size={24} />
              <h3 className="text-lg font-semibold text-yellow-400">A Vencer (7 dias)</h3>
            </div>
            <p className="text-3xl font-bold text-yellow-400">{dashboard.contas_a_vencer_7_dias}</p>
            <p className="text-sm text-dark-400 mt-2">Contas com vencimento próximo</p>
          </motion.div>
        )}
      </div>

      {/* Próximos Vencimentos */}
      {proximosVencimentos.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <h2 className="text-xl font-semibold text-dark-50 mb-4">Próximos Vencimentos (7 dias)</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-700/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-dark-300 uppercase">Tipo</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-dark-300 uppercase">Descrição</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-dark-300 uppercase">Valor</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-dark-300 uppercase">Vencimento</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700">
                {proximosVencimentos.map((conta, idx) => (
                  <tr key={idx} className="hover:bg-dark-700/30">
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        conta.tipo === 'receber' 
                          ? 'bg-green-600/20 text-green-400' 
                          : 'bg-red-600/20 text-red-400'
                      }`}>
                        {conta.tipo === 'receber' ? 'Receber' : 'Pagar'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-dark-200">{conta.descricao}</td>
                    <td className="px-4 py-3 text-sm font-medium text-dark-200">
                      {formatCurrency(conta.valor)}
                    </td>
                    <td className="px-4 py-3 text-sm text-dark-200">
                      {formatDate(conta.data_vencimento)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Resumo */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <h3 className="text-lg font-semibold text-dark-50 mb-4">Receitas Pendentes</h3>
          <p className="text-3xl font-bold text-green-400 mb-2">
            {formatCurrency(dashboard.receitas_pendentes)}
          </p>
          <p className="text-sm text-dark-400">Valor total de contas a receber pendentes</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <h3 className="text-lg font-semibold text-dark-50 mb-4">Despesas Pendentes</h3>
          <p className="text-3xl font-bold text-red-400 mb-2">
            {formatCurrency(dashboard.despesas_pendentes)}
          </p>
          <p className="text-sm text-dark-400">Valor total de contas a pagar pendentes</p>
        </motion.div>
      </div>
    </div>
  )
}
