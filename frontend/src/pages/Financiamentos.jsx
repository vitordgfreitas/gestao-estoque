import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { financiamentosAPI, itensAPI } from '../services/api'
import { 
  Plus, DollarSign, Calendar, Building2, Trash2, Edit, Eye, 
  Search, ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  Percent, Hash, Info
} from 'lucide-react'
import toast from 'react-hot-toast'
import TabelaParcelas from '../components/TabelaParcelas'
import CalculadoraNPV from '../components/CalculadoraNPV'
import ValorPresenteCard from '../components/ValorPresenteCard'
import { 
  formatCurrency, formatDate, formatPercentage, roundToTwoDecimals, 
  formatItemName, parseDecimalInput, formatDecimalInput, 
  formatCurrencyInput, formatPercentageInput, formatPercentageDisplay 
} from '../utils/format'

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
  
  // --- NOVOS ESTADOS PARA OTIMIZAÇÃO ---
  const [pagina, setPagina] = useState(1)
  const [totalRecords, setTotalRecords] = useState(0)
  const [busca, setBusca] = useState('')
  const [expandedId, setExpandedId] = useState(null) // ID do card aberto
  const [detalhesFin, setDetalhesFin] = useState({}) // Cache de detalhes { id: dados }
  const [loadingDetalhes, setLoadingDetalhes] = useState(false)
  const porPagina = 10

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

  // Carregamento inicial e re-trigger por filtros/página
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        await Promise.all([
          loadItens(),
          loadFinanciamentos()
        ]);
      } catch (error) {
        console.error("Erro na carga inicial", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [filtroStatus, pagina]);

  // Debounce para busca global
  useEffect(() => {
    const timer = setTimeout(() => {
      if (pagina !== 1) setPagina(1);
      else loadFinanciamentos();
    }, 500);
    return () => clearTimeout(timer);
  }, [busca]);

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
      const params = {
        pagina: pagina,
        por_pagina: porPagina,
        q: busca,
        ...(filtroStatus !== 'Todos' && { status: filtroStatus })
      }
      const response = await financiamentosAPI.listar(params)
      // O backend agora retorna { data: [], total: x }
      setFinanciamentos(response.data.data || [])
      setTotalRecords(response.data.total || 0)
    } catch (error) {
      toast.error('Erro ao carregar financiamentos')
    } finally {
      setLoading(false)
    }
  }

  // Função para abrir o Accordion e buscar detalhes (Lazy Load)
  const toggleAccordion = async (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (!detalhesFin[id]) {
      try {
        setLoadingDetalhes(true);
        const response = await financiamentosAPI.buscar(id);
        setDetalhesFin(prev => ({ ...prev, [id]: response.data }));
      } catch (error) {
        toast.error('Erro ao carregar parcelas');
      } finally {
        setLoadingDetalhes(false);
      }
    }
  };

  const addItem = (itemId) => {
    if (!itemId) return
    const item = itens.find(i => i.id === parseInt(itemId))
    if (!item) return
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setFormLoading(true)
      const valorTotal = roundToTwoDecimals(parseDecimalInput(formData.valor_total || '0'))
      const valorEntrada = roundToTwoDecimals(parseDecimalInput(formData.valor_entrada || '0'))
      const taxaJuros = parseDecimalInput(formData.taxa_juros)
      
      if (valorEntrada > valorTotal) {
        toast.error('Valor de entrada não pode ser maior que o valor total')
        setFormLoading(false)
        return
      }
      if (selectedItens.length === 0) {
        toast.error('Selecione pelo menos um item para financiar')
        setFormLoading(false)
        return
      }
      
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
      
      setShowForm(false)
      setSelectedFinanciamento(null)
      setSelectedItens([])
      setFormData({
        item_id: '', valor_total: '', valor_entrada: '', numero_parcelas: '',
        taxa_juros: '', data_inicio: '', instituicao_financeira: '', observacoes: ''
      })
      setParcelasFixas(true)
      setParcelasCustomizadas([])
      loadFinanciamentos()
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
      const response = await financiamentosAPI.buscar(fin.id)
      const finCompleto = response.data
      setSelectedFinanciamento(finCompleto)
      if (finCompleto.itens && finCompleto.itens.length > 0) {
        setSelectedItens(finCompleto.itens.map(item => ({ id: item.id, nome: item.nome })))
      } else {
        setSelectedItens([])
      }
      const valorTotalFormatado = formatDecimalInput(finCompleto.valor_total, 2)
      const valorEntradaFormatado = formatDecimalInput(finCompleto.valor_entrada || 0, 2)
      setFormData({
        item_id: finCompleto.item_id,
        codigo_contrato: finCompleto.codigo_contrato || '',
        valor_total: valorTotalFormatado.includes(',') ? valorTotalFormatado : valorTotalFormatado + ',00',
        valor_entrada: valorEntradaFormatado.includes(',') ? valorEntradaFormatado : valorEntradaFormatado + ',00',
        numero_parcelas: finCompleto.numero_parcelas,
        taxa_juros: formatDecimalInput(finCompleto.taxa_juros * 100, 9),
        data_inicio: finCompleto.data_inicio,
        instituicao_financeira: finCompleto.instituicao_financeira || '',
        observacoes: finCompleto.observacoes || ''
      })
      setShowForm(true)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao carregar dados do financiamento')
    }
  }

  const totalPaginas = Math.ceil(totalRecords / porPagina);

  return (
    <div className="p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white uppercase tracking-tighter italic">Financiamentos</h1>
          <p className="text-dark-400 mt-1 text-xs uppercase font-bold tracking-widest">Controle de Ativos e Amortizações</p>
        </div>
        <button
          onClick={() => {
            setShowForm(true); setSelectedFinanciamento(null); setParcelasFixas(true);
            setParcelasCustomizadas([]); setSelectedItens([]);
            setFormData({ item_id: '', codigo_contrato: '', valor_total: '', valor_entrada: '', numero_parcelas: '', taxa_juros: '', data_inicio: '', instituicao_financeira: '', observacoes: '' });
          }}
          className="flex items-center gap-2 px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-all shadow-lg shadow-primary-500/20 font-black uppercase text-xs"
        >
          <Plus size={18} /> Novo Financiamento
        </button>
      </div>

      {/* Busca e Filtros */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div className="md:col-span-3 relative">
          <label className="text-[10px] font-black text-dark-500 uppercase ml-2 mb-1 block tracking-widest">Buscar em tudo pelo código</label>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-400" size={18} />
            <input 
              type="text" 
              placeholder="Digite o código do contrato..."
              className="w-full pl-12 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-2xl text-white focus:ring-2 focus:ring-primary-500 outline-none transition-all"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
        </div>
        <div>
          <label className="text-[10px] font-black text-dark-500 uppercase ml-2 mb-1 block tracking-widest">Status</label>
          <select
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
            className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-2xl text-white outline-none focus:ring-2 focus:ring-primary-500"
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
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="bg-dark-800 rounded-[2rem] p-8 border border-dark-700 shadow-2xl">
          <h2 className="text-xl font-black text-white mb-6 uppercase tracking-tight">
            {selectedFinanciamento ? '📝 Editar Registro' : '➕ Novo Registro'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="p-4 bg-dark-900/50 rounded-2xl border border-dark-700">
                  <label className="block text-[10px] font-black text-dark-500 uppercase tracking-widest mb-2">Filtrar Categoria de Itens</label>
                  <select
                    value={categoriaFiltro}
                    onChange={(e) => { setCategoriaFiltro(e.target.value); setFormData({ ...formData, item_id: '' }); }}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-xl text-white text-sm"
                  >
                    <option value="Todas">Todas as Categorias</option>
                    {categoriasAPI.listar && <option value="Carros">Carros</option>}
                    <option value="Estrutura de Evento">Estrutura de Evento</option>
                    <option value="Peças de Carro">Peças de Carro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-black text-dark-500 uppercase tracking-widest ml-2 mb-2">Selecionar Itens para Financiar</label>
                  <select
                    onChange={(e) => { addItem(e.target.value); e.target.value = ''; }}
                    className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-2xl text-white outline-none focus:border-primary-500"
                  >
                    <option value="">+ Clique para adicionar itens</option>
                    {itensFiltrados.map(item => <option key={item.id} value={item.id}>{formatItemName(item)}</option>)}
                  </select>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {selectedItens.map((item, idx) => (
                      <span key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-primary-500/10 border border-primary-500/30 text-primary-400 rounded-xl text-xs font-bold uppercase">
                        {item.nome}
                        <button type="button" onClick={() => removeItem(idx)} className="hover:text-white"><X size={14}/></button>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <InputGroup label="Código Contrato" icon={<Hash size={14}/>}>
                  <input type="text" value={formData.codigo_contrato} onChange={(e) => setFormData({ ...formData, codigo_contrato: e.target.value })} className="input-field" placeholder="Ex: CTR-99"/>
                </InputGroup>
                <InputGroup label="Valor Total" icon={<DollarSign size={14}/>}>
                  <input type="text" value={formData.valor_total} onChange={(e) => setFormData({ ...formData, valor_total: formatCurrencyInput(e.target.value) })} className="input-field" required/>
                </InputGroup>
                <InputGroup label="Valor Entrada" icon={<ArrowRight size={14}/>}>
                  <input type="text" value={formData.valor_entrada} onChange={(e) => setFormData({ ...formData, valor_entrada: formatCurrencyInput(e.target.value) })} className="input-field" />
                </InputGroup>
                <InputGroup label="Taxa Mensal (%)" icon={<Percent size={14}/>}>
                  <input type="text" value={formData.taxa_juros} onChange={(e) => setFormData({ ...formData, taxa_juros: formatPercentageInput(e.target.value) })} className="input-field" required/>
                </InputGroup>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               <div className="p-5 bg-dark-900/30 rounded-3xl border border-dark-700">
                  <label className="block text-[10px] font-black text-dark-500 uppercase tracking-widest mb-3">Estrutura de Pagamento</label>
                  <div className="flex gap-2 p-1 bg-dark-800 rounded-xl mb-4">
                    <button type="button" onClick={() => setParcelasFixas(true)} className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase transition-all ${parcelasFixas ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-500'}`}>Fixas</button>
                    <button type="button" onClick={() => { setParcelasFixas(false); if(parcelasCustomizadas.length === 0) setParcelasCustomizadas([{valor:'', data_vencimento:''}]) }} className={`flex-1 py-2 rounded-lg text-[10px] font-black uppercase transition-all ${!parcelasFixas ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-500'}`}>Variáveis</button>
                  </div>
                  {parcelasFixas ? (
                    <input type="number" value={formData.numero_parcelas} onChange={(e) => setFormData({ ...formData, numero_parcelas: e.target.value })} className="w-full bg-dark-700 border-none rounded-xl p-3 text-white font-bold" placeholder="Qtd Parcelas" required />
                  ) : (
                    <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar pr-2">
                      {parcelasCustomizadas.map((p, idx) => (
                        <div key={idx} className="flex gap-1">
                          <input type="text" value={p.valor} onChange={(e) => { const n = [...parcelasCustomizadas]; n[idx].valor = formatCurrencyInput(e.target.value); setParcelasCustomizadas(n); }} className="w-1/2 bg-dark-700 rounded-lg p-2 text-[10px] text-white" placeholder="Valor" />
                          <input type="date" value={p.data_vencimento} onChange={(e) => { const n = [...parcelasCustomizadas]; n[idx].data_vencimento = e.target.value; setParcelasCustomizadas(n); }} className="w-1/2 bg-dark-700 rounded-lg p-2 text-[10px] text-white" />
                          <button type="button" onClick={() => setParcelasCustomizadas(parcelasCustomizadas.filter((_, i) => i !== idx))} className="text-red-500 px-1">×</button>
                        </div>
                      ))}
                      <button type="button" onClick={() => setParcelasCustomizadas([...parcelasCustomizadas, {valor:'', data_vencimento:''}])} className="w-full py-2 border border-dashed border-dark-600 rounded-lg text-[9px] font-black uppercase text-dark-400">+ Add</button>
                    </div>
                  )}
               </div>
               <InputGroup label="Início do Contrato" icon={<Calendar size={14}/>}>
                  <input type="date" value={formData.data_inicio} onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })} className="input-field" required/>
               </InputGroup>
               <InputGroup label="Instituição Financeira" icon={<Building2 size={14}/>}>
                  <input type="text" value={formData.instituicao_financeira} onChange={(e) => setFormData({ ...formData, instituicao_financeira: e.target.value })} className="input-field" placeholder="Ex: Banco do Brasil"/>
               </InputGroup>
            </div>

            <div className="flex justify-end gap-4 pt-4 border-t border-dark-700">
              <button type="button" onClick={() => { setShowForm(false); setSelectedFinanciamento(null); }} className="px-8 py-3 text-dark-400 font-black uppercase text-xs hover:text-white transition-colors">Cancelar</button>
              <button type="submit" disabled={formLoading} className="px-10 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-2xl font-black uppercase text-xs shadow-xl shadow-primary-500/20 disabled:opacity-50">
                {formLoading ? 'Processando...' : 'Confirmar Registro'}
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Lista de Financiamentos com Accordion */}
      {loading && !showForm ? (
        <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary-500"></div></div>
      ) : (
        <div className="space-y-4">
          {financiamentos.map((fin) => (
            <motion.div key={fin.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-dark-800 rounded-[2rem] border border-dark-700 overflow-hidden shadow-xl hover:border-dark-600 transition-all">
              {/* Accordion Header */}
              <div 
                onClick={() => toggleAccordion(fin.id)}
                className="p-6 flex flex-col md:flex-row md:items-center justify-between cursor-pointer gap-4 group"
              >
                <div className="flex items-center gap-5">
                  <div className={`p-4 rounded-2xl ${fin.status === 'Ativo' ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500'} shadow-inner`}>
                    <DollarSign size={24} />
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-white uppercase tracking-tight group-hover:text-primary-400 transition-colors">
                      {fin.codigo_contrato || `CONTRATO #${fin.id}`}
                    </h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={`px-2 py-0.5 rounded-md text-[8px] font-black uppercase border ${fin.status === 'Ativo' ? 'border-green-500/20 text-green-500' : 'border-blue-500/20 text-blue-500'}`}>
                        {fin.status}
                      </span>
                      <p className="text-[10px] text-dark-500 font-bold uppercase tracking-widest">
                         {fin.itens?.length || 0} Itens • Total: {formatCurrency(fin.valor_total)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between md:justify-end gap-6">
                  <div className="text-right">
                    <p className="text-[9px] font-black text-dark-500 uppercase tracking-[0.2em]">Quitação Hoje</p>
                    <p className="text-lg font-black text-green-400 font-mono italic">{formatCurrency(fin.valor_quitacao_hoje)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={(e) => { e.stopPropagation(); handleView(fin.id); }} className="p-2 bg-dark-700 hover:bg-primary-500/20 text-dark-300 hover:text-primary-400 rounded-xl transition-all"><Eye size={18}/></button>
                    <button onClick={(e) => { e.stopPropagation(); handleEdit(fin); }} className="p-2 bg-dark-700 hover:bg-blue-500/20 text-dark-300 hover:text-blue-400 rounded-xl transition-all"><Edit size={18}/></button>
                    <button onClick={(e) => { e.stopPropagation(); handleDelete(fin.id); }} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-500/60 hover:text-red-500 rounded-xl transition-all"><Trash2 size={18}/></button>
                    <div className="ml-2 text-dark-600 group-hover:text-primary-500 transition-colors">
                      {expandedId === fin.id ? <ChevronUp size={24}/> : <ChevronDown size={24}/>}
                    </div>
                  </div>
                </div>
              </div>

              {/* Accordion Content (Lazy Loaded) */}
              <AnimatePresence>
                {expandedId === fin.id && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="border-t border-dark-700 bg-dark-900/20">
                    {loadingDetalhes && !detalhesFin[fin.id] ? (
                      <div className="p-10 text-center animate-pulse text-dark-600 text-[10px] font-black uppercase tracking-[0.3em]">Sincronizando parcelas do banco...</div>
                    ) : (
                      <div className="p-8 space-y-8">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                           <DataBadge label="Instituição" value={fin.instituicao_financeira || 'DIRETO'} icon={<Building2 size={12}/>} />
                           <DataBadge label="Taxa Contratada" value={formatPercentageDisplay(fin.taxa_juros)} icon={<Percent size={12}/>} />
                           <DataBadge label="Amortização" value={`${fin.numero_parcelas}x de ${formatCurrency(fin.valor_parcela)}`} icon={<Calendar size={12}/>} />
                           <DataBadge label="Saldo Devedor Bruto" value={formatCurrency(fin.saldo_devedor_nominal)} color="text-red-400" icon={<Info size={12}/>} />
                        </div>

                        {/* Lista de Itens Detalhada */}
                        {fin.itens?.length > 0 && (
                          <div className="bg-dark-800/40 p-5 rounded-3xl border border-dark-700/50">
                            <p className="text-[9px] font-black text-dark-500 uppercase tracking-widest mb-3 flex items-center gap-2"><Package size={12}/> Itens Vinculados</p>
                            <div className="flex flex-wrap gap-2">
                               {fin.itens.map((it, idx) => (
                                 <span key={idx} className="px-4 py-2 bg-dark-700 rounded-xl text-[11px] font-bold text-dark-200 border border-dark-600">{it.nome}</span>
                               ))}
                            </div>
                          </div>
                        )}

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                          <div className="lg:col-span-2">
                             <TabelaParcelas 
                                parcelas={detalhesFin[fin.id]?.parcelas || []} 
                                financiamentoId={fin.id} 
                                onPagar={async () => {
                                  setDetalhesFin(prev => { const n = {...prev}; delete n[fin.id]; return n; });
                                  const response = await financiamentosAPI.buscar(fin.id);
                                  setDetalhesFin(prev => ({ ...prev, [fin.id]: response.data }));
                                  loadFinanciamentos();
                                }} 
                             />
                          </div>
                          <div className="space-y-6">
                             <div className="bg-green-500/5 p-6 rounded-[2rem] border border-green-500/20">
                                <h4 className="text-[10px] font-black text-green-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2"><DollarSign size={14}/> Economia Potencial</h4>
                                <p className="text-3xl font-black text-green-400 font-mono">{formatCurrency(fin.saldo_devedor_nominal - fin.valor_quitacao_hoje)}</p>
                                <p className="text-[9px] text-green-600 font-bold uppercase mt-1">Desconto aplicado para quitação hoje</p>
                             </div>
                             <CalculadoraNPV financiamentoId={fin.id} />
                             <ValorPresenteCard valorPresente={fin.valor_presente} compact />
                          </div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      )}

      {/* Paginação */}
      {!loading && totalPaginas > 1 && (
        <div className="flex items-center justify-between bg-dark-800 p-6 rounded-[2rem] border border-dark-700 shadow-2xl">
          <p className="text-xs text-dark-500 font-bold uppercase tracking-widest">
            Exibindo <span className="text-white">{financiamentos.length}</span> de <span className="text-white">{totalRecords}</span> registros
          </p>
          <div className="flex gap-3">
            <button disabled={pagina === 1} onClick={() => setPagina(p => p - 1)} className="p-3 bg-dark-700 text-white rounded-xl disabled:opacity-20 hover:bg-primary-500 transition-all shadow-lg"><ChevronLeft size={20}/></button>
            <div className="flex items-center px-6 bg-dark-700 text-white rounded-xl font-black text-sm border border-dark-600 italic">PÁGINA {pagina} / {totalPaginas}</div>
            <button disabled={pagina === totalPaginas} onClick={() => setPagina(p => p + 1)} className="p-3 bg-dark-700 text-white rounded-xl disabled:opacity-20 hover:bg-primary-500 transition-all shadow-lg"><ChevronRight size={20}/></button>
          </div>
        </div>
      )}

      {/* Modal Legado (View Detalhes) - Mantido por segurança */}
      {selectedFinanciamento && !showForm && expandedId !== selectedFinanciamento.id && (
        <Modal isOpen={true} onClose={() => setSelectedFinanciamento(null)} title={`CONTRATO ${selectedFinanciamento.codigo_contrato}`}>
           <div className="space-y-6 max-h-[80vh] overflow-y-auto p-2">
              <div className="grid grid-cols-2 gap-4">
                <DataBadge label="Status" value={selectedFinanciamento.status} />
                <DataBadge label="Valor Total" value={formatCurrency(selectedFinanciamento.valor_total)} />
              </div>
              {selectedFinanciamento.parcelas && (
                <>
                  <TabelaParcelas parcelas={selectedFinanciamento.parcelas} financiamentoId={selectedFinanciamento.id} onPagar={loadFinanciamentos} />
                  <CalculadoraNPV financiamentoId={selectedFinanciamento.id} />
                </>
              )}
           </div>
        </Modal>
      )}
    </div>
  )
}

// Sub-componentes estilizados
function InputGroup({ label, icon, children }) {
  return (
    <div className="space-y-2">
      <label className="flex items-center gap-2 text-[10px] font-black text-dark-500 uppercase tracking-widest ml-2 italic">
        {icon} {label}
      </label>
      {children}
    </div>
  )
}

function DataBadge({ label, value, color = "text-white", icon }) {
  return (
    <div className="bg-dark-900/40 p-4 rounded-2xl border border-dark-700/50 flex flex-col justify-center shadow-inner">
      <p className="text-[8px] font-black text-dark-500 uppercase tracking-widest mb-1 flex items-center gap-1">{icon} {label}</p>
      <p className={`text-xs font-black uppercase ${color}`}>{value}</p>
    </div>
  )
}