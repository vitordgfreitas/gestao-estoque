import { useState, useEffect, useMemo } from 'react'
import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { 
  Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, 
  Package, FileText, PlayCircle, ExternalLink, CheckCircle, 
  Clock, AlertCircle, Filter, LayoutGrid, CalendarDays, X, 
  ArrowRight, TrendingUp, DollarSign, Receipt, Tag, AlignLeft,
  Check, UploadCloud, CreditCard, History, Search
} from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import { formatItemName, formatDate, formatCurrency } from '../utils/format'

export default function Calendario() {
  const [compromissos, setCompromissos] = useState([])
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [localizacoes, setLocalizacoes] = useState([])
  const [viewMode, setViewMode] = useState('mensal') // mensal ou diaria
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [loading, setLoading] = useState(true)
  
  // Navegação
  const [mesAtual, setMesAtual] = useState(new Date().getMonth() + 1)
  const [anoAtual, setAnoAtual] = useState(new Date().getFullYear())
  const [diaSelecionado, setDiaSelecionado] = useState(new Date())
  const [detalhesDia, setDetalhesDia] = useState(null)
  const [parcelasMes, setParcelasMes] = useState([])
  const [parcelaEmBaixa, setParcelaEmBaixa] = useState(null)

  // 🔥 FIX TIMEZONE DEFINITIVO: Gera string local YYYY-MM-DD
  const dataToStr = (d) => {
    if (!d) return ''
    if (typeof d === 'string') return d.split('T')[0]
    const date = d instanceof Date ? d : new Date(d)
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }

  useEffect(() => { loadData() }, [])

  useEffect(() => {
    let cancelled = false
    const loadFinanceiro = async () => {
      try {
        const res = await api.get('/api/parcelas', { params: { mes: mesAtual, ano: anoAtual, incluir_pagas: true } })
        if (!cancelled) setParcelasMes(res.data || [])
      } catch (e) { if (!cancelled) setParcelasMes([]) }
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
      setCompromissos(compRes.data || [])
      setItens(itensRes.data || [])
      setCategorias(catRes.data || [])
      const locs = new Set()
      compRes.data?.forEach(c => { if(c.cidade) locs.add(`${c.cidade} - ${c.uf}`) })
      setLocalizacoes(Array.from(locs).sort())
    } catch (error) { toast.error('Erro ao carregar banco de dados.') }
    finally { setLoading(false) }
  }

  // Engine de filtragem unificada para Mês e Dia
  const compromissosFiltrados = useMemo(() => {
    return (compromissos || []).filter(comp => {
      const matchCat = categoriaFiltro === 'Todas as Categorias' || 
                       comp.compromisso_itens?.some(ci => ci.itens?.categoria === categoriaFiltro)
      const matchLoc = localizacaoFiltro === 'Todas as Localizações' || 
                       `${comp.cidade} - ${comp.uf}` === localizacaoFiltro
      return matchCat && matchLoc
    })
  }, [compromissos, categoriaFiltro, localizacaoFiltro])

  const getEventosNoDia = (data) => {
    const dStr = dataToStr(data)
    return {
      iniciam: compromissosFiltrados.filter(c => dataToStr(c.data_inicio) === dStr),
      ativos: compromissosFiltrados.filter(c => {
        const s = dataToStr(c.data_inicio); const e = dataToStr(c.data_fim)
        return dStr >= s && dStr <= e
      }),
      parcelas: (parcelasMes || []).filter(p => dataToStr(p.data_vencimento) === dStr)
    }
  }

  const getContratosUnicos = (iniciam, ativos) => {
    const misturados = [...iniciam, ...ativos]
    return Array.from(new Map(misturados.map(c => [c.id, c])).values())
  }

  const abrirDetalhesDia = async (data) => {
    const ev = getEventosNoDia(data)
    const dStr = dataToStr(data)
    setDetalhesDia({
      data: new Date(data),
      compromissosInicio: ev.iniciam,
      compromissosAtivos: ev.ativos,
      parcelas: [],
      loadingParcelas: true
    })
    try {
      const res = await api.get('/api/parcelas', { params: { data_vencimento: dStr, incluir_pagas: true } })
      setDetalhesDia(prev => (prev && dataToStr(prev.data) === dStr ? { ...prev, parcelas: res.data || [], loadingParcelas: false } : prev))
    } catch (e) { setDetalhesDia(prev => prev ? { ...prev, loadingParcelas: false } : null) }
  }

  const handleSalvarBaixa = async (formData) => {
    const loadId = toast.loading('Salvando...')
    try {
      await api.post(`/api/financiamentos/0/parcelas/${parcelaEmBaixa.id}/pagar`, {
        valor_pago: parseFloat(formData.valor_pago),
        link_comprovante: String(formData.link_comprovante || ''),
        data_pagamento: dataToStr(new Date())
      })
      toast.success('Baixa realizada!'); setParcelaEmBaixa(null); loadData() 
    } catch (e) {
      // 🔥 CORREÇÃO ERRO #31: Garante que o erro renderizado seja string
      const msg = e.response?.data?.detail || e.message || 'Erro desconhecido'
      toast.error(typeof msg === 'object' ? JSON.stringify(msg) : msg)
    } finally { toast.dismiss(loadId) }
  }

  // --- NAVEGAÇÃO ---
  const navegarMes = (dir) => {
    if (dir === 'anterior') {
      if (mesAtual === 1) { setMesAtual(12); setAnoAtual(anoAtual - 1) }
      else setMesAtual(mesAtual - 1)
    } else {
      if (mesAtual === 12) { setMesAtual(1); setAnoAtual(anoAtual + 1) }
      else setMesAtual(mesAtual + 1)
    }
  }

  const navegarDia = (dir) => {
    const novo = new Date(diaSelecionado)
    novo.setDate(diaSelecionado.getDate() + (dir === 'anterior' ? -1 : 1))
    setDiaSelecionado(novo)
  }

  const renderCalendarioMensal = () => {
    const nomesMeses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    const ultimoDia = new Date(anoAtual, mesAtual, 0).getDate()
    const startIdx = new Date(anoAtual, mesAtual - 1, 1).getDay() === 0 ? 6 : new Date(anoAtual, mesAtual - 1, 1).getDay() - 1
    const semanas = []; let semanaAtual = []
    for (let i = 0; i < startIdx; i++) semanaAtual.push(null)
    for (let d = 1; d <= ultimoDia; d++) {
      semanaAtual.push(d); if (semanaAtual.length === 7) { semanas.push(semanaAtual); semanaAtual = [] }
    }
    if (semanaAtual.length > 0) { while(semanaAtual.length < 7) semanaAtual.push(null); semanas.push(semanaAtual) }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-dark-800 p-4 rounded-xl border border-dark-700 shadow-lg">
          <button onClick={() => navegarMes('anterior')} className="p-2 text-primary-400 hover:bg-dark-700 rounded-lg"><ChevronLeft/></button>
          <h3 className="text-xl font-black text-dark-50 uppercase tracking-widest">{nomesMeses[mesAtual-1]} {anoAtual}</h3>
          <button onClick={() => navegarMes('proximo')} className="p-2 text-primary-400 hover:bg-dark-700 rounded-lg"><ChevronRight/></button>
        </div>
        <div className="grid grid-cols-7 gap-2">
          {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map(d => <div key={d} className="text-center text-[10px] font-black text-dark-500 uppercase">{d}</div>)}
          {semanas.map((sem, sIdx) => sem.map((dia, dIdx) => {
            if (!dia) return <div key={`${sIdx}-${dIdx}`} className="aspect-square" />
            const data = new Date(anoAtual, mesAtual - 1, dia)
            const ev = getEventosNoDia(data)
            const isHoje = data.toDateString() === new Date().toDateString()
            return (
              <button key={`${sIdx}-${dIdx}`} onClick={() => abrirDetalhesDia(data)} className={`aspect-square p-2 rounded-lg border text-left flex flex-col transition-all ${isHoje ? 'bg-primary-600 border-primary-500 text-white' : (ev.parcelas.length > 0 || ev.ativos.length > 0) ? 'bg-primary-600/10 border-primary-600/30' : 'bg-dark-800 border-dark-700'}`}>
                <span className="text-sm font-black">{dia}</span>
                <div className="mt-auto space-y-0.5 w-full overflow-hidden">
                   {ev.parcelas.length > 0 && <div className="text-[7px] font-black flex items-center gap-1 text-green-400 bg-green-400/10 rounded px-1 w-fit">💰 {ev.parcelas.length}</div>}
                   {ev.iniciam.length > 0 && <div className="text-[7px] font-black flex items-center gap-1 text-primary-400 bg-primary-400/10 rounded px-1 w-fit">🚀 {ev.iniciam.length}</div>}
                </div>
              </button>
            )
          }))}
        </div>
      </div>
    )
  }

  if (loading) return <div className="flex h-96 items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary-500"></div></div>

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto px-4 pb-10">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-dark-50 uppercase italic tracking-tighter">Agenda Star Gestão</h1>
          <p className="text-dark-400 text-xs font-bold uppercase tracking-widest">Controle Central Brasília/DF</p>
        </div>
        <div className="flex gap-2 p-1 bg-dark-800 rounded-xl border border-dark-700 shadow-2xl">
          <button onClick={() => setViewMode('mensal')} className={`px-5 py-2 rounded-lg text-xs font-black transition-all ${viewMode === 'mensal' ? 'bg-primary-500 text-white shadow-xl' : 'text-dark-400'}`}><LayoutGrid size={16}/></button>
          <button onClick={() => setViewMode('diaria')} className={`px-5 py-2 rounded-lg text-xs font-black transition-all ${viewMode === 'diaria' ? 'bg-primary-500 text-white shadow-xl' : 'text-dark-400'}`}><CalendarDays size={16}/></button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FilterSelect label="Filtrar Categoria" value={categoriaFiltro} onChange={setCategoriaFiltro} options={['Todas as Categorias', ...categorias]} />
        <FilterSelect label="Filtrar Localização" value={localizacaoFiltro} onChange={setLocalizacaoFiltro} options={['Todas as Localizações', ...localizacoes]} />
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={viewMode} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-6 bg-dark-900/40 border-dark-700 shadow-2xl backdrop-blur-md">
          {viewMode === 'mensal' ? renderCalendarioMensal() : (
            <DailyView data={diaSelecionado} eventos={getEventosNoDia(diaSelecionado)} navegar={navegarDia} abrirDetalhes={abrirDetalhesDia} getContratosUnicos={getContratosUnicos} />
          )}
        </motion.div>
      </AnimatePresence>

      {/* MODAL RIQUÍSSIMO EM DADOS */}
      {detalhesDia && (
        <Modal isOpen={true} onClose={() => setDetalhesDia(null)} title={`DADOS DO DIA: ${formatDate(dataToStr(detalhesDia.data))}`}>
          <div className="space-y-8 max-h-[80vh] overflow-y-auto pr-2 custom-scrollbar">
            
            <Section title="Logística e Entregas" icon={<Package size={16}/>} color="text-primary-500">
              {getContratosUnicos(detalhesDia.compromissosInicio, detalhesDia.compromissosAtivos).length > 0 ? (
                getContratosUnicos(detalhesDia.compromissosInicio, detalhesDia.compromissosAtivos).map(c => (
                  <div key={c.id} className="p-6 bg-dark-800 rounded-[2rem] border border-dark-700 border-l-4 border-l-primary-500 shadow-xl mb-6">
                    <div className="flex justify-between items-start mb-6">
                      <div><h5 className="font-black text-dark-50 text-xl uppercase leading-tight">{c.nome_contrato}</h5><p className="text-primary-400 text-[10px] font-bold uppercase">{c.contratante}</p></div>
                      <span className="text-green-400 font-black text-lg font-mono">{formatCurrency(c.valor_total_contrato)}</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <InfoBox label="Descrição" value={c.descricao || 'Sem notas registradas.'} />
                      <InfoBox label="Local da Operação" value={`${c.endereco || 'Brasília'} - ${c.cidade}/${c.uf}`} />
                    </div>
                    <div className="bg-dark-900/60 p-5 rounded-2xl border border-dark-700/50">
                      <p className="text-[9px] font-black text-dark-500 uppercase mb-3 flex items-center gap-2"><Tag size={12}/> Checklist de Carga (Qtd + Nome)</p>
                      <div className="flex flex-wrap gap-2">
                        {c.compromisso_itens?.map(ci => (
                          <span key={ci.id} className="px-3 py-1.5 bg-dark-700 text-dark-50 rounded-xl text-[11px] font-black border border-dark-600 flex items-center gap-2 shadow-inner">
                            <span className="text-primary-500 bg-primary-500/10 px-1.5 rounded-md">{ci.quantidade}x</span> {ci.itens?.nome}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))
              ) : <p className="text-dark-600 text-center py-6 italic text-xs">Agenda operacional livre.</p>}
            </Section>

            <Section title="Vencimentos Financeiros" icon={<DollarSign size={16}/>} color="text-green-500">
              {detalhesDia.loadingParcelas ? <div className="py-10 text-center animate-pulse text-xs font-black uppercase tracking-widest text-dark-500">Buscando banco...</div> :
               detalhesDia.parcelas?.length > 0 ? (
                 <div className="overflow-x-auto rounded-2xl border border-dark-700 shadow-2xl bg-dark-900/20">
                   <table className="w-full text-xs text-left">
                     <thead className="bg-dark-800 text-dark-500 uppercase font-black text-[9px] tracking-widest border-b border-dark-700">
                       <tr>
                         <th className="p-4">Vencimento</th>
                         <th className="p-4">Contrato</th>
                         <th className="p-4 text-right">Original</th>
                         <th className="p-4 text-right">Pago</th>
                         <th className="p-4 text-center">Status</th>
                         <th className="p-4 text-center">Boletos / Recibos</th>
                         <th className="p-4 text-center">Ações</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-dark-800">
                       {detalhesDia.parcelas.map(p => {
                         const statusColor = p.status === 'Paga' ? 'text-green-400 border-green-500/20 bg-green-500/5' : 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5'
                         return (
                           <tr key={p.id} className="hover:bg-green-500/5 transition-colors group">
                             <td className="p-4 font-bold text-dark-200">{formatDate(p.data_vencimento)}</td>
                             <td className="p-4 font-black text-dark-50 uppercase truncate max-w-[120px]">{p.codigo_contrato}</td>
                             <td className="p-4 text-right font-mono text-dark-50 font-black">{formatCurrency(p.valor_original)}</td>
                             <td className="p-4 text-right font-mono text-green-400 font-black">{p.valor_pago > 0 ? formatCurrency(p.valor_pago) : '—'}</td>
                             <td className="p-4 text-center"><span className={`px-2.5 py-0.5 rounded-full font-black text-[8px] border shadow-sm ${statusColor}`}>{p.status}</span></td>
                             <td className="p-4 text-center"><div className="flex justify-center gap-2">
                               {p.link_boleto && <a href={p.link_boleto} target="_blank" rel="noreferrer" title="Boleto" className="p-2 bg-dark-700 text-primary-400 rounded-lg hover:bg-primary-500/20 shadow-lg"><FileText size={16}/></a>}
                               {p.link_comprovante && <a href={p.link_comprovante} target="_blank" rel="noreferrer" title="Comprovante" className="p-2 bg-dark-700 text-green-400 rounded-lg hover:bg-green-500/20 shadow-lg"><Receipt size={16}/></a>}
                             </div></td>
                             <td className="p-4 text-center">
                                {p.status !== 'Paga' && <button onClick={() => setParcelaEmBaixa(p)} className="p-2 bg-green-500 text-white rounded-lg shadow-lg hover:scale-110 active:scale-95 transition-all"><Check size={16}/></button>}
                             </td>
                           </tr>
                         )
                       })}
                     </tbody>
                   </table>
                 </div>
               ) : <p className="text-dark-600 text-center py-10 italic">Sem boletos hoje.</p>}
            </Section>
          </div>
        </Modal>
      )}

      {/* MODAL BAIXA FINANCEIRA */}
      {parcelaEmBaixa && (
        <Modal isOpen={true} onClose={() => setParcelaEmBaixa(null)} title="Registrar Baixa">
           <form onSubmit={(e) => { e.preventDefault(); handleSalvarBaixa(Object.fromEntries(new FormData(e.target))); }} className="space-y-6">
              <div className="p-5 bg-dark-800 rounded-3xl border border-dark-700 flex justify-between items-center shadow-inner">
                 <div><p className="text-[10px] font-black text-dark-500 uppercase tracking-widest">Valor do Título</p><p className="text-2xl font-black text-dark-50 font-mono">{formatCurrency(parcelaEmBaixa.valor_original)}</p></div>
                 <CreditCard size={32} className="text-primary-500 opacity-20"/>
              </div>
              <div className="space-y-4">
                <div><label className="label uppercase text-[10px] font-black tracking-widest">Valor Efetivamente Pago</label><input name="valor_pago" type="number" step="0.01" className="input font-mono text-green-400 text-lg" defaultValue={parcelaEmBaixa.valor_original} required /></div>
                <div><label className="label uppercase text-[10px] font-black tracking-widest">Link/Obs do Comprovante (Qualquer formato)</label><div className="relative"><UploadCloud className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-500" size={18}/><input name="link_comprovante" type="text" placeholder="Cole o link ou nota aqui..." className="input pl-10 bg-dark-900 shadow-inner" /></div></div>
              </div>
              <button type="submit" className="btn btn-primary w-full py-4 font-black uppercase shadow-xl shadow-primary-500/40 text-base">Salvar Baixa Financeira</button>
           </form>
        </Modal>
      )}
    </div>
  )
}

// --- SUB-COMPONENTES AUXILIARES ---
function Section({ title, icon, color, children }) { return <div className="space-y-5"><h4 className={`text-[11px] font-black ${color} uppercase tracking-[0.3em] flex items-center gap-3 border-b border-dark-700 pb-3`}>{icon} {title}</h4>{children}</div> }
function InfoBox({ label, value }) { return <div className="bg-dark-900/40 p-4 rounded-2xl border border-dark-700/50 h-full shadow-inner"><p className="text-[9px] font-black text-dark-500 uppercase mb-2">{label}</p><p className="text-xs text-dark-200 leading-relaxed italic">{value}</p></div> }
function FilterSelect({ label, value, onChange, options }) { return <div className="space-y-2 flex-1"><label className="text-[10px] font-black uppercase text-dark-500 ml-2 tracking-widest">{label}</label><select value={value} onChange={e => onChange(e.target.value)} className="input h-14 bg-dark-800/50 border-dark-700 rounded-2xl shadow-inner">{(options || []).map(opt => <option key={opt}>{opt}</option>)}</select></div> }

function DailyView({ data, eventos, navegar, abrirDetalhes, getContratosUnicos }) {
  const contratos = getContratosUnicos(eventos.iniciam, eventos.ativos);
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between bg-dark-800/80 p-10 rounded-[3rem] border border-dark-700 shadow-2xl">
        <button onClick={() => navegar('anterior')} className="p-4 text-primary-400 hover:bg-dark-700 rounded-2xl transition-all"><ChevronLeft size={32}/></button>
        <div className="text-center">
          <h2 className="text-5xl font-black text-dark-50 uppercase tracking-tighter mb-2 italic">{data.toLocaleDateString('pt-BR', { weekday: 'long' })}</h2>
          <p className="text-primary-500 font-black tracking-[0.5em] uppercase text-sm">{formatDate(data)}</p>
        </div>
        <button onClick={() => navegar('proximo')} className="p-4 text-primary-400 hover:bg-dark-700 rounded-2xl transition-all"><ChevronRight size={32}/></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <DayCard title="Logística" icon={<Package size={24}/>} count={contratos.length} items={contratos} onClick={() => abrirDetalhes(data)} />
        <DayCard title="Financeiro" icon={<DollarSign size={24}/>} count={eventos.parcelas.length} items={eventos.parcelas} isFin onClick={() => abrirDetalhes(data)} />
      </div>
    </div>
  )
}

function DayCard({ title, icon, count, items, onClick, isFin }) {
  return (
    <div onClick={onClick} className="p-8 rounded-[3rem] border border-dark-700 bg-dark-800/60 shadow-2xl cursor-pointer hover:border-primary-500/40 transition-all group">
      <div className="flex justify-between items-center mb-8">
        <h3 className="text-xs font-black uppercase tracking-[0.4em] flex items-center gap-4 text-dark-400 group-hover:text-primary-400">{icon} {title}</h3>
        <span className="text-xs font-black px-4 py-1.5 rounded-full text-white bg-primary-500 shadow-lg">{count}</span>
      </div>
      <div className="space-y-4">
        {(items || []).slice(0, 5).map(i => (
          <div key={i.id} className="p-5 bg-dark-900/60 rounded-2xl border border-dark-800 flex justify-between items-center group-hover:border-dark-700 transition-colors">
            <div>
              <p className="font-black text-dark-50 text-sm truncate">{i.nome_contrato || i.codigo_contrato || 'Operação'}</p>
              {i.contratante && <p className="text-[10px] text-dark-500 font-bold uppercase mt-1 tracking-widest">{i.contratante}</p>}
            </div>
            <ArrowRight size={18} className="text-dark-600"/>
          </div>
        ))}
        {(!items || items.length === 0) && <p className="text-dark-600 text-[10px] font-black uppercase italic py-10 text-center opacity-40">Agenda Livre</p>}
      </div>
    </div>
  )
}