import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import api from '../services/api'
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, Package, FileText, PlayCircle, Calendar, ExternalLink, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'
import { formatItemName, formatDate } from '../utils/format'

const formatCurrency = (value) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0)

export default function Calendario() {
  const [compromissos, setCompromissos] = useState([])
  const [itens, setItens] = useState([])
  const [categorias, setCategorias] = useState([])
  const [localizacoes, setLocalizacoes] = useState([])
  const [viewMode, setViewMode] = useState('mensal') // mensal, semanal, diaria
  const [categoriaFiltro, setCategoriaFiltro] = useState('Todas as Categorias')
  const [localizacaoFiltro, setLocalizacaoFiltro] = useState('Todas as Localizações')
  const [loading, setLoading] = useState(true)
  
  // Estados para calendário mensal
  const [mesAtual, setMesAtual] = useState(new Date().getMonth() + 1)
  const [anoAtual, setAnoAtual] = useState(new Date().getFullYear())
  
  // Estados para calendário semanal
  const [semanaInicio, setSemanaInicio] = useState(() => {
    const hoje = new Date()
    const diasParaSegunda = hoje.getDay() === 0 ? 6 : hoje.getDay() - 1
    const segunda = new Date(hoje)
    segunda.setDate(hoje.getDate() - diasParaSegunda)
    return segunda
  })
  
  // Estados para calendário diário
  const [diaSelecionado, setDiaSelecionado] = useState(new Date())
  
  // Estado para modal de detalhes
  const [detalhesDia, setDetalhesDia] = useState(null)
  // Parcelas do mês (para contagem nos dias)
  const [parcelasMes, setParcelasMes] = useState([])

  const dataToStr = (d) => (d instanceof Date ? d.toISOString().split('T')[0] : (d || '').split('T')[0])

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const res = await api.get('/api/parcelas', { params: { mes: mesAtual, ano: anoAtual } })
        if (!cancelled) setParcelasMes(res.data || [])
      } catch (e) {
        if (!cancelled) setParcelasMes([])
      }
    }
    load()
    return () => { cancelled = true }
  }, [mesAtual, anoAtual])

  const abrirDetalhesDia = async (data, compsInicio, compsAtivos) => {
    const dataObj = data instanceof Date ? data : new Date(data)
    const dataStr = dataToStr(dataObj)
    setDetalhesDia({
      data: dataObj,
      compromissosInicio: compsInicio || [],
      compromissosAtivos: compsAtivos || [],
      parcelas: [],
      loadingParcelas: true
    })
    try {
      const res = await api.get('/api/parcelas', { params: { data_vencimento: dataStr, incluir_pagas: true } })
      setDetalhesDia((prev) => {
        if (!prev) return prev
        if (dataToStr(prev.data) !== dataStr) return prev
        return { ...prev, parcelas: res.data || [], loadingParcelas: false }
      })
    } catch (error) {
      console.error('Erro ao carregar parcelas do dia:', error)
      setDetalhesDia((prev) => (prev ? { ...prev, parcelas: [], loadingParcelas: false } : prev))
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (compromissos.length > 0) {
      const locs = new Set()
      compromissos.forEach(comp => {
        if (comp.cidade && comp.uf) {
          locs.add(`${comp.cidade} - ${comp.uf}`)
        }
      })
      setLocalizacoes(Array.from(locs).sort())
    }
  }, [compromissos])

  const loadData = async () => {
    try {
      setLoading(true)
      const [compRes, itensRes, catRes] = await Promise.all([
        compromissosAPI.listar(),
        itensAPI.listar().catch(() => ({ data: [] })),
        categoriasAPI.listar().catch(() => ({ data: [] }))
      ])
      setCompromissos(compRes.data)
      setItens(itensRes.data || [])
      setCategorias(catRes.data || [])
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao carregar dados')
      console.error('Erro ao carregar dados:', error)
    } finally {
      setLoading(false)
    }
  }

  const compromissosFiltrados = compromissos.filter(comp => {
    if (categoriaFiltro !== 'Todas as Categorias') {
      if (!comp.item || comp.item.categoria !== categoriaFiltro) {
        return false
      }
    }
    if (localizacaoFiltro !== 'Todas as Localizações') {
      const [cidade, uf] = localizacaoFiltro.split(' - ')
      if (comp.cidade !== cidade || comp.uf !== uf) {
        return false
      }
    }
    return true
  })

  const compromissosPorData = (data) => {
    const dataStr = data.toISOString().split('T')[0]
    return compromissosFiltrados.filter(comp => {
      const inicio = new Date(comp.data_inicio).toISOString().split('T')[0]
      const fim = new Date(comp.data_fim).toISOString().split('T')[0]
      return dataStr >= inicio && dataStr <= fim
    })
  }

  const navegarMes = (direcao) => {
    if (direcao === 'anterior') {
      if (mesAtual === 1) {
        setMesAtual(12)
        setAnoAtual(anoAtual - 1)
      } else {
        setMesAtual(mesAtual - 1)
      }
    } else {
      if (mesAtual === 12) {
        setMesAtual(1)
        setAnoAtual(anoAtual + 1)
      } else {
        setMesAtual(mesAtual + 1)
      }
    }
  }

  const navegarSemana = (direcao) => {
    const novaSemana = new Date(semanaInicio)
    novaSemana.setDate(semanaInicio.getDate() + (direcao === 'anterior' ? -7 : 7))
    setSemanaInicio(novaSemana)
  }

  const navegarDia = (direcao) => {
    const novoDia = new Date(diaSelecionado)
    novoDia.setDate(diaSelecionado.getDate() + (direcao === 'anterior' ? -1 : 1))
    setDiaSelecionado(novoDia)
  }

  const renderCalendarioMensal = () => {
    const primeiroDia = new Date(anoAtual, mesAtual - 1, 1)
    const ultimoDia = new Date(anoAtual, mesAtual, 0)
    const diasNoMes = ultimoDia.getDate()
    const primeiroDiaSemana = primeiroDia.getDay() === 0 ? 6 : primeiroDia.getDay() - 1 // Segunda = 0
    
    const semanas = []
    let semanaAtual = []
    
    // Preenche dias vazios do início
    for (let i = 0; i < primeiroDiaSemana; i++) {
      semanaAtual.push(null)
    }
    
    // Preenche dias do mês
    for (let dia = 1; dia <= diasNoMes; dia++) {
      semanaAtual.push(dia)
      if (semanaAtual.length === 7) {
        semanas.push(semanaAtual)
        semanaAtual = []
      }
    }
    
    // Preenche dias vazios do fim
    while (semanaAtual.length < 7 && semanaAtual.length > 0) {
      semanaAtual.push(null)
    }
    if (semanaAtual.length > 0) {
      semanas.push(semanaAtual)
    }

    const nomesMeses = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    const diasSemana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

    return (
      <div className="space-y-4">
        {/* Navegação do mês */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navegarMes('anterior')}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <ChevronLeft className="text-dark-400" size={20} />
          </button>
          <h3 className="text-xl font-semibold text-dark-50">
            {nomesMeses[mesAtual - 1]} {anoAtual}
          </h3>
          <button
            onClick={() => navegarMes('proximo')}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <ChevronRight className="text-dark-400" size={20} />
          </button>
        </div>

        {/* Grid do calendário */}
        <div className="grid grid-cols-7 gap-2">
          {/* Cabeçalho dos dias da semana */}
          {diasSemana.map(dia => (
            <div key={dia} className="p-2 text-center text-sm font-semibold text-dark-400">
              {dia}
            </div>
          ))}

          {/* Dias do calendário */}
          {semanas.map((semana, semanaIdx) =>
            semana.map((dia, diaIdx) => {
              if (dia === null) {
                return <div key={`${semanaIdx}-${diaIdx}`} className="aspect-square" />
              }

              const dataAtual = new Date(anoAtual, mesAtual - 1, dia)
              const dataStr = dataToStr(dataAtual)
              const hoje = new Date()
              const isHoje = dataAtual.toDateString() === hoje.toDateString()
              const compsAtivos = compromissosPorData(dataAtual)
              const compsInicio = compromissosFiltrados.filter(c => dataToStr(c.data_inicio) === dataStr)
              const numBoletos = parcelasMes.filter(p => dataToStr(p.data_vencimento) === dataStr).length
              const temAlgo = numBoletos > 0 || compsInicio.length > 0 || compsAtivos.length > 0

              return (
                <button
                  key={`${semanaIdx}-${diaIdx}`}
                  onClick={() => abrirDetalhesDia(dataAtual, compsInicio, compsAtivos)}
                  className={`aspect-square p-1.5 rounded-lg border transition-colors text-left ${
                    isHoje
                      ? 'bg-primary-600 border-primary-500 text-white'
                      : temAlgo
                      ? 'bg-primary-600/20 border-primary-600/30 hover:bg-primary-600/30'
                      : 'bg-dark-800 border-dark-700 hover:bg-dark-700'
                  }`}
                >
                  <div className="flex flex-col h-full gap-0.5">
                    <span className={`text-sm font-medium ${isHoje ? 'text-white' : 'text-dark-50'}`}>
                      {dia}
                    </span>
                    {(numBoletos > 0 || compsInicio.length > 0 || compsAtivos.length > 0) && (
                      <div className={`text-[10px] mt-auto space-y-0.5 ${isHoje ? 'text-white/90' : 'text-dark-300'}`}>
                        {numBoletos > 0 && <div className="flex items-center gap-1"><FileText size={10} /> {numBoletos} boleto{numBoletos !== 1 ? 's' : ''}</div>}
                        {compsInicio.length > 0 && <div className="flex items-center gap-1"><PlayCircle size={10} /> {compsInicio.length} início</div>}
                        {compsAtivos.length > 0 && <div className="flex items-center gap-1"><Calendar size={10} /> {compsAtivos.length} ativo{compsAtivos.length !== 1 ? 's' : ''}</div>}
                      </div>
                    )}
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>
    )
  }

  const renderCalendarioSemanal = () => {
    const semanaFim = new Date(semanaInicio)
    semanaFim.setDate(semanaInicio.getDate() + 6)

    const diasSemana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    const dias = []
    for (let i = 0; i < 7; i++) {
      const dia = new Date(semanaInicio)
      dia.setDate(semanaInicio.getDate() + i)
      dias.push(dia)
    }

    return (
      <div className="space-y-4">
        {/* Navegação da semana */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navegarSemana('anterior')}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <ChevronLeft className="text-dark-400" size={20} />
          </button>
          <h3 className="text-xl font-semibold text-dark-50">
            {formatDate(semanaInicio.toISOString().split('T')[0])} - {formatDate(semanaFim.toISOString().split('T')[0])}
          </h3>
          <button
            onClick={() => navegarSemana('proximo')}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <ChevronRight className="text-dark-400" size={20} />
          </button>
        </div>

        {/* Dias da semana */}
        <div className="space-y-4">
          {dias.map((dia, idx) => {
            const dataStr = dataToStr(dia)
            const compsAtivos = compromissosPorData(dia)
            const compsInicio = compromissosFiltrados.filter(c => dataToStr(c.data_inicio) === dataStr)
            const numBoletos = parcelasMes.filter(p => dataToStr(p.data_vencimento) === dataStr).length
            const hoje = new Date()
            const isHoje = dia.toDateString() === hoje.toDateString()

            return (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${
                  isHoje
                    ? 'bg-primary-600/20 border-primary-600/30'
                    : 'bg-dark-800 border-dark-700'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-dark-50">
                    {diasSemana[idx]} - {formatDate(dia.toISOString().split('T')[0])}
                  </h4>
                  <div className="flex gap-2 text-xs text-dark-400">
                    {numBoletos > 0 && <span>{numBoletos} boleto{numBoletos !== 1 ? 's' : ''}</span>}
                    {compsInicio.length > 0 && <span>{compsInicio.length} início</span>}
                    {compsAtivos.length > 0 && <span>{compsAtivos.length} ativo{compsAtivos.length !== 1 ? 's' : ''}</span>}
                  </div>
                </div>

                {(compsAtivos.length > 0 || compsInicio.length > 0 || numBoletos > 0) ? (
                  <>
                    <button
                      type="button"
                      onClick={() => abrirDetalhesDia(dia, compsInicio, compsAtivos)}
                      className="text-sm text-primary-400 hover:text-primary-300 mb-2"
                    >
                      Ver detalhes do dia
                    </button>
                    <div className="space-y-2">
                      {compsAtivos.map(comp => (
                        <div
                          key={comp.id}
                          onClick={() => abrirDetalhesDia(dia, compsInicio, compsAtivos)}
                          className="p-3 bg-dark-700/50 rounded-lg hover:bg-dark-700 cursor-pointer transition-colors"
                        >
                          <p className="font-medium text-dark-50">{formatItemName(comp.item) || 'Item Deletado'}</p>
                          <p className="text-sm text-dark-400">
                            {comp.quantidade} unidades • {comp.contratante || 'Sem contratante'}
                          </p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-dark-400">Nada neste dia.</p>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderCalendarioDiario = () => {
    const dataStr = dataToStr(diaSelecionado)
    const compsAtivos = compromissosPorData(diaSelecionado)
    const compsInicio = compromissosFiltrados.filter(c => dataToStr(c.data_inicio) === dataStr)
    const numBoletos = parcelasMes.filter(p => dataToStr(p.data_vencimento) === dataStr).length
    const hoje = new Date()
    const isHoje = diaSelecionado.toDateString() === hoje.toDateString()
    const diasSemana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    const diaSemanaNome = diasSemana[diaSelecionado.getDay()]

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <button onClick={() => navegarDia('anterior')} className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
            <ChevronLeft className="text-dark-400" size={20} />
          </button>
          <h3 className={`text-xl font-semibold ${isHoje ? 'text-primary-400' : 'text-dark-50'}`}>
            {diaSemanaNome} - {formatDate(diaSelecionado.toISOString().split('T')[0])}
            {isHoje && ' (Hoje)'}
          </h3>
          <button onClick={() => navegarDia('proximo')} className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
            <ChevronRight className="text-dark-400" size={20} />
          </button>
        </div>
        <div className="flex gap-4 text-sm text-dark-400 mb-4">
          {numBoletos > 0 && <span>{numBoletos} boleto{numBoletos !== 1 ? 's' : ''}</span>}
          {compsInicio.length > 0 && <span>{compsInicio.length} que iniciam</span>}
          {compsAtivos.length > 0 && <span>{compsAtivos.length} ativo{compsAtivos.length !== 1 ? 's' : ''}</span>}
        </div>
        <button
          type="button"
          onClick={() => abrirDetalhesDia(diaSelecionado, compsInicio, compsAtivos)}
          className="text-primary-400 hover:text-primary-300 text-sm"
        >
          Ver detalhes do dia (compromissos e boletos)
        </button>
        {compsAtivos.length > 0 && (
          <div className="space-y-3">
            {compsAtivos.map(comp => (
              <div
                key={comp.id}
                onClick={() => abrirDetalhesDia(diaSelecionado, compsInicio, compsAtivos)}
                className="p-4 bg-dark-800 border border-dark-700 rounded-lg hover:border-primary-600/50 cursor-pointer transition-colors"
              >
                <h4 className="font-semibold text-dark-50 mb-2">{formatItemName(comp.item) || 'Item Deletado'}</h4>
                <div className="space-y-1 text-sm text-dark-400">
                  <p>Quantidade: {comp.quantidade} unidades</p>
                  <p>Período: {formatDate(comp.data_inicio)} a {formatDate(comp.data_fim)}</p>
                  {comp.contratante && <p>Contratante: {comp.contratante}</p>}
                  {comp.cidade && comp.uf && (
                    <div className="flex items-center gap-1 mt-2">
                      <MapPin size={14} />
                      <span>{comp.cidade} - {comp.uf}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        {compsAtivos.length === 0 && numBoletos === 0 && (
          <div className="text-center py-12 text-dark-400">
            <CalendarIcon className="mx-auto mb-3 opacity-50" size={48} />
            <p>Nada neste dia.</p>
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Calendário de Compromissos</h1>
        <p className="text-dark-400">Visualize seus compromissos em formato de calendário</p>
      </div>

      {/* Filtros */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Filtrar por Categoria</label>
            <select
              value={categoriaFiltro}
              onChange={(e) => setCategoriaFiltro(e.target.value)}
              className="input"
            >
              <option value="Todas as Categorias">Todas as Categorias</option>
              {categorias.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Filtrar por Localização</label>
            <select
              value={localizacaoFiltro}
              onChange={(e) => setLocalizacaoFiltro(e.target.value)}
              className="input"
            >
              <option value="Todas as Localizações">Todas as Localizações</option>
              {localizacoes.map(loc => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Visualização</label>
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={() => setViewMode('mensal')}
                className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                  viewMode === 'mensal'
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                Mensal
              </button>
              <button
                onClick={() => setViewMode('semanal')}
                className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                  viewMode === 'semanal'
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                Semanal
              </button>
              <button
                onClick={() => setViewMode('diaria')}
                className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                  viewMode === 'diaria'
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                }`}
              >
                Diária
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Calendário */}
      <div className="card">
        {viewMode === 'mensal' && renderCalendarioMensal()}
        {viewMode === 'semanal' && renderCalendarioSemanal()}
        {viewMode === 'diaria' && renderCalendarioDiario()}
      </div>

      {/* Modal de detalhes do dia */}
      {detalhesDia && (
        <Modal
          isOpen={!!detalhesDia}
          onClose={() => setDetalhesDia(null)}
          title={`Agenda em ${formatDate(detalhesDia.data.toISOString().split('T')[0])}`}
        >
          <div className="space-y-6 max-h-[70vh] overflow-y-auto">
            {/* Compromissos que iniciam neste dia */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-dark-200 flex items-center gap-2">
                <PlayCircle size={16} /> Compromissos que iniciam neste dia ({detalhesDia.compromissosInicio?.length || 0})
              </h4>
              {detalhesDia.compromissosInicio?.length > 0 ? (
                detalhesDia.compromissosInicio.map(comp => (
                  <div key={comp.id} className="p-4 bg-dark-700/50 rounded-lg border border-dark-700">
                    <h5 className="font-semibold text-dark-50 mb-2">{formatItemName(comp.item) || 'Item Deletado'}</h5>
                    <div className="space-y-1 text-sm text-dark-400">
                      <p>Quantidade: {comp.quantidade} • Período: {formatDate(comp.data_inicio)} a {formatDate(comp.data_fim)}</p>
                      {comp.contratante && <p>Contratante: {comp.contratante}</p>}
                      {comp.cidade && comp.uf && <p><MapPin size={12} className="inline" /> {comp.cidade} - {comp.uf}</p>}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-dark-500 text-sm">Nenhum compromisso inicia neste dia.</p>
              )}
            </div>

            {/* Compromissos ativos neste dia */}
            <div className="space-y-3 pt-2 border-t border-dark-700">
              <h4 className="text-sm font-semibold text-dark-200 flex items-center gap-2">
                <Calendar size={16} /> Compromissos ativos neste dia ({detalhesDia.compromissosAtivos?.length || 0})
              </h4>
              {detalhesDia.compromissosAtivos?.length > 0 ? (
                detalhesDia.compromissosAtivos.map(comp => (
                  <div key={comp.id} className="p-4 bg-dark-700/50 rounded-lg border border-dark-700">
                    <h5 className="font-semibold text-dark-50 mb-2">{formatItemName(comp.item) || 'Item Deletado'}</h5>
                    <div className="space-y-1 text-sm text-dark-400">
                      <p>Quantidade: {comp.quantidade} • Período: {formatDate(comp.data_inicio)} a {formatDate(comp.data_fim)}</p>
                      {comp.contratante && <p>Contratante: {comp.contratante}</p>}
                      {comp.cidade && comp.uf && <p><MapPin size={12} className="inline" /> {comp.cidade} - {comp.uf}</p>}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-dark-500 text-sm">Nenhum compromisso ativo neste dia.</p>
              )}
            </div>

            {/* Parcelas (boletos) – mesmo layout do olhinho do financiamento */}
            <div className="space-y-3 pt-2 border-t border-dark-700">
              <h4 className="text-sm font-semibold text-dark-200 flex items-center gap-2">
                <FileText size={16} /> Parcelas (boletos) com vencimento neste dia
              </h4>
              {detalhesDia.loadingParcelas ? (
                <p className="text-dark-400 text-center py-4">Carregando parcelas...</p>
              ) : detalhesDia.parcelas?.length > 0 ? (
                <div className="overflow-x-auto -mx-1">
                  <table className="w-full text-base min-w-[720px]">
                    <thead>
                      <tr className="border-b-2 border-dark-600">
                        <th className="text-left py-3 px-3 text-dark-300 font-semibold">Contrato</th>
                        <th className="text-left py-3 px-3 text-dark-300 font-semibold">Parc.</th>
                        <th className="text-left py-3 px-3 text-dark-300 font-semibold">Vencimento</th>
                        <th className="text-right py-3 px-3 text-dark-300 font-semibold">Valor</th>
                        <th className="text-right py-3 px-3 text-dark-300 font-semibold">Pago</th>
                        <th className="text-left py-3 px-3 text-dark-300 font-semibold">Status</th>
                        <th className="text-left py-3 px-3 text-dark-300 font-semibold">Boleto</th>
                        <th className="text-left py-3 px-3 text-dark-300 font-semibold">Comprov.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detalhesDia.parcelas.map((p) => {
                        const StatusIcon = p.status === 'Paga' ? CheckCircle : p.status === 'Atrasada' ? AlertCircle : Clock
                        const statusColor = p.status === 'Paga' ? 'text-green-400' : p.status === 'Atrasada' ? 'text-red-400' : 'text-yellow-400'
                        const codigo = (p.codigo_contrato && String(p.codigo_contrato).trim()) || `Financiamento #${p.financiamento_id}`
                        return (
                          <tr key={p.id} className="border-b border-dark-700/50 hover:bg-dark-700/30">
                            <td className="py-3 px-3 text-dark-50 font-medium break-words min-w-[100px]" title={codigo}>{codigo}</td>
                            <td className="py-3 px-3 text-dark-50">{p.numero_parcela}</td>
                            <td className="py-3 px-3 text-dark-400 whitespace-nowrap">{formatDate(p.data_vencimento)}</td>
                            <td className="py-3 px-3 text-right text-dark-50 font-medium whitespace-nowrap">{formatCurrency(p.valor_original)}</td>
                            <td className="py-3 px-3 text-right text-dark-400 whitespace-nowrap">{formatCurrency(p.valor_pago)}</td>
                            <td className="py-3 px-3">
                              <span className={`inline-flex items-center gap-1.5 ${statusColor}`}>
                                <StatusIcon size={16} />
                                {p.status}
                              </span>
                            </td>
                            <td className="py-3 px-3">
                              {p.link_boleto ? (
                                <a href={p.link_boleto} target="_blank" rel="noreferrer" className="text-primary-400 hover:text-primary-300 inline-flex items-center gap-1">
                                  <ExternalLink size={16} /> Boleto
                                </a>
                              ) : (
                                <span className="text-dark-500">—</span>
                              )}
                            </td>
                            <td className="py-3 px-3">
                              {p.link_comprovante ? (
                                <a href={p.link_comprovante} target="_blank" rel="noreferrer" className="text-green-400 hover:text-green-300 inline-flex items-center gap-1">
                                  <ExternalLink size={16} /> Comprov.
                                </a>
                              ) : (
                                <span className="text-dark-500">—</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-dark-500 text-sm">Nenhuma parcela vence neste dia.</p>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
