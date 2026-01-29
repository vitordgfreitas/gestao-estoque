import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { compromissosAPI, itensAPI, categoriasAPI } from '../services/api'
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, MapPin, Package } from 'lucide-react'
import toast from 'react-hot-toast'
import Modal from '../components/Modal'

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
      toast.error('Erro ao carregar dados')
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
              const hoje = new Date()
              const isHoje = dataAtual.toDateString() === hoje.toDateString()
              const compsDia = compromissosPorData(dataAtual)
              const numComps = compsDia.length

              return (
                <button
                  key={`${semanaIdx}-${diaIdx}`}
                  onClick={() => {
                    if (numComps > 0) {
                      setDetalhesDia({ data: dataAtual, compromissos: compsDia })
                    }
                  }}
                  className={`aspect-square p-2 rounded-lg border transition-colors ${
                    isHoje
                      ? 'bg-primary-600 border-primary-500 text-white'
                      : numComps > 0
                      ? 'bg-primary-600/20 border-primary-600/30 hover:bg-primary-600/30'
                      : 'bg-dark-800 border-dark-700 hover:bg-dark-700'
                  }`}
                >
                  <div className="flex flex-col h-full">
                    <span className={`text-sm font-medium ${isHoje ? 'text-white' : 'text-dark-50'}`}>
                      {dia}
                    </span>
                    {numComps > 0 && (
                      <span className={`text-xs mt-auto ${isHoje ? 'text-white/80' : 'text-primary-400'}`}>
                        {numComps} comp{numComps > 1 ? 's' : ''}
                      </span>
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
            {semanaInicio.toLocaleDateString('pt-BR')} - {semanaFim.toLocaleDateString('pt-BR')}
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
            const compsDia = compromissosPorData(dia)
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
                    {diasSemana[idx]} - {dia.toLocaleDateString('pt-BR')}
                  </h4>
                  {compsDia.length > 0 && (
                    <span className="text-sm text-primary-400">
                      {compsDia.length} compromisso{compsDia.length > 1 ? 's' : ''}
                    </span>
                  )}
                </div>

                {compsDia.length > 0 ? (
                  <div className="space-y-2">
                    {compsDia.map(comp => (
                      <div
                        key={comp.id}
                        onClick={() => setDetalhesDia({ data: dia, compromissos: [comp] })}
                        className="p-3 bg-dark-700/50 rounded-lg hover:bg-dark-700 cursor-pointer transition-colors"
                      >
                        <p className="font-medium text-dark-50">{comp.item?.nome || 'Item Deletado'}</p>
                        <p className="text-sm text-dark-400">
                          {comp.quantidade} unidades • {comp.contratante || 'Sem contratante'}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-dark-400">Nenhum compromisso neste dia.</p>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const renderCalendarioDiario = () => {
    const compsDia = compromissosPorData(diaSelecionado)
    const hoje = new Date()
    const isHoje = diaSelecionado.toDateString() === hoje.toDateString()

    const diasSemana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    const diaSemanaNome = diasSemana[diaSelecionado.getDay()]

    return (
      <div className="space-y-4">
        {/* Navegação do dia */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navegarDia('anterior')}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <ChevronLeft className="text-dark-400" size={20} />
          </button>
          <h3 className={`text-xl font-semibold ${isHoje ? 'text-primary-400' : 'text-dark-50'}`}>
            {diaSemanaNome} - {diaSelecionado.toLocaleDateString('pt-BR')}
            {isHoje && ' (Hoje)'}
          </h3>
          <button
            onClick={() => navegarDia('proximo')}
            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
          >
            <ChevronRight className="text-dark-400" size={20} />
          </button>
        </div>

        {/* Compromissos do dia */}
        {compsDia.length > 0 ? (
          <div className="space-y-3">
            {compsDia.map(comp => (
              <div
                key={comp.id}
                onClick={() => setDetalhesDia({ data: diaSelecionado, compromissos: [comp] })}
                className="p-4 bg-dark-800 border border-dark-700 rounded-lg hover:border-primary-600/50 cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-dark-50 mb-2">
                      {comp.item?.nome || 'Item Deletado'}
                    </h4>
                    <div className="space-y-1 text-sm text-dark-400">
                      <p>Quantidade: {comp.quantidade} unidades</p>
                      <p>
                        Período: {new Date(comp.data_inicio).toLocaleDateString('pt-BR')} a{' '}
                        {new Date(comp.data_fim).toLocaleDateString('pt-BR')}
                      </p>
                      {comp.descricao && <p>Descrição: {comp.descricao}</p>}
                      {comp.contratante && <p>Contratante: {comp.contratante}</p>}
                      {comp.cidade && comp.uf && (
                        <div className="flex items-center gap-1 mt-2">
                          <MapPin size={14} />
                          <span>{comp.cidade} - {comp.uf}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-dark-400">
            <CalendarIcon className="mx-auto mb-3 opacity-50" size={48} />
            <p>Nenhum compromisso neste dia.</p>
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
            <div className="flex gap-2">
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

      {/* Modal de detalhes */}
      {detalhesDia && (
        <Modal
          isOpen={!!detalhesDia}
          onClose={() => setDetalhesDia(null)}
          title={`Compromissos em ${detalhesDia.data.toLocaleDateString('pt-BR')}`}
        >
          <div className="space-y-4">
            {detalhesDia.compromissos.length > 0 ? (
              detalhesDia.compromissos.map(comp => (
                <div key={comp.id} className="p-4 bg-dark-700/50 rounded-lg border border-dark-700">
                  <h4 className="font-semibold text-dark-50 mb-3">
                    {comp.item?.nome || 'Item Deletado'}
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-dark-400">Quantidade:</span>
                      <span className="text-dark-50 font-medium">{comp.quantidade} unidades</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-400">Período:</span>
                      <span className="text-dark-50">
                        {new Date(comp.data_inicio).toLocaleDateString('pt-BR')} a{' '}
                        {new Date(comp.data_fim).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                    {comp.descricao && (
                      <div>
                        <span className="text-dark-400">Descrição:</span>
                        <p className="text-dark-50 mt-1">{comp.descricao}</p>
                      </div>
                    )}
                    {comp.contratante && (
                      <div className="flex justify-between">
                        <span className="text-dark-400">Contratante:</span>
                        <span className="text-dark-50">{comp.contratante}</span>
                      </div>
                    )}
                    {comp.cidade && comp.uf && (
                      <div className="flex items-center gap-2 mt-2">
                        <MapPin size={14} className="text-dark-400" />
                        <span className="text-dark-400">{comp.cidade} - {comp.uf}</span>
                        {comp.endereco && (
                          <span className="text-dark-400">({comp.endereco})</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-dark-400 text-center py-8">Nenhum compromisso neste dia.</p>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}
