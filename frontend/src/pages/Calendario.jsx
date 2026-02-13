import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, List, CalendarDays 
} from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import { formatItemName, formatDate } from '../utils/format'

const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0)

export default function Calendario() {
  const [compromissos, setCompromissos] = useState([])
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [localizacoes, setLocalizacoes] = useState([])
  const [viewMode, setViewMode] = useState('mensal')
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [loading, setLoading] = useState(true)
  
  const [mesAtual, setMesAtual] = useState(new Date().getMonth() + 1)
  const [anoAtual, setAnoAtual] = useState(new Date().getFullYear())
  const [diaSelecionado, setDiaSelecionado] = useState(new Date())
  const [detalhesDia, setDetalhesDia] = useState(null)
  const [parcelasMes, setParcelasMes] = useState([])

  const dataToStr = (d) => (d instanceof Date ? d.toISOString().split('T')[0] : (d || '').split('T')[0])

  useEffect(() => { loadData() }, [])

  // Sincroniza parcelas e dados ao mudar o mês
  useEffect(() => {
    let cancelled = false
    const loadMonthlyContext = async () => {
      try {
        const res = await api.get('/api/parcelas', { params: { mes: mesAtual, ano: anoAtual, incluir_pagas: true } })
        if (!cancelled) setParcelasMes(res.data || [])
      } catch (e) {
        if (!cancelled) setParcelasMes([])
      }
    }
    loadMonthlyContext()
    return () => { cancelled = true }
  }, [mesAtual, anoAtual])

  const loadData = async () => {
    try {
      setLoading(true)
      const [compRes, itensRes, catRes] = await Promise.all([
        compromissosAPI.listar(),
        itensAPI.listar().catch(() => ({ data: [] })),
        categoriasAPI.listar().catch(() => ({ data: [] }))
      ])
      setCompromissos(compRes.data || [])
      setItens(itensRes.data || [])
      setCategorias(catRes.data || [])
      
      const locs = new Set()
      compRes.data.forEach(c => { if(c.cidade) locs.add(`${c.cidade} - ${c.uf}`) })
      setLocalizacoes(Array.from(locs).sort())
    } catch (error) {
      toast.error('Erro ao carregar agenda')
    } finally {
      setLoading(false)
    }
  }

  // --- FILTRAGEM INTELIGENTE ---
  const filtrados = useMemo(() => {
    return compromissos.filter(c => {
      const matchCat = categoriaFiltro === 'Todas as Categorias' || 
                       c.compromisso_itens?.some(ci => ci.itens?.categoria === categoriaFiltro)
      const matchLoc = localizacaoFiltro === 'Todas as Localizações' || 
                       `${c.cidade} - ${c.uf}` === localizacaoFiltro
      return matchCat && matchLoc
    })
  }, [compromissos, categoriaFiltro, localizacaoFiltro])

  const getEventosDia = (data) => {
    const dStr = dataToStr(data)
    return {
      iniciam: filtrados.filter(c => dataToStr(c.data_inicio) === dStr),
      ativos: filtrados.filter(c => dStr > dataToStr(c.data_inicio) && dStr <= dataToStr(c.data_fim)),
      parcelas: parcelasMes.filter(p => dataToStr(p.data_vencimento) === dStr)
    }
  }

  const abrirDetalhes = (data) => {
    const ev = getEventosDia(data)
    setDetalhesDia({
      data,
      compromissosInicio: ev.iniciam,
      compromissosAtivos: ev.ativos,
      parcelas: ev.parcelas
    })
  }

  const navegarMes = (dir) => {
    if (dir === 'ant') {
      if (mesAtual === 1) { setMesAtual(12); setAnoAtual(anoAtual - 1) }
      else setMesAtual(mesAtual - 1)
    } else {
      if (mesAtual === 12) { setMesAtual(1); setAnoAtual(anoAtual + 1) }
      else setMesAtual(mesAtual + 1)
    }
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto px-4 pb-10">
      {/* HEADER DINÂMICO */}
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase">Agenda de Operações</h1>
          <p className="text-dark-400 font-medium tracking-widest uppercase text-[10px]">Star Gestão • Logística & Vencimentos</p>
        </div>
        
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-inner">
          <ViewBtn active={viewMode === 'mensal'} icon={<LayoutGrid size={18}/>} label="Mês" onClick={() => setViewMode('mensal')} />
          <ViewBtn active={viewMode === 'diaria'} icon={<CalendarDays size={18}/>} label="Dia" onClick={() => setViewMode('diaria')} />
        </div>
      </div>

      {/* FILTROS E NAVEGAÇÃO */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-2 flex gap-3">
          <div className="relative flex-1 group">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500 group-focus-within:text-primary-500" size={16}/>
            <select value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)} className="input pl-10 h-12 bg-dark-800/50 border-dark-700">
              <option>Todas as Categorias</option>
              {categorias.map(cat => <option key={cat}>{cat}</option>)}
            </select>
          </div>
          <div className="relative flex-1 group">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500 group-focus-within:text-primary-500" size={16}/>
            <select value={localizacaoFiltro} onChange={e => setLocalizacaoFiltro(e.target.value)} className="input pl-10 h-12 bg-dark-800/50 border-dark-700">
              <option>Todas as Localizações</option>
              {localizacoes.map(loc => <option key={loc}>{loc}</option>)}
            </select>
          </div>
        </div>

        <div className="lg:col-span-2 flex items-center justify-between bg-dark-800 px-4 rounded-xl border border-dark-700">
          <button onClick={() => navegarMes('ant')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><ChevronLeft/></button>
          <span className="text-lg font-black text-dark-50 uppercase tracking-widest">
            {new Date(anoAtual, mesAtual-1).toLocaleString('pt-BR', { month: 'long', year: 'numeric' })}
          </span>
          <button onClick={() => navegarMes('prox')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><ChevronRight/></button>
        </div>
      </div>

      {/* CALENDÁRIO MENSAL */}
      <AnimatePresence mode="wait">
        {viewMode === 'mensal' ? (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="card p-0 overflow-hidden border-dark-700 shadow-2xl">
            <div className="grid grid-cols-7 border-b border-dark-700 bg-dark-800/80">
              {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map(d => (
                <div key={d} className="py-3 text-center text-[10px] font-black text-dark-400 uppercase tracking-[0.2em]">{d}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 min-h-[600px] bg-dark-900/20">
              {renderDays(anoAtual, mesAtual, getEventosDia, abrirDetalhes)}
            </div>
          </motion.div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <DailyView data={diaSelecionado} eventos={getEventosDia(diaSelecionado)} setDia={setDiaSelecionado} abrirDetalhes={abrirDetalhes} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* MODAL DE DETALHES (O CORE DA GESTÃO) */}
      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`Logística: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-6 max-h-[75vh] overflow-y-auto pr-2">
            
            {/* SEÇÃO LOGÍSTICA */}
            <div className="space-y-3">
              <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-widest flex items-center gap-2 border-b border-dark-700 pb-2">
                <Package size={14}/> Movimentações e Aluguéis
              </h4>
              {detalhesDia.compromissosInicio.concat(detalhesDia.compromissosAtivos).length > 0 ? (
                detalhesDia.compromissosInicio.concat(detalhesDia.compromissosAtivos).map(c => (
                  <div key={c.id} className="p-4 bg-dark-800 rounded-2xl border border-dark-700 relative overflow-hidden group">
                    {dataToStr(c.data_inicio) === dataToStr(detalhesDia.data) && (
                      <div className="absolute top-0 right-0 bg-primary-600 text-white text-[8px] font-black px-3 py-1 rounded-bl-xl uppercase">Início do Contrato</div>
                    )}
                    <h5 className="font-black text-dark-50 text-base mb-1">{c.nome_contrato}</h5>
                    <p className="text-dark-400 text-xs font-bold mb-3 uppercase tracking-tighter">{c.contratante}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {c.compromisso_itens?.map(ci => (
                        <span key={ci.id} className="px-2 py-0.5 bg-dark-700 text-primary-400 rounded text-[10px] font-black border border-primary-500/20">
                          {ci.quantidade}x {ci.itens?.nome}
                        </span>
                      ))}
                    </div>
                  </div>
                ))
              ) : <p className="text-dark-500 text-xs italic">Sem aluguéis ativos para este dia.</p>}
            </div>

            {/* SEÇÃO FINANCEIRA (Vencimentos) */}
            <div className="space-y-3">
              <h4 className="text-[10px] font-black text-green-500 uppercase tracking-widest flex items-center gap-2 border-b border-dark-700 pb-2">
                <DollarSign size={14}/> Vencimentos e Boletos
              </h4>
              {detalhesDia.parcelas.length > 0 ? (
                <div className="overflow-hidden rounded-2xl border border-dark-700">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px]">
                      <tr><th className="p-3">Contrato</th><th className="p-3">Valor</th><th className="p-3">Status</th></tr>
                    </thead>
                    <tbody className="divide-y divide-dark-800 bg-dark-900/50">
                      {detalhesDia.parcelas.map(p => (
                        <tr key={p.id}>
                          <td className="p-3 font-bold text-dark-100">{p.codigo_contrato || `Fin. #${p.financiamento_id}`}</td>
                          <td className="p-3 font-mono text-green-400 font-black">{formatCurrency(p.valor_original)}</td>
                          <td className="p-3">
                            <span className={`px-2 py-0.5 rounded-full font-black uppercase text-[8px] border ${p.status === 'Paga' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                              {p.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <p className="text-dark-500 text-xs italic">Nenhum vencimento para este dia.</p>}
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

// --- HELPERS E COMPONENTES AUXILIARES ---

function renderDays(ano, mes, getEventos, abrir) {
  const start = new Date(ano, mes - 1, 1)
  const end = new Date(ano, mes, 0)
  const days = []
  
  // Ajuste para começar na segunda-feira
  let firstDayIdx = start.getDay() === 0 ? 6 : start.getDay() - 1
  for (let i = 0; i < firstDayIdx; i++) days.push(<div key={`empty-${i}`} className="border border-dark-800/30 opacity-20" />)

  for (let d = 1; d <= end.getDate(); d++) {
    const data = new Date(ano, mes - 1, d)
    const ev = getEventos(data)
    const isHoje = data.toDateString() === new Date().toDateString()
    
    days.push(
      <button 
        key={d} 
        onClick={() => abrir(data)}
        className={`group relative p-2 border border-dark-800/50 hover:bg-primary-500/5 transition-all text-left flex flex-col h-full min-h-[100px] ${isHoje ? 'bg-primary-500/10' : ''}`}
      >
        <span className={`text-xs font-black ${isHoje ? 'text-primary-400 underline decoration-2 underline-offset-4' : 'text-dark-400 group-hover:text-dark-50'}`}>{d}</span>
        
        <div className="mt-2 space-y-1 overflow-hidden">
          {ev.iniciam.map(c => (
            <div key={c.id} className="text-[8px] bg-primary-500 text-white font-black px-1.5 py-0.5 rounded truncate uppercase shadow-sm">
              🚀 {c.nome_contrato}
            </div>
          ))}
          {ev.ativos.length > 0 && (
            <div className="text-[8px] text-dark-500 font-bold px-1 py-0.5 border border-dark-700 rounded bg-dark-800 truncate">
              ⚙️ {ev.ativos.length} Alugueis ativos
            </div>
          )}
          {ev.parcelas.length > 0 && (
            <div className="text-[8px] bg-green-500/20 text-green-500 font-black px-1.5 py-0.5 rounded truncate uppercase border border-green-500/20">
              💰 {ev.parcelas.length} Boleto(s)
            </div>
          )}
        </div>
      </button>
    )
  }
  return days
}

function StatMini({ label, value, isCurrency, color = "text-dark-50" }) {
  return (
    <div className="bg-dark-800/80 border border-dark-700 px-6 py-4 rounded-3xl min-w-[170px] shadow-xl">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-dark-500 mb-2">{label}</p>
      <p className={`text-2xl font-black ${color}`}>
        {isCurrency ? formatCurrency(value).replace('R$', 'R$ ') : value}
      </p>
    </div>
  )
}

function ViewBtn({ active, icon, label, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-black transition-all ${active ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>
      {icon} {label}
    </button>
  )
}

function TabItem({ active, label, count, icon, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-6 py-3.5 rounded-xl font-black text-sm transition-all ${active ? 'bg-primary-500 text-white shadow-lg' : 'text-dark-400 hover:text-dark-100'}`}>
      {icon} {label} <span className="text-[10px] bg-dark-700/50 px-2 py-0.5 rounded-full font-bold">{count}</span>
    </button>
  )
}

function DailyView({ data, eventos, setDia, abrirDetalhes }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-dark-800 p-6 rounded-3xl border border-dark-700 shadow-xl">
        <button onClick={() => setDia(new Date(data.setDate(data.getDate() - 1)))} className="p-3 hover:bg-dark-700 rounded-2xl text-primary-400 transition-colors"><ChevronLeft size={24}/></button>
        <div className="text-center">
          <h2 className="text-3xl font-black text-dark-50 uppercase tracking-tighter">{data.toLocaleDateString('pt-BR', { weekday: 'long' })}</h2>
          <p className="text-primary-500 font-bold tracking-widest uppercase text-xs">{formatDate(data.toISOString().split('T')[0])}</p>
        </div>
        <button onClick={() => setDia(new Date(data.setDate(data.getDate() + 1)))} className="p-3 hover:bg-dark-700 rounded-2xl text-primary-400 transition-colors"><ChevronRight size={24}/></button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card bg-primary-500/5 border-primary-500/20">
          <h3 className="text-[10px] font-black text-primary-500 uppercase tracking-widest mb-4 flex items-center gap-2"><PlayCircle size={16}/> Começando hoje</h3>
          {eventos.iniciam.length > 0 ? eventos.iniciam.map(c => (
            <div key={c.id} className="p-4 bg-dark-800 rounded-2xl border border-dark-700 mb-3">
              <p className="font-black text-dark-50">{c.nome_contrato}</p>
              <p className="text-[10px] text-dark-500 font-bold uppercase">{c.contratante}</p>
            </div>
          )) : <p className="text-dark-600 text-xs italic">Nenhuma entrega programada.</p>}
        </div>

        <div className="card bg-green-500/5 border-green-500/20">
          <h3 className="text-[10px] font-black text-green-500 uppercase tracking-widest mb-4 flex items-center gap-2"><DollarSign size={16}/> Financeiro do dia</h3>
          {eventos.parcelas.length > 0 ? eventos.parcelas.map(p => (
            <div key={p.id} className="p-4 bg-dark-800 rounded-2xl border border-dark-700 mb-3 flex justify-between items-center">
              <div>
                <p className="font-black text-dark-50">{p.codigo_contrato || `Fin. #${p.financiamento_id}`}</p>
                <p className="text-[10px] text-dark-500 font-bold uppercase">{p.status}</p>
              </div>
              <p className="text-green-400 font-black">{formatCurrency(p.valor_original)}</p>
            </div>
          )) : <p className="text-dark-600 text-xs italic">Nenhum boleto vencendo hoje.</p>}
        </div>
      </div>
    </div>
  )
}