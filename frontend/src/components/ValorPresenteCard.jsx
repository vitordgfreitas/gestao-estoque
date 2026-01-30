import { useState, useEffect } from 'react'
import { financiamentosAPI } from '../services/api'
import { TrendingDown } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ValorPresenteCard({ financiamentoId, compact = false }) {
  const [valorPresente, setValorPresente] = useState(null)
  const [loading, setLoading] = useState(false)
  const [usarCdi, setUsarCdi] = useState(false)

  useEffect(() => {
    if (financiamentoId) {
      loadValorPresente()
    }
  }, [financiamentoId, usarCdi])

  const loadValorPresente = async () => {
    try {
      setLoading(true)
      const response = await financiamentosAPI.valorPresente(financiamentoId, usarCdi)
      setValorPresente(response.data)
    } catch (error) {
      // Silencioso - não mostra erro se não conseguir calcular
      console.error('Erro ao calcular valor presente:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
  }

  const formatPercent = (value) => {
    return `${(value * 100).toFixed(2)}%`
  }

  if (loading) {
    return (
      <div className="flex justify-center py-2">
        <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (!valorPresente) {
    return null
  }

  if (compact) {
    return (
      <div className="mt-2 p-3 bg-dark-700 rounded-lg border border-dark-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingDown className="text-primary-400" size={16} />
            <span className="text-sm text-dark-400">Valor Presente:</span>
          </div>
          <span className="text-lg font-bold text-primary-400">
            {formatCurrency(valorPresente.valor_presente)}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
      <div className="flex items-center gap-2 mb-4">
        <TrendingDown className="text-primary-400" size={20} />
        <h3 className="text-lg font-bold text-white">Valor Presente (NPV)</h3>
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <input
            type="checkbox"
            id={`usarCdi-${financiamentoId}`}
            checked={usarCdi}
            onChange={(e) => setUsarCdi(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor={`usarCdi-${financiamentoId}`} className="text-sm text-dark-300">
            Usar CDI ao invés de SELIC
          </label>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-dark-400">Taxa de Desconto</p>
            <p className="text-xl font-bold text-white">{formatPercent(valorPresente.taxa_desconto)}</p>
          </div>
          <div>
            <p className="text-sm text-dark-400">Parcelas Restantes</p>
            <p className="text-xl font-bold text-white">{valorPresente.parcelas_restantes}</p>
          </div>
        </div>
        
        <div className="pt-4 border-t border-dark-600">
          <div className="flex justify-between items-center mb-2">
            <p className="text-sm text-dark-400">Valor Total Restante</p>
            <p className="text-lg font-semibold text-white">{formatCurrency(valorPresente.valor_total_restante)}</p>
          </div>
          <div className="flex justify-between items-center">
            <p className="text-lg font-bold text-white">Valor Presente (NPV)</p>
            <p className="text-2xl font-bold text-primary-400">{formatCurrency(valorPresente.valor_presente)}</p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-dark-600 rounded text-xs text-dark-300">
          <p>O valor presente (NPV) representa o valor atual das parcelas futuras, descontado pela taxa {usarCdi ? 'CDI' : 'SELIC'}.</p>
        </div>
      </div>
    </div>
  )
}
