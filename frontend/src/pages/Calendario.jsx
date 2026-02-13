import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, CalendarDays, X, 
  ArrowRight, TrendingUp, DollarSign, Receipt, Info, Tag, AlignLeft, Check
} from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import { formatItemName, formatDate, formatCurrency } from '../utils/format'

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

  // Função para tratar data sem erro de fuso horário
  const dataToStr = (d) => {
    if (!d) return ''
    const date = d instanceof Date ? d : new Date(d)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  useEffect(() => { loadData() }, [])

  // Sincroniza Financeiro do mês atual
  useEffect(() => {
    let active = true
    const fetchFinanceiro = async () => {
      try {
        const res = await api.get('/api/parcelas', { 
          params: { mes: mesAtual, ano: anoAtual, incluir_pagas: true } 
        })
        if (active) setParcelasMes(res.data || [])
      } catch (e) { if (active) setParcelasMes([]) }
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
      toast.error('Erro de conexão operacional.')
    } finally { setLoading(false) }
  }

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

  const abrirDetalhesDia = (data) => {
    const ev = getEventosNoDia(data)
    setDetalhesDia({
      data: new Date(data),
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
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase italic">Agenda de Operações</h1>
          <p className="text-dark-400 font-medium tracking-widest uppercase text-[10px]">Star Gestão • Logística & Financeiro Integrado</p>
        </div>
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-2xl">
          <ViewBtn active={viewMode === 'mensal'} icon={<LayoutGrid size={18}/>} label="Mensal" onClick={() => setViewMode('mensal')} />
          <ViewBtn active={viewMode === 'diaria'} icon={<CalendarDays size={18}/>} label="Diária" onClick={() => setViewMode('diaria')} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-2 flex gap-3">
          <FilterSelect icon={<Filter size={16}/>} value={categoriaFiltro} onChange={setCategoriaFiltro} options={['Todas as Categorias', ...categorias]} />
          <FilterSelect icon={<MapPin size={16}/>} value={localizacaoFiltro} onChange={setLocalizacaoFiltro} options={['Todas as Localizações', ...localizacoes]} />
        </div>
        <div className="lg:col-span-2 flex items-center justify-between bg-dark-800 px-6 rounded-xl border border-dark-700 shadow-lg">
          <button onClick={() => navegarMes('ant')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><ChevronLeft/></button>
          <span className="text-lg font-black text-dark-50 uppercase tracking-widest">{new Date(anoAtual, mesAtual-1).toLocaleString('pt-BR', { month: 'long', year: 'numeric' })}</span>
          <button onClick={() => navegarMes('prox')} className="p-2 hover:bg-dark-700 rounded-lg text-primary-400"><ChevronRight/></button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        {viewMode === 'mensal' ? (
          <motion.div key="mensal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-0 overflow-hidden border-dark-700 bg-dark-900/40 backdrop-blur-xl shadow-2xl">
            <div className="grid grid-cols-7 border-b border-dark-700 bg-dark-800/80">
              {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map(d => <div key={d} className="py-4 text-center text-[10px] font-black text-dark-500 uppercase tracking-[0.3em]">{d}</div>)}
            </div>
            <div className="grid grid-cols-7 min-h-[650px]">{renderCalendarDays(anoAtual, mesAtual, getEventosNoDia, abrirDetalhesDia)}</div>
          </motion.div>
        ) : (
          <DailyView data={diaSelecionado} eventos={getEventosNoDia(diaSelecionado)} setDia={setDiaSelecionado} abrirDetalhes={abrirDetalhesDia} />
        )}
      </AnimatePresence>

      {/* MODAL RIQUÍSSIMO EM INFORMAÇÃO (BASEADO NA image_89ed8e.png) */}
      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`RELATÓRIO OPERACIONAL: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-8 max-h-[80vh] overflow-y-auto pr-3 custom-scrollbar">
            
            {/* SEÇÃO LOGÍSTICA DETALHADA */}
            <Section title="Logística e Entregas" icon={<Package size={16}/>} color="text-primary-500">
              {([...detalhesDia.compromissosInicio, ...detalhesDia.compromissosAtivos]).length > 0 ? (
                ([...detalhesDia.compromissosInicio, ...detalhesDia.compromissosAtivos]).map(c => (
                  <div key={c.id} className="p-6 bg-dark-800 rounded-[2rem] border border-dark-700 shadow-2xl relative overflow-hidden border-l-4 border-l-primary-500 mb-6">
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <h5 className="font-black text-dark-50 text-xl uppercase tracking-tight">{c.nome_contrato}</h5>
                        <p className="text-primary-400 text-[10px] font-bold uppercase mt-1 tracking-widest">{c.contratante}</p>
                      </div>
                      <span className="text-green-400 font-black text-lg font-mono">{formatCurrency(c.valor_total_contrato)}</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                       <InfoBox icon={<AlignLeft size={14}/>} label="Descrição do Contrato" value={c.descricao || 'Sem observações.'} />
                       <InfoBox icon={<MapPin size={14}/>} label="Endereço da Operação" value={`${c.endereco || 'Brasília'} - ${c.cidade}/${c.uf}`} />
                    </div>

                    <div className="bg-dark-900/60 p-5 rounded-2xl border border-dark-700/50">
                      <p className="text-[9px] font-black text-dark-500 uppercase mb-3 flex items-center gap-2"><Tag size={12}/> Equipamentos Vinculados</p>
                      <div className="flex flex-wrap gap-2">
                        {c.compromisso_itens?.map(ci => (
                          <span key={ci.id} className="px-3 py-1.5 bg-dark-700 text-dark-50 rounded-xl text-[11px] font-black border border-dark-600 flex items-center gap-2 shadow-inner">
                            <span className="text-primary-500 bg-primary-500/10 px-1.5 rounded-md">{ci.quantidade}x</span> {ci.itens?.nome}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-dark-400 font-bold mt-6 pt-4 border-t border-dark-700/30">
                      <span>🚀 Início: {formatDate(c.data_inicio)}</span>
                      <span>🏁 Término: {formatDate(c.data_fim)}</span>
                    </div>
                  </div>
                ))
              ) : <EmptyState icon={<Package size={40}/>} text="Nenhuma movimentação para hoje." />}
            </Section>

            {/* SEÇÃO FINANCEIRA (VENCIMENTOS) */}
            <Section title="Vencimentos Financeiros" icon={<DollarSign size={16}/>} color="text-green-500">
               {detalhesDia.parcelas?.length > 0 ? (
                 <div className="overflow-hidden rounded-[2rem] border border-dark-700 shadow-2xl bg-dark-900/20">
                   <table className="w-full text-xs text-left border-collapse">
                     <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px] tracking-widest">
                       <tr>
                         <th className="p-5">Contrato / Parcela</th>
                         <th className="p-5 text-right">Valor Original</th>
                         <th className="p-5 text-right">Valor Pago</th>
                         <th className="p-5 text-center">Ações</th>
                         <th className="p-5 text-center">Status</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-dark-800">
                       {detalhesDia.parcelas.map(p => {
                         const StatusIcon = p.status === 'Paga' ? CheckCircle : p.status === 'Atrasada' ? AlertCircle : Clock
                         const statusColor = p.status === 'Paga' ? 'text-green-400' : p.status === 'Atrasada' ? 'text-red-400' : 'text-yellow-400'
                         return (
                           <tr key={p.id} className="hover:bg-green-500/5 transition-colors group">
                             <td className="p-5">
                               <div className="font-black text-dark-50 text-sm uppercase">{p.codigo_contrato || 'Financiamento'}</div>
                               <div className="text-[9px] text-dark-500 font-black mt-1 uppercase">Parcela nº {p.numero_parcela}</div>
                             </td>
                             <td className="p-5 text-right font-mono text-dark-50 font-black">{formatCurrency(p.valor_original)}</td>
                             <td className="p-5 text-right font-mono text-green-400 font-black">{p.valor_pago > 0 ? formatCurrency(p.valor_pago) : '—'}</td>
                             <td className="p-5">
                                <div className="flex justify-center gap-2">
                                  {p.link_boleto && <a href={p.link_boleto} target="_blank" rel="noreferrer" className="p-2 bg-dark-700 text-primary-400 rounded-xl hover:bg-primary-500/30 transition-all shadow-lg"><FileText size={18}/></a>}
                                  {p.link_comprovante && <a href={p.link_comprovante} target="_blank" rel="noreferrer" className="p-2 bg-dark-700 text-green-400 rounded-xl hover:bg-green-500/30 transition-all shadow-lg"><Receipt size={18}/></a>}
                                </div>
                             </td>
                             <td className="p-5 text-center">
                               <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full font-black uppercase text-[8px] border shadow-sm ${statusColor} border-current/20 bg-current/5`}>
                                 <StatusIcon size={12} /> {p.status}
                               </span>
                             </td>
                           </tr>
                         )
                       })}
                     </tbody>
                   </table>
                 </div>
               ) : <EmptyState icon={<DollarSign size={40}/>} text="Caixa livre para hoje." />}
            </Section>
          </div>
        </Modal>
      )}
    </div>
  )
}

// --- SUB-COMPONENTES AUXILIARES ---

function ViewBtn({ active, icon, label, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-6 py-3 rounded-xl text-xs font-black transition-all ${active ? 'bg-primary-500 text-white shadow-xl' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'}`}>{icon} {label}</button>
  )
}

function FilterSelect({ icon, value, onChange, options }) {
  return (
    <div className="relative flex-1 group">
      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-dark-500 group-focus-within:text-primary-500">{icon}</div>
      <select value={value} onChange={e => onChange(e.target.value)} className="input pl-12 h-14 bg-dark-800/50 border-dark-700 rounded-2xl shadow-inner">
        {(options || []).map(opt => <option key={opt} value={opt}>{opt}</option>)}
      </select>
    </div>
  )
}

function Section({ title, icon, color, children }) {
  return (
    <div className="space-y-5">
      <h4 className={`text-[11px] font-black ${color} uppercase tracking-[0.3em] flex items-center gap-3 border-b border-dark-700 pb-3`}>{icon} {title}</h4>
      {children}
    </div>
  )
}

function InfoBox({ icon, label, value }) {
  return (
    <div className="bg-dark-900/40 p-4 rounded-2xl border border-dark-700/50 h-full shadow-inner">
      <p className="text-[9px] font-black text-dark-500 uppercase mb-2 flex items-center gap-2">{icon} {label}</p>
      <p className="text-xs text-dark-200 leading-relaxed font-medium">{value}</p>
    </div>
  )
}

function EmptyState({ icon, text }) {
  return (
    <div className="py-20 text-center bg-dark-800/30 rounded-[3rem] border border-dashed border-dark-700">
      <div className="text-dark-600 opacity-20 mb-4 flex justify-center">{icon}</div>
      <p className="text-dark-500 text-[11px] font-bold uppercase tracking-widest italic">{text}</p>
    </div>
  )
}

function renderCalendarDays(ano, mes, getEventos, onDayClick) {
  const start = new Date(ano, mes - 1, 1); const end = new Date(ano, mes, 0); const days = []
  let startIdx = start.getDay() === 0 ? 6 : start.getDay() - 1
  for (let i = 0; i < startIdx; i++) days.push(<div key={`blank-${i}`} className="border border-dark-800/10 bg-dark-900/5 opacity-10" />)

  const hojeStr = new Date().toDateString()
  for (let d = 1; d <= end.getDate(); d++) {
    const data = new Date(ano, mes - 1, d); const ev = getEventos(data); const isHoje = data.toDateString() === hojeStr
    days.push(
      <button key={d} onClick={() => onDayClick(data)} className={`relative p-3 border border-dark-800/40 hover:bg-primary-500/5 transition-all text-left flex flex-col h-full min-h-[120px] overflow-hidden ${isHoje ? 'bg-primary-500/10 ring-1 ring-primary-500/30' : ''}`}>
        <span className={`text-xs font-black mb-2 ${isHoje ? 'text-primary-400 underline decoration-2' : 'text-dark-500'}`}>{d < 10 ? `0${d}` : d}</span>
        <div className="space-y-1.5 w-full">
          {ev.iniciam.slice(0, 1).map(c => <div key={c.id} className="text-[7px] bg-primary-600 text-white font-black px-2 py-0.5 rounded truncate uppercase shadow-lg">🚀 {c.nome_contrato}</div>)}
          {ev.ativos.length > 0 && <div className="text-[7px] text-dark-300 font-bold px-1.5 py-0.5 border border-dark-700 rounded bg-dark-800/90 truncate flex items-center gap-1"><Package size={8}/> {ev.ativos.length} Ativos</div>}
          {ev.parcelas.length > 0 && <div className="text-[7px] bg-green-500/20 text-green-500 font-black px-1.5 py-0.5 rounded border border-green-500/20 truncate flex items-center gap-1">💰 Vencimentos</div>}
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
    <div className="space-y-8">
      <div className="flex items-center justify-between bg-dark-800/80 p-12 rounded-[3rem] border border-dark-700 shadow-2xl backdrop-blur-2xl">
        <button onClick={() => move('ant')} className="p-5 hover:bg-dark-700 rounded-[2rem] text-primary-400 transition-all active:scale-90"><ChevronLeft size={40}/></button>
        <div className="text-center">
          <h2 className="text-6xl font-black text-dark-50 uppercase tracking-tighter mb-2 italic">{data.toLocaleDateString('pt-BR', { weekday: 'long' })}</h2>
          <p className="text-primary-500 font-black tracking-[0.5em] uppercase text-base">{data.toLocaleDateString('pt-BR')}</p>
        </div>
        <button onClick={() => move('prox')} className="p-5 hover:bg-dark-700 rounded-[2rem] text-primary-400 transition-all active:scale-90"><ChevronRight size={40}/></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
        <DayCard title="Cronograma Logístico" icon={<PlayCircle size={24}/>} count={eventos.iniciam.length} color="primary" items={eventos.iniciam} onClick={() => abrirDetalhes(data)} />
        <DayCard title="Compromissos Financeiros" icon={<DollarSign size={24}/>} count={eventos.parcelas.length} color="green" items={eventos.parcelas} onClick={() => abrirDetalhes(data)} />
      </div>
    </div>
  )
}

function DayCard({ title, icon, count, color, items, onClick }) {
  const isPrimary = color === 'primary'
  return (
    <div className={`p-10 rounded-[3rem] border shadow-2xl ${isPrimary ? 'bg-primary-500/[0.04] border-primary-500/20' : 'bg-green-500/[0.04] border-green-500/20'}`}>
      <div className="flex justify-between items-center mb-10">
        <h3 className={`text-[12px] font-black uppercase tracking-[0.4em] flex items-center gap-4 ${isPrimary ? 'text-primary-500' : 'text-green-500'}`}>{icon} {title}</h3>
        <span className={`text-xs font-black px-4 py-1.5 rounded-full text-white ${isPrimary ? 'bg-primary-500' : 'bg-green-500'} shadow-xl`}>{count}</span>
      </div>
      <div className="space-y-4">
        {(items || []).slice(0, 6).map(i => (
          <div key={i.id} onClick={onClick} className="p-6 bg-dark-800 rounded-[2rem] border border-dark-700 flex justify-between items-center cursor-pointer hover:border-primary-500/40 transition-all group shadow-lg">
            <div>
              <p className="font-black text-dark-50 text-base truncate">{i.nome_contrato || i.codigo_contrato || 'Operação'}</p>
              {i.contratante && <p className="text-[11px] text-dark-500 font-bold uppercase mt-1 tracking-widest italic">{i.contratante}</p>}
              {i.valor_original && <p className="text-green-400 font-mono text-xs font-black mt-2">{formatCurrency(i.valor_original)}</p>}
            </div>
            <div className="p-3 bg-dark-900 rounded-2xl group-hover:bg-primary-500 transition-colors"><ArrowRight size={20} className="text-dark-400 group-hover:text-white"/></div>
          </div>
        ))}
        {(!items || items.length === 0) && <p className="text-dark-600 text-[11px] font-black uppercase tracking-widest italic opacity-40 text-center py-12">Agenda livre.</p>}
      </div>
    </div>
  )
}