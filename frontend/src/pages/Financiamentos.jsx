import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { financiamentosAPI, itensAPI } from '../services/api'
import { Plus, DollarSign, Calendar, Building2, Trash2, Edit, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import TabelaParcelas from '../components/TabelaParcelas'
import CalculadoraNPV from '../components/CalculadoraNPV'
import ValorPresenteCard from '../components/ValorPresenteCard'

export default function Financiamentos() {
  const [financiamentos, setFinanciamentos] = useState([])
  const [itens, setItens] = useState([])
  const [loading, setLoading] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedFinanciamento, setSelectedFinanciamento] = useState(null)
  const [selectedItem, setSelectedItem] = useState(null)
  const [filtroStatus, setFiltroStatus] = useState('Todos')
  const [parcelasFixas, setParcelasFixas] = useState(true)
  const [parcelasCustomizadas, setParcelasCustomizadas] = useState([])
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
      setFormLoading(true)
      const data = {
        ...formData,
        item_id: parseInt(formData.item_id),
        valor_total: parseFloat(formData.valor_total),
        numero_parcelas: parcelasFixas ? parseInt(formData.numero_parcelas) : parcelasCustomizadas.length,
        // Converte % para decimal: usuário digita 3 (querendo 3%), salva como 0.03
        // SEMPRE divide por 100 se o valor for >= 1 (assumindo que é porcentagem)
        // Garante que nunca envia taxa > 1 (sempre converte para decimal)
        taxa_juros: (() => {
          const taxa = parseFloat(formData.taxa_juros)
          if (isNaN(taxa)) return 0
          // Se >= 1, assume que é porcentagem e converte para decimal
          return taxa >= 1 ? taxa / 100 : taxa
        })(),
      }
      
      // Se parcelas variáveis, adiciona array de parcelas
      if (!parcelasFixas && parcelasCustomizadas.length > 0) {
        data.parcelas_customizadas = parcelasCustomizadas.map((p, idx) => ({
          numero: idx + 1,
          valor: parseFloat(p.valor),
          data_vencimento: p.data_vencimento
        }))
      }
      
      if (selectedFinanciamento) {
        await financiamentosAPI.atualizar(selectedFinanciamento.id, data)
        toast.success('Financiamento atualizado com sucesso!')
      } else {
        await financiamentosAPI.criar(data)
        toast.success('Financiamento criado com sucesso!')
      }
      
      // Fecha formulário primeiro
      setShowForm(false)
      setSelectedFinanciamento(null)
      setSelectedItem(null)
      setFormData({
        item_id: '',
        valor_total: '',
        numero_parcelas: '',
        taxa_juros: '',
        data_inicio: '',
        instituicao_financeira: '',
        observacoes: ''
      })
      setParcelasFixas(true)
      setParcelasCustomizadas([])
      
      // Pequeno delay para feedback visual antes de recarregar
      setTimeout(() => {
        loadFinanciamentos()
      }, 300)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao salvar financiamento')
    } finally {
      setFormLoading(false)
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
    const item = itens.find(i => i.id === fin.item_id)
    setSelectedItem(item || null)
    setFormData({
      item_id: fin.item_id,
      valor_total: fin.valor_total,
      numero_parcelas: fin.numero_parcelas,
      // Backend sempre retorna taxa como decimal (0.03 para 3%), então sempre multiplicamos por 100 para exibir
      // Garante que sempre converte para porcentagem para exibição
      taxa_juros: fin.taxa_juros < 1 ? (fin.taxa_juros * 100).toFixed(2) : fin.taxa_juros.toFixed(2),
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
            setSelectedItem(null)
            setParcelasFixas(true)
            setParcelasCustomizadas([])
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
                  onChange={(e) => {
                    const itemId = e.target.value
                    const item = itens.find(i => i.id === parseInt(itemId))
                    console.log('Item selecionado:', item)
                    console.log('dados_categoria:', item?.dados_categoria)
                    console.log('carro:', item?.carro)
                    setSelectedItem(item || null)
                    setFormData({ ...formData, item_id: itemId })
                  }}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="">Selecione um item</option>
                  {itens.map(item => {
                    // Se for carro, mostra nome e placa
                    if (item.categoria === 'Carros') {
                      const placa = item.dados_categoria?.Placa || 
                                   item.dados_categoria?.placa || 
                                   item.carro?.placa || ''
                      return (
                        <option key={item.id} value={item.id}>
                          {item.nome}{placa ? ` - ${placa}` : ''}
                        </option>
                      )
                    }
                    // Para outros itens, mostra apenas o nome
                    return (
                      <option key={item.id} value={item.id}>{item.nome}</option>
                    )
                  })}
                </select>
                {selectedItem && selectedItem.categoria === 'Carros' && (
                  <div className="mt-2 p-2 bg-dark-700/50 rounded text-sm text-dark-300">
                    <p><span className="font-semibold">Nome:</span> {selectedItem.nome}</p>
                    {/* Tenta obter placa de diferentes fontes */}
                    {(selectedItem.dados_categoria?.Placa || 
                      selectedItem.dados_categoria?.placa || 
                      selectedItem.carro?.placa) && (
                      <p><span className="font-semibold">Placa:</span> {
                        selectedItem.dados_categoria?.Placa || 
                        selectedItem.dados_categoria?.placa || 
                        selectedItem.carro?.placa
                      }</p>
                    )}
                    {/* Tenta obter marca de diferentes fontes */}
                    {(selectedItem.dados_categoria?.Marca || 
                      selectedItem.dados_categoria?.marca || 
                      selectedItem.carro?.marca) && (
                      <p><span className="font-semibold">Marca:</span> {
                        selectedItem.dados_categoria?.Marca || 
                        selectedItem.dados_categoria?.marca || 
                        selectedItem.carro?.marca
                      }</p>
                    )}
                    {/* Tenta obter modelo de diferentes fontes */}
                    {(selectedItem.dados_categoria?.Modelo || 
                      selectedItem.dados_categoria?.modelo || 
                      selectedItem.carro?.modelo) && (
                      <p><span className="font-semibold">Modelo:</span> {
                        selectedItem.dados_categoria?.Modelo || 
                        selectedItem.dados_categoria?.modelo || 
                        selectedItem.carro?.modelo
                      }</p>
                    )}
                  </div>
                )}
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
                <label className="block text-sm font-medium text-dark-300 mb-2">Tipo de Parcelas</label>
                <div className="flex gap-4 mb-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      checked={parcelasFixas}
                      onChange={() => {
                        setParcelasFixas(true)
                        setParcelasCustomizadas([])
                      }}
                      className="w-4 h-4"
                    />
                    <span className="text-white">Parcelas Fixas</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      checked={!parcelasFixas}
                      onChange={() => {
                        setParcelasFixas(false)
                        if (parcelasCustomizadas.length === 0) {
                          setParcelasCustomizadas([{ valor: '', data_vencimento: '' }])
                        }
                      }}
                      className="w-4 h-4"
                    />
                    <span className="text-white">Parcelas Variáveis</span>
                  </label>
                </div>
                {parcelasFixas ? (
                  <input
                    type="number"
                    value={formData.numero_parcelas}
                    onChange={(e) => setFormData({ ...formData, numero_parcelas: e.target.value })}
                    required
                    min="1"
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                    placeholder="Número de Parcelas"
                  />
                ) : (
                  <div className="space-y-2">
                    {parcelasCustomizadas.map((parcela, idx) => (
                      <div key={idx} className="flex gap-2">
                        <input
                          type="number"
                          step="0.01"
                          value={parcela.valor}
                          onChange={(e) => {
                            const novas = [...parcelasCustomizadas]
                            novas[idx].valor = e.target.value
                            setParcelasCustomizadas(novas)
                          }}
                          placeholder="Valor"
                          className="flex-1 px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                        />
                        <input
                          type="date"
                          value={parcela.data_vencimento}
                          onChange={(e) => {
                            const novas = [...parcelasCustomizadas]
                            novas[idx].data_vencimento = e.target.value
                            setParcelasCustomizadas(novas)
                          }}
                          className="flex-1 px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            setParcelasCustomizadas(parcelasCustomizadas.filter((_, i) => i !== idx))
                          }}
                          className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => {
                        setParcelasCustomizadas([...parcelasCustomizadas, { valor: '', data_vencimento: '' }])
                      }}
                      className="w-full px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
                    >
                      + Adicionar Parcela
                    </button>
                    {parcelasCustomizadas.length > 0 && (
                      <div className="text-sm text-dark-400">
                        Total: {formatCurrency(parcelasCustomizadas.reduce((sum, p) => sum + (parseFloat(p.valor) || 0), 0))}
                      </div>
                    )}
                  </div>
                )}
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
                disabled={formLoading}
                className="px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {formLoading ? 'Salvando...' : 'Salvar'}
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
                      {/* Exibe taxa: se >= 1, já está em %, senão multiplica por 100 */}
                      <p className="text-lg font-semibold text-white">{(fin.taxa_juros >= 1 ? fin.taxa_juros : fin.taxa_juros * 100).toFixed(2)}%</p>
                    </div>
                  </div>
                  
                  {fin.instituicao_financeira && (
                    <div className="mt-2">
                      <p className="text-sm text-dark-400">Instituição</p>
                      <p className="text-white">{fin.instituicao_financeira}</p>
                    </div>
                  )}
                  
                  <ValorPresenteCard financiamentoId={fin.id} compact />
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
