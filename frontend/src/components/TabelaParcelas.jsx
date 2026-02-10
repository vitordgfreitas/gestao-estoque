import { useState } from 'react'
import { financiamentosAPI } from '../services/api'
import { CheckCircle, Clock, AlertCircle, Edit, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'

export default function TabelaParcelas({ parcelas, financiamentoId, onPagar }) {
  const [showPagarModal, setShowPagarModal] = useState(null)
  const [showEditModal, setShowEditModal] = useState(null)
  const [editingStatus, setEditingStatus] = useState({})
  const [pagamentoData, setPagamentoData] = useState({
    valor_pago: '',
    data_pagamento: new Date().toISOString().split('T')[0],
    juros: '0',
    multa: '0',
    desconto: '0'
  })
  const [editData, setEditData] = useState({
    status: '',
    link_boleto: '',
    link_comprovante: '',
    valor_original: '',
    data_vencimento: ''
  })

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('pt-BR')
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Paga':
        return <CheckCircle size={18} className="text-green-400" />
      case 'Atrasada':
        return <AlertCircle size={18} className="text-red-400" />
      default:
        return <Clock size={18} className="text-yellow-400" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Paga':
        return 'bg-green-500/20 text-green-400'
      case 'Atrasada':
        return 'bg-red-500/20 text-red-400'
      default:
        return 'bg-yellow-500/20 text-yellow-400'
    }
  }

  const calcularValorTotal = (parcela) => {
    return parcela.valor_original + parcela.juros + parcela.multa - parcela.desconto
  }

  const handlePagar = async () => {
    try {
      await financiamentosAPI.pagarParcela(financiamentoId, showPagarModal, {
        valor_pago: parseFloat(pagamentoData.valor_pago),
        data_pagamento: pagamentoData.data_pagamento,
        juros: parseFloat(pagamentoData.juros) || 0,
        multa: parseFloat(pagamentoData.multa) || 0,
        desconto: parseFloat(pagamentoData.desconto) || 0
      })
      toast.success('Pagamento registrado com sucesso!')
      setShowPagarModal(null)
      setPagamentoData({
        valor_pago: '',
        data_pagamento: new Date().toISOString().split('T')[0],
        juros: '0',
        multa: '0',
        desconto: '0'
      })
      // Aguarda um pouco para garantir que o backend processou
      await new Promise(resolve => setTimeout(resolve, 300))
      // Recarrega os dados
      if (onPagar) {
        await onPagar()
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao registrar pagamento')
    }
  }

  const handleStatusChange = async (parcelaId, newStatus) => {
    try {
      await financiamentosAPI.atualizarParcela(financiamentoId, parcelaId, { status: newStatus })
      toast.success('Status atualizado com sucesso!')
      setEditingStatus({ ...editingStatus, [parcelaId]: false })
      // Aguarda um pouco para garantir que o backend processou
      await new Promise(resolve => setTimeout(resolve, 300))
      // Recarrega os dados
      if (onPagar) {
        await onPagar()
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar status')
    }
  }

  const handleEdit = (parcela) => {
    setShowEditModal(parcela.id)
    setEditData({
      status: parcela.status,
      link_boleto: parcela.link_boleto || '',
      link_comprovante: parcela.link_comprovante || '',
      valor_original: parcela.valor_original.toString(),
      data_vencimento: parcela.data_vencimento.split('T')[0] || new Date(parcela.data_vencimento).toISOString().split('T')[0]
    })
  }

  const handleSaveEdit = async () => {
    try {
      await financiamentosAPI.atualizarParcela(financiamentoId, showEditModal, {
        status: editData.status,
        link_boleto: editData.link_boleto,
        valor_original: parseFloat(editData.valor_original),
        data_vencimento: editData.data_vencimento
      })
      toast.success('Parcela atualizada com sucesso!')
      setShowEditModal(null)
      if (onPagar) onPagar()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar parcela')
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white">Parcelas</h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">#</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Vencimento</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-dark-400">Valor</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-dark-400">Valor Pago</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Link Boleto</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Link Comprovante</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-dark-400">Ações</th>
            </tr>
          </thead>
          <tbody>
            {parcelas.map((parcela) => (
              <tr key={parcela.id} className="border-b border-dark-700">
                <td className="py-3 px-4 text-white">{parcela.numero_parcela}</td>
                <td className="py-3 px-4 text-white">{formatDate(parcela.data_vencimento)}</td>
                <td className="py-3 px-4 text-white text-right font-semibold">{formatCurrency(parcela.valor_original)}</td>
                <td className="py-3 px-4 text-white text-right">{formatCurrency(parcela.valor_pago)}</td>
                <td className="py-3 px-4">
                  {editingStatus[parcela.id] ? (
                    <select
                      value={parcela.status}
                      onChange={(e) => handleStatusChange(parcela.id, e.target.value)}
                      onBlur={() => setEditingStatus({ ...editingStatus, [parcela.id]: false })}
                      className="px-2 py-1 bg-dark-700 border border-dark-600 rounded text-sm text-white"
                      autoFocus
                    >
                      <option value="Pendente">Pendente</option>
                      <option value="Paga">Paga</option>
                      <option value="Atrasada">Atrasada</option>
                    </select>
                  ) : (
                    <div 
                      className="flex items-center gap-2 cursor-pointer"
                      onClick={() => setEditingStatus({ ...editingStatus, [parcela.id]: true })}
                    >
                      {getStatusIcon(parcela.status)}
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(parcela.status)}`}>
                        {parcela.status}
                      </span>
                    </div>
                  )}
                </td>
                <td className="py-3 px-4">
                  {parcela.link_boleto ? (
                    <a
                      href={parcela.link_boleto}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-primary-400 hover:text-primary-300 text-sm"
                    >
                      <ExternalLink size={14} />
                      Ver Boleto
                    </a>
                  ) : (
                    <span className="text-dark-500 text-sm">-</span>
                  )}
                </td>
                <td className="py-3 px-4">
                  {parcela.link_comprovante ? (
                    <a
                      href={parcela.link_comprovante}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-green-400 hover:text-green-300 text-sm"
                    >
                      <ExternalLink size={14} />
                      Ver Comprovante
                    </a>
                  ) : (
                    <span className="text-dark-500 text-sm">-</span>
                  )}
                </td>
                <td className="py-3 px-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(parcela)}
                      className="p-1 bg-dark-700 hover:bg-dark-600 text-white rounded transition-colors"
                      title="Editar parcela"
                    >
                      <Edit size={14} />
                    </button>
                    {parcela.status !== 'Paga' && (
                      <button
                        onClick={() => {
                          setShowPagarModal(parcela.id)
                          setPagamentoData({
                            valor_pago: calcularValorTotal(parcela).toFixed(2),
                            data_pagamento: new Date().toISOString().split('T')[0],
                            juros: parcela.juros.toString(),
                            multa: parcela.multa.toString(),
                            desconto: parcela.desconto.toString()
                          })
                        }}
                        className="px-3 py-1 bg-primary-500 hover:bg-primary-600 text-white rounded text-sm transition-colors"
                      >
                        Pagar
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal de Pagamento */}
      {showPagarModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg p-6 max-w-md w-full border border-dark-700">
            <h3 className="text-xl font-bold text-white mb-4">Registrar Pagamento</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Valor Pago</label>
                <input
                  type="number"
                  step="0.01"
                  value={pagamentoData.valor_pago}
                  onChange={(e) => setPagamentoData({ ...pagamentoData, valor_pago: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Data Pagamento</label>
                <input
                  type="date"
                  value={pagamentoData.data_pagamento}
                  onChange={(e) => setPagamentoData({ ...pagamentoData, data_pagamento: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Juros</label>
                  <input
                    type="number"
                    step="0.01"
                    value={pagamentoData.juros}
                    onChange={(e) => setPagamentoData({ ...pagamentoData, juros: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Multa</label>
                  <input
                    type="number"
                    step="0.01"
                    value={pagamentoData.multa}
                    onChange={(e) => setPagamentoData({ ...pagamentoData, multa: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">Desconto</label>
                  <input
                    type="number"
                    step="0.01"
                    value={pagamentoData.desconto}
                    onChange={(e) => setPagamentoData({ ...pagamentoData, desconto: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  />
                </div>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={handlePagar}
                  className="flex-1 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
                >
                  Confirmar Pagamento
                </button>
                <button
                  onClick={() => setShowPagarModal(null)}
                  className="flex-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Edição */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg p-6 max-w-md w-full border border-dark-700">
            <h3 className="text-xl font-bold text-white mb-4">Editar Parcela</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Status</label>
                <select
                  value={editData.status}
                  onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="Pendente">Pendente</option>
                  <option value="Paga">Paga</option>
                  <option value="Atrasada">Atrasada</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Link do Boleto</label>
                <input
                  type="url"
                  value={editData.link_boleto}
                  onChange={(e) => setEditData({ ...editData, link_boleto: e.target.value })}
                  placeholder="https://..."
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Link do Comprovante</label>
                <input
                  type="url"
                  value={editData.link_comprovante}
                  onChange={(e) => setEditData({ ...editData, link_comprovante: e.target.value })}
                  placeholder="https://..."
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Valor Original</label>
                <input
                  type="number"
                  step="0.01"
                  value={editData.valor_original}
                  onChange={(e) => setEditData({ ...editData, valor_original: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Data de Vencimento</label>
                <input
                  type="date"
                  value={editData.data_vencimento}
                  onChange={(e) => setEditData({ ...editData, data_vencimento: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              <div className="flex gap-4">
                <button
                  onClick={handleSaveEdit}
                  className="flex-1 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
                >
                  Salvar
                </button>
                <button
                  onClick={() => setShowEditModal(null)}
                  className="flex-1 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
