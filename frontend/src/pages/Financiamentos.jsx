import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { financiamentosAPI, itensAPI } from '../services/api'
import { Plus, DollarSign, Calendar, Building2, Trash2, Edit, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import TabelaParcelas from '../components/TabelaParcelas'
import CalculadoraNPV from '../components/CalculadoraNPV'
import ValorPresenteCard from '../components/ValorPresenteCard'
import { formatCurrency, formatDate, formatPercentage, roundToTwoDecimals, formatItemName, formatDecimalWhileTyping, parseDecimalInput, formatDecimalInput, formatCurrencyInput, formatPercentageInput, formatPercentageDisplay } from '../utils/format'

export default function Financiamentos() {
  const [financiamentos, setFinanciamentos] = useState([])
  const [itens, setItens] = useState([])
  const [loading, setLoading] = useState(false)
  const [formLoading, setFormLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [selectedFinanciamento, setSelectedFinanciamento] = useState(null)
  const [selectedItem, setSelectedItem] = useState(null)
  const [filtroStatus, setFiltroStatus] = useState('Todos')
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas')
  const [itensFiltrados, setItensFiltrados] = useState([])
  const [parcelasFixas, setParcelasFixas] = useState(true)
  const [parcelasCustomizadas, setParcelasCustomizadas] = useState([])
  const [selectedItens, setSelectedItens] = useState([])  // Array de {id, nome, valor}
  const [formData, setFormData] = useState({
    item_id: '',
    codigo_contrato: '',
    valor_total: '',
    valor_entrada: '',
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

  useEffect(() => {
    if (categoriaFiltro === 'Todas') {
      setItensFiltrados(itens)
    } else {
      setItensFiltrados(itens.filter(i => i.categoria === categoriaFiltro))
    }
  }, [categoriaFiltro, itens])

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

  // Handlers para múltiplos itens
  const addItem = (itemId) => {
    if (!itemId) return
    
    const item = itens.find(i => i.id === parseInt(itemId))
    if (!item) return
    
    // Verifica se já foi adicionado
    if (selectedItens.find(i => i.id === item.id)) {
      toast.error('Item já adicionado')
      return
    }
    
    setSelectedItens([...selectedItens, { 
      id: item.id, 
      nome: formatItemName(item)
    }])
  }

  const removeItem = (index) => {
    setSelectedItens(selectedItens.filter((_, i) => i !== index))
  }

  // Não precisamos mais de updateItemValor - apenas selecionamos itens

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setFormLoading(true)
      
      // Converte valores com precisão (converte vírgula para ponto)
      const valorTotal = roundToTwoDecimals(parseDecimalInput(formData.valor_total || '0'))
      const valorEntrada = roundToTwoDecimals(parseDecimalInput(formData.valor_entrada || '0'))
      // Taxa: converte e garante que está em formato decimal (0.0155 = 1,55%)
      let taxaJuros = parseDecimalInput(formData.taxa_juros)
      // Se a taxa for >= 1, assume que o usuário digitou em % (ex: 1.55 = 1,55%), divide por 100
      if (taxaJuros >= 1) {
        taxaJuros = taxaJuros / 100
      }
      // Se a taxa for >= 0.1 (10%), provavelmente digitou errado, avisa
      if (taxaJuros >= 0.1) {
        const confirmacao = window.confirm(
          `A taxa de juros está ${(taxaJuros * 100).toFixed(2)}% ao mês. Isso está correto?\n\n` +
          `Se você quis dizer ${(taxaJuros).toFixed(4)}%, clique em Cancelar e corrija.`
        )
        if (!confirmacao) {
          setFormLoading(false)
          return
        }
      }
      
      // Valida entrada
      if (valorEntrada > valorTotal) {
        toast.error('Valor de entrada não pode ser maior que o valor total')
        setFormLoading(false)
        return
      }
      
      // Valida que pelo menos um item foi selecionado
      if (selectedItens.length === 0) {
        toast.error('Selecione pelo menos um item para financiar')
        setFormLoading(false)
        return
      }
      
      // Prepara apenas os IDs dos itens (sem valores individuais)
      const itens_ids = selectedItens.map(item => parseInt(item.id))
      
      const data = {
        codigo_contrato: formData.codigo_contrato || null,
        itens_ids: itens_ids,
        valor_total: valorTotal,
        valor_entrada: valorEntrada,
        numero_parcelas: parcelasFixas ? parseInt(formData.numero_parcelas) : parcelasCustomizadas.length,
        taxa_juros: taxaJuros,
        data_inicio: formData.data_inicio,
        instituicao_financeira: formData.instituicao_financeira || null,
        observacoes: formData.observacoes || null
      }
      
      // Se parcelas variáveis, adiciona array de parcelas
      if (!parcelasFixas && parcelasCustomizadas.length > 0) {
        data.parcelas_customizadas = parcelasCustomizadas.map((p, idx) => ({
          numero: idx + 1,
          valor: roundToTwoDecimals(parseDecimalInput(p.valor)),
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
      
      // Fecha formulário e limpa
      setShowForm(false)
      setSelectedFinanciamento(null)
      setSelectedItem(null)
      setSelectedItens([])
      setFormData({
        item_id: '',
        valor_total: '',
        valor_entrada: '',
        numero_parcelas: '',
        taxa_juros: '',
        data_inicio: '',
        instituicao_financeira: '',
        observacoes: ''
      })
      setParcelasFixas(true)
      setParcelasCustomizadas([])
      
      // Recarrega a lista
      await loadFinanciamentos()
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

  const handleEdit = async (fin) => {
    try {
      // Busca dados completos do financiamento com itens
      const response = await financiamentosAPI.buscar(fin.id)
      const finCompleto = response.data
      
      setSelectedFinanciamento(finCompleto)
      const item = itens.find(i => i.id === finCompleto.item_id)
      setSelectedItem(item || null)
      
      // Popula a lista de itens selecionados a partir do financiamento COMPLETO
      if (finCompleto.itens && finCompleto.itens.length > 0) {
        setSelectedItens(finCompleto.itens.map(item => ({
          id: item.id,
          nome: item.nome
        })))
      } else {
        setSelectedItens([])
      }
      
      // Garante que valores sempre tenham 2 casas decimais com vírgula
      const valorTotalFormatado = formatDecimalInput(finCompleto.valor_total, 2)
      const valorEntradaFormatado = formatDecimalInput(finCompleto.valor_entrada || 0, 2)
      
      setFormData({
        item_id: finCompleto.item_id,
        codigo_contrato: finCompleto.codigo_contrato || '',
        // Converte ponto para vírgula para exibição, sempre com 2 casas decimais
        valor_total: valorTotalFormatado.includes(',') ? valorTotalFormatado : valorTotalFormatado + ',00',
        valor_entrada: valorEntradaFormatado.includes(',') ? valorEntradaFormatado : valorEntradaFormatado + ',00',
        numero_parcelas: finCompleto.numero_parcelas,
        // Backend retorna taxa como decimal (0.0275 = 2,75%)
        // Formata para exibir no input com 4 casas decimais
        taxa_juros: formatDecimalInput(finCompleto.taxa_juros, 7),
        data_inicio: finCompleto.data_inicio,
        instituicao_financeira: finCompleto.instituicao_financeira || '',
        observacoes: finCompleto.observacoes || ''
      })
      setShowForm(true)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao carregar dados do financiamento')
    }
  }

  return (
    <div className="p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
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
              codigo_contrato: '',
              valor_total: '',
              valor_entrada: '',
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
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
        <div className="text-sm text-dark-400">Filtrar por status</div>
        <div className="flex flex-col xs:flex-row gap-3">
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg text-white max-w-xs"
          >
            <option value="Todos">Todos</option>
            <option value="Ativo">Ativos</option>
            <option value="Quitado">Quitados</option>
            <option value="Cancelado">Cancelados</option>
          </select>
        </div>
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
                <label className="block text-sm font-medium text-dark-300 mb-2">Categoria</label>
                <select
                  value={categoriaFiltro}
                  onChange={(e) => {
                    setCategoriaFiltro(e.target.value)
                    setFormData({ ...formData, item_id: '' })
                    setSelectedItem(null)
                  }}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="Todas">Todas as Categorias</option>
                  <option value="Carros">Carros</option>
                  <option value="Estrutura de Evento">Estrutura de Evento</option>
                  <option value="Peças de Carro">Peças de Carro</option>
                  <option value="Pecas">Pecas</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Itens Financiados</label>
                <select
                  onChange={(e) => {
                    addItem(e.target.value)
                    e.target.value = '' // Reseta o select
                  }}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                >
                  <option value="">+ Adicionar item</option>
                  {itensFiltrados.map(item => (
                    <option key={item.id} value={item.id}>
                      {formatItemName(item)}
                    </option>
                  ))}
                </select>
                
                {/* Lista de itens selecionados */}
                {selectedItens.length > 0 && (
                  <div className="space-y-2 mt-3">
                    <div className="bg-dark-700/50 p-2 rounded text-sm mb-2">
                      <p className="text-dark-300">
                        <span className="font-semibold">{selectedItens.length} {selectedItens.length === 1 ? 'item selecionado' : 'itens selecionados'}</span>
                      </p>
                    </div>
                    {selectedItens.map((item, idx) => (
                      <div key={idx} className="flex gap-2 items-center bg-dark-700 p-3 rounded-lg">
                        <span className="flex-1 text-white font-medium">{item.nome}</span>
                        <button 
                          type="button"
                          onClick={() => removeItem(idx)}
                          className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Código do Contrato</label>
                <input
                  type="text"
                  value={formData.codigo_contrato}
                  onChange={(e) => setFormData({ ...formData, codigo_contrato: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  placeholder="Ex: CTR-2024-001"
                />
                <p className="text-xs text-dark-400 mt-1">Código único do contrato (opcional)</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Valor Total</label>
                <input
                  type="text"
                  value={formData.valor_total}
                  onChange={(e) => {
                    // Formata tipo "caixa registradora" - sempre últimos 2 dígitos são centavos
                    const formatted = formatCurrencyInput(e.target.value)
                    setFormData({ ...formData, valor_total: formatted })
                  }}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  placeholder="Ex: 8000050 será R$ 80.000,50"
                />
                <p className="text-xs text-dark-400 mt-1">Digite apenas números - começa pelos centavos (ex: 8000050 = R$ 80.000,50)</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Valor de Entrada</label>
                <input
                  type="text"
                  value={formData.valor_entrada}
                  onChange={(e) => {
                    // Formata tipo "caixa registradora" - sempre últimos 2 dígitos são centavos
                    const formatted = formatCurrencyInput(e.target.value)
                    setFormData({ ...formData, valor_entrada: formatted })
                  }}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  placeholder="Ex: 500025 será R$ 5.000,25"
                />
                <p className="text-xs text-dark-400 mt-1">Digite apenas números - começa pelos centavos (ex: 500025 = R$ 5.000,25)</p>
                {formData.valor_total && parseDecimalInput(formData.valor_entrada) > 0 && (
                  <p className="text-xs text-dark-400 mt-1">
                    Valor financiado: {formatCurrency(parseDecimalInput(formData.valor_total) - parseDecimalInput(formData.valor_entrada))}
                  </p>
                )}
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
                          type="text"
                          value={parcela.valor}
                          onChange={(e) => {
                            // Formata tipo "caixa registradora" - sempre últimos 2 dígitos são centavos
                            const formatted = formatCurrencyInput(e.target.value)
                            const novas = [...parcelasCustomizadas]
                            novas[idx].valor = formatted
                            setParcelasCustomizadas(novas)
                          }}
                          placeholder="Ex: 422969 será R$ 4.229,69"
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
                        Total: {formatCurrency(parcelasCustomizadas.reduce((sum, p) => sum + parseDecimalInput(p.valor), 0))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">Taxa de Juros (% ao mês)</label>
                <input
                  type="text"
                  value={formData.taxa_juros}
                  onChange={(e) => {
                    // Formata tipo "caixa registradora" - sempre últimos 7 dígitos são decimais
                    const formatted = formatPercentageInput(e.target.value)
                    setFormData({ ...formData, taxa_juros: formatted })
                  }}
                  required
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white"
                  placeholder="Ex: 123456 = 1,234567% ou digite 1,234567"
                />
                <p className="text-xs text-dark-400 mt-1">Digite números (até 7 decimais). Ex: 1234567 = 1,234567%</p>
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
                className="w-full sm:w-auto px-6 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {formLoading ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setSelectedFinanciamento(null)
                }}
                className="w-full sm:w-auto px-6 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors"
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
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-white mb-1">
                        {fin.codigo_contrato || `Financiamento #${fin.id}`}
                      </h3>
                      {fin.itens && fin.itens.length > 0 && (
                        <div className="text-sm text-dark-300">
                          {fin.itens.length === 1 ? (
                            <span>{fin.itens[0].nome}</span>
                          ) : (
                            <span>{fin.itens.length} itens: {fin.itens.map(i => i.nome).join(', ')}</span>
                          )}
                        </div>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      fin.status === 'Ativo' ? 'bg-green-500/20 text-green-400' :
                      fin.status === 'Quitado' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {fin.status}
                    </span>
                  </div>
                  
                  {/* Detalhamento dos itens */}
                  {fin.itens && fin.itens.length > 1 && (
                    <div className="mb-3 p-2 bg-dark-700/50 rounded">
                      <p className="text-xs text-dark-400 mb-1">Itens Financiados:</p>
                      {fin.itens.map((item, idx) => (
                        <div key={idx} className="text-sm text-dark-300">
                          <span>• {item.nome}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-dark-400">Valor Total</p>
                      <p className="text-lg font-semibold text-white">{formatCurrency(fin.valor_total)}</p>
                    </div>
                    {fin.valor_entrada > 0 && (
                      <div>
                        <p className="text-sm text-dark-400">Entrada</p>
                        <p className="text-lg font-semibold text-green-400">{formatCurrency(fin.valor_entrada)}</p>
                      </div>
                    )}
                    <div>
                      <p className="text-sm text-dark-400">Valor Financiado</p>
                      <p className="text-lg font-semibold text-white">{formatCurrency(fin.valor_financiado || (fin.valor_total - (fin.valor_entrada || 0)))}</p>
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
                      <p className="text-lg font-semibold text-white">
                        {formatPercentageDisplay(fin.taxa_juros)}
                      </p>
                    </div>
                  </div>
                  
                  {fin.instituicao_financeira && (
                    <div className="mt-2">
                      <p className="text-sm text-dark-400">Instituição</p>
                      <p className="text-white">{fin.instituicao_financeira}</p>
                    </div>
                  )}
                  
                  <ValorPresenteCard valorPresente={fin.valor_presente} compact />
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
              <div>
                <h2 className="text-2xl font-bold text-white">
                  {selectedFinanciamento.codigo_contrato || `Financiamento #${selectedFinanciamento.id}`}
                </h2>
                {selectedFinanciamento.codigo_contrato && (
                  <p className="text-sm text-dark-400 mt-1">ID: #{selectedFinanciamento.id}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedFinanciamento(null)}
                className="text-dark-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              {/* Código do Contrato */}
              {selectedFinanciamento.codigo_contrato && (
                <div className="bg-dark-700/50 p-4 rounded-lg">
                  <p className="text-sm text-dark-400 mb-1">Código do Contrato</p>
                  <p className="text-white font-semibold">{selectedFinanciamento.codigo_contrato}</p>
                </div>
              )}
              
              {/* Itens Financiados */}
              {selectedFinanciamento.itens && selectedFinanciamento.itens.length > 0 && (
                <div className="bg-dark-700/50 p-4 rounded-lg">
                  <p className="text-sm text-dark-400 mb-2">Itens Financiados ({selectedFinanciamento.itens.length})</p>
                  <div className="space-y-2">
                    {selectedFinanciamento.itens.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 p-2 bg-dark-700 rounded">
                        <span className="w-6 h-6 flex items-center justify-center bg-primary-500/20 text-primary-400 rounded-full text-xs font-bold">
                          {idx + 1}
                        </span>
                        <span className="text-white font-medium">{item.nome}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
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
                {selectedFinanciamento.parcelas && (
                  <>
                    <div>
                      <p className="text-sm text-dark-400">Parcelas Pagas</p>
                      <p className="text-white font-semibold text-green-400">
                        {selectedFinanciamento.parcelas.filter(p => p.status === 'Paga').length}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-dark-400">Parcelas Faltantes</p>
                      <p className="text-white font-semibold text-yellow-400">
                        {selectedFinanciamento.parcelas.filter(p => p.status !== 'Paga').length}
                      </p>
                    </div>
                  </>
                )}
              </div>
              
              {selectedFinanciamento.parcelas && (
                <>
                  <TabelaParcelas 
                    parcelas={selectedFinanciamento.parcelas} 
                    financiamentoId={selectedFinanciamento.id} 
                    onPagar={async () => {
                      await loadFinanciamentos()
                      // Recarrega o financiamento selecionado para atualizar as parcelas
                      const updated = await financiamentosAPI.buscar(selectedFinanciamento.id)
                      if (updated?.data) {
                        setSelectedFinanciamento(updated.data)
                      }
                    }} 
                  />
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
