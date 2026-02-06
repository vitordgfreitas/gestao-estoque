import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { contasPagarAPI, itensAPI } from '../services/api'
import { Plus, CheckCircle, XCircle, Clock, Filter } from 'lucide-react'
import toast from 'react-hot-toast'
import { formatItemName } from '../utils/format'

const CATEGORIAS = ['Fornecedor', 'Manutenção', 'Despesa', 'Outro']

export default function ContasPagar() {
  const [contas, setContas] = useState([])
  const [itens, setItens] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [filtroStatus, setFiltroStatus] = useState('Todos')
  const [filtroCategoria, setFiltroCategoria] = useState('Todas')
  const [formData, setFormData] = useState({
    descricao: '',
    categoria: 'Fornecedor',
    valor: '',
    data_vencimento: '',
    fornecedor: '',
    item_id: '',
    forma_pagamento: '',
    observacoes: ''
  })

  useEffect(() => {
    loadContas()
    loadItens()
  }, [filtroStatus, filtroCategoria])

  const loadItens = async () => {
    try {
      const response = await itensAPI.listar()
      setItens(response.data || [])
    } catch (error) {
      console.error('Erro ao carregar itens:', error)
    }
  }

  const loadContas = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filtroStatus !== 'Todos') params.status = filtroStatus
      if (filtroCategoria !== 'Todas') params.categoria = filtroCategoria
      const response = await contasPagarAPI.listar(params)
      setContas(response.data || [])
    } catch (error) {
      toast.error('Erro ao carregar contas a pagar')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      await contasPagarAPI.criar({
        ...formData,
        valor: parseFloat(formData.valor),
        item_id: formData.item_id ? parseInt(formData.item_id) : null
      })
      toast.success('Conta a pagar criada com sucesso!')
      setShowForm(false)
      setFormData({
        descricao: '',
        categoria: 'Fornecedor',
        valor: '',
        data_vencimento: '',
        fornecedor: '',
        item_id: '',
        forma_pagamento: '',
        observacoes: ''
      })
      loadContas()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar conta a pagar')
    } finally {
      setLoading(false)
    }
  }

  const handleMarcarPaga = async (id) => {
    try {
      await contasPagarAPI.marcarPaga(id, { data_pagamento: new Date().toISOString().split('T')[0] })
      toast.success('Conta marcada como paga!')
      loadContas()
    } catch (error) {
      toast.error('Erro ao marcar conta como paga')
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      'Pago': { icon: CheckCircle, color: 'text-green-400 bg-green-400/10', label: 'Pago' },
      'Pendente': { icon: Clock, color: 'text-yellow-400 bg-yellow-400/10', label: 'Pendente' },
      'Vencido': { icon: XCircle, color: 'text-red-400 bg-red-400/10', label: 'Vencido' }
    }
    const badge = badges[status] || badges['Pendente']
    const Icon = badge.icon
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon size={12} />
        {badge.label}
      </span>
    )
  }

  const contasFiltradas = contas.filter(c => {
    if (filtroStatus !== 'Todos' && c.status !== filtroStatus) return false
    if (filtroCategoria !== 'Todas' && c.categoria !== filtroCategoria) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-dark-50">Contas a Pagar</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          <Plus size={20} />
          Nova Conta
        </button>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-4">
        <Filter size={20} className="text-dark-400" />
        <select
          value={filtroStatus}
          onChange={(e) => setFiltroStatus(e.target.value)}
          className="px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-dark-50"
        >
          <option value="Todos">Todos os Status</option>
          <option value="Pendente">Pendentes</option>
          <option value="Pago">Pagas</option>
          <option value="Vencido">Vencidas</option>
        </select>
        <select
          value={filtroCategoria}
          onChange={(e) => setFiltroCategoria(e.target.value)}
          className="px-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-dark-50"
        >
          <option value="Todas">Todas as Categorias</option>
          {CATEGORIAS.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* Formulário */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card bg-dark-800 border-dark-700 p-6"
        >
          <h2 className="text-xl font-semibold text-dark-50 mb-4">Nova Conta a Pagar</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Descrição *</label>
                <input
                  type="text"
                  required
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                  placeholder="Descrição da conta"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Categoria *</label>
                <select
                  required
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                >
                  {CATEGORIAS.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Valor *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.valor}
                  onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Data Vencimento *</label>
                <input
                  type="date"
                  required
                  value={formData.data_vencimento}
                  onChange={(e) => setFormData({ ...formData, data_vencimento: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Fornecedor</label>
                <input
                  type="text"
                  value={formData.fornecedor}
                  onChange={(e) => setFormData({ ...formData, fornecedor: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                  placeholder="Nome do fornecedor"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Item (opcional)</label>
                <select
                  value={formData.item_id}
                  onChange={(e) => setFormData({ ...formData, item_id: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                >
                  <option value="">Nenhum</option>
                  {itens.map(item => (
                    <option key={item.id} value={item.id}>{formatItemName(item)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Forma de Pagamento</label>
                <input
                  type="text"
                  value={formData.forma_pagamento}
                  onChange={(e) => setFormData({ ...formData, forma_pagamento: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                  placeholder="Ex: PIX, Boleto, Cartão..."
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Observações</label>
              <textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-dark-50"
                rows="3"
                placeholder="Observações adicionais..."
              />
            </div>
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Lista */}
      {loading && contas.length === 0 ? (
        <div className="text-center py-12 text-dark-400">Carregando...</div>
      ) : contasFiltradas.length === 0 ? (
        <div className="text-center py-12 text-dark-400">Nenhuma conta a pagar encontrada</div>
      ) : (
        <div className="card bg-dark-800 border-dark-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">Descrição</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">Categoria</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">Valor</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">Vencimento</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-300 uppercase">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-700">
                {contasFiltradas.map((conta) => (
                  <tr key={conta.id} className="hover:bg-dark-700/30">
                    <td className="px-6 py-4 text-sm text-dark-300">#{conta.id}</td>
                    <td className="px-6 py-4 text-sm text-dark-200">{conta.descricao}</td>
                    <td className="px-6 py-4 text-sm text-dark-200">{conta.categoria}</td>
                    <td className="px-6 py-4 text-sm text-dark-200 font-medium">
                      R$ {parseFloat(conta.valor).toFixed(2).replace('.', ',')}
                    </td>
                    <td className="px-6 py-4 text-sm text-dark-200">
                      {new Date(conta.data_vencimento).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(conta.status)}</td>
                    <td className="px-6 py-4">
                      {conta.status !== 'Pago' && (
                        <button
                          onClick={() => handleMarcarPaga(conta.id)}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                        >
                          Marcar Paga
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
