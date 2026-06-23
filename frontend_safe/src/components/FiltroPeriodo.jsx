import { useState } from 'react'
import { Calendar } from 'lucide-react'

export default function FiltroPeriodo({ onPeriodoChange }) {
  const [periodo, setPeriodo] = useState('mes')
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')

  const calcularPeriodo = (tipo) => {
    const hoje = new Date()
    let inicio, fim

    switch (tipo) {
      case 'hoje':
        inicio = fim = hoje
        break
      case 'semana':
        inicio = new Date(hoje.getTime() - 7 * 24 * 60 * 60 * 1000)
        fim = hoje
        break
      case 'mes':
        inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
        fim = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0)
        break
      case 'trimestre':
        const trimestre = Math.floor(hoje.getMonth() / 3)
        inicio = new Date(hoje.getFullYear(), trimestre * 3, 1)
        fim = new Date(hoje.getFullYear(), (trimestre + 1) * 3, 0)
        break
      case 'ano':
        inicio = new Date(hoje.getFullYear(), 0, 1)
        fim = new Date(hoje.getFullYear(), 11, 31)
        break
      case 'customizado':
        return { data_inicio: dataInicio, data_fim: dataFim }
      default:
        return null
    }

    return {
      data_inicio: inicio.toISOString().split('T')[0],
      data_fim: fim.toISOString().split('T')[0]
    }
  }

  const handlePeriodoChange = (novoPeriodo) => {
    setPeriodo(novoPeriodo)
    if (novoPeriodo !== 'customizado') {
      const datas = calcularPeriodo(novoPeriodo)
      if (datas && onPeriodoChange) {
        onPeriodoChange(datas)
      }
    }
  }

  const handleCustomSubmit = () => {
    if (dataInicio && dataFim && onPeriodoChange) {
      onPeriodoChange({ data_inicio: dataInicio, data_fim: dataFim })
    }
  }

  return (
    <div className="flex items-center gap-4">
      <Calendar size={20} className="text-dark-400" />
      <select
        value={periodo}
        onChange={(e) => handlePeriodoChange(e.target.value)}
        className="px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-dark-50"
      >
        <option value="hoje">Hoje</option>
        <option value="semana">Últimos 7 dias</option>
        <option value="mes">Este mês</option>
        <option value="trimestre">Este trimestre</option>
        <option value="ano">Este ano</option>
        <option value="customizado">Período customizado</option>
      </select>

      {periodo === 'customizado' && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-dark-50"
            placeholder="Data início"
          />
          <span className="text-dark-400">até</span>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-dark-50"
            placeholder="Data fim"
          />
          <button
            onClick={handleCustomSubmit}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            Aplicar
          </button>
        </div>
      )}
    </div>
  )
}
