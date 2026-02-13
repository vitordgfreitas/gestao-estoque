import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, CalendarDays, X, ArrowRight
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
  const [viewMode, setViewMode] = useState('mensal') // mensal ou diaria
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [loading, setLoading] = useState(true)
  
  const [mesAtual, setMesAtual] = useState(new Date().getMonth() + 1)
  const [anoAtual, setAnoAtual] = useState(new Date().getFullYear())
  const [diaSelecionado, setDiaSelecionado] = useState(new Date())
  const [detalhesDia, setDetalhesDia] = useState(null)
  const [parcelasMes, setParcelasMes] = useState([])

  // Função utilitária blindada contra nulos
  const dataToStr = (d) => {
    if (!d) return ''
    if (d instanceof Date) return d.toISOString().split('T')[0]
    return String(d).split('T')[0]
  }

  useEffect(() => { loadData() }, [])

  // Sincroniza parcelas do mês para exibir contadores no grid
  useEffect(() => {
    let cancelled = false
    const loadFinanceiro = async () => {
      try {
        const res = await api.get('/api/parcelas', { 
          params: { mes: mesAtual, ano: anoAtual, incluir_pagas: true } 
        })
        if (!cancelled) setParcelasMes(res.data || [])
      } catch (e) {
        if (!cancelled) setParcelasMes([])
      }
    }
    loadFinanceiro()
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
      
      const dataComps = compRes.data || []
      setCompromissos(dataComps)
      setItens(itensRes.data || [])
      setCategorias(catRes.data || [])
      
      // Extrai localizações únicas para o filtro
      const locs = new Set()
      dataComps.forEach(c => {
        if(c.cidade && c.uf) locs.add(`${c.cidade} - ${c.uf}`)
      })
      setLocalizacoes(Array.from(locs).sort())
    } catch (error) {
      toast.error('Erro ao sincronizar agenda')
    } finally {
      setLoading(false)
    }
  }

  // --- FILTRAGEM ---
  const filtrados = useMemo(() => {
    return compromissos.filter(c => {
      const matchCat = categoriaFiltro === 'Todas as Categorias' || 
                       c.compromisso_itens?.some(ci => ci.itens?.categoria === categoriaFiltro)
      const matchLoc = localizacaoFiltro === 'Todas as Localizações' || 
                       `${c.cidade} - ${c.uf}` === localizacaoFiltro
      return matchCat && matchLoc
    })
  }, [compromissos, categoriaFiltro, localizacaoFiltro])

  // --- LÓGICA DE EVENTOS POR DIA ---
  const getEventosDia = (data) => {
    const dStr = dataToStr(data)
    return {
      iniciam: filtrados.filter(c => dataToStr(c.data_inicio) === dStr),
      // Compromissos que estão acontecendo mas não começaram hoje
      ativos: filtrados.filter(c => {
        const start = dataToStr(c.data_inicio)
        const end = dataToStr(c.data_fim)
        return dStr > start && dStr <= end
      }),
      parcelas: parcelasMes.filter(p => dataToStr(p.data_vencimento) === dStr)
    }
  }

  const handleAbrirDetalhes = (data) => {
    try {
      const ev = getEventosDia(data)
      setDetalhesDia({
        data,
        compromissosInicio: ev.iniciam || [],
        compromissosAtivos: ev.ativos || [],
        parcelas: ev.parcelas || []
      })
    } catch (e) {
      console.error("Erro ao processar detalhes do dia:", e)
      toast.error("Erro ao carregar eventos deste dia")
    }
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
      {/* HEADER */}
      <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-end">
        <div>
          <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase">Agenda Mestre</h1>
          <p className="text-dark-400 font-medium tracking-widest uppercase text-[10px]">Star Gestão • Operação Integrada • Brasília, DF</p>
        </div>
        
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-inner">
          <ViewBtn active={viewMode === 'mensal'} icon={<LayoutGrid size={18}/>} label="Mensal" onClick={() => setViewMode('mensal')} />
          <ViewBtn active={viewMode === 'diaria'} icon={<CalendarDays size={18}/>} label="Diária" onClick={() => setViewMode('diaria')} />
        </div>
      </div>

      {/* BARRA DE FILTROS */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-2 flex gap-3">
          <div className="relative flex-1 group">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500" size={16}/>
            <select value={categoriaFiltro} onChange={e => setCategoriaFiltro(e.target.value)} className="input pl-10 h-12 bg-dark-800/50 border-dark-700">
              <option>Todas as Categorias</option>
              {categorias.map(cat => <option key={cat}>{cat}</option>)}
            </select>
          </div>
          <div className="relative flex-1 group">
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

      {/* ÁREA DO CALENDÁRIO */}
      <AnimatePresence mode="wait">
        {viewMode === 'mensal' ? (
          <motion.div key="mensal" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="card p-0 overflow-hidden border-dark-700 bg-dark-900/40 shadow-2xl">
            <div className="grid grid-cols-7 border-b border-dark-700 bg-dark-800/80">
              {['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'].map(d => (
                <div key={d} className="py-4 text-center text-[10px] font-black text-dark-500 uppercase tracking-[0.2em]">{d}</div>
              ))}
            </div>
            <div className="grid grid-cols-7 min-h-[650px] bg-dark-900/10">
              {renderGridDays(anoAtual, mesAtual, getEventosDia, handleAbrirDetalhes)}
            </div>
          </motion.div>
        ) : (
          <motion.div key="diaria" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
            <DailyView data={diaSelecionado} eventos={getEventosDia(diaSelecionado)} setDia={setDiaSelecionado} abrirDetalhes={handleAbrirDetalhes} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* MODAL DE DETALHES DO DIA (BLINDADO) */}
      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`Agenda: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-8 max-h-[75vh] overflow-y-auto pr-2 custom-scrollbar">
            
            {/* SEÇÃO LOGÍSTICA: COMPROMISSOS */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-black text-primary-500 uppercase tracking-[0.2em] flex items-center gap-2 border-b border-dark-700 pb-2">
                <Package size={14}/> Gestão de Entregas e Ativos
              </h4>
              
              {/* Une as listas garantindo que sejam arrays */}
              {([...(detalhesDia.compromissosInicio || []), ...(detalhesDia.compromissosAtivos || [])]).length > 0 ? (
                ([...(detalhesDia.compromissosInicio || []), ...(detalhesDia.compromissosAtivos || [])]).map(c => (
                  <div key={c.id} className="p-5 bg-dark-800 rounded-3xl border border-dark-700 relative overflow-hidden group hover:border-primary-500/50 transition-all shadow-lg">
                    {dataToStr(c.data_inicio) === dataToStr(detalhesDia.data) && (
                      <div className="absolute top-0 right-0 bg-primary-600 text-white text-[9px] font-black px-4 py-1.5 rounded-bl-2xl uppercase shadow-md">
                        Início de Contrato
                      </div>
                    )}
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h5 className="font-black text-dark-50 text-lg uppercase leading-tight">{c.nome_contrato || `Contrato #${c.id}`}</h5>
                        <p className="text-primary-400 text-[10px] font-bold uppercase tracking-widest mt-1">{c.contratante}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-green-400 font-mono font-black text-sm">{formatCurrency(c.valor_total_contrato)}</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2 mb-4">
                      {c.compromisso_itens?.map(ci => (
                        <span key={ci.id} className="px-2.5 py-1 bg-dark-700 text-dark-200 rounded-lg text-[10px] font-black border border-dark-600 flex items-center gap-1.5 shadow-sm">
                          <span className="text-primary-500">{ci.quantidade}x</span> {ci.itens?.nome}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 text-[10px] text-dark-400 font-bold border-t border-dark-700/50 pt-3">
                      <div className="flex items-center gap-1.5"><MapPin size={12} className="text-primary-500"/> {c.cidade} - {c.uf}</div>
                      <div className="flex items-center gap-1.5"><Clock size={12} className="text-primary-500"/> Expira em {formatDate(c.data_fim)}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-12 text-center bg-dark-800/30 rounded-3xl border border-dashed border-dark-700">
                  <Package className="mx-auto mb-3 text-dark-600 opacity-20" size={40}/>
                  <p className="text-dark-500 text-xs font-bold uppercase tracking-widest">Sem movimentações previstas</p>
                </div>
              )}
            </div>

            {/* SEÇÃO FINANCEIRA: VENCIMENTOS */}
            <div className="space-y-4">
              <h4 className="text-[10px] font-black text-green-500 uppercase tracking-[0.2em] flex items-center gap-2 border-b border-dark-700 pb-2">
                <DollarSign size={14}/> Compromissos Financeiros
              </h4>
              
              {detalhesDia.parcelas?.length > 0 ? (
                <div className="overflow-hidden rounded-3xl border border-dark-700 shadow-2xl">
                  <table className="w-full text-xs text-left border-collapse">
                    <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px] tracking-widest">
                      <tr>
                        <th className="p-4">Identificação</th>
                        <th className="p-4 text-right">Valor Original</th>
                        <th className="p-4 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-dark-800 bg-dark-900/60">
                      {detalhesDia.parcelas.map(p => (
                        <tr key={p.id} className="hover:bg-green-500/5 transition-colors">
                          <td className="p-4">
                            <div className="font-bold text-dark-100">{p.codigo_contrato || `Parcela #${p.numero_parcela}`}</div>
                            <div className="text-[9px] text-dark-500 uppercase font-black">Fin. ID: {p.financiamento_id}</div>
                          </td>
                          <td className="p-4 text-right font-mono text-green-400 font-black text-sm">
                            {formatCurrency(p.valor_original)}
                          </td>
                          <td className="p-4 text-center">
                            <span className={`px-2.5 py-1 rounded-lg font-black uppercase text-[8px] border shadow-sm ${
                              p.status === 'Paga' 
                              ? 'bg-green-500/10 text-green-500 border-green-500/20' 
                              : 'bg-red-500/10 text-red-400 border-red-500/20'
                            }`}>
                              {p.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center bg-dark-800/30 rounded-3xl border border-dashed border-dark-700">
                  <DollarSign className="mx-auto mb-3 text-dark-600 opacity-20" size={40}/>
                  <p className="text-dark-500 text-xs font-bold uppercase tracking-widest">Nenhum boleto vencendo hoje</p>
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

// --- COMPONENTES AUXILIARES INTERNOS ---

function renderGridDays(ano, mes, getEventos, abrir) {
  const start = new Date(ano, mes - 1, 1)
  const end = new Date(ano, mes, 0)
  const days = []
  
  // Ajuste Segunda-Feira como primeiro dia
  let firstDayIdx = start.getDay() === 0 ? 6 : start.getDay() - 1
  for (let i = 0; i < firstDayIdx; i++) {
    days.push(<div key={`empty-${i}`} className="border border-dark-800/30 bg-dark-900/5 opacity-10" />)
  }

  const hoje = new Date().toDateString()

  for (let d = 1; d <= end.getDate(); d++) {
    const data = new Date(ano, mes - 1, d)
    const ev = getEventos(data)
    const isHoje = data.toDateString() === hoje
    
    days.push(
      <button 
        key={d} 
        onClick={() => abrir(data)}
        className={`group relative p-3 border border-dark-800/60 hover:bg-primary-500/5 transition-all text-left flex flex-col h-full min-h-[110px] overflow-hidden ${
          isHoje ? 'bg-primary-500/10 ring-1 ring-inset ring-primary-500/30' : 'bg-dark-900/20'
        }`}
      >
        <span className={`text-xs font-black mb-2 transition-colors ${
          isHoje ? 'text-primary-400' : 'text-dark-500 group-hover:text-dark-50'
        }`}>
          {d < 10 ? `0${d}` : d}
        </span>
        
        <div className="space-y-1.5 w-full">
          {ev.iniciam.slice(0, 2).map(c => (
            <div key={c.id} className="text-[8px] bg-primary-600 text-white font-black px-2 py-0.5 rounded-md truncate uppercase shadow-sm">
              🚀 {c.nome_contrato || 'Contrato'}
            </div>
          ))}
          {ev.ativos.length > 0 && (
            <div className="text-[8px] text-dark-300 font-bold px-1.5 py-0.5 border border-dark-700 rounded bg-dark-800/80 flex items-center gap-1">
              <Package size={8} className="text-primary-500"/> {ev.ativos.length} Alugueis ativos
            </div>
          )}
          {ev.parcelas.length > 0 && (
            <div className="text-[8px] bg-green-500/20 text-green-500 font-black px-1.5 py-0.5 rounded-md border border-green-500/20 flex items-center gap-1 shadow-inner">
              💰 {ev.parcelas.length} Vencimento(s)
            </div>
          )}
          {ev.iniciam.length > 2 && <div className="text-[7px] text-dark-500 font-black text-center">+ {ev.iniciam.length - 2} eventos</div>}
        </div>
        
        {isHoje && <div className="absolute top-1 right-1 w-1.5 h-1.5 bg-primary-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(139,92,246,0.8)]"/>}
      </button>
    )
  }
  return days
}

function ViewBtn({ active, icon, label, onClick }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black transition-all duration-300 ${
      active 
      ? 'bg-primary-500 text-white shadow-xl shadow-primary-500/30 scale-[1.02]' 
      : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700'
    }`}>
      {icon} {label}
    </button>
  )
}

function DailyView({ data, eventos, setDia, abrirDetalhes }) {
  const navegar = (dir) => {
    const nd = new Date(data)
    nd.setDate(data.getDate() + (dir === 'ant' ? -1 : 1))
    setDia(nd)
  }

  return (
    <div className="space-y-6">
      {/* SELETOR DE DIA MOBILE/DESKTOP */}
      <div className="flex items-center justify-between bg-dark-800/80 p-8 rounded-[2rem] border border-dark-700 shadow-2xl backdrop-blur-xl">
        <button onClick={() => navegar('ant')} className="p-4 hover:bg-dark-700 rounded-2xl text-primary-400 transition-all active:scale-90"><ChevronLeft size={32}/></button>
        <div className="text-center">
          <h2 className="text-4xl font-black text-dark-50 uppercase tracking-tighter mb-1">
            {data.toLocaleDateString('pt-BR', { weekday: 'long' })}
          </h2>
          <div className="flex items-center justify-center gap-3">
            <span className="h-px w-8 bg-primary-500/50"/>
            <p className="text-primary-500 font-black tracking-[0.3em] uppercase text-sm">
              {data.toLocaleDateString('pt-BR')}
            </p>
            <span className="h-px w-8 bg-primary-500/50"/>
          </div>
        </div>
        <button onClick={() => navegar('prox')} className="p-4 hover:bg-dark-700 rounded-2xl text-primary-400 transition-all active:scale-90"><ChevronRight size={32}/></button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* CARD LOGÍSTICA */}
        <div className="card bg-primary-500/[0.03] border-primary-500/20 p-8 rounded-[2rem] shadow-xl">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-[10px] font-black text-primary-500 uppercase tracking-[0.3em] flex items-center gap-3">
              <PlayCircle size={20}/> Cronograma de Entregas
            </h3>
            <span className="bg-primary-500 text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg">
              {eventos.iniciam.length}
            </span>
          </div>
          
          <div className="space-y-4">
            {eventos.iniciam.length > 0 ? eventos.iniciam.map(c => (
              <div key={c.id} onClick={() => abrirDetalhes(data)} className="p-5 bg-dark-800 rounded-2xl border border-dark-700 flex justify-between items-center group cursor-pointer hover:border-primary-500/40 transition-all">
                <div>
                  <p className="font-black text-dark-50 text-base">{c.nome_contrato}</p>
                  <p className="text-[10px] text-dark-500 font-bold uppercase tracking-widest mt-1">{c.contratante}</p>
                </div>
                <ArrowRight size={18} className="text-dark-600 group-hover:text-primary-400 transition-colors"/>
              </div>
            )) : (
              <div className="py-10 text-center opacity-30">
                <CalendarIcon className="mx-auto mb-2" size={32}/>
                <p className="text-[10px] font-bold uppercase">Dia livre de entregas</p>
              </div>
            )}
          </div>
        </div>

        {/* CARD FINANCEIRO */}
        <div className="card bg-green-500/[0.03] border-green-500/20 p-8 rounded-[2rem] shadow-xl">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-[10px] font-black text-green-500 uppercase tracking-[0.3em] flex items-center gap-3">
              <DollarSign size={20}/> Fluxo de Caixa do Dia
            </h3>
            <span className="bg-green-500 text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg">
              {eventos.parcelas.length}
            </span>
          </div>
          
          <div className="space-y-4">
            {eventos.parcelas.length > 0 ? eventos.parcelas.map(p => (
              <div key={p.id} className="p-5 bg-dark-800 rounded-2xl border border-dark-700 flex justify-between items-center shadow-md">
                <div>
                  <p className="font-black text-dark-50">{p.codigo_contrato || `Parcela ${p.numero_parcela}`}</p>
                  <p className={`text-[9px] font-black uppercase tracking-tighter mt-1 ${p.status === 'Paga' ? 'text-green-500' : 'text-red-400'}`}>
                    Status: {p.status}
                  </p>
                </div>
                <p className="text-green-400 font-black font-mono text-base">{formatCurrency(p.valor_original)}</p>
              </div>
            )) : (
              <div className="py-10 text-center opacity-30">
                <CheckCircle className="mx-auto mb-2" size={32}/>
                <p className="text-[10px] font-bold uppercase">Sem vencimentos hoje</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}