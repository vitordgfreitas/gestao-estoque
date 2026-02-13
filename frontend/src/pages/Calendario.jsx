import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, CalendarDays, X, 
  ArrowRight, TrendingUp, DollarSign, Receipt, Info, Tag, LocateFixed
} from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import { formatItemName, formatDate } from '../utils/format'

const formatCurrency = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0)

export default function Calendario() {
  // --- ESTADOS GLOBAIS ---
  const [compromissos, setCompromissos] = useState([])
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [localizacoes, setLocalizacoes] = useState([])
  const [viewMode, setViewMode] = useState('mensal') 
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [loading, setLoading] = useState(true)
  
  // --- NAVEGAÇÃO ---
  const [mesAtual, setMesAtual] = useState(new Date().getMonth() + 1)
  const [anoAtual, setAnoAtual] = useState(new Date().getFullYear())
  const [diaSelecionado, setDiaSelecionado] = useState(new Date())
  const [detalhesDia, setDetalhesDia] = useState(null)
  const [parcelasMes, setParcelasMes] = useState([])

  // Helper de fuso horário local (Brasília)
  const dataToStr = (d) => {
    if (!d) return ''
    const date = d instanceof Date ? d : new Date(d)
    if (isNaN(date.getTime())) return ''
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  }

  useEffect(() => { loadData() }, [])

  // Sincroniza Financeiro (Boletos) do mês visível
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
      comps.forEach(c => { if(c.cidade) locs.add(`${c.cidade} - ${c.uf}`) })
      setLocalizacoes(Array.from(locs).sort())
    } catch (error) {
      toast.error('Erro ao sincronizar dados operacionais.')
    } finally {
      setLoading(false)
    }
  }

  // --- LOGICA DE FILTRAGEM (image_85d57b.png) ---
  const filtrados = useMemo(() => {
    return (compromissos || []).filter(c => {
      const matchCat = categoriaFiltro === 'Todas as Categorias' || 
                       c.compromisso_itens?.some(ci => ci.itens?.categoria === categoriaFiltro)
      const matchLoc = localizacaoFiltro === 'Todas as Localizações' || 
                       `${c.cidade} - ${c.uf}` === localizacaoFiltro
      return matchCat && matchLoc
    })
  }, [compromissos, categoriaFiltro, localizacaoFiltro])

  const getEventosNoDia = (data) => {
    const dStr = dataToStr(data)
    return {
      iniciam: filtrados.filter(c => dataToStr(c.data_inicio) === dStr),
      ativos: filtrados.filter(c => {
        const s = dataToStr(c.data_inicio); const e = dataToStr(c.data_fim)
        return dStr > s && dStr <= e
      }),
      parcelas: (parcelasMes || []).filter(p => dataToStr(p.data_vencimento) === dStr)
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
      {/* 1. HEADER COM DASHBOARD MINI */}
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase italic">Operações Star</h1>
          <p className="text-dark-400 font-medium tracking-widest uppercase text-[10px]">Star Gestão • Brasília Operational Center</p>
        </div>
        
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-2xl">
          <ViewBtn active={viewMode === 'mensal'} icon={<LayoutGrid size={18}/>} label="Mensal" onClick={() => setViewMode('mensal')} />
          <ViewBtn active={viewMode === 'diaria'} icon={<CalendarDays size={18}/>} label="Diária" onClick={() => setViewMode('diaria')} />
        </div>
      </div>

      {/* 2. FILTROS E NAVEGAÇÃO */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-2 flex gap-3">
          <FilterSelect icon={<Filter size={16}/>} value={categoriaFiltro} onChange={setCategoriaFiltro} options={['Todas as Categorias', ...categorias]} />
          <FilterSelect icon={<MapPin size={16}/>} value={localizacaoFiltro} onChange={setLocalizacaoFiltro} options={['Todas as Localizações', ...localizacoes]} />
        </div>
        <div className="lg:col-span-2 flex items-center justify-between bg-dark-800 px-6 rounded-xl border border-dark-700 shadow-lg group">
          <button onClick={() => navegarMes('ant')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400 transition-colors"><ChevronLeft/></button>
          <span className="text-lg font-black text-dark-50 uppercase tracking-widest group-hover:text-primary-400 transition-colors">
            {new Date(anoAtual, mesAtual-1).toLocaleString('pt-BR', { month: 'long', year: 'numeric' })}
          </span>
          <button onClick={() => navegarMes('prox')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400 transition-colors"><ChevronRight/></button>
        </div>
      </div>

      {/* 3. CALENDÁRIO / MODO DIÁRIO */}
      <AnimatePresence mode="wait">
        {viewMode === 'mensal' ? (
          <motion.div key="mensal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-0 overflow-hidden border-dark-700 bg-dark-900/40 backdrop-blur-xl shadow-2xl">
            <div className="grid grid-cols-7 border-b border-dark-700 bg-dark-800/80">
              {['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'].map(d => (
                <div key={d} className="py-4 text-center text-[10px] font-black text-dark-500 uppercase tracking-[0.3em]">{d}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 min-h-[680px]">
              {renderCalendarDays(anoAtual, mesAtual, getEventosNoDia, handleDayClick)}
            </div>
          </motion.div>
        ) : (
          <motion.div key="diaria" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <DailyView data={diaSelecionado} eventos={getEventosNoDia(diaSelecionado)} setDia={setDiaSelecionado} abrirDetalhes={handleDayClick} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 4. MODAL DE DETALHES DE ALTA DENSIDADE */}
      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`OPERACIONAL: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-8 max-h-[75vh] overflow-y-auto pr-3 custom-scrollbar">
            
            {/* SEÇÃO LOGÍSTICA (image_7af074.png) */}
            <Section title="Inventário em Operação" icon={<Package size={14}/>} color="text-primary-500">
              {([...detalhesDia.compromissosInicio, ...detalhesDia.compromissosAtivos]).length > 0 ? (
                ([...detalhesDia.compromissosInicio, ...detalhesDia.compromissosAtivos]).map(c => (
                  <div key={c.id} className="p-6 bg-dark-800 rounded-3xl border border-dark-700 border-l-4 border-l-primary-500 shadow-xl mb-4 hover:border-primary-500/50 transition-all">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <h5 className="font-black text-dark-50 text-lg uppercase leading-tight">{c.nome_contrato}</h5>
                          {dataToStr(c.data_inicio) === dataToStr(detalhesDia.data) && <span className="bg-primary-600 text-[8px] px-2 py-0.5 rounded-full font-black uppercase shadow-lg">Início</span>}
                        </div>
                        <p className="text-primary-400 text-[10px] font-bold uppercase mt-1 tracking-widest">{c.contratante}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-green-400 font-black text-base font-mono">{formatCurrency(c.valor_total_contrato)}</span>
                      </div>
                    </div>

                    <div className="bg-dark-900/50 rounded-2xl p-4 mb-4 border border-dark-700/50">
                      <p className="text-[9px] font-black text-dark-500 uppercase mb-2 flex items-center gap-2"><Tag size={10}/> Detalhamento de Itens</p>
                      <div className="flex flex-wrap gap-2">
                        {c.compromisso_itens?.map(ci => (
                          <span key={ci.id} className="px-3 py-1 bg-dark-700 text-dark-100 rounded-xl text-[10px] font-black border border-dark-600 flex items-center gap-2">
                            <span className="text-primary-500">{ci.quantidade}x</span> {ci.itens?.nome}
                          </span>
                        )) || <span className="text-dark-600 text-xs italic">Nenhum item listado.</span>}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-[10px] text-dark-400 font-bold border-t border-dark-700/50 pt-4">
                      <div className="flex items-center gap-2"><LocateFixed size={12} className="text-primary-500"/> {c.cidade} - {c.uf}</div>
                      <div className="flex items-center gap-2 justify-end"><Clock size={12} className="text-primary-500"/> Termina em {formatDate(c.data_fim)}</div>
                    </div>
                  </div>
                ))
              ) : <EmptyState icon={<Package size={40}/>} text="Nenhuma movimentação para este dia." />}
            </Section>

            {/* SEÇÃO FINANCEIRA (Vencimentos com Links) */}
            <Section title="Controle Financeiro" icon={<DollarSign size={14}/>} color="text-green-500">
              {detalhesDia.parcelas?.length > 0 ? (
                <div className="overflow-hidden rounded-3xl border border-dark-700 shadow-2xl">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px] tracking-widest">
                      <tr>
                        <th className="p-4">Identificação</th>
                        <th className="p-4 text-center">Parcela</th>
                        <th className="p-4 text-right">Valor Original</th>
                        <th className="p-4 text-center">Documentos</th>
                        <th className="p-4 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-800 bg-dark-900/60">
                      {detalhesDia.parcelas.map(p => (
                        <tr key={p.id} className="hover:bg-green-500/5 transition-colors group">
                          <td className="p-4">
                            <div className="font-bold text-dark-50">{p.codigo_contrato || `Fin. #${p.financiamento_id}`}</div>
                          </td>
                          <td className="p-4 text-center font-black text-dark-400">#{p.numero_parcela}</td>
                          <td className="p-4 text-right font-mono text-green-400 font-black text-sm">
                            {formatCurrency(p.valor_original)}
                          </td>
                          <td className="p-4 text-center">
                            <div className="flex justify-center gap-2">
                              {p.link_boleto ? (
                                <a href={p.link_boleto} target="_blank" rel="noreferrer" title="Ver Boleto" className="p-2 bg-dark-700 hover:bg-primary-500/30 text-primary-400 rounded-lg transition-all"><FileText size={16}/></a>
                              ) : <span className="opacity-10"><FileText size={16}/></span>}
                              {p.link_comprovante ? (
                                <a href={p.link_comprovante} target="_blank" rel="noreferrer" title="Ver Comprovante" className="p-2 bg-dark-700 hover:bg-green-500/30 text-green-500 rounded-lg transition-all"><Receipt size={16}/></a>
                              ) : <span className="opacity-10"><Receipt size={16}/></span>}
                            </div>
                          </td>
                          <td className="p-4 text-center">
                            <span className={`px-2.5 py-1 rounded-lg font-black uppercase text-[8px] border shadow-sm ${
                              p.status === 'Paga' ? 'bg-green-500/10 text-green-500 border-green-500/20' : 
                              p.status === 'Atrasada' ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                              'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                            }`}>{p.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : <EmptyState icon={<DollarSign size={40}/>} text="Nenhum vencimento financeiro hoje." />}
            </Section>
          </div>
        </Modal>
      )}
    </div>
  )
}

// --- SUB-COMPONENTES INTERNOS (DEFINIDOS AQUI PARA EVITAR TELA BRANCA) ---

function ViewBtn({ active, icon, label, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black transition-all ${active ? 'bg-primary-500 text-white shadow-xl shadow-primary-500/30' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>
      {icon} {label}
    </button>
  )
}

function StatMini({ label, value, isCurrency, color = "text-dark-50" }) {
  return (
    <div className="bg-dark-800/80 border border-dark-700 px-5 py-3 rounded-2xl min-w-[150px] shadow-lg">
      <p className="text-[9px] font-black uppercase tracking-widest text-dark-500 mb-1">{label}</p>
      <p className={`text-xl font-black ${color}`}>{isCurrency ? formatCurrency(value) : value}</p>
    </div>
  )
}

function FilterSelect({ icon, value, onChange, options }) {
  return (
    <div className="relative flex-1 group">
      <div className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500 group-focus-within:text-primary-500">{icon}</div>
      <select value={value} onChange={e => onChange(e.target.value)} className="input pl-10 h-12 bg-dark-800/50 border-dark-700">
        {(options || []).map(opt => <option key={opt} value={opt}>{opt}</option>)}
      </select>
    </div>
  )
}

function Section({ title, icon, color, children }) {
  return (
    <div className="space-y-4">
      <h4 className={`text-[10px] font-black ${color} uppercase tracking-[0.2em] flex items-center gap-3 border-b border-dark-700 pb-2`}>{icon} {title}</h4>
      {children}
    </div>
  )
}

function EmptyState({ icon, text }) {
  return (
    <div className="py-16 text-center bg-dark-800/30 rounded-[2rem] border border-dashed border-dark-700">
      <div className="text-dark-600 opacity-20 mb-3 flex justify-center">{icon}</div>
      <p className="text-dark-500 text-[10px] font-bold uppercase tracking-widest italic">{text}</p>
    </div>
  )
}

function renderCalendarDays(ano, mes, getEventos, onDayClick) {
  const start = new Date(ano, mes - 1, 1); const end = new Date(ano, mes, 0); const days = []
  let startIdx = start.getDay() === 0 ? 6 : start.getDay() - 1
  for (let i = 0; i < startIdx; i++) days.push(<div key={`blank-${i}`} className="border border-dark-800/20 bg-dark-900/5 opacity-10" />)

  const hojeStr = new Date().toDateString()
  for (let d = 1; d <= end.getDate(); d++) {
    const data = new Date(ano, mes - 1, d); const ev = getEventos(data)
    const isHoje = data.toDateString() === hojeStr
    
    days.push(
      <button key={d} onClick={() => onDayClick(data)} className={`relative p-3 border border-dark-800/40 hover:bg-primary-500/5 transition-all text-left flex flex-col h-full min-h-[115px] overflow-hidden ${isHoje ? 'bg-primary-500/10' : ''}`}>
        <span className={`text-xs font-black mb-2 ${isHoje ? 'text-primary-400 underline decoration-2 underline-offset-4' : 'text-dark-500'}`}>{d < 10 ? `0${d}` : d}</span>
        <div className="space-y-1 w-full">
          {ev.iniciam.slice(0, 1).map(c => <div key={c.id} className="text-[7px] bg-primary-600 text-white font-black px-1.5 py-0.5 rounded truncate uppercase shadow-sm">🚀 {c.nome_contrato}</div>)}
          {ev.ativos.length > 0 && <div className="text-[7px] text-dark-300 font-bold px-1 py-0.5 border border-dark-700 rounded bg-dark-800/80 truncate">⚙️ {ev.ativos.length} Aluguéis</div>}
          {ev.parcelas.length > 0 && <div className="text-[7px] bg-green-500/20 text-green-500 font-black px-1.5 py-0.5 rounded border border-green-500/20 truncate flex items-center gap-1 shadow-inner">💰 {ev.parcelas.length} Venc.</div>}
        </div>
      </button>
    )
  }
  return days
}

function DailyView({ data, eventos, setDia, abrirDetalhes }) {
  const move = (dir) => {
    const next = new Date(data.getTime()); next.setDate(next.getDate() + (dir === 'ant' ? -1 : 1))
    setDia(next)
  }
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between bg-dark-800/80 p-10 rounded-[2.5rem] border border-dark-700 shadow-2xl backdrop-blur-xl">
        <button onClick={() => move('ant')} className="p-4 hover:bg-dark-700 rounded-2xl text-primary-400 transition-all active:scale-90"><ChevronLeft size={32}/></button>
        <div className="text-center">
          <h2 className="text-5xl font-black text-dark-50 uppercase tracking-tighter mb-2">{data.toLocaleDateString('pt-BR', { weekday: 'long' })}</h2>
          <p className="text-primary-500 font-black tracking-[0.4em] uppercase text-sm">{data.toLocaleDateString('pt-BR')}</p>
        </div>
        <button onClick={() => move('prox')} className="p-4 hover:bg-dark-700 rounded-2xl text-primary-400 transition-all active:scale-90"><ChevronRight size={32}/></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <DayCard title="Movimentações Logísticas" icon={<PlayCircle size={20}/>} count={eventos.iniciam.length} color="primary" items={eventos.iniciam} onClick={() => abrirDetalhes(data)} />
        <DayCard title="Faturamento e Boletos" icon={<DollarSign size={20}/>} count={eventos.parcelas.length} color="green" items={eventos.parcelas} onClick={() => abrirDetalhes(data)} />
      </div>
    </div>
  )
}

function DayCard({ title, icon, count, color, items, onClick }) {
  const isPrimary = color === 'primary'
  return (
    <div className={`p-8 rounded-[2rem] border shadow-2xl ${isPrimary ? 'bg-primary-500/[0.03] border-primary-500/20' : 'bg-green-500/[0.03] border-green-500/20'}`}>
      <div className="flex justify-between items-center mb-8">
        <h3 className={`text-[10px] font-black uppercase tracking-[0.3em] flex items-center gap-3 ${isPrimary ? 'text-primary-500' : 'text-green-500'}`}>{icon} {title}</h3>
        <span className={`text-[10px] font-black px-3 py-1 rounded-full text-white ${isPrimary ? 'bg-primary-500' : 'bg-green-500'} shadow-lg`}>{count}</span>
      </div>
      <div className="space-y-4">
        {(items || []).slice(0, 5).map(i => (
          <div key={i.id} onClick={onClick} className="p-6 bg-dark-800 rounded-3xl border border-dark-700 flex justify-between items-center cursor-pointer hover:border-primary-500/40 transition-all group">
            <div>
              <p className="font-black text-dark-50 text-base truncate">{i.nome_contrato || i.codigo_contrato || 'Operação'}</p>
              {i.contratante && <p className="text-[10px] text-dark-500 font-bold uppercase mt-1 tracking-widest">{i.contratante}</p>}
              {i.valor_original && <p className="text-green-400 font-mono text-[11px] font-black mt-1">{formatCurrency(i.valor_original)}</p>}
            </div>
            <ArrowRight size={20} className="text-dark-600 group-hover:text-primary-400 transition-colors"/>
          </div>
        ))}
        {(!items || items.length === 0) && <p className="text-dark-600 text-[10px] uppercase font-bold italic opacity-40 text-center py-10">Agenda livre.</p>}
      </div>
    </div>
  )
}