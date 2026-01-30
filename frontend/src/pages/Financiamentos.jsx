import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { financiamentosAPI, itensAPI } from '../services/api'
import { Plus, DollarSign, Calendar, Building2, Trash2, Edit, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import TabelaParcelas from '../components/TabelaParcelas'
import CalculadoraNPV from '../components/CalculadoraNPV'

export default function Financiamentos() {
  const [financiamentos, setFinanciamentos] = useState([])
  const [itens, setItens] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedFinanciamento, setSelectedFinanciamento] = useState(null)
  const [filtroStatus, setFiltroStatus] = useState('Todos')
  const [formData, setFormData] = useState({
    item_id: '',
    valor_total: '',
    numero_parcelas: '',
    taxa_juros: '',
    data_inicio: '',
    instituicao_financeira: '',
    observacoes: ''
  })

  useEffect(() => {
    loadFinanciamentos()
    loadItens()
  }, [filtroStatus])

  const loadItens = async () => {
    try {
      const response = await itensAPI.listar()
      setItens(response.data || [])
    } catch (error) {
      console.error('Erro ao carregar itens:', error)
    }
  }

  const loadFinanciamentos = async () => {
    try {
      setLoading(true)
      const params = filtroStatus !== 'Todos' ? { status: filtroStatus } : {}
      const response = await financiamentosAPI.listar(params)
      setFinanciamentos(response.data || [])
    } catch (error) {
      toast.error('Erro ao carregar financiamentos')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      const data = {
        ...formData,
        item_id: parseInt(formData.item_id),
        valor_total: parseFloat(formData.valor_total),
        numero_parcelas: parseInt(formData.numero_parcelas),
        taxa_juros: parseFloat(formData.taxa_juros) / 100, // Converte % para decimal
      }
      
      if (selectedFinanciamento) {
        await financiamentosAPI.atualizar(selectedFinanciamento.id, data)
        toast.success('Financiamento atualizado com sucesso!')
      } else {
        await financiamentosAPI.criar(data)
        toast.success('Financiamento criado com sucesso!')
      }
      
      setShowForm(false)
      setSelectedFinanciamento(null)
      setFormData({
        item_id: '',
        valor_total: '',
        numero_parcelas: '',
        taxa_juros: '',
        data_inicio: '',
        instituicao_financeira: '',
        observacoes: ''
      })
      loadFinanciamentos()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar financiamento')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Tem certeza que deseja deletar este financiamento?')) return
    
    try {
      await financiamentosAPI.deletar(id)
      toast.success('Financiamento deletado com sucesso!')
      loadFinanciamentos()
    } catch (error) {
      toast.error('Erro ao deletar financiamento')
    }
  }

  const handleView = async (id) => {
    try {
      const response = await financiamentosAPI.buscar(id)
      setSelectedFinanciamento(response.data)
    } catch (error) {
      toast.error('Erro ao carregar detalhes do financiamento')
    }
  }

  const handleEdit = (fin) => {
    setSelectedFinanciamento(fin)
    setFormData({
      item_id: fin.item_id,
      valor_total: fin.valor_total,
      numero_parcelas: fin.numero_parcelas,
      taxa_juros: (fin.taxa_juros * 100).toFixed(2), // Converte para %
      data_inicio: fin.data_inicio,
      instituicao_financeira: fin.instituicao_financeira || '',
      observacoes: fin.observacoes || ''
    })
    setShowForm(true)
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR')
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Financiamentos</h1>
          <p className="text-dark-400 mt-1">Gerencie os financiamentos dos seus itens</p>
        </div>
        <button
          onClick={() => {
            setShowForm(true)
            setSelectedFinanciamento(null)
            setFormData({
              item_id: '',
              valor_total: '',
              numero_parcelas: '',
              taxa_juros: '',
              data_inicio: '',
              instituicao_financeira: '',
              observacoes: ''
            })
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
        >
          <Plus size={20} />
          Novo Financiamento
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-4">
        <select
          value={filtroStatus}
          onChange={(e) => setFiltroStatus(e.target.value)}
          className="px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white"
        >
          <option value="Todos">Todos</option>
          <option value="Ativo">Ativos</option>
          <option value="Quitado">Quitados</option>
          <option value="Cancelado">Cancelados</option>
        </select>
      </div>

      {/* Formulário */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-dark-800 rounded-lg p-6 border border-dark-700"
        >
          <h2 className="text-xl font-bold text-white mb-4">
            {selectedFinanciamento ? 'Editar Financiamento' : 'Novo Financiamento'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Item</label>
                <select
                  value={formData.item_id}
                  onChange={(e) => setFormData({ ...formData, item_id: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="">Selecione um item</option>
                  {itens.map(item => (
                    <option key={item.id} value={item.id}>{item.nome}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Valor Total</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.valor_total}
                  onChange={(e) => setFormData({ ...formData, valor_total: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Número de Parcelas</label>
                <input
                  type="number"
                  value={formData.numero_parcelas}
                  onChange={(e) => setFormData({ ...formData, numero_parcelas: e.target.value })}
                  required
                  min="1"
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Taxa de Juros (% ao mês)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.taxa_juros}
                  onChange={(e) => setFormData({ ...formData, taxa_juros: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Data de Início</label>
                <input
                  type="date"
                  value={formData.data_inicio}
                  onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Instituição Financeira</label>
                <input
                  type="text"
                  value={formData.instituicao_financeira}
                  onChange={(e) => setFormData({ ...formData, instituicao_financeira: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Observações</label>
              <textarea
                value={formData.observacoes}
                onChange={(e) => setFormData({ ...formData, observacoes: e.target.value })}
                rows="3"
                className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
              />
            </div>
            
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setSelectedFinanciamento(null)
                }}
                className="px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Lista de Financiamentos */}
      {loading && !showForm ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {financiamentos.map((fin) => (
            <motion.div
              key={fin.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-dark-800 rounded-lg p-6 border border-dark-700"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-bold text-white">
                      {itens.find(i => i.id === fin.item_id)?.nome || `Item #${fin.item_id}`}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      fin.status === 'Ativo' ? 'bg-green-500/20 text-green-400' :
                      fin.status === 'Quitado' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {fin.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-dark-400">Valor Total</p>
                      <p className="text-lg font-semibold text-white">{formatCurrency(fin.valor_total)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-dark-400">Parcelas</p>
                      <p className="text-lg font-semibold text-white">{fin.numero_parcelas}x</p>
                    </div>
                    <div>
                      <p className="text-sm text-dark-400">Valor Parcela</p>
                      <p className="text-lg font-semibold text-white">{formatCurrency(fin.valor_parcela)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-dark-400">Taxa Juros</p>
                      <p className="text-lg font-semibold text-white">{(fin.taxa_juros * 100).toFixed(2)}%</p>
                    </div>
                  </div>
                  
                  {fin.instituicao_financeira && (
                    <div className="mt-2">
                      <p className="text-sm text-dark-400">Instituição</p>
                      <p className="text-white">{fin.instituicao_financeira}</p>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleView(fin.id)}
                    className="p-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                  >
                    <Eye size={18} />
                  </button>
                  <button
                    onClick={() => handleEdit(fin)}
                    className="p-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(fin.id)}
                    className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Modal de Detalhes */}
      {selectedFinanciamento && !showForm && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedFinanciamento(null)}
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-dark-800 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-dark-700"
          >
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-2xl font-bold text-white">Detalhes do Financiamento</h2>
              <button
                onClick={() => setSelectedFinanciamento(null)}
                className="text-dark-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-dark-400">Item</p>
                  <p className="text-white font-semibold">
                    {itens.find(i => i.id === selectedFinanciamento.item_id)?.nome || `Item #${selectedFinanciamento.item_id}`}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-400">Status</p>
                  <p className="text-white font-semibold">{selectedFinanciamento.status}</p>
                </div>
                <div>
                  <p className="text-sm text-dark-400">Valor Total</p>
                  <p className="text-white font-semibold">{formatCurrency(selectedFinanciamento.valor_total)}</p>
                </div>
                <div>
                  <p className="text-sm text-dark-400">Número de Parcelas</p>
                  <p className="text-white font-semibold">{selectedFinanciamento.numero_parcelas}</p>
                </div>
              </div>
              
              {selectedFinanciamento.parcelas && (
                <>
                  <TabelaParcelas parcelas={selectedFinanciamento.parcelas} financiamentoId={selectedFinanciamento.id} onPagar={loadFinanciamentos} />
                  <CalculadoraNPV financiamentoId={selectedFinanciamento.id} />
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}
