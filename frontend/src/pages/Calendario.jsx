import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, CalendarDays, X, 
  ArrowRight, DollarSign, Receipt, Tag, AlignLeft, Check
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
  const [detalhesDia, setDetalhesDia] = useState(null)
  const [parcelasMes, setParcelasMes] = useState([])

  // 🔥 FIX TIMEZONE DEFINITIVO: Gera string YYYY-MM-DD local pura
  const dataToStr = (d) => {
    if (!d) return ''
    const date = d instanceof Date ? d : new Date(d)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  useEffect(() => { loadData() }, [])

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
      setCompromissos(compRes.data || [])
      setItens(itensRes.data || [])
      setCategorias(catRes.data || [])
      const locs = new Set()
      compRes.data?.forEach(c => { if(c.cidade) locs.add(`${c.cidade} - ${c.uf}`) })
      setLocalizacoes(Array.from(locs).sort())
    } catch (error) { toast.error('Erro de carregamento.') }
    finally { setLoading(false) }
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

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto px-4 pb-10">
      <div className="flex justify-between items-end">
        <h1 className="text-4xl font-black text-dark-50 tracking-tighter uppercase italic">Agenda Star Gestão</h1>
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-2xl">
          <button onClick={() => setViewMode('mensal')} className={`px-6 py-2.5 rounded-lg text-xs font-black transition-all ${viewMode === 'mensal' ? 'bg-primary-500 text-white' : 'text-dark-400'}`}>Mensal</button>
          <button onClick={() => setViewMode('diaria')} className={`px-6 py-2.5 rounded-lg text-xs font-black transition-all ${viewMode === 'diaria' ? 'bg-primary-500 text-white' : 'text-dark-400'}`}>Diária</button>
        </div>
      </div>

      <div className="card p-0 overflow-hidden border-dark-700 bg-dark-900/40 shadow-2xl">
        <div className="grid grid-cols-7 border-b border-dark-700 bg-dark-800/80">
          {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map(d => <div key={d} className="py-4 text-center text-[10px] font-black text-dark-500 uppercase">{d}</div>)}
        </div>
        <div className="grid grid-cols-7 min-h-[600px]">
          {renderCalendarDays(anoAtual, mesAtual, getEventosNoDia, abrirDetalhesDia)}
        </div>
      </div>

      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`RELATÓRIO: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-8 max-h-[75vh] overflow-y-auto pr-4 custom-scrollbar">
            
            {/* LOGÍSTICA (image_89ed8e.png) */}
            <Section title="Logística e Entregas" icon={<Package size={16}/>} color="text-primary-500">
              {([...detalhesDia.compromissosInicio, ...detalhesDia.compromissosAtivos]).map(c => (
                <div key={c.id} className="p-6 bg-dark-800 rounded-[2rem] border border-dark-700 shadow-xl border-l-4 border-l-primary-500 mb-6">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h5 className="font-black text-dark-50 text-xl uppercase tracking-tight">{c.nome_contrato}</h5>
                      <p className="text-primary-400 text-[10px] font-bold uppercase">{c.contratante}</p>
                    </div>
                    <span className="text-green-400 font-black text-lg font-mono">{formatCurrency(c.valor_total_contrato)}</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <InfoBox icon={<AlignLeft size={14}/>} label="Descrição" value={c.descricao || 'Sem observações.'} />
                    <InfoBox icon={<MapPin size={14}/>} label="Endereço" value={`${c.endereco || 'Brasília'} - ${c.cidade}/${c.uf}`} />
                  </div>
                  <div className="bg-dark-900/60 p-5 rounded-2xl border border-dark-700/50">
                    <p className="text-[9px] font-black text-dark-500 uppercase mb-3 flex items-center gap-2"><Tag size={12}/> Checklist de Carga</p>
                    <div className="flex flex-wrap gap-2">
                      {c.compromisso_itens?.map(ci => (
                        <span key={ci.id} className="px-3 py-1.5 bg-dark-700 text-dark-50 rounded-xl text-[11px] font-black border border-dark-600 flex items-center gap-2 shadow-inner">
                          <span className="text-primary-500 bg-primary-500/10 px-1.5 rounded-md">{ci.quantidade}x</span> {ci.itens?.nome}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </Section>

            {/* FINANCEIRO (image_89ed8e.png) */}
            <Section title="Vencimentos Financeiros" icon={<DollarSign size={16}/>} color="text-green-500">
               {detalhesDia.parcelas?.length > 0 ? (
                 <div className="overflow-hidden rounded-[2rem] border border-dark-700 shadow-2xl">
                   <table className="w-full text-xs text-left">
                     <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px] tracking-widest">
                       <tr>
                         <th className="p-5">Contrato</th>
                         <th className="p-5 text-right">Original</th>
                         <th className="p-5 text-right">Pago</th>
                         <th className="p-5 text-center">Status</th>
                         <th className="p-5 text-center">Ações</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-dark-800 bg-dark-900/40">
                       {detalhesDia.parcelas.map(p => (
                         <tr key={p.id}>
                           <td className="p-5 font-black text-dark-50 uppercase">{p.codigo_contrato}</td>
                           <td className="p-5 text-right font-mono text-dark-50">{formatCurrency(p.valor_original)}</td>
                           <td className="p-5 text-right font-mono text-green-400">{p.valor_pago > 0 ? formatCurrency(p.valor_pago) : '—'}</td>
                           <td className="p-5 text-center">
                             <span className={`px-3 py-1 rounded-full font-black text-[8px] border ${p.status === 'Paga' ? 'text-green-400 border-green-500/20' : 'text-yellow-400 border-yellow-500/20'}`}>{p.status}</span>
                           </td>
                           <td className="p-5">
                              <div className="flex justify-center gap-2">
                                {p.link_boleto && <a href={p.link_boleto} target="_blank" rel="noreferrer" className="p-2 bg-dark-700 text-primary-400 rounded-xl hover:bg-primary-500/20 transition-all"><FileText size={18}/></a>}
                                {p.link_comprovante && <a href={p.link_comprovante} target="_blank" rel="noreferrer" className="p-2 bg-dark-700 text-green-400 rounded-xl hover:bg-green-500/20 transition-all"><Receipt size={18}/></a>}
                              </div>
                           </td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
               ) : <p className="text-dark-600 text-center py-10 italic">Nenhum vencimento para hoje.</p>}
            </Section>
          </div>
        </Modal>
      )}
    </div>
  )
}

// --- HELPERS (Não mexe no que funciona) ---
function Section({ title, icon, color, children }) { return <div className="space-y-5"><h4 className={`text-[11px] font-black ${color} uppercase flex items-center gap-3 border-b border-dark-700 pb-3`}>{icon} {title}</h4>{children}</div> }
function InfoBox({ icon, label, value }) { return <div className="bg-dark-900/40 p-4 rounded-2xl border border-dark-700/50"><p className="text-[9px] font-black text-dark-500 uppercase mb-2 flex items-center gap-2">{icon} {label}</p><p className="text-xs text-dark-200">{value}</p></div> }
function renderCalendarDays(ano, mes, getEventos, onDayClick) {
  const start = new Date(ano, mes - 1, 1); const end = new Date(ano, mes, 0); const days = []; let startIdx = start.getDay() === 0 ? 6 : start.getDay() - 1
  for (let i = 0; i < startIdx; i++) days.push(<div key={`blank-${i}`} className="opacity-10 border border-dark-800" />)
  for (let d = 1; d <= end.getDate(); d++) {
    const data = new Date(ano, mes - 1, d); const ev = getEventos(data); const isHoje = data.toDateString() === new Date().toDateString()
    days.push(<button key={d} onClick={() => onDayClick(data)} className={`relative p-3 border border-dark-800/40 hover:bg-primary-500/5 text-left flex flex-col h-full min-h-[120px] ${isHoje ? 'bg-primary-500/10 ring-1 ring-primary-500/30 shadow-[0_0_15px_rgba(139,92,246,0.2)]' : ''}`}><span className={`text-xs font-black mb-2 ${isHoje ? 'text-primary-400 underline underline-offset-4' : 'text-dark-500'}`}>{d}</span><div className="space-y-1.5 w-full">{ev.iniciam.slice(0, 1).map(c => <div key={c.id} className="text-[7px] bg-primary-600 text-white font-black px-2 py-0.5 rounded truncate uppercase shadow-lg">🚀 {c.nome_contrato}</div>)}{ev.parcelas.length > 0 && <div className="text-[7px] bg-green-500/20 text-green-500 font-black px-1.5 py-0.5 rounded">💰 {ev.parcelas.length} Boleto(s)</div>}</div></button>)
  }
  return days
}