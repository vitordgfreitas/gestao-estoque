import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, CalendarDays, X, ArrowRight, TrendingUp
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

  // Helper de data imutável para evitar tela branca
  const dataToStr = (d) => {
    if (!d) return ''
    const date = d instanceof Date ? d : new Date(d)
    if (isNaN(date.getTime())) return ''
    return date.toISOString().split('T')[0]
  }

  useEffect(() => { loadData() }, [])

  // Sincroniza Financeiro (Boletos) do mês atual
  useEffect(() => {
    let active = true
    const fetchFinanceiro = async () => {
      try {
        const res = await api.get('/api/parcelas', { 
          params: { mes: mesAtual, ano: anoAtual, incluir_pagas: true } 
        })
        if (active) setParcelasMes(res.data || [])
      } catch (e) {
        if (active) setParcelasMes([])
      }
    }
    fetchFinanceiro()
    return () => { active = false }
  }, [mesAtual, anoAtual])

  const loadData = async () => {
    try {
      setLoading(true)
      const [compRes, itensRes, catRes] = await Promise.all([
        compromissosAPI.listar(),
        itensAPI.listar().catch(() => ({ data: [] })),
        categoriasAPI.listar().catch(() => ({ data: [] }))
      ])
      
      const comps = compRes.data || []
      setCompromissos(comps)
      setItens(itensRes.data || [])
      setCategorias(catRes.data || [])
      
      const locs = new Set()
      comps.forEach(c => { if(c.cidade && c.uf) locs.add(`${c.cidade} - ${c.uf}`) })
      setLocalizacoes(Array.from(locs).sort())
    } catch (error) {
      toast.error('Falha na comunicação com o servidor Railway.')
    } finally {
      setLoading(false)
    }
  }

  // --- ENGINE DE FILTRAGEM (image_85d57b.png) ---
  const filtrados = useMemo(() => {
    return compromissos.filter(c => {
      const matchCat = categoriaFiltro === 'Todas as Categorias' || 
                       c.compromisso_itens?.some(ci => ci.itens?.categoria === categoriaFiltro)
      const matchLoc = localizacaoFiltro === 'Todas as Localizações' || 
                       `${c.cidade} - ${c.uf}` === localizacaoFiltro
      return matchCat && matchLoc
    })
  }, [compromissos, categoriaFiltro, localizacaoFiltro])

  const getEventosNoDia = (data) => {
    const dStr = dataToStr(data)
    if (!dStr) return { iniciam: [], ativos: [], parcelas: [] }

    return {
      iniciam: filtrados.filter(c => dataToStr(c.data_inicio) === dStr),
      ativos: filtrados.filter(c => {
        const s = dataToStr(c.data_inicio)
        const e = dataToStr(c.data_fim)
        return dStr > s && dStr <= e
      }),
      parcelas: parcelasMes.filter(p => dataToStr(p.data_vencimento) === dStr)
    }
  }

  const handleDayClick = (data) => {
    const ev = getEventosNoDia(data)
    setDetalhesDia({
      data: new Date(data),
      compromissosInicio: ev.iniciam || [],
      compromissosAtivos: ev.ativos || [],
      parcelas: ev.parcelas || []
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
          <p className="text-dark-400 font-medium tracking-widest uppercase text-[10px]">Logística e Vencimentos Financeiros</p>
        </div>
        
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-2xl">
          <ViewBtn active={viewMode === 'mensal'} icon={<LayoutGrid size={18}/>} label="Visualização Mensal" onClick={() => setViewMode('mensal')} />
          <ViewBtn active={viewMode === 'diaria'} icon={<CalendarDays size={18}/>} label="Modo Diário" onClick={() => setViewMode('diaria')} />
        </div>
      </div>

      {/* FILTROS E CONTROLES */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-2 flex gap-3">
          <div className="relative flex-1">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500" size={16}/>
            <select value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)} className="input pl-10 h-12 bg-dark-800/50 border-dark-700">
              <option>Todas as Categorias</option>
              {categorias.map(cat => <option key={cat}>{cat}</option>)}
            </select>
          </div>
          <div className="relative flex-1">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500" size={16}/>
            <select value={localizacaoFiltro} onChange={e => setLocalizacaoFiltro(e.target.value)} className="input pl-10 h-12 bg-dark-800/50 border-dark-700">
              <option>Todas as Localizações</option>
              {localizacoes.map(loc => <option key={loc}>{loc}</option>)}
            </select>
          </div>
        </div>

        <div className="lg:col-span-2 flex items-center justify-between bg-dark-800 px-6 rounded-xl border border-dark-700 shadow-lg">
          <button onClick={() => navegarMes('ant')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400 transition-colors"><ChevronLeft/></button>
          <span className="text-lg font-black text-dark-50 uppercase tracking-widest">
            {new Date(anoAtual, mesAtual-1).toLocaleString('pt-BR', { month: 'long', year: 'numeric' })}
          </span>
          <button onClick={() => navegarMes('prox')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400 transition-colors"><ChevronRight/></button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {viewMode === 'mensal' ? (
          <motion.div key="mensal" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="card p-0 overflow-hidden border-dark-700 bg-dark-900/40 backdrop-blur-xl">
            <div className="grid grid-cols-7 border-b border-dark-700 bg-dark-800/80">
              {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map(d => (
                <div key={d} className="py-4 text-center text-[10px] font-black text-dark-500 uppercase tracking-[0.3em]">{d}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 min-h-[650px]">
              {renderCalendarDays(anoAtual, mesAtual, getEventosNoDia, handleDayClick)}
            </div>
          </motion.div>
        ) : (
          <motion.div key="diaria" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <DailyView data={diaSelecionado} eventos={getEventosNoDia(diaSelecionado)} setDia={setDiaSelecionado} abrirDetalhes={handleDayClick} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* MODAL DE DETALHES (O CORE DO NEGÓCIO) */}
      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`Operações: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-8 max-h-[70vh] overflow-y-auto pr-3 custom-scrollbar">
            
            {/* LOGÍSTICA */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-[0.2em] flex items-center gap-2 border-b border-dark-700 pb-2">
                <Package size={14}/> Cronograma de Aluguéis
              </h4>
              {([...(detalhesDia.compromissosInicio || []), ...(detalhesDia.compromissosAtivos || [])]).length > 0 ? (
                ([...(detalhesDia.compromissosInicio || []), ...(detalhesDia.compromissosAtivos || [])]).map(c => (
                  <div key={c.id} className="p-5 bg-dark-800 rounded-3xl border border-dark-700 relative overflow-hidden shadow-lg border-l-4 border-l-primary-500">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h5 className="font-black text-dark-50 text-base uppercase tracking-tight">{c.nome_contrato || `Contrato #${c.id}`}</h5>
                        <p className="text-primary-400 text-[10px] font-bold uppercase mt-1">{c.contratante}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-green-400 font-black text-sm font-mono">{formatCurrency(c.valor_total_contrato)}</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2 mb-4">
                      {c.compromisso_itens?.map(ci => (
                        <span key={ci.id} className="px-2 py-1 bg-dark-700 text-dark-200 rounded-lg text-[10px] font-black border border-dark-600 flex items-center gap-1.5 shadow-sm">
                          <span className="text-primary-500">{ci.quantidade}x</span> {ci.itens?.nome}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-dark-400 font-bold border-t border-dark-700/50 pt-3">
                      <div className="flex items-center gap-1.5"><MapPin size={12} className="text-primary-500"/> {c.cidade} - {c.uf}</div>
                      <div className="flex items-center gap-1.5"><TrendingUp size={12} className="text-primary-500"/> Expira {formatDate(c.data_fim)}</div>
                    </div>
                  </div>
                ))
              ) : <p className="text-dark-600 text-xs italic text-center py-4">Sem movimentações previstas.</p>}
            </div>

            {/* FINANCEIRO */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-black text-green-500 uppercase tracking-[0.2em] flex items-center gap-2 border-b border-dark-700 pb-2">
                <DollarSign size={14}/> Vencimentos de Boletos
              </h4>
              {detalhesDia.parcelas?.length > 0 ? (
                <div className="overflow-hidden rounded-3xl border border-dark-700 shadow-2xl">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px]">
                      <tr><th className="p-4">Contrato</th><th className="p-4 text-right">Valor</th><th className="p-4 text-center">Status</th></tr>
                    </thead>
                    <tbody className="divide-y divide-dark-800 bg-dark-900/50">
                      {detalhesDia.parcelas.map(p => (
                        <tr key={p.id}>
                          <td className="p-4 font-bold text-dark-100">{p.codigo_contrato || `Fin. #${p.financiamento_id}`}</td>
                          <td className="p-4 text-right font-mono text-green-400 font-black">{formatCurrency(p.valor_original)}</td>
                          <td className="p-4 text-center">
                            <span className={`px-2.5 py-1 rounded-lg font-black uppercase text-[8px] border shadow-sm ${p.status === 'Paga' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>{p.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <p className="text-dark-600 text-xs italic text-center py-4">Nenhum vencimento para hoje.</p>}
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

// --- SUB-COMPONENTES AUXILIARES ---

function renderCalendarDays(ano, mes, getEventos, onDayClick) {
  const start = new Date(ano, mes - 1, 1)
  const end = new Date(ano, mes, 0)
  const days = []
  
  // Ajuste para Segunda-feira
  let startIdx = start.getDay() === 0 ? 6 : start.getDay() - 1
  for (let i = 0; i < startIdx; i++) days.push(<div key={`blank-${i}`} className="border border-dark-800/20 bg-dark-900/5 opacity-10" />)

  const hojeStr = new Date().toDateString()

  for (let d = 1; d <= end.getDate(); d++) {
    const data = new Date(ano, mes - 1, d)
    const ev = getEventos(data)
    const isHoje = data.toDateString() === hojeStr
    
    days.push(
      <button key={d} onClick={() => onDayClick(data)} className={`relative p-3 border border-dark-800/40 hover:bg-primary-500/5 transition-all text-left flex flex-col h-full min-h-[110px] ${isHoje ? 'bg-primary-500/10' : ''}`}>
        <span className={`text-xs font-black mb-2 ${isHoje ? 'text-primary-400' : 'text-dark-500'}`}>{d < 10 ? `0${d}` : d}</span>
        <div className="space-y-1 w-full overflow-hidden">
          {ev.iniciam.slice(0, 2).map(c => (
            <div key={c.id} className="text-[7px] bg-primary-600 text-white font-black px-1.5 py-0.5 rounded truncate uppercase">🚀 {c.nome_contrato}</div>
          ))}
          {ev.ativos.length > 0 && <div className="text-[7px] text-dark-300 font-bold px-1 py-0.5 border border-dark-700 rounded bg-dark-800 truncate">⚙️ {ev.ativos.length} Aluguéis</div>}
          {ev.parcelas.length > 0 && <div className="text-[7px] bg-green-500/20 text-green-500 font-black px-1.5 py-0.5 rounded border border-green-500/20 truncate">💰 {ev.parcelas.length} Boletos</div>}
        </div>
        {isHoje && <div className="absolute top-2 right-2 w-1 h-1 bg-primary-500 rounded-full animate-ping"/>}
      </button>
    )
  }
  return days
}

function DailyView({ data, eventos, setDia, abrirDetalhes }) {
  const move = (dir) => {
    const next = new Date(data.getTime())
    next.setDate(data.getDate() + (dir === 'ant' ? -1 : 1))
    setDia(next)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-dark-800/80 p-8 rounded-[2rem] border border-dark-700 shadow-2xl backdrop-blur-xl">
        <button onClick={() => move('ant')} className="p-4 hover:bg-dark-700 rounded-2xl text-primary-400 transition-all"><ChevronLeft size={32}/></button>
        <div className="text-center">
          <h2 className="text-4xl font-black text-dark-50 uppercase tracking-tighter mb-1">{data.toLocaleDateString('pt-BR', { weekday: 'long' })}</h2>
          <p className="text-primary-500 font-black tracking-[0.3em] uppercase text-sm">{data.toLocaleDateString('pt-BR')}</p>
        </div>
        <button onClick={() => move('prox')} className="p-4 hover:bg-dark-700 rounded-2xl text-primary-400 transition-all"><ChevronRight size={32}/></button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <DayCard title="Entregas do Dia" icon={<PlayCircle size={20}/>} count={eventos.iniciam.length} color="primary" items={eventos.iniciam} onClick={() => abrirDetalhes(data)} />
        <DayCard title="Fluxo de Caixa" icon={<DollarSign size={20}/>} count={eventos.parcelas.length} color="green" items={eventos.parcelas} onClick={() => abrirDetalhes(data)} />
      </div>
    </div>
  )
}

function DayCard({ title, icon, count, color, items, onClick }) {
  const isPrimary = color === 'primary'
  return (
    <div className={`card ${isPrimary ? 'bg-primary-500/[0.03] border-primary-500/20' : 'bg-green-500/[0.03] border-green-500/20'} p-8 rounded-[2rem] shadow-xl`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className={`text-[10px] font-black ${isPrimary ? 'text-primary-500' : 'text-green-500'} uppercase tracking-[0.3em] flex items-center gap-3`}>{icon} {title}</h3>
        <span className={`${isPrimary ? 'bg-primary-500' : 'bg-green-500'} text-white text-[10px] font-black px-3 py-1 rounded-full`}>{count}</span>
      </div>
      <div className="space-y-3">
        {items.length > 0 ? items.map(i => (
          <div key={i.id} onClick={onClick} className="p-4 bg-dark-800 rounded-2xl border border-dark-700 flex justify-between items-center cursor-pointer hover:border-primary-500/40 transition-all">
            <p className="font-black text-dark-50 text-sm truncate">{i.nome_contrato || i.codigo_contrato || 'Registro'}</p>
            <ArrowRight size={16} className="text-dark-600"/>
          </div>
        )) : <p className="text-dark-600 text-xs italic opacity-50">Nenhuma atividade.</p>}
      </div>
    </div>
  )
}

function ViewBtn({ active, icon, label, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-xs font-black transition-all ${active ? 'bg-primary-500 text-white shadow-xl' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>
      {icon} {label}
    </button>
  )
}