import { TrendingDown } from 'lucide-react'

export default function ValorPresenteCard({ valorPresente, compact = false }) {
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
  }

  if (!valorPresente || valorPresente === 0) {
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
            {formatCurrency(valorPresente)}
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
        <div className="pt-4 border-t border-dark-600">
          <div className="flex justify-between items-center">
            <p className="text-lg font-bold text-white">Valor Presente (NPV)</p>
            <p className="text-2xl font-bold text-primary-400">{formatCurrency(valorPresente)}</p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-dark-600 rounded text-xs text-dark-300">
          <p>O valor presente (NPV) representa o valor atual das parcelas futuras. Este valor é calculado no Google Sheets.</p>
        </div>
      </div>
    </div>
  )
}
